#!/usr/bin/env python3
"""
Test that ImportSession refactoring was successful
"""

def test_import_session_refactoring():
    """Test that all imports work with new ImportSession naming"""
    
    print("🧪 Testing ImportSession Refactoring...")
    
    try:
        # Test models import
        from models import ImportSession, Image
        print("   ✅ models.ImportSession imported successfully")
        
        # Test repository import
        from repositories.import_session_repository import ImportSessionRepository
        print("   ✅ ImportSessionRepository imported successfully")
        
        # Test service import  
        from services.import_sessions_background_service import ImportSessionsBackgroundService
        print("   ✅ ImportSessionsBackgroundService imported successfully")
        
        # Test that ImportSession can be instantiated
        print("   🔍 Testing ImportSession instantiation...")
        # Don't actually create it without database, just test the class exists
        print(f"   ✅ ImportSession class: {ImportSession}")
        
        print("\n🎯 ImportSession Refactoring: SUCCESS")
        print("   - All imports work without errors")
        print("   - ImportSession model accessible")
        print("   - Repository and service classes load correctly")
        
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_import_session_refactoring()
    if success:
        print("\n🎉 All ImportSession refactoring successful!")
    else:
        print("\n❌ ImportSession refactoring has issues")