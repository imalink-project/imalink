#!/usr/bin/env python3
"""
FileStorage Simplified Test Suite - Updated after property removal
Tests only the essential backend CRUD functionality without removed properties
"""
import sys
from pathlib import Path
import re
from datetime import datetime

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from models.file_storage import FileStorage


def test_basic_creation():
    """Test basic FileStorage creation"""
    print("Testing basic creation...")
    
    storage = FileStorage("/media/photos")
    
    assert storage.base_path == "/media/photos"
    assert storage.storage_uuid is not None
    assert len(storage.storage_uuid) == 36  # UUID4 format
    assert storage.directory_name is not None
    
    print("✅ Basic creation works")


def test_creation_with_metadata():
    """Test creation with optional metadata"""
    print("Testing creation with metadata...")
    
    storage = FileStorage(
        base_path="/test/path",
        display_name="My Photos",
        description="Family collection"
    )
    
    assert storage.display_name == "My Photos"
    assert storage.description == "Family collection"
    
    print("✅ Metadata creation works")


def test_factory_method():
    """Test factory method"""
    print("Testing factory method...")
    
    storage = FileStorage.create_storage(
        base_path="/factory/test",
        display_name="Factory Created",
        description="Via factory"
    )
    
    assert storage.base_path == "/factory/test"
    assert storage.display_name == "Factory Created"
    assert storage.description == "Via factory"
    
    print("✅ Factory method works")


def test_uuid_uniqueness():
    """Test UUID uniqueness"""
    print("Testing UUID uniqueness...")
    
    storage1 = FileStorage("/test1")
    storage2 = FileStorage("/test2")
    
    assert storage1.storage_uuid != storage2.storage_uuid
    
    print("✅ UUID uniqueness works")


def test_directory_naming():
    """Test directory name generation"""
    print("Testing directory naming...")
    
    storage = FileStorage("/test")
    
    # Test format
    pattern = r'^imalink_\d{8}_\d{6}_[a-f0-9]{8}$'
    assert re.match(pattern, storage.directory_name) is not None
    
    # Test contains UUID part
    uuid_part = storage.storage_uuid[:8]
    assert uuid_part in storage.directory_name
    
    print("✅ Directory naming works")


def test_full_path_computation():
    """Test full path property"""
    print("Testing full path computation...")
    
    storage = FileStorage("/media/external")
    expected_path = f"/media/external/{storage.directory_name}"
    
    assert storage.full_path == expected_path
    
    print("✅ Full path computation works")


def test_index_paths():
    """Test index file path generation"""
    print("Testing index paths...")
    
    storage = FileStorage("/media/test")
    
    # Test master index path
    expected_master = f"{storage.full_path}/index.json"
    assert storage.master_index_path == expected_master
    
    # Test imports directory
    expected_imports = f"{storage.full_path}/imports"
    assert storage.imports_index_dir == expected_imports
    
    # Test session index path
    session_id = 123
    expected_session = f"{storage.full_path}/imports/session_123.json"
    assert storage.get_session_index_path(session_id) == expected_session
    
    print("✅ Index paths work")


def test_master_index_generation():
    """Test master index data generation"""
    print("Testing master index generation...")
    
    storage = FileStorage(
        base_path="/test/master",
        display_name="Test Storage",
        description="Description"
    )
    
    index_data = storage.generate_master_index_data()
    
    # Check structure
    assert "storage_info" in index_data
    assert "import_sessions" in index_data
    assert "imalink_version" in index_data
    
    # Check storage info
    info = index_data["storage_info"]
    assert info["uuid"] == storage.storage_uuid
    assert info["display_name"] == "Test Storage"
    assert info["description"] == "Description"
    
    # Sessions (empty)
    assert index_data["import_sessions"] == []
    assert index_data["imalink_version"] == "2.0"
    
    print("✅ Master index generation works")


def test_string_representation():
    """Test string representation"""
    print("Testing string representation...")
    
    storage = FileStorage("/test/repr")
    
    repr_str = repr(storage)
    assert f"FileStorage(id={storage.id}" in repr_str
    assert storage.directory_name in repr_str
    
    print("✅ String representation works")


def test_edge_cases():
    """Test edge cases and error conditions"""
    print("Testing edge cases...")
    
    # Empty base path should still work
    storage = FileStorage("")
    assert storage.base_path == ""
    assert storage.storage_uuid is not None
    
    # None metadata should work
    storage2 = FileStorage("/test", display_name=None, description=None)
    assert storage2.display_name is None
    assert storage2.description is None
    
    print("✅ Edge cases work")


def run_all_tests():
    """Run all tests"""
    print("🚀 Running FileStorage Simplified Test Suite")
    print("=" * 50)
    
    test_functions = [
        test_basic_creation,
        test_creation_with_metadata,
        test_factory_method,
        test_uuid_uniqueness,
        test_directory_naming,
        test_full_path_computation,
        test_index_paths,
        test_master_index_generation,
        test_string_representation,
        test_edge_cases
    ]
    
    passed = 0
    failed = 0
    
    for test_func in test_functions:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"❌ {test_func.__name__} failed: {e}")
            failed += 1
    
    print("=" * 50)
    print(f"📊 Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All FileStorage simplified tests passed!")
    else:
        print(f"⚠️ {failed} test(s) failed")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)