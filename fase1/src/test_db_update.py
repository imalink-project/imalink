"""
Simple test to check if Import updates work correctly
"""

def test_database_update():
    """Test basic database operations"""
    try:
        from database.connection import get_db_sync
        from models import Import
        from datetime import datetime
        
        db = get_db_sync()
        
        # Try to get a session
        session = db.query(Import).first()
        if session:
            print(f"Found session: {session.id}, status: {session.status}")
            
            # Try to update it
            old_status = session.status
            session.status = "testing"
            db.commit()
            
            print(f"Updated status from {old_status} to {session.status}")
            
            # Change it back
            session.status = old_status
            db.commit()
            
            print(f"Restored status to {session.status}")
            
        else:
            print("No sessions found - creating a test session")
            
            test_session = Import(
                source_path="C:\\test",
                source_description="Test session",
                status="test"
            )
            
            db.add(test_session)
            db.commit()
            
            print(f"Created test session: {test_session.id}")
            
            # Try to update it
            test_session.status = "updated"
            test_session.total_files_found = 42
            db.commit()
            
            print(f"Updated test session: status={test_session.status}, files={test_session.total_files_found}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing database operations...")
    success = test_database_update()
    print(f"Test result: {'PASS' if success else 'FAIL'}")
