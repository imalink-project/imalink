#!/usr/bin/env python3
"""
Quick test runner script - kjører de minimale route-testene
"""

import subprocess
import sys
from pathlib import Path

def run_tests():
    """Run the minimal route tests"""
    test_file = Path(__file__).parent / "test_routes.py"
    
    # Change to tests directory to run tests
    import os
    old_cwd = os.getcwd()
    os.chdir(Path(__file__).parent)
    
    print("🧪 Kjører minimale route-tester...")
    print("=" * 50)
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            str(test_file), 
            "-v",
            "--tb=short"  # Kortere error messages
        ], check=False)
        
        if result.returncode == 0:
            print("\n✅ Alle tester passerte!")
            print("📌 Rutene eksisterer og returnerer forventede statuskoder")
        else:
            print(f"\n❌ {result.returncode} tester feilet")
            print("🔍 Sjekk output over for detaljer")
        
        return result.returncode == 0
        
    except KeyboardInterrupt:
        print("\n⏹️  Tester avbrutt av bruker")
        return False
    except Exception as e:
        print(f"\n💥 Feil under kjøring av tester: {e}")
        return False
    finally:
        # Restore original working directory
        os.chdir(old_cwd)


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)