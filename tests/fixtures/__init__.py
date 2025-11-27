"""
Test fixtures for ImaLink.

Provides pre-configured test data collections (PhotoCreateSchemas) for consistent testing.
"""
from tests.fixtures.photo_create_schemas import (
    timeline_photos,
    visibility_photos,
    rating_photos,
    gps_photos
)

__all__ = [
    "timeline_photos",
    "visibility_photos",
    "rating_photos",
    "gps_photos"
]
