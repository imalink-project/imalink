"""
Test script to verify all componen                json_data = '{"source_path": "C:\\temp\\test", "source_description": "Test"}'   source_path=\"C:\\test\",s load correctly
"""

def test_imports():
    """Test that all modules can be imported"""
    tests = [
        ("main", "from main import app"),
        ("models", "from models import Image, Author, ImportSession"),
        ("database", "from database.connection import get_db"),
        ("import_service", "from services.import_session_service import ImportSessionService"),
        ("import_repository", "from repositories.import_session_repository import ImportSessionRepository"),
        ("import_requests", "from schemas.requests.import_session_requests import ImportStartRequest"),
        ("import_api", "from api.v1.import_sessions import router"),
        ("dependencies", "from core.dependencies import get_import_service")
    ]
    
    results = {}
    
    for name, import_stmt in tests:
        try:
            exec(import_stmt)
            results[name] = "✅ OK"
        except Exception as e:
            results[name] = f"❌ ERROR: {e}"
    
    print("Component Import Test Results:")
    print("=" * 50)
    for name, result in results.items():
        print(f"{name:20}: {result}")
    
    # Test creating request object
    print("\nTesting ImportStartRequest creation:")
    try:
        from schemas.requests.import_session_requests import ImportStartRequest
        
        # Test with source_directory
        request1 = ImportStartRequest(
            source_directory="C:\\test",
            source_description="Test"
        )
        print(f"✅ Request created: source_path={request1.source_path}")
        print(f"✅ Property access: source_path={request1.source_path}")
        
        # Test JSON parsing (simulating API call)
        import json
        json_data = '{"source_directory": "C:\\\\temp\\\\test", "source_description": "Test"}'
        parsed_data = json.loads(json_data)
        request2 = ImportStartRequest(**parsed_data)
        print(f"✅ JSON parsing works: {request2.source_path}")
        
    except Exception as e:
        print(f"❌ ImportStartRequest test failed: {e}")

if __name__ == "__main__":
    test_imports()
