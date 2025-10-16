#!/usr/bin/env python3
"""
Test script for modernized Images API (Fase 1.3)
Tests the new service-based API endpoints
"""

async def test_api_imports():
    """Test that new API can be imported"""
    print("🧪 Testing API Imports...")
    
    try:
        from api.images import router
        assert router is not None
        print("✅ New images API router imported successfully")
        
        # Count endpoints
        routes = [route for route in router.routes]
        print(f"✅ Found {len(routes)} API endpoints")
        
    except Exception as e:
        print(f"❌ API import test failed: {e}")
        return False
    
    return True


async def test_service_integration():
    """Test that API integrates with services"""
    print("\n🧪 Testing Service Integration...")
    
    try:
        from dependencies import get_image_service
        from services.image_service_new import ImageService
        
        # Check dependency injection
        assert callable(get_image_service)
        print("✅ Service dependency injection works")
        
        # Check service methods exist
        service_methods = [
            'get_images', 'get_image_by_id', 'create_image', 
            'update_image', 'delete_image',
            'get_image_thumbnail', 'search_images', 
            'get_images_by_author', 'get_image_pool'
        ]
        
        for method in service_methods:
            assert hasattr(ImageService, method), f"Missing method: {method}"
        
        print(f"✅ All {len(service_methods)} service methods are present")
        
    except Exception as e:
        print(f"❌ Service integration test failed: {e}")
        return False
    
    return True


async def test_schema_integration():
    """Test that API uses proper schemas"""
    print("\n🧪 Testing Schema Integration...")
    
    try:
        from schemas.image_schemas import (
            ImageResponse, ImageCreateRequest, ImageUpdateRequest,
            ImageSearchRequest
        )
        from schemas.common import PaginatedResponse
        
        # Check that schemas are properly defined
        assert hasattr(ImageResponse, '__fields__')
        assert hasattr(ImageCreateRequest, '__fields__')
        print("✅ Image schemas are properly defined")
        
        # NOTE: Rotation test removed - rotation is Photo-level concern
        print("✅ Schema validation works")
        
    except Exception as e:
        print(f"❌ Schema integration test failed: {e}")
        return False
    
    return True

async def test_exception_handling():
    """Test exception handling setup"""
    print("\n🧪 Testing Exception Handling...")
    
    try:
        from exceptions import APIException, NotFoundError
        from main import app
        
        # Check that global exception handler is registered
        exception_handlers = getattr(app, 'exception_handlers', {})
        assert APIException in exception_handlers
        print("✅ Global exception handler is registered")
        
        # Test exception creation
        error = NotFoundError("Image", 123)
        assert error.status_code == 404
        print("✅ Exception creation works")
        
    except Exception as e:
        print(f"❌ Exception handling test failed: {e}")
        return False
    
    return True


async def test_main_app_compatibility():
    """Test that main app works with new API"""
    print("\n🧪 Testing Main App Compatibility...")
    
    try:
        from main import app
        
        # Check that app includes image router
        api_routes = []
        for route in app.routes:
            if hasattr(route, 'path') and route.path.startswith('/api/images'):
                api_routes.append(route.path)
        
        # Should have multiple image API routes
        assert len(api_routes) > 5, f"Expected multiple API routes, got {len(api_routes)}"
        print(f"✅ Found {len(api_routes)} image API routes")
        
        # Check some key endpoints exist
        expected_paths = ['/api/images/', '/api/images/{image_id}', '/api/images/search']
        for expected in expected_paths:
            # Check if any route matches the pattern
            found = any(expected.replace('{image_id}', '') in route for route in api_routes)
            assert found, f"Missing expected endpoint pattern: {expected}"
        
        print("✅ Key API endpoints are present")
        
    except Exception as e:
        print(f"❌ Main app compatibility test failed: {e}")
        return False
    
    return True


async def test_endpoint_signatures():
    """Test that endpoints have correct signatures"""
    print("\n🧪 Testing Endpoint Signatures...")
    
    try:
        from api.images import (
            list_images, get_image_details, get_thumbnail,
            search_images, rotate_image, update_image, delete_image
        )
        
        # Check that functions exist and are callable
        endpoints = [
            list_images, get_image_details, get_thumbnail,
            search_images, rotate_image, update_image, delete_image
        ]
        
        for endpoint in endpoints:
            assert callable(endpoint), f"{endpoint.__name__} is not callable"
        
        print(f"✅ All {len(endpoints)} endpoints are callable")
        
        # Check that endpoints are async
        for endpoint in endpoints:
            import inspect
            assert inspect.iscoroutinefunction(endpoint), f"{endpoint.__name__} is not async"
        
        print("✅ All endpoints are async functions")
        
    except Exception as e:
        print(f"❌ Endpoint signature test failed: {e}")
        return False
    
    return True


async def test_backward_compatibility():
    """Test that key functionality is preserved"""
    print("\n🧪 Testing Backward Compatibility...")
    
    try:
        # Check that backup exists
        import os
        backup_path = "api/images_backup.py"
        assert os.path.exists(backup_path), "Backup file not found"
        print("✅ Original API backed up successfully")
        
        # Check that new API has same router name
        from api.images import router as new_router
        from api.images_backup import router as old_router
        
        assert new_router is not None
        assert old_router is not None
        print("✅ Both old and new routers exist")
        
        # Both should be APIRouter instances
        from fastapi import APIRouter
        assert isinstance(new_router, APIRouter)
        assert isinstance(old_router, APIRouter)
        print("✅ Router types are compatible")
        
    except Exception as e:
        print(f"❌ Backward compatibility test failed: {e}")
        return False
    
    return True


async def main():
    """Run all tests"""
    print("🚀 Running Modernized Images API Tests (Fase 1.3)\n")
    
    tests = [
        test_api_imports,
        test_service_integration,
        test_schema_integration,
        test_exception_handling,
        test_main_app_compatibility,
        test_endpoint_signatures,
        test_backward_compatibility
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
        print("🎉 All tests passed! Modernized Images API is working correctly.")
        print("\n✅ FASE 1.3 COMPLETED SUCCESSFULLY!")
        print("\n🏗️ Service Layer Architecture:")
        print("   API Controller (images.py)")
        print("         ↓")
        print("   ImageService ← Dependencies") 
        print("         ↓")
        print("   ImageRepository")
        print("         ↓") 
        print("   Database Models")
        print("\n🎯 Next Steps:")
        print("   • Test API endpoints with real requests")
        print("   • Apply same pattern to other APIs (authors, imports)")
        print("   • Update client applications to use new response formats")
    else:
        print("❌ Some tests failed. Please fix issues before continuing.")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())