"""
Selection Service for ImaLink

Handles three types of selections:
1. Saved - Database-stored search criteria that dynamically update
2. Algorithmic - Runtime-generated based on temporal/contextual algorithms  
3. Manual - Explicit lists of manually chosen images

This service implements the core philosophy that Selections are more powerful
than traditional albums because they can be dynamic, temporal, and contextual.
"""
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc

from database.models import Selection, Image, Author


class SelectionService:
    """
    Core service for managing and executing Selections
    """
    
    def __init__(self):
        self.algorithmic_generators = {
            'daily': self._generate_daily,
            'weekly': self._generate_weekly,
            'monthly': self._generate_monthly,
            'yearly': self._generate_yearly,
            'seasonal': self._generate_seasonal,
            'camera': self._generate_by_camera,
            'location': self._generate_by_location,
            'memories': self._generate_memories,  # Same date previous years
            'recent': self._generate_recent,
            'top_rated': self._generate_top_rated
        }

    # === CRUD Operations ===
    
    def create_selection(self, db: Session, name: str, is_algorithmic: bool = False, **kwargs) -> Selection:
        """Create a new selection - either criteria-based or algorithmic"""
        
        # Prepare search criteria (includes manual image lists)
        search_criteria = kwargs.get('search_criteria')
        if kwargs.get('image_list'):  # Manual selection becomes search criteria
            if not search_criteria:
                search_criteria = {}
            search_criteria['image_ids'] = kwargs.get('image_list')
        
        selection = Selection(
            name=name,
            is_algorithmic=is_algorithmic,
            description=kwargs.get('description'),
            color=kwargs.get('color'),
            parent_selection_id=kwargs.get('parent_selection_id'),
            icon=kwargs.get('icon'),
            search_criteria=json.dumps(search_criteria) if search_criteria else None,
            algorithm_type=kwargs.get('algorithm_type') if is_algorithmic else None,
            algorithm_params=json.dumps(kwargs.get('algorithm_params', {})) if is_algorithmic and kwargs.get('algorithm_params') else None,
            is_favorite=kwargs.get('is_favorite', False),
            is_public=kwargs.get('is_public', False),
            sort_order=kwargs.get('sort_order', 0)
        )
        
        db.add(selection)
        db.commit()
        db.refresh(selection)
        return selection

    def get_selection(self, db: Session, selection_id: int) -> Optional[Selection]:
        """Get selection by ID and update access tracking"""
        selection = db.query(Selection).filter(Selection.id == selection_id).first()
        if selection:
            # Update access tracking
            db.query(Selection).filter(Selection.id == selection_id).update({
                Selection.last_accessed: datetime.utcnow(),
                Selection.access_count: Selection.access_count + 1
            })
            db.commit()
            db.refresh(selection)
        return selection

    def list_selections(self, db: Session, include_algorithmic: bool = True) -> List[Selection]:
        """List all selections with optional algorithmic ones"""
        query = db.query(Selection)
        
        if not include_algorithmic:
            query = query.filter(Selection.is_algorithmic == False)
            
        return query.order_by(Selection.is_favorite.desc(), Selection.sort_order, Selection.name).all()

    def delete_selection(self, db: Session, selection_id: int) -> bool:
        """Delete a selection"""
        selection = db.query(Selection).filter(Selection.id == selection_id).first()
        if selection:
            db.delete(selection)
            db.commit()
            return True
        return False

    # === Core Execution ===
    
    def execute_selection(self, db: Session, selection: Selection, 
                         limit: Optional[int] = None, offset: int = 0) -> Tuple[List[Image], int]:
        """
        Execute a selection and return matching images + total count
        Supports cascading: if selection has parent, filter results through parent first
        Returns (images, total_count)
        """
        # Handle cascading: if this selection has a parent, execute parent first
        base_image_ids = None
        parent_id = getattr(selection, 'parent_selection_id', None)
        
        if parent_id:
            parent_selection = db.query(Selection).filter(Selection.id == parent_id).first()
            if parent_selection:
                # Execute parent selection to get base set of images
                parent_images, _ = self.execute_selection(db, parent_selection)
                base_image_ids = [getattr(img, 'id', 0) for img in parent_images]
                
                # If parent returns no results, child will also be empty
                if not base_image_ids:
                    return [], 0
        
        # Execute this selection with optional base set constraint
        is_algorithmic = getattr(selection, 'is_algorithmic', False)
        if is_algorithmic:
            return self._execute_algorithmic_selection(db, selection, limit, offset, base_image_ids)
        else:
            return self._execute_criteria_selection(db, selection, limit, offset, base_image_ids)

    def _execute_criteria_selection(self, db: Session, selection: Selection, 
                                   limit: Optional[int], offset: int, base_image_ids: Optional[List[int]] = None) -> Tuple[List[Image], int]:
        """Execute selection with search criteria (includes manual image lists)"""
        search_criteria_str = getattr(selection, 'search_criteria', None)
        if not search_criteria_str:
            return [], 0
            
        criteria = json.loads(search_criteria_str)
        
        # Handle manual selection (image_ids in criteria)
        if 'image_ids' in criteria:
            return self._execute_manual_from_criteria(db, criteria['image_ids'], limit, offset, base_image_ids)
        
        # Handle regular criteria-based selection
        query = db.query(Image)
        
        # Apply cascading constraint if parent selection provided base set
        if base_image_ids is not None:
            query = query.filter(Image.id.in_(base_image_ids))
        
        # Apply search criteria
        query = self._apply_search_criteria(query, criteria)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        if offset > 0:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
            
        images = query.all()
        return images, total_count
    
    def _execute_manual_from_criteria(self, db: Session, image_ids: List[int], 
                                     limit: Optional[int], offset: int, base_image_ids: Optional[List[int]] = None) -> Tuple[List[Image], int]:
        """Execute manual selection from image_ids in criteria"""
        # Apply cascading constraint if parent selection provided base set
        if base_image_ids is not None:
            # Filter manual list to only include images that are in parent's result set
            image_ids = [img_id for img_id in image_ids if img_id in base_image_ids]
        
        total_count = len(image_ids)
        
        # Apply pagination to ID list
        paginated_ids = image_ids[offset:offset + limit if limit else None]
        
        if not paginated_ids:
            return [], total_count
            
        # Fetch images maintaining order
        images = []
        for img_id in paginated_ids:
            image = db.query(Image).filter(Image.id == img_id).first()
            if image:
                images.append(image)
                
        return images, total_count

    def _execute_algorithmic_selection(self, db: Session, selection: Selection,
                                     limit: Optional[int], offset: int, base_image_ids: Optional[List[int]] = None) -> Tuple[List[Image], int]:
        """Execute algorithmic selection using generator functions"""
        algo_type = getattr(selection, 'algorithm_type', None)
        if not algo_type or algo_type not in self.algorithmic_generators:
            return [], 0
            
        algo_params = getattr(selection, 'algorithm_params', None) or '{}'
        params = json.loads(algo_params)
        generator_func = self.algorithmic_generators[algo_type]
        
        return generator_func(db, params, limit, offset, base_image_ids)

    def _execute_manual_selection(self, db: Session, selection: Selection,
                                 limit: Optional[int], offset: int, base_image_ids: Optional[List[int]] = None) -> Tuple[List[Image], int]:
        """Execute manual selection from explicit image list"""
        image_list_str = getattr(selection, 'image_list', None)
        if not image_list_str:
            return [], 0
            
        image_ids = json.loads(image_list_str)
        
        # Apply cascading constraint if parent selection provided base set
        if base_image_ids is not None:
            # Filter manual list to only include images that are in parent's result set
            image_ids = [img_id for img_id in image_ids if img_id in base_image_ids]
        
        total_count = len(image_ids)
        
        # Apply pagination to ID list
        paginated_ids = image_ids[offset:offset + limit if limit else None]
        
        if not paginated_ids:
            return [], total_count
            
        # Fetch images maintaining order
        images = []
        for img_id in paginated_ids:
            image = db.query(Image).filter(Image.id == img_id).first()
            if image:
                images.append(image)
                
        return images, total_count

    # === Search Criteria Application ===
    
    def _apply_search_criteria(self, query, criteria: Dict[str, Any]):
        """Apply search criteria to image query"""
        
        # Date range
        if criteria.get('date_from'):
            query = query.filter(Image.taken_at >= criteria['date_from'])
        if criteria.get('date_to'):
            query = query.filter(Image.taken_at <= criteria['date_to'])
            
        # Filename search
        if criteria.get('filename'):
            query = query.filter(Image.original_filename.ilike(f"%{criteria['filename']}%"))
            
        # File format
        if criteria.get('format'):
            formats = criteria['format'] if isinstance(criteria['format'], list) else [criteria['format']]
            query = query.filter(Image.file_format.in_(formats))
            
        # Author/photographer
        if criteria.get('author_id'):
            query = query.filter(Image.author_id == criteria['author_id'])
            
        # Rating
        if criteria.get('min_rating'):
            query = query.filter(Image.rating >= criteria['min_rating'])
        if criteria.get('max_rating'):
            query = query.filter(Image.rating <= criteria['max_rating'])
            
        # GPS coordinates (bounding box)
        if criteria.get('gps_bounds'):
            bounds = criteria['gps_bounds']  # {"north": lat, "south": lat, "east": lng, "west": lng}
            query = query.filter(
                and_(
                    Image.gps_latitude >= bounds['south'],
                    Image.gps_latitude <= bounds['north'],
                    Image.gps_longitude >= bounds['west'],
                    Image.gps_longitude <= bounds['east']
                )
            )
            
        # Dimensions
        if criteria.get('min_width'):
            query = query.filter(Image.width >= criteria['min_width'])
        if criteria.get('min_height'):
            query = query.filter(Image.height >= criteria['min_height'])
            
        # Tags (when implemented)
        if criteria.get('tags'):
            tags = criteria['tags'] if isinstance(criteria['tags'], list) else [criteria['tags']]
            # This will need updating when proper tag system is implemented
            for tag in tags:
                query = query.filter(Image.tags.ilike(f"%{tag}%"))
        
        # Sorting
        sort_by = criteria.get('sort_by', 'taken_at')
        sort_order = criteria.get('sort_order', 'desc')
        
        if hasattr(Image, sort_by):
            sort_column = getattr(Image, sort_by)
            if sort_order.lower() == 'asc':
                query = query.order_by(asc(sort_column))
            else:
                query = query.order_by(desc(sort_column))
        
        return query

    # === Algorithmic Generators ===
    
    def _generate_daily(self, db: Session, params: Dict, limit: Optional[int], offset: int, base_image_ids: Optional[List[int]] = None) -> Tuple[List[Image], int]:
        """Generate selection for specific day"""
        target_date = datetime.fromisoformat(params.get('date', datetime.now().isoformat()))
        start_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
        
        query = db.query(Image).filter(
            and_(Image.taken_at >= start_date, Image.taken_at < end_date)
        )
        
        # Apply cascading constraint if parent selection provided base set
        if base_image_ids is not None:
            query = query.filter(Image.id.in_(base_image_ids))
        
        query = query.order_by(desc(Image.taken_at))
        
        total_count = query.count()
        if offset > 0:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
            
        return query.all(), total_count

    def _generate_weekly(self, db: Session, params: Dict, limit: Optional[int], offset: int, base_image_ids: Optional[List[int]] = None) -> Tuple[List[Image], int]:
        """Generate selection for specific week"""
        target_date = datetime.fromisoformat(params.get('date', datetime.now().isoformat()))
        start_date = target_date - timedelta(days=target_date.weekday())
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=7)
        
        query = db.query(Image).filter(
            and_(Image.taken_at >= start_date, Image.taken_at < end_date)
        )
        
        # Apply cascading constraint if parent selection provided base set
        if base_image_ids is not None:
            query = query.filter(Image.id.in_(base_image_ids))
        
        query = query.order_by(desc(Image.taken_at))
        
        total_count = query.count()
        if offset > 0:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
            
        return query.all(), total_count

    def _generate_monthly(self, db: Session, params: Dict, limit: Optional[int], offset: int, base_image_ids: Optional[List[int]] = None) -> Tuple[List[Image], int]:
        """Generate selection for specific month"""
        target_date = datetime.fromisoformat(params.get('date', datetime.now().isoformat()))
        start_date = target_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Calculate next month
        if start_date.month == 12:
            end_date = start_date.replace(year=start_date.year + 1, month=1)
        else:
            end_date = start_date.replace(month=start_date.month + 1)
        
        query = db.query(Image).filter(
            and_(Image.taken_at >= start_date, Image.taken_at < end_date)
        )
        
        # Apply cascading constraint if parent selection provided base set
        if base_image_ids is not None:
            query = query.filter(Image.id.in_(base_image_ids))
        
        query = query.order_by(desc(Image.taken_at))
        
        total_count = query.count()
        if offset > 0:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
            
        return query.all(), total_count

    def _generate_yearly(self, db: Session, params: Dict, limit: Optional[int], offset: int, base_image_ids: Optional[List[int]] = None) -> Tuple[List[Image], int]:
        """Generate selection for specific year"""
        year = params.get('year', datetime.now().year)
        start_date = datetime(year, 1, 1)
        end_date = datetime(year + 1, 1, 1)
        
        query = db.query(Image).filter(
            and_(Image.taken_at >= start_date, Image.taken_at < end_date)
        )
        
        # Apply cascading constraint if parent selection provided base set
        if base_image_ids is not None:
            query = query.filter(Image.id.in_(base_image_ids))
        
        query = query.order_by(desc(Image.taken_at))
        
        total_count = query.count()
        if offset > 0:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
            
        return query.all(), total_count

    def _generate_memories(self, db: Session, params: Dict, limit: Optional[int], offset: int, base_image_ids: Optional[List[int]] = None) -> Tuple[List[Image], int]:
        """Generate 'On This Day' memories from previous years"""
        target_date = datetime.fromisoformat(params.get('date', datetime.now().isoformat()))
        
        # Look for images on this day in previous years (excluding current year)
        query = db.query(Image).filter(
            and_(
                func.extract('month', Image.taken_at) == target_date.month,
                func.extract('day', Image.taken_at) == target_date.day,
                func.extract('year', Image.taken_at) < target_date.year
            )
        )
        
        # Apply cascading constraint if parent selection provided base set
        if base_image_ids is not None:
            query = query.filter(Image.id.in_(base_image_ids))
        
        query = query.order_by(desc(Image.taken_at))
        
        total_count = query.count()
        if offset > 0:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
            
        return query.all(), total_count

    def _generate_recent(self, db: Session, params: Dict, limit: Optional[int], offset: int, base_image_ids: Optional[List[int]] = None) -> Tuple[List[Image], int]:
        """Generate recent images"""
        days_back = params.get('days', 30)
        since_date = datetime.now() - timedelta(days=days_back)
        
        query = db.query(Image).filter(
            Image.taken_at >= since_date
        )
        
        # Apply cascading constraint if parent selection provided base set
        if base_image_ids is not None:
            query = query.filter(Image.id.in_(base_image_ids))
        
        query = query.order_by(desc(Image.taken_at))
        
        total_count = query.count()
        if offset > 0:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
            
        return query.all(), total_count

    def _generate_top_rated(self, db: Session, params: Dict, limit: Optional[int], offset: int, base_image_ids: Optional[List[int]] = None) -> Tuple[List[Image], int]:
        """Generate top rated images"""
        min_rating = params.get('min_rating', 4)
        
        query = db.query(Image).filter(
            Image.rating >= min_rating
        )
        
        # Apply cascading constraint if parent selection provided base set
        if base_image_ids is not None:
            query = query.filter(Image.id.in_(base_image_ids))
        
        query = query.order_by(desc(Image.rating), desc(Image.taken_at))
        
        total_count = query.count()
        if offset > 0:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
            
        return query.all(), total_count

    # Additional generators can be added here
    def _generate_seasonal(self, db: Session, params: Dict, limit: Optional[int], offset: int, base_image_ids: Optional[List[int]] = None) -> Tuple[List[Image], int]:
        """Generate seasonal collections"""
        # Implementation for seasonal selections - placeholder
        return [], 0
        
    def _generate_by_camera(self, db: Session, params: Dict, limit: Optional[int], offset: int, base_image_ids: Optional[List[int]] = None) -> Tuple[List[Image], int]:
        """Generate by camera/lens combination"""  
        # Implementation for camera-specific selections - placeholder
        return [], 0
        
    def _generate_by_location(self, db: Session, params: Dict, limit: Optional[int], offset: int, base_image_ids: Optional[List[int]] = None) -> Tuple[List[Image], int]:
        """Generate by geographic location"""
        # Implementation for location-based selections - placeholder
        return [], 0

    # === Smart Suggestions ===
    
    def suggest_selections(self, db: Session, limit: int = 10) -> List[Dict]:
        """Suggest potential selections based on image analysis"""
        suggestions = []
        
        # Analyze existing images to suggest collections
        # This could be expanded with ML/AI in the future
        
        # Example: High-rated images from current year
        current_year = datetime.now().year
        high_rated_count = db.query(Image).filter(
            and_(
                Image.rating >= 4,
                func.extract('year', Image.taken_at) == current_year
            )
        ).count()
        
        if high_rated_count > 5:
            suggestions.append({
                'name': f'Årets høydepunkter ({current_year})',
                'description': f'{high_rated_count} bilder med høy rating fra i år',
                'icon': '⭐',
                'type': 'saved',
                'criteria': {
                    'min_rating': 4,
                    'date_from': f'{current_year}-01-01',
                    'date_to': f'{current_year}-12-31'
                }
            })
        
        return suggestions[:limit]