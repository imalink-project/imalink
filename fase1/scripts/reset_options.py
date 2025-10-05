#!/usr/bin/env python3
"""
Database Reset Options

Multiple ways to reset the database during development.
Choose the method that works best for your situation.
"""

def show_reset_options():
    """Show all available database reset options"""
    
    print("🔄 ImaLink Database Reset Options")
    print("=" * 50)
    print()
    print("Choose your reset method:")
    print()
    
    print("1️⃣  🌐 API Reset (Recommended)")
    print("   Command: uv run python scripts/api_fresh_start.py")
    print("   ✅ Uses debug API endpoint")
    print("   ✅ Server must be running")
    print("   ✅ Safe and controlled")
    print()
    
    print("2️⃣  💥 Nuclear Reset")
    print("   Command: uv run python scripts/nuclear_reset.py")
    print("   ✅ Direct file deletion")
    print("   ✅ Best when server is stopped")
    print("   ⚠️  Can fail if server holds file lock")
    print("   ⚠️  Requires server restart if running")
    print()
    
    print("3️⃣  📋 Full Reset Script")
    print("   Command: uv run python scripts/reset_database.py")
    print("   ✅ Complete reset with verification")
    print("   ✅ Creates backup")
    print("   ✅ Detailed logging")
    print()
    
    print("4️⃣  🔗 Direct API Call")
    print("   Command: curl -X POST 'http://localhost:8000/api/v1/debug/reset-database?confirm=DELETE_EVERYTHING'")
    print("   ✅ One-liner for quick resets")
    print("   ⚠️  No confirmation prompts")
    print()
    
    print("💡 Quick Start Workflow:")
    print("   1. uv run python scripts/api_fresh_start.py")
    print("   2. uv run python python_demos/health_demo.py")
    print("   3. Start experimenting!")
    print()
    
    print("⚠️  All methods DELETE ALL DATA!")
    print("⚠️  Only use during development/experimentation!")

if __name__ == "__main__":
    show_reset_options()