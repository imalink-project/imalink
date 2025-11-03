"""
Tag Service - Business logic for tag operations
"""
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from repositories.tag_repository import TagRepository
from repositories.photo_repository import PhotoRepository
from schemas.tag_schemas import (
    TagResponse, TagListResponse, TagAutocompleteResponse, TagAutocompleteItem,
    AddTagsResponse, RemoveTagResponse, DeleteTagResponse, RenameTagResponse,
    TagSummary
)
from core.exceptions import NotFoundError, ValidationError, ConflictError


class TagService:
    """Service layer for tag business logic"""
    
    def __init__(self, db: Session):
        self.db = db
        self.tag_repo = TagRepository(db)
        self.photo_repo = PhotoRepository(db)
    
    def get_all_tags(self, user_id: int, sort_by: str = 'name', order: str = 'asc') -> TagListResponse:
        """
        Get all tags for user with photo counts
        
        Args:
            user_id: User ID
            sort_by: Sort field ('name', 'count', 'created_at')
            order: Sort direction ('asc', 'desc')
        """
        tags = self.tag_repo.get_all_for_user(user_id, sort_by, order)
        
        tag_responses = [
            TagResponse(
                id=tag.id,
                name=tag.name,
                photo_count=getattr(tag, 'photo_count', 0),
                created_at=tag.created_at,
                updated_at=tag.updated_at
            )
            for tag in tags
        ]
        
        return TagListResponse(tags=tag_responses, total=len(tag_responses))
    
    def autocomplete(self, query: str, user_id: int, limit: int = 10) -> TagAutocompleteResponse:
        """
        Get tag autocomplete suggestions
        
        Args:
            query: Search prefix
            user_id: User ID
            limit: Max results
        """
        if limit > 50:
            limit = 50
        
        tags = self.tag_repo.autocomplete(query, user_id, limit)
        
        suggestions = [
            TagAutocompleteItem(
                id=tag.id,
                name=tag.name,
                photo_count=getattr(tag, 'photo_count', 0)
            )
            for tag in tags
        ]
        
        return TagAutocompleteResponse(suggestions=suggestions)
    
    def add_tags_to_photo(self, hothash: str, tag_names: List[str], user_id: int) -> AddTagsResponse:
        """
        Add multiple tags to a photo
        
        Args:
            hothash: Photo hash
            tag_names: List of tag names (will be normalized)
            user_id: User ID
        
        Returns:
            Response with added tags and counts
        """
        # Verify photo exists and belongs to user
        photo = self.photo_repo.get_by_hash(hothash, user_id)
        if not photo:
            raise NotFoundError("Photo", hothash)
        
        added_count = 0
        skipped_count = 0
        skipped_tags = []
        
        # Process each tag
        for tag_name in tag_names:
            # Get or create tag
            tag = self.tag_repo.get_or_create(tag_name, user_id)
            
            # Try to add association
            was_added = self.tag_repo.add_tag_to_photo(hothash, tag.id)
            if was_added:
                added_count += 1
            else:
                skipped_count += 1
                skipped_tags.append(tag_name)
        
        # Commit all changes
        self.db.commit()
        
        # Get updated tag list for photo
        photo_tags = self.tag_repo.get_photo_tags(hothash)
        tag_summaries = [TagSummary(id=tag.id, name=tag.name) for tag in photo_tags]
        
        # Build response message
        message = None
        if skipped_count > 0:
            if skipped_count == 1:
                message = f"Tag '{skipped_tags[0]}' was already applied to this photo"
            else:
                message = f"{skipped_count} tags were already applied to this photo"
        
        return AddTagsResponse(
            hothash=hothash,
            tags=tag_summaries,
            added=added_count,
            skipped=skipped_count,
            message=message
        )
    
    def remove_tag_from_photo(self, hothash: str, tag_name: str, user_id: int) -> RemoveTagResponse:
        """
        Remove a tag from a photo
        
        Args:
            hothash: Photo hash
            tag_name: Tag name to remove
            user_id: User ID
        """
        # Verify photo exists and belongs to user
        photo = self.photo_repo.get_by_hash(hothash, user_id)
        if not photo:
            raise NotFoundError("Photo", hothash)
        
        # Find tag
        tag = self.tag_repo.get_by_name(tag_name, user_id)
        if not tag:
            raise NotFoundError("Tag", tag_name)
        
        # Remove association
        was_removed = self.tag_repo.remove_tag_from_photo(hothash, tag.id)
        if not was_removed:
            raise NotFoundError("Tag association", f"{tag_name} on photo {hothash}")
        
        self.db.commit()
        
        # Get remaining tags
        remaining_tags = self.tag_repo.get_photo_tags(hothash)
        tag_summaries = [TagSummary(id=t.id, name=t.name) for t in remaining_tags]
        
        return RemoveTagResponse(
            hothash=hothash,
            removed_tag=tag_name,
            remaining_tags=tag_summaries
        )
    
    def delete_tag(self, tag_id: int, user_id: int) -> DeleteTagResponse:
        """
        Delete a tag completely (removes from all photos)
        
        Args:
            tag_id: Tag ID
            user_id: User ID
        """
        # Get tag
        tag = self.tag_repo.get_by_id(tag_id, user_id)
        if not tag:
            raise NotFoundError("Tag", str(tag_id))
        
        # Count affected photos before deletion
        photo_count = self.tag_repo.count_photos_with_tag(tag_id)
        tag_name = tag.name
        
        # Delete tag (cascade deletes photo_tags associations)
        self.tag_repo.delete(tag_id, user_id)
        self.db.commit()
        
        return DeleteTagResponse(
            deleted_tag=tag_name,
            photos_affected=photo_count,
            message=f"Tag '{tag_name}' deleted from {photo_count} photo(s)"
        )
    
    def rename_tag(self, tag_id: int, new_name: str, user_id: int) -> RenameTagResponse:
        """
        Rename a tag (affects all photos using it)
        
        Args:
            tag_id: Tag ID
            new_name: New tag name
            user_id: User ID
        """
        # Get tag
        tag = self.tag_repo.get_by_id(tag_id, user_id)
        if not tag:
            raise NotFoundError("Tag", str(tag_id))
        
        old_name = tag.name
        
        # Check if new name already exists
        existing = self.tag_repo.get_by_name(new_name, user_id)
        if existing and existing.id != tag_id:
            raise ConflictError(f"Tag '{new_name}' already exists")
        
        # Update name
        try:
            updated_tag = self.tag_repo.update_name(tag_id, new_name, user_id)
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise ConflictError(f"Tag '{new_name}' already exists")
        
        # Count photos
        photo_count = self.tag_repo.count_photos_with_tag(tag_id)
        
        return RenameTagResponse(
            id=updated_tag.id,
            old_name=old_name,
            new_name=updated_tag.name,
            photo_count=photo_count,
            updated_at=updated_tag.updated_at
        )
