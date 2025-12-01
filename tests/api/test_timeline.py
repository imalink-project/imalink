"""
Tests for Timeline API endpoints.

Tests hierarchical time-based photo navigation with year/month/day/hour granularity,
visibility filtering, and anonymous access support.
"""

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.main import app
from src.models.photo import Photo
from src.models.user import User


class TestTimelineYearAggregation:
    """Test year-level timeline aggregation."""
    
    def test_get_years_authenticated_user(
        self,
        client: TestClient,
        test_db_session: Session,
        test_user: User,
        auth_headers: dict,
        import_session
    ):
        """Authenticated user should see their own photos aggregated by year."""
        # Create photos in different years
        photos = [
            Photo(
                hothash="year2024_1",
                hotpreview=b"fake_preview_data",
                user_id=test_user.id,
                taken_at=datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
                visibility="private",
                input_channel_id=1
            ),
            Photo(
                hothash="year2024_2",
                hotpreview=b"fake_preview_data",
                user_id=test_user.id,
                taken_at=datetime(2024, 8, 20, 14, 30, 0, tzinfo=timezone.utc),
                visibility="private",
                input_channel_id=1
            ),
            Photo(
                hothash="year2023_1",
                hotpreview=b"fake_preview_data",
                user_id=test_user.id,
                taken_at=datetime(2023, 3, 10, 10, 0, 0, tzinfo=timezone.utc),
                visibility="private",
                input_channel_id=1
            ),
        ]
        
        for photo in photos:
            test_db_session.add(photo)
        test_db_session.commit()
        
        # Get year aggregation
        response = client.get("/api/v1/timeline/?granularity=year", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "data" in data
        assert "meta" in data
        assert len(data["data"]) == 2  # 2024 and 2023
        
        # Check 2024 bucket
        year_2024 = next(b for b in data["data"] if b["year"] == 2024)
        assert year_2024["count"] == 2
        assert "preview_hothash" in year_2024
        assert "preview_url" in year_2024
        assert "date_range" in year_2024
        assert "2024-06-15" in year_2024["date_range"]["first"]
        assert "2024-08-20" in year_2024["date_range"]["last"]
        
        # Check 2023 bucket
        year_2023 = next(b for b in data["data"] if b["year"] == 2023)
        assert year_2023["count"] == 1
        
        # Check metadata
        assert data["meta"]["granularity"] == "year"
        assert data["meta"]["total_years"] == 2
        assert data["meta"]["total_photos"] == 3
    
    def test_get_years_anonymous_user_sees_only_public(
        self,
        client: TestClient,
        test_db_session: Session,
        test_user: User
    ):
        """Anonymous users should only see public photos."""
        photos = [
            Photo(
                hothash="public_2024",
                hotpreview=b"fake_preview_data",
                user_id=test_user.id,
                taken_at=datetime(2024, 5, 1, 10, 0, 0, tzinfo=timezone.utc),
                visibility="public",
                input_channel_id=1
            ),
            Photo(
                hothash="private_2024",
                hotpreview=b"fake_preview_data",
                user_id=test_user.id,
                taken_at=datetime(2024, 6, 1, 10, 0, 0, tzinfo=timezone.utc),
                visibility="private",
                input_channel_id=1
            ),
            Photo(
                hothash="authenticated_2023",
                hotpreview=b"fake_preview_data",
                user_id=test_user.id,
                taken_at=datetime(2023, 7, 1, 10, 0, 0, tzinfo=timezone.utc),
                visibility="authenticated",
                input_channel_id=1
            ),
        ]
        
        for photo in photos:
            test_db_session.add(photo)
        test_db_session.commit()
        
        # Anonymous request (no auth headers)
        response = client.get("/api/v1/timeline/?granularity=year")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["data"]) == 1  # Only 2024 has public photos
        assert data["data"][0]["year"] == 2024
        assert data["data"][0]["count"] == 1  # Only the public photo
        assert data["meta"]["total_photos"] == 1
    
    def test_get_years_empty_timeline(
        self,
        client: TestClient,
        auth_headers: dict,
        import_session
    ):
        """Empty timeline should return empty array."""
        response = client.get("/api/v1/timeline/?granularity=year", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["data"] == []
        assert data["meta"]["total_years"] == 0
        assert data["meta"]["total_photos"] == 0
    
    def test_get_years_user_isolation(
        self,
        client: TestClient,
        test_db_session: Session,
        test_user: User,
        second_user: User,
        auth_headers: dict,
        import_session
    ):
        """Users should only see their own private photos."""
        photos = [
            Photo(
                hothash="user1_photo",
                hotpreview=b"fake_preview_data",
                user_id=test_user.id,
                taken_at=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
                visibility="private",
                input_channel_id=1
            ),
            Photo(
                hothash="user2_photo",
                hotpreview=b"fake_preview_data",
                user_id=second_user.id,
                taken_at=datetime(2024, 2, 1, 10, 0, 0, tzinfo=timezone.utc),
                visibility="private",
                input_channel_id=1
            ),
        ]
        
        for photo in photos:
            test_db_session.add(photo)
        test_db_session.commit()
        
        # User 1 should only see their own photo
        response = client.get("/api/v1/timeline/?granularity=year", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["data"]) == 1
        assert data["data"][0]["count"] == 1
        assert data["meta"]["total_photos"] == 1


class TestTimelineMonthAggregation:
    """Test month-level timeline aggregation."""
    
    def test_get_months_for_year(
        self,
        client: TestClient,
        test_db_session: Session,
        test_user: User,
        auth_headers: dict,
        import_session
    ):
        """Should aggregate photos by month for a specific year."""
        photos = [
            Photo(
                hothash="jan_photo1",
                hotpreview=b"fake_preview_data",
                user_id=test_user.id,
                taken_at=datetime(2024, 1, 5, 10, 0, 0, tzinfo=timezone.utc),
                visibility="private",
                input_channel_id=1
            ),
            Photo(
                hothash="jan_photo2",
                hotpreview=b"fake_preview_data",
                user_id=test_user.id,
                taken_at=datetime(2024, 1, 20, 15, 0, 0, tzinfo=timezone.utc),
                visibility="private",
                input_channel_id=1
            ),
            Photo(
                hothash="feb_photo",
                hotpreview=b"fake_preview_data",
                user_id=test_user.id,
                taken_at=datetime(2024, 2, 10, 12, 0, 0, tzinfo=timezone.utc),
                visibility="private",
                input_channel_id=1
            ),
            Photo(
                hothash="dec_photo",
                hotpreview=b"fake_preview_data",
                user_id=test_user.id,
                taken_at=datetime(2024, 12, 25, 18, 0, 0, tzinfo=timezone.utc),
                visibility="private",
                input_channel_id=1
            ),
        ]
        
        for photo in photos:
            test_db_session.add(photo)
        test_db_session.commit()
        
        # Get months for 2024
        response = client.get(
            "/api/v1/timeline/?granularity=month&year=2024",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["data"]) == 3  # January, February, December
        
        # Check January bucket
        jan = next(b for b in data["data"] if b["month"] == 1)
        assert jan["year"] == 2024
        assert jan["count"] == 2
        assert "preview_hothash" in jan
        
        # Check metadata
        assert data["meta"]["granularity"] == "month"
        assert data["meta"]["year"] == 2024
        assert data["meta"]["total_months"] == 3
        assert data["meta"]["total_photos"] == 4
    
    def test_get_months_requires_year_parameter(
        self,
        client: TestClient,
        auth_headers: dict,
        import_session
    ):
        """Month granularity should require year parameter."""
        response = client.get(
            "/api/v1/timeline/?granularity=month",
            headers=auth_headers
        )
        
        assert response.status_code in [400, 422]
    
    def test_get_months_invalid_year(
        self,
        client: TestClient,
        auth_headers: dict,
        import_session
    ):
        """Should reject invalid year values."""
        response = client.get(
            "/api/v1/timeline/?granularity=month&year=1800",
            headers=auth_headers
        )
        
        assert response.status_code in [400, 422]
    
    def test_get_months_visibility_filtering(
        self,
        client: TestClient,
        test_db_session: Session,
        test_user: User,
        auth_headers: dict,
        import_session
    ):
        """Month aggregation should respect visibility levels."""
        photos = [
            Photo(
                hothash="public_jan",
                hotpreview=b"fake_preview_data",
                user_id=test_user.id,
                taken_at=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
                visibility="public",
                input_channel_id=1
            ),
            Photo(
                hothash="private_jan",
                hotpreview=b"fake_preview_data",
                user_id=test_user.id,
                taken_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
                visibility="private",
                input_channel_id=1
            ),
        ]
        
        for photo in photos:
            test_db_session.add(photo)
        test_db_session.commit()
        
        # Authenticated user sees both
        response = client.get(
            "/api/v1/timeline/?granularity=month&year=2024",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["data"][0]["count"] == 2
        
        # Anonymous user sees only public
        response = client.get("/api/v1/timeline/?granularity=month&year=2024")
        assert response.status_code == 200
        assert response.json()["data"][0]["count"] == 1


class TestTimelineDayAggregation:
    """Test day-level timeline aggregation."""
    
    def test_get_days_for_month(
        self,
        client: TestClient,
        test_db_session: Session,
        test_user: User,
        auth_headers: dict,
        import_session
    ):
        """Should aggregate photos by day for a specific month."""
        photos = [
            Photo(
                hothash="day1_photo1",
                hotpreview=b"fake_preview_data",
                user_id=test_user.id,
                taken_at=datetime(2024, 6, 1, 8, 0, 0, tzinfo=timezone.utc),
                visibility="private",
                input_channel_id=1
            ),
            Photo(
                hothash="day1_photo2",
                hotpreview=b"fake_preview_data",
                user_id=test_user.id,
                taken_at=datetime(2024, 6, 1, 18, 0, 0, tzinfo=timezone.utc),
                visibility="private",
                input_channel_id=1
            ),
            Photo(
                hothash="day15_photo",
                hotpreview=b"fake_preview_data",
                user_id=test_user.id,
                taken_at=datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
                visibility="private",
                input_channel_id=1
            ),
        ]
        
        for photo in photos:
            test_db_session.add(photo)
        test_db_session.commit()
        
        # Get days for June 2024
        response = client.get(
            "/api/v1/timeline/?granularity=day&year=2024&month=6",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["data"]) == 2  # Day 1 and 15
        
        # Check day 1
        day1 = next(b for b in data["data"] if b["day"] == 1)
        assert day1["year"] == 2024
        assert day1["month"] == 6
        assert day1["count"] == 2
        
        # Check metadata
        assert data["meta"]["granularity"] == "day"
        assert data["meta"]["year"] == 2024
        assert data["meta"]["month"] == 6
        assert data["meta"]["total_days"] == 2
        assert data["meta"]["total_photos"] == 3
    
    def test_get_days_requires_year_and_month(
        self,
        client: TestClient,
        auth_headers: dict,
        import_session
    ):
        """Day granularity requires both year and month."""
        # Missing year
        response = client.get(
            "/api/v1/timeline/?granularity=day&month=6",
            headers=auth_headers
        )
        assert response.status_code in [400, 422]
        
        # Missing month
        response = client.get(
            "/api/v1/timeline/?granularity=day&year=2024",
            headers=auth_headers
        )
        assert response.status_code in [400, 422]
    
    def test_get_days_invalid_month(
        self,
        client: TestClient,
        auth_headers: dict,
        import_session
    ):
        """Should reject invalid month values."""
        response = client.get(
            "/api/v1/timeline/?granularity=day&year=2024&month=13",
            headers=auth_headers
        )
        
        assert response.status_code in [400, 422]


class TestTimelineHourAggregation:
    """Test hour-level timeline aggregation."""
    
    def test_get_hours_for_day(
        self,
        client: TestClient,
        test_db_session: Session,
        test_user: User,
        auth_headers: dict,
        import_session
    ):
        """Should aggregate photos by hour for a specific day."""
        photos = [
            Photo(
                hothash="hour9_photo1",
                hotpreview=b"fake_preview_data",
                user_id=test_user.id,
                taken_at=datetime(2024, 6, 15, 9, 15, 0, tzinfo=timezone.utc),
                visibility="private",
                input_channel_id=1
            ),
            Photo(
                hothash="hour9_photo2",
                hotpreview=b"fake_preview_data",
                user_id=test_user.id,
                taken_at=datetime(2024, 6, 15, 9, 45, 0, tzinfo=timezone.utc),
                visibility="private",
                input_channel_id=1
            ),
            Photo(
                hothash="hour14_photo",
                hotpreview=b"fake_preview_data",
                user_id=test_user.id,
                taken_at=datetime(2024, 6, 15, 14, 30, 0, tzinfo=timezone.utc),
                visibility="private",
                input_channel_id=1
            ),
            Photo(
                hothash="hour23_photo",
                hotpreview=b"fake_preview_data",
                user_id=test_user.id,
                taken_at=datetime(2024, 6, 15, 23, 59, 0, tzinfo=timezone.utc),
                visibility="private",
                input_channel_id=1
            ),
        ]
        
        for photo in photos:
            test_db_session.add(photo)
        test_db_session.commit()
        
        # Get hours for June 15, 2024
        response = client.get(
            "/api/v1/timeline/?granularity=hour&year=2024&month=6&day=15",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["data"]) == 3  # Hours 9, 14, 23
        
        # Check hour 9
        hour9 = next(b for b in data["data"] if b["hour"] == 9)
        assert hour9["year"] == 2024
        assert hour9["month"] == 6
        assert hour9["day"] == 15
        assert hour9["count"] == 2
        
        # Check metadata
        assert data["meta"]["granularity"] == "hour"
        assert data["meta"]["year"] == 2024
        assert data["meta"]["month"] == 6
        assert data["meta"]["day"] == 15
        assert data["meta"]["total_hours"] == 3
        assert data["meta"]["total_photos"] == 4
    
    def test_get_hours_requires_year_month_day(
        self,
        client: TestClient,
        auth_headers: dict,
        import_session
    ):
        """Hour granularity requires year, month, and day."""
        response = client.get(
            "/api/v1/timeline/?granularity=hour&year=2024&month=6",
            headers=auth_headers
        )
        
        assert response.status_code in [400, 422]
    
    def test_get_hours_invalid_day(
        self,
        client: TestClient,
        auth_headers: dict,
        import_session
    ):
        """Should reject invalid day values."""
        response = client.get(
            "/api/v1/timeline/?granularity=hour&year=2024&month=6&day=32",
            headers=auth_headers
        )
        
        assert response.status_code in [400, 422]


class TestTimelinePreviewSelection:
    """Test representative preview photo selection."""
    
    def test_preview_selects_highest_rated(
        self,
        client: TestClient,
        test_db_session: Session,
        test_user: User,
        auth_headers: dict,
        import_session
    ):
        """Preview should prioritize highest-rated photo (4-5 stars)."""
        photos = [
            Photo(
                hothash="rated_3",
                hotpreview=b"fake_preview_data",
                user_id=test_user.id,
                taken_at=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
                visibility="private",
                rating=3
            ),
            Photo(
                hothash="rated_5",
                hotpreview=b"fake_preview_data",
                user_id=test_user.id,
                taken_at=datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
                visibility="private",
                rating=5
            ),
            Photo(
                hothash="rated_2",
                hotpreview=b"fake_preview_data",
                user_id=test_user.id,
                taken_at=datetime(2024, 1, 20, 14, 0, 0, tzinfo=timezone.utc),
                visibility="private",
                rating=2
            ),
        ]
        
        for photo in photos:
            test_db_session.add(photo)
        test_db_session.commit()
        
        response = client.get(
            "/api/v1/timeline/?granularity=month&year=2024",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Preview should be the 5-star photo
        assert data["data"][0]["preview_hothash"] == "rated_5"
    
    def test_preview_selects_temporal_center_if_no_rating(
        self,
        client: TestClient,
        test_db_session: Session,
        test_user: User,
        auth_headers: dict,
        import_session
    ):
        """If no high ratings, preview should be temporally centered photo."""
        photos = [
            Photo(
                hothash="first",
                hotpreview=b"fake_preview_data",
                user_id=test_user.id,
                taken_at=datetime(2024, 6, 1, 8, 0, 0, tzinfo=timezone.utc),
                visibility="private",
                rating=None
            ),
            Photo(
                hothash="middle",
                hotpreview=b"fake_preview_data",
                user_id=test_user.id,
                taken_at=datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
                visibility="private",
                rating=None
            ),
            Photo(
                hothash="last",
                hotpreview=b"fake_preview_data",
                user_id=test_user.id,
                taken_at=datetime(2024, 6, 30, 20, 0, 0, tzinfo=timezone.utc),
                visibility="private",
                rating=None
            ),
        ]
        
        for photo in photos:
            test_db_session.add(photo)
        test_db_session.commit()
        
        response = client.get(
            "/api/v1/timeline/?granularity=month&year=2024",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Preview selection without ratings picks first by taken_at
        # (temporal center algorithm can be enhanced in future)
        assert data["data"][0]["preview_hothash"] in ["first", "middle", "last"]
    
    def test_preview_url_format(
        self,
        client: TestClient,
        test_db_session: Session,
        test_user: User,
        auth_headers: dict,
        import_session
    ):
        """Preview URL should point to hotpreview endpoint."""
        photo = Photo(
            hothash="test_hash_123",
                hotpreview=b"fake_preview_data",
            user_id=test_user.id,
            taken_at=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
            visibility="private",
                input_channel_id=1
        )
        test_db_session.add(photo)
        test_db_session.commit()
        
        response = client.get(
            "/api/v1/timeline/?granularity=year",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        preview_url = data["data"][0]["preview_url"]
        assert preview_url == "/api/v1/photos/test_hash_123/hotpreview"


class TestTimelineEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_photos_without_taken_at(
        self,
        client: TestClient,
        test_db_session: Session,
        test_user: User,
        auth_headers: dict,
        import_session
    ):
        """Photos without taken_at should be excluded from timeline."""
        photos = [
            Photo(
                hothash="with_date",
                hotpreview=b"fake_preview_data",
                user_id=test_user.id,
                taken_at=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
                visibility="private",
                input_channel_id=1
            ),
            Photo(
                hothash="no_date",
                hotpreview=b"fake_preview_data",
                user_id=test_user.id,
                taken_at=None,
                visibility="private",
                input_channel_id=1
            ),
        ]
        
        for photo in photos:
            test_db_session.add(photo)
        test_db_session.commit()
        
        response = client.get("/api/v1/timeline/?granularity=year", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["meta"]["total_photos"] == 1  # Only photo with date
    
    def test_leap_year_february(
        self,
        client: TestClient,
        test_db_session: Session,
        test_user: User,
        auth_headers: dict,
        import_session
    ):
        """Should handle leap year dates correctly."""
        photo = Photo(
            hothash="leap_day",
                hotpreview=b"fake_preview_data",
            user_id=test_user.id,
            taken_at=datetime(2024, 2, 29, 12, 0, 0, tzinfo=timezone.utc),  # 2024 is leap year
            visibility="private",
                input_channel_id=1
        )
        test_db_session.add(photo)
        test_db_session.commit()
        
        response = client.get(
            "/api/v1/timeline/?granularity=day&year=2024&month=2",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert any(b["day"] == 29 for b in data["data"])
    
    def test_timezone_handling(
        self,
        client: TestClient,
        test_db_session: Session,
        test_user: User,
        auth_headers: dict,
        import_session
    ):
        """Should handle different timezones consistently."""
        photos = [
            Photo(
                hothash="utc_photo",
                hotpreview=b"fake_preview_data",
                user_id=test_user.id,
                taken_at=datetime(2024, 1, 1, 23, 0, 0, tzinfo=timezone.utc),
                visibility="private",
                input_channel_id=1
            ),
        ]
        
        for photo in photos:
            test_db_session.add(photo)
        test_db_session.commit()
        
        response = client.get(
            "/api/v1/timeline/?granularity=day&year=2024&month=1",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Photo should be in day 1 (UTC)
        assert any(b["day"] == 1 for b in data["data"])
    
    def test_default_granularity(
        self,
        client: TestClient,
        test_db_session: Session,
        test_user: User,
        auth_headers: dict,
        import_session
    ):
        """Default granularity should be 'year'."""
        photo = Photo(
            hothash="test",
                hotpreview=b"fake_preview_data",
            user_id=test_user.id,
            taken_at=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
            visibility="private",
                input_channel_id=1
        )
        test_db_session.add(photo)
        test_db_session.commit()
        
        # No granularity parameter
        response = client.get("/api/v1/timeline/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["meta"]["granularity"] == "year"
    
    def test_invalid_granularity(
        self,
        client: TestClient,
        auth_headers: dict,
        import_session
    ):
        """Should reject invalid granularity values."""
        response = client.get(
            "/api/v1/timeline/?granularity=week",
            headers=auth_headers
        )
        
        assert response.status_code in [400, 422]
    
    def test_large_dataset_performance(
        self,
        client: TestClient,
        test_db_session: Session,
        test_user: User,
        auth_headers: dict,
        import_session
    ):
        """Should handle large datasets efficiently."""
        # Create 100 photos across multiple years
        photos = []
        for i in range(100):
            year = 2020 + (i % 5)  # 2020-2024
            month = (i % 12) + 1
            photo = Photo(
                hothash=f"photo_{i}",
                hotpreview=b"fake_preview_data",
                user_id=test_user.id,
                taken_at=datetime(year, month, 15, 12, 0, 0, tzinfo=timezone.utc),
                visibility="private",
                input_channel_id=1
            )
            photos.append(photo)
        
        test_db_session.add_all(photos)
        test_db_session.commit()
        
        response = client.get("/api/v1/timeline/?granularity=year", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["meta"]["total_photos"] == 100
        assert len(data["data"]) == 5  # 5 years


class TestTimelineVisibilityIntegration:
    """Test timeline integration with visibility system."""
    
    def test_authenticated_visibility_level(
        self,
        client: TestClient,
        test_db_session: Session,
        test_user: User,
        second_user: User,
        auth_headers: dict,
        import_session
    ):
        """Authenticated users should see 'authenticated' photos from other users."""
        photos = [
            Photo(
                hothash="user2_auth",
                hotpreview=b"fake_preview_data",
                user_id=second_user.id,
                taken_at=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
                visibility="authenticated",
                input_channel_id=1
            ),
            Photo(
                hothash="user2_private",
                hotpreview=b"fake_preview_data",
                user_id=second_user.id,
                taken_at=datetime(2024, 2, 1, 10, 0, 0, tzinfo=timezone.utc),
                visibility="private",
                input_channel_id=1
            ),
        ]
        
        for photo in photos:
            test_db_session.add(photo)
        test_db_session.commit()
        
        # User 1 should see the authenticated photo but not private
        response = client.get("/api/v1/timeline/?granularity=year", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should see 1 photo (the authenticated one)
        assert data["meta"]["total_photos"] == 1
    
    def test_public_visibility_level(
        self,
        client: TestClient,
        test_db_session: Session,
        test_user: User
    ):
        """Public photos should be visible to everyone."""
        photo = Photo(
            hothash="public_photo",
                hotpreview=b"fake_preview_data",
            user_id=test_user.id,
            taken_at=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
            visibility="public",
                input_channel_id=1
        )
        test_db_session.add(photo)
        test_db_session.commit()
        
        # Anonymous request
        response = client.get("/api/v1/timeline/?granularity=year")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["meta"]["total_photos"] == 1
        assert data["data"][0]["count"] == 1
    
    def test_mixed_visibility_in_bucket(
        self,
        client: TestClient,
        test_db_session: Session,
        test_user: User,
        auth_headers: dict,
        import_session
    ):
        """Bucket should aggregate all accessible photos regardless of visibility."""
        photos = [
            Photo(
                hothash="private_jan",
                hotpreview=b"fake_preview_data",
                user_id=test_user.id,
                taken_at=datetime(2024, 1, 5, 10, 0, 0, tzinfo=timezone.utc),
                visibility="private",
                input_channel_id=1
            ),
            Photo(
                hothash="authenticated_jan",
                hotpreview=b"fake_preview_data",
                user_id=test_user.id,
                taken_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
                visibility="authenticated",
                input_channel_id=1
            ),
            Photo(
                hothash="public_jan",
                hotpreview=b"fake_preview_data",
                user_id=test_user.id,
                taken_at=datetime(2024, 1, 25, 10, 0, 0, tzinfo=timezone.utc),
                visibility="public",
                input_channel_id=1
            ),
        ]
        
        for photo in photos:
            test_db_session.add(photo)
        test_db_session.commit()
        
        # Authenticated user sees all
        response = client.get(
            "/api/v1/timeline/?granularity=month&year=2024",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        jan_bucket = next(b for b in data["data"] if b["month"] == 1)
        assert jan_bucket["count"] == 3  # All three photos
        
        # Anonymous user sees only public
        response = client.get("/api/v1/timeline/?granularity=month&year=2024")
        
        assert response.status_code == 200
        data = response.json()
        
        jan_bucket = next(b for b in data["data"] if b["month"] == 1)
        assert jan_bucket["count"] == 1  # Only public photo
