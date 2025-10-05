#!/usr/bin/env python3
"""
Run All ImaLink Python Demos

Runs all available Python demos in sequence.
"""

import subprocess
import sys
from pathlib import Path


def run_demo(script_name, description):
    """Run a single demo script and return success status"""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run([
            "uv", "run", "python", f"python_demos/{script_name}"
        ], capture_output=False, text=True, cwd=Path(__file__).parent.parent)
        
        success = result.returncode == 0
        print(f"\n{'✅ PASSED' if success else '❌ FAILED'}: {script_name}")
        return success
        
    except Exception as e:
        print(f"❌ ERROR running {script_name}: {e}")
        return False


def main():
    print("🚀 ImaLink Python Demo Runner")
    print("Running all available demos...")
    
    demos = [
        ("health_demo.py", "Health Check - Server Status Demo"),
        ("author_demo.py", "Author API - Complete CRUD Demo"),
        ("api_demo_suite.py", "API Demo Suite - All Endpoints"),
        ("import_session_demo.py", "Import Session - Complete Workflow Demo")
    ]
    
    results = []
    
    for script, description in demos:
        success = run_demo(script, description)
        results.append((script, success))
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 DEMO SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for script, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}  {script}")
    
    print(f"\nResults: {passed}/{total} demos passed")
    
    if passed == total:
        print("🎉 All demos completed successfully!")
        return 0
    else:
        print(f"⚠️  {total - passed} demo(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())