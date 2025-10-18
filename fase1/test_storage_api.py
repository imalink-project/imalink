#!/usr/bin/env python3
"""
Test script for new storage info API endpoints and computed properties
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from database.connection import get_db_sync
from repositories.image_file_repository import ImageFileRepository
from repositories.photo_repository import PhotoRepository
from services.image_file_service import ImageFileService
from services.photo_service import PhotoService

def test_storage_info():
    """Test storage info functionality"""
    print("🧪 Testing refactored Photo and ImageFile models...")
    
    # Get database session
    db_session = get_db_sync()
    
    # Create repositories and services
    image_file_repo = ImageFileRepository(db_session)
    photo_repo = PhotoRepository(db_session)
    
    image_file_service = ImageFileService(db_session)
    photo_service = PhotoService(db_session)
    
    try:
        # Get image files
        image_files, total = image_file_repo.get_image_files(limit=10)
        print(f"Found {len(image_files)} image files (total: {total})")
        
        if image_files:
            image_file = image_files[0]
            print(f"\n📸 ImageFile ID: {image_file.image_id}")
            print(f"   Filename: {image_file.filename}")
            print(f"   Hothash: {image_file.hothash}")
            print(f"   Import session ID: {image_file.import_session_id}")
            print(f"   Imported time: {image_file.imported_time}")
            print(f"   Imported info: {image_file.imported_info}")
            print(f"   Local storage info: {image_file.local_storage_info}")
            print(f"   Cloud storage info: {image_file.cloud_storage_info}")
            
            # Test storage info service
            print(f"\n🔧 Testing storage info service...")
            storage_info = image_file_service.get_storage_info(image_file.image_id)
            print(f"   Service returned: {storage_info}")
            
            # Get related Photo and test computed properties
            photos, total = photo_repo.get_photos(limit=10)
            if photos:
                photo = photos[0]
                print(f"\n📷 Photo hothash: {photo.hothash}")
                print(f"   Import sessions: {photo.import_sessions}")
                print(f"   First imported: {photo.first_imported}")
                print(f"   Last imported: {photo.last_imported}")
                
                # Test PhotoService response conversion
                photo_response = photo_service._convert_to_response(photo)
                print(f"\n🔄 PhotoResponse:")
                print(f"   Import sessions: {photo_response.import_sessions}")
                print(f"   First imported: {photo_response.first_imported}")  
                print(f"   Last imported: {photo_response.last_imported}")
                
        print(f"\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        db_session.close()

if __name__ == "__main__":
    test_storage_info()