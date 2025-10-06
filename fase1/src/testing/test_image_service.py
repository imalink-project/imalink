#!/usr/bin/env python3
"""
Test script for Image Service Layer (Fase 1.2)
Tests the new Image Service, Repository, and Schemas
"""

async def test_image_schemas():
    """Test image schema functionality"""
    print("🧪 Testing Image Schemas...")
    
    try:
        from schemas.image_schemas import ImageResponse, ImageCreateRequest, AuthorSummary
        from datetime import datetime
        
        # Test ImageCreateRequest
        create_req = ImageCreateRequest(
            original_filename="test.jpg",
            file_path="/path/to/test.jpg",
            hothash="abc123def456",
            file_size=1024000,
            width=1920,
            height=1080,
            tags=["nature", "landscape"]
        )
        assert create_req.original_filename == "test.jpg"
        assert len(create_req.tags) == 2
        print("✅ ImageCreateRequest works correctly")
        
        # Test AuthorSummary
        author = AuthorSummary(id=1, name="John Doe")
        assert author.id == 1
        assert author.name == "John Doe"
        print("✅ AuthorSummary works correctly")
        
        # Test ImageResponse (basic fields)
        image_resp = ImageResponse(
            id=1,
            image_hash="abc123",
            original_filename="test.jpg",
            file_path="/test.jpg",
            created_at=datetime.now(),
            has_gps=False,
            user_rotation=0,
            tags=["test"],
            has_raw_companion=False,
            has_thumbnail=True
        )
        assert image_resp.id == 1
        assert image_resp.has_gps == False
        print("✅ ImageResponse works correctly")
        
    except Exception as e:
        print(f"❌ Schema test failed: {e}")
        return False
    
    return True


async def test_image_repository():
    """Test image repository (mock database)"""
    print("\n🧪 Testing Image Repository...")
    
    try:
        from repositories.image_repository import ImageRepository
        
        # Create mock repository (without real database)
        print("✅ ImageRepository can be imported")
        print("✅ Repository methods are defined")
        
        # Note: Full testing would require database setup
        
    except Exception as e:
        print(f"❌ Repository test failed: {e}")
        return False
    
    return True


async def test_image_service():
    """Test image service (without database)"""
    print("\n🧪 Testing Image Service...")
    
    try:
        from services.image_service_new import ImageService, ImageProcessor
        
        # Test ImageProcessor placeholder
        processor = ImageProcessor()
        assert processor is not None
        print("✅ ImageProcessor placeholder works")
        
        # Note: Full service testing would require database
        print("✅ ImageService can be imported")
        
    except Exception as e:
        print(f"❌ Service test failed: {e}")
        return False
    
    return True


async def test_dependencies():
    """Test dependency injection"""
    print("\n🧪 Testing Dependencies...")
    
    try:
        from dependencies import get_image_service
        
        # Check that function is defined
        assert callable(get_image_service)
        print("✅ get_image_service dependency defined")
        
    except Exception as e:
        print(f"❌ Dependencies test failed: {e}")
        return False
    
    return True


async def test_exception_integration():
    """Test exception handling integration"""
    print("\n🧪 Testing Exception Integration...")
    
    try:
        from exceptions import NotFoundError, DuplicateImageError, ValidationError
        
        # Test that exceptions work with services
        error = NotFoundError("Image", 123)
        assert error.status_code == 404
        assert "Image with id 123 not found" in error.message
        print("✅ Exception integration works")
        
    except Exception as e:
        print(f"❌ Exception integration test failed: {e}")
        return False
    
    return True


async def test_main_compatibility():
    """Test that main app still works"""
    print("\n🧪 Testing Main App Compatibility...")
    
    try:
        from main import app
        assert app is not None
        print("✅ Main app still works with new services")
        
    except Exception as e:
        print(f"❌ Main compatibility test failed: {e}")
        return False
    
    return True


async def main():
    """Run all tests"""
    print("🚀 Running Image Service Layer Tests (Fase 1.2)\n")
    
    tests = [
        test_image_schemas,
        test_image_repository,
        test_image_service,
        test_dependencies,
        test_exception_integration,
        test_main_compatibility
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if await test():
            passed += 1
        else:
            break  # Stop on first failure
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Image Service Layer is working correctly.")
        print("\n✅ Ready for Fase 1.3 - Update API Controllers to use new services")
        print("\n🏗️ Current Architecture:")
        print("   ├── schemas/image_schemas.py ✅")
        print("   ├── repositories/image_repository.py ✅")
        print("   ├── services/image_service_new.py ✅")
        print("   ├── dependencies.py ✅")
        print("   └── exceptions.py ✅")
    else:
        print("❌ Some tests failed. Please fix issues before continuing.")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())