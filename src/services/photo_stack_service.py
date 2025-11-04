"""
PhotoStack Service - Business logic for PhotoStack operations
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from src.repositories.photo_stack_repository import PhotoStackRepository
from src.repositories.photo_repository import PhotoRepository
from src.core.exceptions import NotFoundError, ValidationError
from src.schemas.common import PaginatedResponse, PaginationMeta
from src.schemas.responses.photo_stack_responses import PhotoStackSummary


class PhotoStackService:
    """Service layer for PhotoStack operations with business logic"""
    
    def __init__(self, db: Session):
        self.db = db
        self.stack_repo = PhotoStackRepository(db)
        self.photo_repo = PhotoRepository(db)
    
    def get_stacks(
        self, 
        user_id: int,
        offset: int = 0, 
        limit: int = 100
    ) -> PaginatedResponse:
        """Get paginated list of photo stacks for user"""
        
        stacks = self.stack_repo.get_all(user_id, offset, limit)
        total = self.stack_repo.count_all(user_id)
        
        # Convert to response models
        stack_responses = []
        for stack in stacks:
            photo_count = self.stack_repo.get_photo_count(stack.id, user_id)  # type: ignore
            
            stack_responses.append({
                "id": stack.id,
                "cover_photo_hothash": stack.cover_photo_hothash,
                "stack_type": stack.stack_type,
                "photo_count": photo_count,
                "created_at": stack.created_at.isoformat(),
                "updated_at": stack.updated_at.isoformat()
            })
        
        # Calculate pagination metadata
        page = (offset // limit) + 1 if limit > 0 else 1
        total_pages = ((total - 1) // limit) + 1 if total > 0 and limit > 0 else 1
        
        return PaginatedResponse(
            data=stack_responses,
            meta=PaginationMeta(
                total=total,
                offset=offset,
                limit=limit,
                page=page,
                pages=total_pages
            ),
            links=None  # Can be added later for HATEOAS support
        )
    
    def get_stack_by_id(self, stack_id: int, user_id: int, include_photos: bool = False) -> dict:
        """Get specific stack by ID with optional photo details"""
        
        stack = self.stack_repo.get_by_id(stack_id, user_id)
        if not stack:
            raise NotFoundError("PhotoStack", stack_id)
        
        response = {
            "id": stack.id,
            "cover_photo_hothash": stack.cover_photo_hothash,
            "stack_type": stack.stack_type,
            "created_at": stack.created_at.isoformat(),
            "updated_at": stack.updated_at.isoformat()
        }
        
        if include_photos:
            photo_hothashes = self.stack_repo.get_photos_in_stack(stack_id, user_id)
            response["photo_hothashes"] = photo_hothashes
            response["photo_count"] = len(photo_hothashes)
        else:
            response["photo_count"] = self.stack_repo.get_photo_count(stack_id, user_id)
        
        return response
    
    def create_stack(self, stack_data: dict, user_id: int) -> dict:
        """Create new photo stack with validation"""
        
        # Validate stack type if provided
        if stack_data.get('stack_type'):
            self._validate_stack_type(stack_data['stack_type'])
        
        # Validate cover photo exists if provided
        if stack_data.get('cover_photo_hothash'):
            if not self._validate_photos_exist([stack_data['cover_photo_hothash']], user_id):
                raise ValidationError("Cover photo does not exist or is not accessible")
        
        # Create stack
        stack = self.stack_repo.create(stack_data, user_id)
        
        return self.get_stack_by_id(stack.id, user_id, include_photos=True)  # type: ignore
    
    def update_stack(self, stack_id: int, update_data: dict, user_id: int) -> dict:
        """Update existing stack"""
        
        # Check stack exists
        existing_stack = self.stack_repo.get_by_id(stack_id, user_id)
        if not existing_stack:
            raise NotFoundError("PhotoStack", stack_id)
        
        # Validate updates
        if 'stack_type' in update_data and update_data['stack_type']:
            self._validate_stack_type(update_data['stack_type'])
        
        # Validate cover photo exists if provided
        if 'cover_photo_hothash' in update_data and update_data['cover_photo_hothash']:
            if not self._validate_photos_exist([update_data['cover_photo_hothash']], user_id):
                raise ValidationError("Cover photo does not exist or is not accessible")
        
        # Update stack
        updated_stack = self.stack_repo.update(stack_id, update_data, user_id)
        if not updated_stack:
            raise NotFoundError("PhotoStack", stack_id)
        
        return self.get_stack_by_id(stack_id, user_id)
    
    def delete_stack(self, stack_id: int, user_id: int) -> bool:
        """Delete stack (photos remain untouched)"""
        
        success = self.stack_repo.delete(stack_id, user_id)
        if not success:
            raise NotFoundError("PhotoStack", stack_id)
        
        return True
    
    def add_photo_to_stack(self, stack_id: int, photo_hothash: str, user_id: int) -> dict:
        """Add a single photo to existing stack (moves photo from other stack if needed)"""
        
        # Check stack exists
        stack = self.stack_repo.get_by_id(stack_id, user_id)
        if not stack:
            raise NotFoundError("PhotoStack", stack_id)
        
        # Validate photo exists
        if not self._validate_photos_exist([photo_hothash], user_id):
            raise ValidationError("Photo does not exist or is not accessible")
        
        # Add photo
        success = self.stack_repo.add_photos(stack_id, [photo_hothash], user_id)
        if not success:
            raise ValidationError("Failed to add photo to stack")
        
        # Get updated stack details
        updated_stack = self.get_stack_by_id(stack_id, user_id, include_photos=True)
        
        return {
            "stack": updated_stack
        }
    
    def add_photos_to_stack(self, stack_id: int, photo_hothashes: List[str], user_id: int) -> dict:
        """Add photos to existing stack (moves photos from other stacks if needed)"""
        
        # Check stack exists
        stack = self.stack_repo.get_by_id(stack_id, user_id)
        if not stack:
            raise NotFoundError("PhotoStack", stack_id)
        
        # Get current photos to calculate how many are actually added
        current_photos = set(self.stack_repo.get_photos_in_stack(stack_id, user_id))
        
        # Validate photos exist
        if not self._validate_photos_exist(photo_hothashes, user_id):
            raise ValidationError("Some photos do not exist or are not accessible")
        
        # Add photos
        success = self.stack_repo.add_photos(stack_id, photo_hothashes, user_id)
        if not success:
            raise ValidationError("Failed to add photos to stack")
        
        # Calculate how many photos were actually added (excluding duplicates)
        new_photos = set(photo_hothashes)
        added_photos = new_photos - current_photos
        
        # Get updated stack details
        updated_stack = self.get_stack_by_id(stack_id, user_id, include_photos=True)
        
        return {
            "added_count": len(added_photos),
            "stack": updated_stack
        }
    
    def remove_photo_from_stack(self, stack_id: int, photo_hothash: str, user_id: int) -> dict:
        """Remove a single photo from stack (no automatic cleanup)"""
        
        # Check stack exists
        stack = self.stack_repo.get_by_id(stack_id, user_id)
        if not stack:
            raise NotFoundError("PhotoStack", stack_id)
        
        # Store current cover photo for comparison
        current_cover_photo = stack.cover_photo_hothash
        
        # Remove photo
        success = self.stack_repo.remove_photos(stack_id, [photo_hothash], user_id)
        if not success:
            raise ValidationError("Failed to remove photo from stack")
        
        # Handle cover photo removal - set new cover if removed photo was cover
        if current_cover_photo is not None and str(current_cover_photo) == photo_hothash:
            # Get remaining photos and set first one as new cover
            remaining_photos = self.stack_repo.get_photos_in_stack(stack_id, user_id)
            if remaining_photos:
                self.stack_repo.update(stack_id, {"cover_photo_hothash": remaining_photos[0]}, user_id)
            else:
                # No photos left, clear cover photo
                self.stack_repo.update(stack_id, {"cover_photo_hothash": None}, user_id)
        
        # Get updated stack details
        updated_stack = self.get_stack_by_id(stack_id, user_id, include_photos=True)
        
        return {
            "stack": updated_stack
        }
    
    def remove_photos_from_stack(self, stack_id: int, photo_hothashes: List[str], user_id: int) -> dict:
        """Remove photos from stack (no automatic cleanup)"""
        
        # Check stack exists
        stack = self.stack_repo.get_by_id(stack_id, user_id)
        if not stack:
            raise NotFoundError("PhotoStack", stack_id)
        
        # Check if cover photo is being removed
        cover_photo_removed = stack.cover_photo_hothash is not None and stack.cover_photo_hothash in photo_hothashes
        
        # Remove photos
        success = self.stack_repo.remove_photos(stack_id, photo_hothashes, user_id)
        if not success:
            raise ValidationError("Failed to remove photos from stack")
        
        # Handle cover photo removal
        if cover_photo_removed:
            # Get remaining photos and set first one as new cover
            remaining_photos = self.stack_repo.get_photos_in_stack(stack_id, user_id)
            new_cover = remaining_photos[0] if remaining_photos else None
            
            # Update stack with new cover photo
            update_data = {"cover_photo_hothash": new_cover}
            updated_stack = self.stack_repo.update(stack_id, update_data, user_id)
        
        # Return updated stack details
        final_stack = self.get_stack_by_id(stack_id, user_id, include_photos=True)
        
        return {
            "removed_count": len(photo_hothashes),
            "stack": final_stack
        }
    
    def get_photo_stack(self, photo_hothash: str, user_id: int) -> Optional[PhotoStackSummary]:
        """Get the stack containing a specific photo (one-to-many: max one stack per photo)"""
        
        stack = self.stack_repo.get_photo_stack(photo_hothash, user_id)
        
        if not stack:
            return None
        
        # Type assertion to help Pylance understand these are actual values, not Column objects
        stack_id: int = stack.id  # type: ignore
        stack_type: Optional[str] = stack.stack_type  # type: ignore
        cover_photo_hothash: Optional[str] = stack.cover_photo_hothash  # type: ignore
            
        photo_count = self.stack_repo.get_photo_count(stack_id, user_id)
        
        return PhotoStackSummary(
            id=stack_id,
            stack_type=stack_type,
            cover_photo_hothash=cover_photo_hothash,
            photo_count=photo_count,
            created_at=stack.created_at,
            updated_at=stack.updated_at
        )
    
    # Private helper methods
    
    def _validate_stack_type(self, stack_type: str) -> None:
        """Validate stack type string"""
        if not stack_type.strip():
            raise ValidationError("Stack type cannot be empty")
        
        if len(stack_type) > 50:
            raise ValidationError("Stack type cannot exceed 50 characters")
        
        # Optional: Add allowed stack types validation
        # allowed_types = ['panorama', 'burst', 'animation', 'hdr', 'focus', 'timelapse']
        # if stack_type not in allowed_types:
        #     raise ValidationError(f"Invalid stack type: {stack_type}")
    
    def _validate_photos_exist(self, photo_hothashes: List[str], user_id: int) -> bool:
        """Validate that photos exist and belong to user"""
        for photo_hothash in photo_hothashes:
            photo = self.photo_repo.get_by_hash(photo_hothash, user_id)
            if not photo:
                return False
        return True