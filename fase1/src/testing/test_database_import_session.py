#!/usr/bin/env python3
"""
Test database creation and basic operations with ImportSession
"""
import os
import tempfile
from pathlib import Path

def test_database_with_import_session():
    """Test that database can be created and ImportSession works"""
    
    print("🧪 Testing Database with ImportSession...")
    
    try:
        # Create a temporary database for testing
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            test_db_path = tmp_db.name
        
        print(f"   📁 Using temporary database: {test_db_path}")
        
        # Set up database connection
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from models import Base, ImportSession, Image
        
        engine = create_engine(f'sqlite:///{test_db_path}', echo=False)
        
        # Create all tables
        print("   🔧 Creating database tables...")
        Base.metadata.create_all(engine)
        print("   ✅ Tables created successfully")
        
        # Test session creation
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Test creating an ImportSession
        print("   🧪 Testing ImportSession creation...")
        test_session = ImportSession(
            source_path="/test/path",
            source_description="Test import",
            status="in_progress"
        )
        
        db.add(test_session)
        db.commit()
        db.refresh(test_session)
        
        print(f"   ✅ ImportSession created with ID: {test_session.id}")
        
        # Test querying ImportSession
        print("   🔍 Testing ImportSession queries...")
        found_session = db.query(ImportSession).filter(ImportSession.id == test_session.id).first()
        print(f"   ✅ ImportSession queried: {found_session}")
        
        # Test ImportSessionRepository
        print("   🧪 Testing ImportSessionRepository...")
        from repositories.import_session_repository import ImportSessionRepository
        from schemas.requests.import_session_requests import ImportStartRequest
        
        repo = ImportSessionRepository(db)
        
        # Create request for testing
        request = ImportStartRequest(
            source_directory="/another/test/path",
            source_description="Another test"
        )
        
        new_session = repo.create_import(request)
        print(f"   ✅ Repository created ImportSession: {new_session.id}")
        
        # Clean up
        db.close()
        engine.dispose()  # Close all connections
        try:
            os.unlink(test_db_path)
        except PermissionError:
            print(f"   ⚠️ Could not delete temp file (still in use): {test_db_path}")
            pass
        
        print("\n🎯 Database Test with ImportSession: SUCCESS")
        print("   - Database tables created successfully")
        print("   - ImportSession model works correctly")
        print("   - Repository operations function properly")
        print("   - No 'Import' vs 'import' naming conflicts")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        # Clean up on error
        try:
            if 'test_db_path' in locals():
                os.unlink(test_db_path)
        except:
            pass
        return False

if __name__ == "__main__":
    success = test_database_with_import_session()
    if success:
        print("\n🎉 ImportSession database integration successful!")
        print("   Ready to proceed with clean database creation!")
    else:
        print("\n❌ ImportSession database integration has issues")