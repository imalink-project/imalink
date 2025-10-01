"""
Selections API for ImaLink

Provides REST endpoints for managing and executing Selections:
- CRUD operations for saved selections
- Execution of all selection types (saved, algorithmic, manual)
- Smart suggestions for new selections
- Sharing and collaboration features
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database.connection import get_db
from database.models import Selection, Image
from services.selection_service import SelectionService


router = APIRouter(tags=["selections"])
selection_service = SelectionService()


# === Pydantic Models ===

class SelectionBase(BaseModel):
    name: str
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None


class SelectionCreate(SelectionBase):
    is_algorithmic: bool = False  # True for algorithmic, False for criteria-based
    search_criteria: Optional[Dict[str, Any]] = None  # Used when is_algorithmic=False
    algorithm_type: Optional[str] = None  # Used when is_algorithmic=True
    algorithm_params: Optional[Dict[str, Any]] = None  # Used when is_algorithmic=True
    is_favorite: bool = False
    is_public: bool = False
    sort_order: int = 0
    parent_selection_id: Optional[int] = None  # For cascading selections


class SelectionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    is_algorithmic: Optional[bool] = None
    search_criteria: Optional[Dict[str, Any]] = None
    algorithm_type: Optional[str] = None
    algorithm_params: Optional[Dict[str, Any]] = None
    parent_selection_id: Optional[int] = None
    icon: Optional[str] = None
    search_criteria: Optional[Dict[str, Any]] = None
    image_list: Optional[List[int]] = None
    algorithm_params: Optional[Dict[str, Any]] = None
    is_favorite: Optional[bool] = None
    is_public: Optional[bool] = None
    sort_order: Optional[int] = None


class SelectionResponse(SelectionBase):
    id: int
    is_algorithmic: bool
    search_criteria: Optional[str] = None  # JSON string for criteria
    algorithm_type: Optional[str] = None
    algorithm_params: Optional[str] = None  # JSON string for algorithm config
    parent_selection_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    last_accessed: Optional[datetime] = None
    access_count: int
    is_favorite: bool
    is_public: bool
    sort_order: int
    created_by: Optional[str] = None
    
    class Config:
        from_attributes = True


class SelectionExecutionResult(BaseModel):
    selection_id: int
    selection_name: str
    images: List[Dict[str, Any]]  # Will be populated with image data
    total_count: int
    page: int
    page_size: int
    has_next: bool
    execution_time_ms: float


class AlgorithmicSelectionPreview(BaseModel):
    algorithm_type: str
    name: str
    description: str
    params: Dict[str, Any]
    preview_count: int
    icon: Optional[str] = None


# === API Endpoints ===

@router.get("/", response_model=List[SelectionResponse])
async def list_selections(
    include_algorithmic: bool = Query(True, description="Include algorithmic selections"),
    favorites_only: bool = Query(False, description="Show only favorites"),
    db: Session = Depends(get_db)
):
    """List all selections"""
    selections = selection_service.list_selections(db, include_algorithmic=include_algorithmic)
    
    if favorites_only:
        selections = [s for s in selections if getattr(s, 'is_favorite', False)]
    
    return selections


@router.get("/{selection_id}", response_model=SelectionResponse)
async def get_selection(selection_id: int, db: Session = Depends(get_db)):
    """Get selection by ID"""
    selection = selection_service.get_selection(db, selection_id)
    if not selection:
        raise HTTPException(status_code=404, detail="Selection not found")
    return selection


@router.post("/", response_model=SelectionResponse)
async def create_selection(selection_data: SelectionCreate, db: Session = Depends(get_db)):
    """Create a new selection"""
    try:
        selection = selection_service.create_selection(
            db=db,
            name=selection_data.name,
            is_algorithmic=selection_data.is_algorithmic,
            description=selection_data.description,
            color=selection_data.color,
            icon=selection_data.icon,
            search_criteria=selection_data.search_criteria,
            algorithm_type=selection_data.algorithm_type,
            algorithm_params=selection_data.algorithm_params,
            is_favorite=selection_data.is_favorite,
            is_public=selection_data.is_public,
            sort_order=selection_data.sort_order,
            parent_selection_id=selection_data.parent_selection_id
        )
        return selection
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create selection: {str(e)}")


@router.put("/{selection_id}", response_model=SelectionResponse)
async def update_selection(
    selection_id: int, 
    selection_update: SelectionUpdate, 
    db: Session = Depends(get_db)
):
    """Update a selection"""
    selection = selection_service.get_selection(db, selection_id)
    if not selection:
        raise HTTPException(status_code=404, detail="Selection not found")
    
    # Update fields that were provided
    update_data = selection_update.dict(exclude_unset=True)
    update_dict = {}
    
    for field, value in update_data.items():
        if field in ['search_criteria', 'image_list', 'algorithm_params'] and value is not None:
            # Convert to JSON string for database storage
            update_dict[field] = json.dumps(value)
        else:
            update_dict[field] = value
    
    # Add updated_at timestamp
    update_dict['updated_at'] = datetime.utcnow()
    
    # Update using SQLAlchemy update method
    db.query(Selection).filter(Selection.id == selection_id).update(update_dict)
    db.commit()
    
    # Refresh the object
    selection = selection_service.get_selection(db, selection_id)
    
    return selection


@router.delete("/{selection_id}")
async def delete_selection(selection_id: int, db: Session = Depends(get_db)):
    """Delete a selection"""
    success = selection_service.delete_selection(db, selection_id)
    if not success:
        raise HTTPException(status_code=404, detail="Selection not found")
    return {"message": "Selection deleted successfully"}


@router.post("/{selection_id}/execute", response_model=SelectionExecutionResult)
async def execute_selection(
    selection_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    db: Session = Depends(get_db)
):
    """Execute a selection and return matching images"""
    selection = selection_service.get_selection(db, selection_id)
    if not selection:
        raise HTTPException(status_code=404, detail="Selection not found")
    
    start_time = datetime.now()
    
    # Calculate offset
    offset = (page - 1) * page_size
    
    # Execute selection
    images, total_count = selection_service.execute_selection(db, selection, page_size, offset)
    
    # Calculate execution time
    execution_time = (datetime.now() - start_time).total_seconds() * 1000
    
    # Convert images to dict format
    image_data = []
    for img in images:
        # Use getattr to safely access SQLAlchemy attributes
        file_path = getattr(img, 'file_path', None)
        taken_at = getattr(img, 'taken_at', None)
        created_at = getattr(img, 'created_at', None)
        
        image_dict = {
            "id": getattr(img, 'id', None),
            "image_hash": getattr(img, 'image_hash', None),
            "original_filename": getattr(img, 'original_filename', None),
            "file_path": str(file_path) if file_path is not None else None,
            "file_size": getattr(img, 'file_size', None),
            "file_format": getattr(img, 'file_format', None),
            "width": getattr(img, 'width', None),
            "height": getattr(img, 'height', None),
            "taken_at": taken_at.isoformat() if taken_at is not None else None,
            "created_at": created_at.isoformat() if created_at is not None else None,
            "rating": getattr(img, 'rating', None),
            "user_rotation": getattr(img, 'user_rotation', None),
            "gps_latitude": getattr(img, 'gps_latitude', None),
            "gps_longitude": getattr(img, 'gps_longitude', None),
            "author_id": getattr(img, 'author_id', None),
            "import_source": getattr(img, 'import_source', None)
        }
        image_data.append(image_dict)
    
    return SelectionExecutionResult(
        selection_id=selection_id,
        selection_name=getattr(selection, 'name', 'Unknown'),
        images=image_data,
        total_count=total_count,
        page=page,
        page_size=page_size,
        has_next=total_count > (page * page_size),
        execution_time_ms=execution_time
    )


@router.get("/algorithmic/preview", response_model=List[AlgorithmicSelectionPreview])
async def get_algorithmic_previews(db: Session = Depends(get_db)):
    """Get preview of available algorithmic selections"""
    current_date = datetime.now()
    
    previews = [
        AlgorithmicSelectionPreview(
            algorithm_type="recent",
            name="Nylige bilder",
            description="Bilder fra de siste 30 dagene",
            params={"days": 30},
            preview_count=0,  # Will be calculated
            icon="📅"
        ),
        AlgorithmicSelectionPreview(
            algorithm_type="memories",
            name="På denne dagen",
            description=f"Bilder fra {current_date.strftime('%d. %B')} tidligere år",
            params={"date": current_date.isoformat()},
            preview_count=0,
            icon="💭"
        ),
        AlgorithmicSelectionPreview(
            algorithm_type="yearly",
            name=f"Året {current_date.year}",
            description=f"Alle bilder fra {current_date.year}",
            params={"year": current_date.year},
            preview_count=0,
            icon="📆"
        ),
        AlgorithmicSelectionPreview(
            algorithm_type="monthly",
            name=current_date.strftime("%B %Y"),
            description=f"Bilder fra {current_date.strftime('%B %Y')}",
            params={"date": current_date.isoformat()},
            preview_count=0,
            icon="🗓️"
        ),
        AlgorithmicSelectionPreview(
            algorithm_type="top_rated",
            name="Favorittbilder",
            description="Bilder med rating 4-5 stjerner",
            params={"min_rating": 4},
            preview_count=0,
            icon="⭐"
        )
    ]
    
    # Calculate preview counts for each
    for preview in previews:
        # Create temporary selection to get count
        temp_selection = Selection(
            name=preview.name,
            selection_type='algorithmic',
            algorithm_type=preview.algorithm_type,
            algorithm_params=json.dumps(preview.params) if preview.params else '{}'
        )
        
        images, count = selection_service.execute_selection(db, temp_selection, limit=1, offset=0)
        preview.preview_count = count
    
    return previews


@router.post("/algorithmic/create", response_model=SelectionResponse)
async def create_algorithmic_selection(
    algorithm_type: str,
    params: Dict[str, Any],
    name: Optional[str] = None,
    save_to_database: bool = Query(False, description="Save as permanent selection"),
    db: Session = Depends(get_db)
):
    """Create and optionally save an algorithmic selection"""
    
    # Generate name if not provided
    if not name:
        if algorithm_type == "recent":
            name = f"Nylige bilder ({params.get('days', 30)} dager)"
        elif algorithm_type == "memories":
            date_str = datetime.fromisoformat(params.get('date', datetime.now().isoformat())).strftime('%d. %B')
            name = f"På denne dagen - {date_str}"
        elif algorithm_type == "yearly":
            name = f"Året {params.get('year', datetime.now().year)}"
        elif algorithm_type == "monthly":
            date = datetime.fromisoformat(params.get('date', datetime.now().isoformat()))
            name = date.strftime('%B %Y')
        else:
            name = f"{algorithm_type.replace('_', ' ').title()} Selection"
    
    if save_to_database:
        # Save as permanent selection
        selection = selection_service.create_selection(
            db=db,
            name=name,
            is_algorithmic=True,
            algorithm_type=algorithm_type,
            algorithm_params=params,
            description=f"Algoritmisk selection: {algorithm_type}"
        )
        return selection
    else:
        # Return temporary selection (not saved)
        return SelectionResponse(
            id=-1,  # Temporary ID
            name=name,
            is_algorithmic=True,
            algorithm_type=algorithm_type,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            access_count=0,
            is_favorite=False,
            is_public=False,
            sort_order=0
        )


@router.get("/suggestions", response_model=List[Dict[str, Any]])
async def get_selection_suggestions(
    limit: int = Query(10, ge=1, le=50, description="Number of suggestions to return"),
    db: Session = Depends(get_db)
):
    """Get smart suggestions for new selections"""
    return selection_service.suggest_selections(db, limit=limit)


@router.post("/{selection_id}/add-images")
async def add_images_to_manual_selection(
    selection_id: int,
    image_ids: List[int],
    db: Session = Depends(get_db)
):
    """Add images to a manual selection"""
    selection = selection_service.get_selection(db, selection_id)
    if not selection:
        raise HTTPException(status_code=404, detail="Selection not found")
    
    if getattr(selection, 'selection_type', None) != 'manual':
        raise HTTPException(status_code=400, detail="Can only add images to manual selections")
    
    # Get current image list
    current_list = json.loads(getattr(selection, 'image_list', None) or '[]')
    
    # Add new images (avoiding duplicates)
    for img_id in image_ids:
        if img_id not in current_list:
            current_list.append(img_id)
    
    # Update selection
    db.query(Selection).filter(Selection.id == selection_id).update({
        Selection.image_list: json.dumps(current_list),
        Selection.updated_at: datetime.utcnow()
    })
    db.commit()
    
    return {"message": f"Added {len(image_ids)} images to selection", "total_images": len(current_list)}


@router.delete("/{selection_id}/remove-images")
async def remove_images_from_manual_selection(
    selection_id: int,
    image_ids: List[int],
    db: Session = Depends(get_db)
):
    """Remove images from a manual selection"""
    selection = selection_service.get_selection(db, selection_id)
    if not selection:
        raise HTTPException(status_code=404, detail="Selection not found")
    
    if getattr(selection, 'selection_type', None) != 'manual':
        raise HTTPException(status_code=400, detail="Can only remove images from manual selections")
    
    # Get current image list
    current_list = json.loads(getattr(selection, 'image_list', None) or '[]')
    
    # Remove images
    removed_count = 0
    for img_id in image_ids:
        if img_id in current_list:
            current_list.remove(img_id)
            removed_count += 1
    
    # Update selection
    db.query(Selection).filter(Selection.id == selection_id).update({
        Selection.image_list: json.dumps(current_list),
        Selection.updated_at: datetime.utcnow()
    })
    db.commit()
    
    return {"message": f"Removed {removed_count} images from selection", "total_images": len(current_list)}


@router.get("/available-parents", response_model=List[SelectionResponse])
async def get_available_parent_selections(
    request: Request,
    db: Session = Depends(get_db)
):
    """Get list of selections that can be used as parent selections for cascading"""
    query = db.query(Selection)
    
    # Get exclude_id from query params if present, ignore other params
    exclude_id = request.query_params.get('exclude_id')
    if exclude_id:
        try:
            exclude_id_int = int(exclude_id)
            query = query.filter(Selection.id != exclude_id_int)
        except (ValueError, TypeError):
            # If exclude_id is not a valid integer, just ignore it
            pass
    
    # Order by name for easy selection
    selections = query.order_by(Selection.name).all()
    
    return selections


@router.get("/{selection_id}/hierarchy", response_model=Dict[str, Any])
async def get_selection_hierarchy(selection_id: int, db: Session = Depends(get_db)):
    """Get the full hierarchy chain for a selection (useful for debugging cascades)"""
    selection = selection_service.get_selection(db, selection_id)
    if not selection:
        raise HTTPException(status_code=404, detail="Selection not found")
    
    # Build hierarchy chain from root to current selection
    hierarchy = []
    current = selection
    
    while current:
        hierarchy.insert(0, {
            "id": getattr(current, 'id', None),
            "name": getattr(current, 'name', ''),
            "selection_type": getattr(current, 'selection_type', ''),
            "parent_selection_id": getattr(current, 'parent_selection_id', None)
        })
        
        parent_id = getattr(current, 'parent_selection_id', None)
        if parent_id:
            current = db.query(Selection).filter(Selection.id == parent_id).first()
        else:
            current = None
    
    # Get child selections
    children = db.query(Selection).filter(Selection.parent_selection_id == selection_id).all()
    child_list = [{
        "id": getattr(child, 'id', None),
        "name": getattr(child, 'name', ''),
        "selection_type": getattr(child, 'selection_type', '')
    } for child in children]
    
    return {
        "selection_id": selection_id,
        "hierarchy_chain": hierarchy,
        "children": child_list,
        "depth": len(hierarchy)
    }