"""
Example test photo fixture collections.

Demonstrates how to use PhotoEgg and PhotoEggCollection for organized test data.
"""
from datetime import datetime, timezone
from src.schemas.test_fixtures import PhotoEgg, PhotoEggCollection, ImageFileEgg, create_test_photo_egg


# Example 1: Simple timeline test collection
timeline_photos = PhotoEggCollection(
    name="timeline_test_photos",
    description="Photos spanning different years and months for timeline API testing",
    version="1.0",
    photos={
        "summer_2024_beach": create_test_photo_egg(
            hothash="a" * 64,
            filename="beach_2024.jpg",
            taken_at=datetime(2024, 6, 15, 14, 30, 0, tzinfo=timezone.utc),
            rating=5,
            visibility="public",
            width=4000,
            height=3000,
            gps_latitude=59.9139,
            gps_longitude=10.7522,
            description="Summer beach photo from 2024"
        ),
        
        "winter_2024_mountains": create_test_photo_egg(
            hothash="b" * 64,
            filename="mountains_2024.jpg",
            taken_at=datetime(2024, 12, 20, 10, 0, 0, tzinfo=timezone.utc),
            rating=4,
            visibility="authenticated",
            width=4000,
            height=3000,
            description="Winter mountain photo from 2024"
        ),
        
        "autumn_2023_forest": create_test_photo_egg(
            hothash="c" * 64,
            filename="forest_2023.jpg",
            taken_at=datetime(2023, 10, 10, 16, 45, 0, tzinfo=timezone.utc),
            rating=3,
            visibility="private",
            width=3000,
            height=4000,
            description="Autumn forest photo from 2023"
        ),
        
        "spring_2023_flowers": create_test_photo_egg(
            hothash="d" * 64,
            filename="flowers_2023.jpg",
            taken_at=datetime(2023, 4, 5, 12, 0, 0, tzinfo=timezone.utc),
            rating=4,
            visibility="public",
            description="Spring flowers photo from 2023"
        ),
    }
)


# Example 2: Visibility test collection
visibility_photos = PhotoEggCollection(
    name="visibility_test_photos",
    description="Photos with different visibility levels for access control testing",
    version="1.0",
    photos={
        "private_family": create_test_photo_egg(
            hothash="private_hash_001",
            filename="family_dinner.jpg",
            taken_at=datetime(2024, 1, 1, 18, 0, 0, tzinfo=timezone.utc),
            visibility="private",
            description="Private family photo - only owner should see"
        ),
        
        "authenticated_event": create_test_photo_egg(
            hothash="auth_hash_001",
            filename="company_event.jpg",
            taken_at=datetime(2024, 2, 1, 14, 0, 0, tzinfo=timezone.utc),
            visibility="authenticated",
            description="Authenticated photo - all logged-in users can see"
        ),
        
        "public_landscape": create_test_photo_egg(
            hothash="public_hash_001",
            filename="oslo_sunset.jpg",
            taken_at=datetime(2024, 3, 1, 19, 30, 0, tzinfo=timezone.utc),
            visibility="public",
            rating=5,
            description="Public landscape - everyone including anonymous can see"
        ),
    }
)


# Example 3: Rating test collection
rating_photos = PhotoEggCollection(
    name="rating_test_photos",
    description="Photos with different ratings for preview selection testing",
    version="1.0",
    photos={
        "five_star": create_test_photo_egg(
            hothash="rating_5_hash",
            filename="masterpiece.jpg",
            rating=5,
            description="5-star photo - should be selected as preview"
        ),
        
        "four_star": create_test_photo_egg(
            hothash="rating_4_hash",
            filename="great_shot.jpg",
            rating=4,
            description="4-star photo - good quality"
        ),
        
        "three_star": create_test_photo_egg(
            hothash="rating_3_hash",
            filename="ok_photo.jpg",
            rating=3,
            description="3-star photo - average"
        ),
        
        "no_rating": create_test_photo_egg(
            hothash="rating_0_hash",
            filename="unrated.jpg",
            rating=0,
            description="Unrated photo"
        ),
    }
)


# Example 4: GPS test collection
gps_photos = PhotoEggCollection(
    name="gps_test_photos",
    description="Photos with and without GPS coordinates for location testing",
    version="1.0",
    photos={
        "oslo_location": create_test_photo_egg(
            hothash="gps_oslo_hash",
            filename="oslo_city.jpg",
            gps_latitude=59.9139,
            gps_longitude=10.7522,
            description="Photo taken in Oslo with GPS"
        ),
        
        "bergen_location": create_test_photo_egg(
            hothash="gps_bergen_hash",
            filename="bergen_harbor.jpg",
            gps_latitude=60.3913,
            gps_longitude=5.3221,
            description="Photo taken in Bergen with GPS"
        ),
        
        "no_gps": create_test_photo_egg(
            hothash="no_gps_hash",
            filename="studio_portrait.jpg",
            description="Studio photo without GPS coordinates"
        ),
    }
)


# Example usage in tests:
"""
def test_timeline_year_aggregation(test_db_session, test_user):
    '''Test year aggregation with timeline photos.'''
    # Load and create all timeline photos
    created = timeline_photos.create_all(test_db_session, test_user.id)
    
    # Now test with the created photos
    response = client.get("/api/v1/timeline?granularity=year")
    assert len(response.json()["data"]) == 2  # 2024 and 2023


def test_visibility_filtering(test_db_session, test_user, test_user2):
    '''Test visibility with different access levels.'''
    # Create photos for user1
    user1_photos = visibility_photos.create_all(test_db_session, test_user.id)
    
    # User2 should see only authenticated and public
    response = client.get("/api/v1/photos", headers=user2_headers)
    assert len(response.json()["data"]) == 2  # authenticated_event + public_landscape


def test_preview_selection(test_db_session, test_user):
    '''Test that highest rated photo is selected as preview.'''
    created = rating_photos.create_all(test_db_session, test_user.id)
    
    response = client.get("/api/v1/timeline?granularity=year&year=2024")
    # Should select five_star as preview
    assert response.json()["data"][0]["preview_hothash"] == "rating_5_hash"


# Or use individual photos:
def test_single_photo(test_db_session, test_user):
    '''Test with a single photo.'''
    from src.models.photo import Photo
    from src.models.image_file import ImageFile
    
    # Get specific photo from collection
    beach_egg = timeline_photos.get("summer_2024_beach")
    
    # Create Photo instance
    photo = Photo(**beach_egg.to_photo_kwargs(test_user.id))
    test_db_session.add(photo)
    test_db_session.flush()
    
    # Create ImageFile
    image_file = ImageFile(**beach_egg.to_image_file_kwargs(photo.id))
    test_db_session.add(image_file)
    test_db_session.commit()
    
    # Now test with this photo
    assert photo.rating == 5
    assert photo.visibility == "public"
"""


# Export collections for easy import in tests
__all__ = [
    "timeline_photos",
    "visibility_photos", 
    "rating_photos",
    "gps_photos"
]
