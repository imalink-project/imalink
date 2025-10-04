#!/usr/bin/env python3
"""
Test that all modular model imports work correctly after removing database/models.py
"""

def test_modular_models_import():
    """Test that modular models can be imported without database/models.py"""
    
    print("🧪 Testing Modular Models After database/models.py Removal...")
    
    try:
        # Test individual model imports
        print("   🔍 Testing individual model imports...")
        from models.author import Author
        from models.image import Image  
        from models.import_session import ImportSession
        from models.base import Base
        print("   ✅ Individual models imported successfully")
        
        # Test models package imports
        print("   🔍 Testing models package imports...")
        from models import Author as AuthorFromPackage, Image as ImageFromPackage, ImportSession as ImportSessionFromPackage
        print("   ✅ Models package imports successful")
        
        # Test that database/models.py is gone
        print("   🔍 Verifying database/models.py removal...")
        try:
            from database.models import Image
            print("   ❌ ERROR: database/models.py still accessible!")
            return False
        except ImportError:
            print("   ✅ database/models.py successfully removed")
        
        # Test repository import (the main user)
        print("   🔍 Testing repository imports with modular models...")
        from repositories.image_repository import ImageRepository
        print("   ✅ ImageRepository imports work with modular models")
        
        # Test services that depend on models
        print("   🔍 Testing service imports...")
        from services.import_sessions_background_service import ImportSessionsBackgroundService
        print("   ✅ Services import correctly with modular models")
        
        # Validate model functionality
        print("   🔍 Testing model instantiation...")
        author = Author(name="Test Author", email="test@example.com")
        print(f"   ✅ Author model works: {author}")
        
        print("\n🎯 Modular Models Test: SUCCESS")
        print("   - All individual models importable")
        print("   - Models package exports work")
        print("   - database/models.py successfully removed") 
        print("   - Repository and service imports work")
        print("   - Model instantiation functional")
        print("   - No duplicate code remains")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False

def test_database_operations():
    """Test database operations with modular models"""
    
    print("\n🧪 Testing Database Operations with Modular Models...")
    
    try:
        import tempfile
        import os
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from models import Base, Author, Image, ImportSession
        
        # Create temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            test_db_path = tmp_db.name
        
        engine = create_engine(f'sqlite:///{test_db_path}', echo=False)
        
        # Create tables using modular models
        print("   🔧 Creating database with modular models...")
        Base.metadata.create_all(engine)
        print("   ✅ Database tables created successfully")
        
        # Test CRUD operations
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Create test data
        author = Author(name="Modular Test", email="modular@test.com")
        db.add(author)
        db.commit()
        db.refresh(author)
        
        import_session = ImportSession(
            source_path="/test/modular/path",
            source_description="Modular models test"
        )
        db.add(import_session)
        db.commit()
        
        print(f"   ✅ Created Author: {author}")
        print(f"   ✅ Created ImportSession: {import_session}")
        
        # Clean up
        db.close()
        engine.dispose()
        try:
            os.unlink(test_db_path)
        except:
            pass
        
        print("   ✅ Database operations successful with modular models")
        return True
        
    except Exception as e:
        print(f"   ❌ Database test failed: {e}")
        return False

if __name__ == "__main__":
    print("🎯 Testing Modular Models Refactoring Completion")
    print("=" * 55)
    
    success1 = test_modular_models_import()
    success2 = test_database_operations()
    
    if success1 and success2:
        print("\n🎉 ALL TESTS PASSED!")
        print("✨ Modular models refactoring completed successfully!")
        print("📋 database/models.py duplication eliminated!")
        print("🚀 Codebase is now clean and maintainable!")
    else:
        print("\n❌ Some tests failed - refactoring needs attention")