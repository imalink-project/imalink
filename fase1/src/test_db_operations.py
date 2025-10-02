"""
Debug background task - minimal test to see what's failing
"""

def test_simple_image_creation():
    """Test creating a single Image record"""
    try:
        from database.connection import get_db_sync
        from models import Image
        from datetime import datetime
        import hashlib
        
        db = get_db_sync()
        
        # Try creating a simple image record
        test_image = Image(
            original_filename="test.jpg",
            file_path="C:\\test\\test.jpg",
            file_size=12345,
            file_format=".jpg",
            import_source="debug_test",
            width=800,
            height=600,
            image_hash=hashlib.md5(b"test_content").hexdigest()
        )
        
        print(f"Created image object: {test_image}")
        
        # Try to add to database
        db.add(test_image)
        db.commit()
        
        print(f"✅ Successfully created image with ID: {test_image.id}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to create image: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_import_session_update():
    """Test updating Import"""
    try:
        from database.connection import get_db_sync
        from models import Import
        
        db = get_db_sync()
        
        # Get latest session
        session = db.query(Import).order_by(Import.id.desc()).first()
        if session:
            print(f"Found session: {session.id}, status: {session.status}")
            
            # Try updating it
            old_imported = session.images_imported
            session.images_imported = (session.images_imported or 0) + 1
            db.commit()
            
            print(f"✅ Updated images_imported from {old_imported} to {session.images_imported}")
        else:
            print("No sessions found")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to update session: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== Testing Database Operations ===")
    
    print("\n1. Testing Image creation:")
    img_success = test_simple_image_creation()
    
    print("\n2. Testing Import update:")
    session_success = test_import_session_update()
    
    print(f"\nResults:")
    print(f"Image creation: {'✅ PASS' if img_success else '❌ FAIL'}")
    print(f"Session update: {'✅ PASS' if session_success else '❌ FAIL'}")
