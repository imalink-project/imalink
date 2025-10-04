#!/usr/bin/env python3
"""
Test script for Service Layer setup
Validates that all new components work correctly
"""

def test_imports():
    """Test that all new modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        from exceptions import APIException, NotFoundError, DuplicateImageError, ValidationError
        print("✅ Exceptions imported successfully")
        
        from dependencies import get_pagination_params
        print("✅ Dependencies imported successfully")
        
        from schemas.common import PaginatedResponse, SingleResponse, ErrorResponse
        print("✅ Common schemas imported successfully")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    return True


def test_exceptions():
    """Test exception functionality"""
    print("\n🧪 Testing exceptions...")
    
    try:
        from exceptions import NotFoundError, DuplicateImageError, ValidationError
        
        # Test NotFoundError
        try:
            raise NotFoundError("Image", 123)
        except NotFoundError as e:
            assert e.status_code == 404
            assert "Image with id 123 not found" in e.message
            print("✅ NotFoundError works correctly")
        
        # Test DuplicateImageError  
        try:
            raise DuplicateImageError("Custom duplicate message")
        except DuplicateImageError as e:
            assert e.status_code == 409
            assert e.code == "DUPLICATE_IMAGE"
            print("✅ DuplicateImageError works correctly")
            
        # Test ValidationError
        try:
            raise ValidationError("Invalid data", [{"field": "name", "message": "Required"}])
        except ValidationError as e:
            assert e.status_code == 422
            assert e.details["field_errors"]
            print("✅ ValidationError works correctly")
        
    except Exception as e:
        print(f"❌ Exception test failed: {e}")
        return False
    
    return True


def test_dependencies():
    """Test dependency functions"""
    print("\n🧪 Testing dependencies...")
    
    try:
        from dependencies import get_pagination_params, get_current_user
        
        # Test pagination params
        params = get_pagination_params(offset=10, limit=50)
        assert params["offset"] == 10
        assert params["limit"] == 50
        print("✅ Pagination params work correctly")
        
        # Test current user (placeholder)
        user = get_current_user()
        assert "id" in user
        print("✅ Current user placeholder works")
        
    except Exception as e:
        print(f"❌ Dependencies test failed: {e}")
        return False
    
    return True


def test_schemas():
    """Test schema functionality"""
    print("\n🧪 Testing schemas...")
    
    try:
        from schemas.common import PaginationMeta, create_paginated_response, create_success_response
        
        # Test PaginationMeta
        meta = PaginationMeta(total=100, offset=0, limit=10, page=1, pages=10)
        assert meta.total == 100
        print("✅ PaginationMeta works correctly")
        
        # Test helper functions
        response = create_paginated_response(data=[1, 2, 3], total=100, offset=0, limit=10)
        assert len(response.data) == 3
        assert response.meta.total == 100
        print("✅ Paginated response helper works")
        
        success = create_success_response("Operation completed")
        assert success.success == True
        assert success.message == "Operation completed"
        print("✅ Success response helper works")
        
    except Exception as e:
        print(f"❌ Schemas test failed: {e}")
        return False
    
    return True


def test_main_app():
    """Test that main app still works"""
    print("\n🧪 Testing main app compatibility...")
    
    try:
        from main import app
        assert app is not None
        print("✅ Main app loads successfully with new modules")
        
    except Exception as e:
        print(f"❌ Main app test failed: {e}")
        return False
    
    return True


if __name__ == "__main__":
    print("🚀 Running Service Layer Setup Tests\n")
    
    tests = [
        test_imports,
        test_exceptions, 
        test_dependencies,
        test_schemas,
        test_main_app
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        else:
            break  # Stop on first failure
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Service Layer setup is working correctly.")
        print("\n✅ Ready to proceed with Fase 1.2 - Image Service Implementation")
    else:
        print("❌ Some tests failed. Please fix issues before continuing.")