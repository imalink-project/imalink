"""
Test runner for ImaLink Fase 1 unit tests
Runs tests in organized categories with detailed reporting
"""
import subprocess
import sys
from pathlib import Path


def run_test_category(category_name, test_path):
    """Run tests for a specific category"""
    print(f"\n{'='*60}")
    print(f"🧪 RUNNING {category_name.upper()} TESTS")
    print(f"{'='*60}")
    
    try:
        # Run pytest with verbose output
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            str(test_path),
            "-v",  # Verbose output
            "--tb=short",  # Short traceback format
            "--capture=no",  # Don't capture output (show prints)
        ], capture_output=False, text=True)
        
        if result.returncode == 0:
            print(f"✅ {category_name} tests PASSED")
            return True
        else:
            print(f"❌ {category_name} tests FAILED")
            return False
            
    except Exception as e:
        print(f"❌ Error running {category_name} tests: {e}")
        return False


def main():
    """Run all test categories"""
    print("🚀 ImaLink Fase 1 Unit Test Runner")
    print("Testing modernized synchronous architecture")
    print("Updated: October 16, 2025")
    
    # Get test directory
    test_dir = Path(__file__).parent
    
    # Define test categories
    test_categories = [
        # API Layer Tests
        ("Authors API", test_dir / "api" / "test_authors_api.py"),
        ("Photos API", test_dir / "api" / "test_photos_api.py"),
        ("Images API", test_dir / "api" / "test_images_api.py"),
        ("ImportSessions API", test_dir / "api" / "test_import_sessions_api.py"),
        
        # Service Layer Tests
        ("Author Service", test_dir / "services" / "test_author_service.py"),
        ("Photo Service", test_dir / "services" / "test_photo_service.py"),
        
        # Model Tests
        ("Photo Model", test_dir / "models" / "test_photo.py"),
    ]
    
    # Track results
    results = {}
    
    # Run each test category
    for category_name, test_path in test_categories:
        if test_path.exists():
            results[category_name] = run_test_category(category_name, test_path)
        else:
            print(f"⚠️  Test file not found: {test_path}")
            results[category_name] = False
    
    # Print summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for success in results.values() if success)
    total = len(results)
    
    for category, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{category:25} {status}")
    
    print(f"\nOverall: {passed}/{total} test categories passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Ready for commit.")
        return 0
    else:
        print("🔧 Some tests failed. Please fix before committing.")
        return 1


if __name__ == "__main__":
    sys.exit(main())