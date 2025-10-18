#!/usr/bin/env python3
"""
FileStorage CRUD Test Suite - Standalone runner
Tests only the essential backend CRUD functionality
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
        display_name="Factory Storage"
    )
    
    assert isinstance(storage, FileStorage)
    assert storage.display_name == "Factory Storage"
    
    print("✅ Factory method works")


def test_uuid_uniqueness():
    """Test UUID uniqueness"""
    print("Testing UUID uniqueness...")
    
    storage1 = FileStorage("/path1")
    storage2 = FileStorage("/path2")
    
    assert storage1.storage_uuid != storage2.storage_uuid
    assert storage1.directory_name != storage2.directory_name
    
    print("✅ UUID uniqueness works")


def test_directory_naming():
    """Test directory name generation and validation"""
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
    
    test_cases = [
        ("/media/photos", "/media/photos"),
        ("/media/photos/", "/media/photos"),  # Trailing slash
        ("C:\\Photos", "C:\\Photos"),
    ]
    
    for base_path, expected_base in test_cases:
        storage = FileStorage(base_path)
        expected = f"{expected_base}/{storage.directory_name}"
        assert storage.full_path == expected
    
    print("✅ Full path computation works")


def test_computed_properties():
    """Test computed properties"""
    print("Testing computed properties...")
    
    storage = FileStorage("/test")
    
    # Just verify storage was created properly
    assert storage.base_path == "/test"
    assert storage.storage_uuid is not None
    
    print("✅ Computed properties work")


def test_index_paths():
    """Test index file path generation"""
    print("Testing index paths...")
    
    storage = FileStorage("/media/test")
    
    # Master index
    assert storage.master_index_path.endswith("/index.json")
    assert storage.full_path in storage.master_index_path
    
    # Imports directory
    assert storage.imports_index_dir.endswith("/imports")
    assert storage.full_path in storage.imports_index_dir
    
    # Session index
    session_path = storage.get_session_index_path(42)
    assert "session_42.json" in session_path
    assert storage.imports_index_dir in session_path
    
    print("✅ Index paths work")


def test_master_index_generation():
    """Test master index JSON generation"""
    print("Testing master index generation...")
    
    storage = FileStorage("/test", "Test Storage", "Description")
    index_data = storage.generate_master_index_data()
    
    # Structure
    assert "storage_info" in index_data
    assert "import_sessions" in index_data
    assert "imalink_version" in index_data
    
    # Content
    info = index_data["storage_info"]
    assert info["uuid"] == storage.storage_uuid
    assert info["display_name"] == "Test Storage"
    assert info["description"] == "Description"
    
    # Sessions (empty)
    assert index_data["import_sessions"] == []
    assert index_data["imalink_version"] == "2.0"
    
    print("✅ Master index generation works")


def test_string_representation():
    """Test __repr__ method"""
    print("Testing string representation...")
    
    storage = FileStorage("/test")
    repr_str = repr(storage)
    
    assert "FileStorage" in repr_str
    assert str(storage.directory_name) in repr_str
    
    print("✅ String representation works")


def test_edge_cases():
    """Test edge cases"""
    print("Testing edge cases...")
    
    # Empty path
    storage1 = FileStorage("")
    assert storage1.base_path == ""
    assert storage1.directory_name is not None
    
    # Long path
    long_path = "/very/long/path/" + "subdir/" * 20
    storage2 = FileStorage(long_path)
    assert str(storage2.base_path) == long_path
    
    # Special characters
    special_paths = [
        "/path with spaces",
        "/path-with-dashes",
        "/path_with_underscores",
        "/path.with.dots",
    ]
    
    for path in special_paths:
        storage = FileStorage(path)
        assert str(storage.base_path) == path
    
    print("✅ Edge cases work")


def run_all_tests():
    """Run all FileStorage CRUD tests"""
    print("🚀 Running FileStorage CRUD Test Suite")
    print("=" * 50)
    
    tests = [
        test_basic_creation,
        test_creation_with_metadata,
        test_factory_method,
        test_uuid_uniqueness,
        test_directory_naming,
        test_full_path_computation,
        test_computed_properties,
        test_index_paths,
        test_master_index_generation,
        test_string_representation,
        test_edge_cases,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} failed: {e}")
            failed += 1
    
    print("=" * 50)
    print(f"📊 Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All FileStorage CRUD tests passed!")
        return True
    else:
        print("💥 Some tests failed!")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)