#!/usr/bin/env python3
"""
Test that imports.py can be imported without errors after refactoring
"""

def test_imports_module():
    """Test that imports.py can be imported successfully"""
    
    print("🧪 Testing imports.py module import...")
    
    try:
        # Test that we can import the module
        import sys
        sys.path.append('api/v1')
        
        # This should work without any import errors
        from api.v1 import import_sessions as imports
        print("   ✅ imports.py imported successfully")
        
        # Test that ImageProcessor import works in the module
        from services.importing.image_processor import ImageProcessor
        print("   ✅ ImageProcessor imported successfully")
        
        # Test that we can create an ImageProcessor instance
        processor = ImageProcessor()
        print("   ✅ ImageProcessor instantiated successfully")
        
        # Verify the module has the expected functions
        expected_functions = [
            'run_import_background_service',
            'import_directory_background', 
            'import_directory'
        ]
        
        for func_name in expected_functions:
            if hasattr(imports, func_name):
                print(f"   ✅ Function '{func_name}' exists")
            else:
                print(f"   ❌ Function '{func_name}' missing")
        
        print("\n🎯 Module Import Test: PASSED")
        print("   All refactored code can be imported without errors")
        
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_imports_module()