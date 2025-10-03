"""
Modernized API endpoints for importing images using Service Layer
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from core.dependencies import get_import_service
from services.import_service import ImportService
from schemas.requests.import_requests import ImportStartRequest, ImportTestRequest
from schemas.responses.import_responses import (
    ImportResponse, ImportStartResponse, ImportListResponse,
    ImportTestResponse
)
from schemas.common import SingleResponse
from core.exceptions import APIException
import datetime as dt

router = APIRouter()


@router.get("/test")
async def test_endpoint():
    """Simple test endpoint to verify routing works"""
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info("🎯 TEST ENDPOINT HIT!")
    print("🎯 TEST ENDPOINT HIT!", flush=True)
    return {"message": "Test endpoint works!", "timestamp": "2025-10-02", "routing_confirmed": True}


def simple_background_test():
    """Simple test function to verify background tasks work"""
    print("🎯 SIMPLE BACKGROUND TASK EXECUTED!")


def run_import_background_service(import_id: int, source_directory: str):
    """Run import using service layer in background"""
    import datetime
    import os
    
    # Write to a debug file to confirm this function runs
    debug_file = "C:/temp/import_debug.txt"
    
    try:
        with open(debug_file, "a", encoding="utf-8") as f:
            f.write(f"{dt.datetime.now()} - 🚀 BACKGROUND SERVICE: Starting import for session {import_id}\n")
            f.write(f"{dt.datetime.now()} - 📦 BACKGROUND SERVICE: Processing directory {source_directory}\n")
        
        # Import here to avoid circular imports
        from database.connection import get_db_sync
        from services.import_service import ImportService
        
        # Get database connection and service
        db = get_db_sync()
        import_service = ImportService(db)
        
        # Actually process the import using direct database calls for now
        from pathlib import Path
        from models import Image, Import
        import hashlib
        
        # Find image files
        source_path = Path(source_directory)
        image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.webp'}
        image_files = []
        
        for ext in image_extensions:
            image_files.extend(source_path.rglob(f'*{ext}'))
            image_files.extend(source_path.rglob(f'*{ext.upper()}'))
        
        # Update session with file count
        from sqlalchemy import text
        session = db.query(Import).filter(Import.id == import_id).first()
        if session:
            # Use direct update to avoid SQLAlchemy column assignment issues
            db.execute(text(f"UPDATE imports SET total_files_found = {len(image_files)} WHERE id = {import_id}"))
            db.commit()
        
        images_processed = 0
        duplicates_skipped = 0
        errors_count = 0
        
        # Process each image file
        for image_file in image_files:
            try:
                # Check if image already exists (by hash)
                with open(image_file, 'rb') as f:
                    file_content = f.read()
                    file_hash = hashlib.md5(file_content).hexdigest()
                
                existing_image = db.query(Image).filter(Image.image_hash == file_hash).first()
                if existing_image:
                    duplicates_skipped += 1
                    with open(debug_file, "a", encoding="utf-8") as f:
                        f.write(f"{dt.datetime.now()} - ⏭️ Duplicate skipped: {image_file.name} (already exists)\n")
                    continue
                
                # Create new image record with EXIF data
                from PIL import Image as PILImage, ImageOps
                from PIL.ExifTags import GPSTAGS
                import json
                
                # Extract image dimensions, EXIF data, date taken, and GPS coordinates
                width, height = 0, 0
                exif_data = None
                taken_at = None
                gps_latitude = None
                gps_longitude = None
                
                try:
                    with PILImage.open(image_file) as img:
                        # Get dimensions from properly rotated image
                        img_rotated = ImageOps.exif_transpose(img)
                        width, height = img_rotated.size
                        
                        # Extract EXIF data
                        exif = img.getexif()
                        if exif:
                            # Store EXIF as JSON
                            exif_dict = {}
                            for tag_id, value in exif.items():
                                try:
                                    tag = PILImage.ExifTags.TAGS.get(tag_id, tag_id)
                                    exif_dict[str(tag)] = str(value)
                                except:
                                    pass
                            
                            if exif_dict:
                                exif_data = json.dumps(exif_dict).encode('utf-8')
                            
                            # Try to extract date taken
                            date_taken = exif.get(36867) or exif.get(306)  # DateTimeOriginal or DateTime
                            if date_taken:
                                try:
                                    taken_at = dt.datetime.strptime(date_taken, '%Y:%m:%d %H:%M:%S')
                                except:
                                    pass
                            
                            # Extract GPS coordinates using GPS IFD
                            try:
                                gps_ifd = exif.get_ifd(0x8825)  # GPS IFD tag
                                if gps_ifd and len(gps_ifd) > 0:
                                    gps_data = {}
                                    for key in gps_ifd.keys():
                                        name = GPSTAGS.get(key, key)
                                        gps_data[name] = gps_ifd[key]
                                    
                                    # Convert GPS coordinates to decimal degrees
                                    def convert_to_degrees(value):
                                        d, m, s = value
                                        return d + (m / 60.0) + (s / 3600.0)
                                    
                                    if 'GPSLatitude' in gps_data and 'GPSLatitudeRef' in gps_data:
                                        lat = convert_to_degrees(gps_data['GPSLatitude'])
                                        if gps_data['GPSLatitudeRef'] == 'S':
                                            lat = -lat
                                        gps_latitude = lat
                                    
                                    if 'GPSLongitude' in gps_data and 'GPSLongitudeRef' in gps_data:
                                        lon = convert_to_degrees(gps_data['GPSLongitude'])
                                        if gps_data['GPSLongitudeRef'] == 'W':
                                            lon = -lon
                                        gps_longitude = lon
                            except Exception:
                                # GPS extraction failed, but that's OK - not all images have GPS
                                pass
                except Exception:
                    # EXIF extraction failed, continue with basic file info
                    pass

                new_image = Image(
                    image_hash=file_hash,
                    original_filename=image_file.name,
                    file_path=str(image_file),
                    file_size=image_file.stat().st_size,
                    import_source=f"Import {import_id}",
                    width=width,
                    height=height,
                    exif_data=exif_data,
                    taken_at=taken_at,
                    gps_latitude=gps_latitude,
                    gps_longitude=gps_longitude
                )
                
                db.add(new_image)
                db.commit()  # Commit immediately to avoid duplicate constraint issues
                images_processed += 1
                
                with open(debug_file, "a", encoding="utf-8") as f:
                    f.write(f"{dt.datetime.now()} - ✅ Imported {image_file.name}\n")
                
            except Exception as e:
                # Check if it's a duplicate error (integrity constraint) vs real error
                if "UNIQUE constraint failed: images.image_hash" in str(e):
                    duplicates_skipped += 1
                    with open(debug_file, "a", encoding="utf-8") as f:
                        f.write(f"{dt.datetime.now()} - ⏭️ Duplicate detected via DB constraint: {image_file.name}\n")
                else:
                    errors_count += 1
                    with open(debug_file, "a", encoding="utf-8") as f:
                        f.write(f"{dt.datetime.now()} - ❌ Error processing {image_file.name}: {e}\n")
        
        # Final database update - success if no real errors, even with duplicates
        final_status = 'completed' if errors_count == 0 else 'failed'
        with open(debug_file, "a", encoding="utf-8") as f:
            f.write(f"\n{dt.datetime.now()} - 🏁 Import completed!\n")
            f.write(f"  📊 Final stats: {images_processed} imported, {duplicates_skipped} duplicates, {errors_count} errors\n")
            f.write(f"  🎯 Status: {final_status}\n")
        db.execute(text(f"UPDATE imports SET images_imported = {images_processed}, duplicates_skipped = {duplicates_skipped}, errors_count = {errors_count}, status = '{final_status}', completed_at = CURRENT_TIMESTAMP WHERE id = {import_id}"))
        db.commit()
        
        result = {
            'images_processed': images_processed,
            'duplicates_skipped': duplicates_skipped,  
            'errors_count': errors_count
        }
        
        with open(debug_file, "a", encoding="utf-8") as f:
            f.write(f"{dt.datetime.now()} - ✅ Processed {result.get('images_processed', 0)} images\n")
            f.write(f"{dt.datetime.now()} - ⚠️ Skipped {result.get('duplicates_skipped', 0)} duplicates\n")
            f.write(f"{dt.datetime.now()} - ❌ Errors: {result.get('errors_count', 0)}\n")
        
        with open(debug_file, "a", encoding="utf-8") as f:
            f.write(f"{dt.datetime.now()} - ✅ BACKGROUND SERVICE: Import completed for session {import_id}\n")
        
    except Exception as e:
        with open(debug_file, "a", encoding="utf-8") as f:
            f.write(f"{dt.datetime.now()} - ❌ BACKGROUND SERVICE ERROR: {e}\n")
        import traceback
        traceback.print_exc()
    finally:
        if 'db' in locals():
            db.close()


def import_directory_background(import_id: int, source_path: str, source_description: str):
    """
    Background task to import all images from a directory
    """
    db = None
    try:
        print(f"🚀 BACKGROUND TASK STARTED - session {import_id}, path: {source_path}")
        
        from database.connection import get_db_sync
        from datetime import datetime
        from pathlib import Path
        import hashlib
        from models import Import, Image
        
        print(f"📦 Imports completed, getting database connection...")
        
        # Get database connection
        db = get_db_sync()
        print(f"✅ Database connection obtained")
        
        # Get database connection
        db = get_db_sync()
        
        # Get the Import
        session = db.query(Import).filter(Import.id == import_id).first()
        if not session:
            print(f"Import {import_id} not found")
            return
        
        # Update session status to processing
        session.status = "processing"
        db.commit()
        
        # Check if directory exists
        source_dir = Path(source_path)
        if not source_dir.exists():
            raise Exception(f"Directory {source_path} does not exist")
        if not source_dir.is_dir():
            raise Exception(f"{source_path} is not a directory")
        
        # Find all image files
        image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.webp'}
        image_files = []
        
        for ext in image_extensions:
            image_files.extend(source_dir.rglob(f'*{ext}'))
            image_files.extend(source_dir.rglob(f'*{ext.upper()}'))
        
        print(f"Found {len(image_files)} image files")
        
        # Update total files count
        session.total_files_found = len(image_files)
        db.commit()
        
        # Process each image file
        for i, image_file in enumerate(image_files):
            try:
                print(f"Processing {image_file.name} ({i+1}/{len(image_files)})")
                
                # Check if image already exists (by hash)
                with open(image_file, 'rb') as f:
                    file_content = f.read()
                    file_hash = hashlib.md5(file_content).hexdigest()
                
                existing_image = db.query(Image).filter(Image.image_hash == file_hash).first()
                if existing_image:
                    session.duplicates_skipped += 1
                    print(f"Duplicate skipped: {image_file.name}")
                    continue
                
                # Create new image record
                new_image = Image(
                    image_hash=file_hash,
                    original_filename=image_file.name,
                    file_path=str(image_file),
                    file_size=image_file.stat().st_size,
                    import_import_id=import_id
                )
                
                db.add(new_image)
                session.images_imported += 1
                
                # Update progress
                progress = ((i + 1) / len(image_files)) * 100
                session.progress_percentage = progress
                
                # Check for RAW files
                raw_extensions = {'.raw', '.cr2', '.nef', '.arw', '.dng', '.orf', '.rw2'}
                if image_file.suffix.lower() in raw_extensions:
                    session.raw_files_skipped += 1
                    print(f"RAW file noted: {image_file.name}")
                    continue
                
                # Update progress every 10 files
                if (i + 1) % 10 == 0:
                    db.commit()
                    progress = ((i + 1) / len(image_files)) * 100
                    print(f"Progress: {progress:.1f}% ({i + 1}/{len(image_files)})")
                
            except Exception as e:
                session.errors_count += 1
                print(f"Error processing {image_file.name}: {e}")
        
        # Final update - mark as completed
        session.status = "completed"
        session.completed_at = datetime.utcnow()
        db.commit()
        
        print(f"Background import completed for session {import_id}")
        print(f"Summary: {session.images_imported} imported, {session.duplicates_skipped} duplicates, {session.errors_count} errors")
        
    except Exception as e:
        print(f"Background import failed for session {import_id}: {e}")
        import traceback
        traceback.print_exc()
        
        # Try to mark session as failed
        if db and import_id:
            try:
                session = db.query(Import).filter(Import.id == import_id).first()
                if session:
                    session.status = "failed"
                    session.error_message = str(e)
                    db.commit()
            except:
                print("Could not update session status to failed")
    
    finally:
        if db:
            db.close()


@router.post("/", response_model=ImportStartResponse)
async def import_directory(
    request: ImportStartRequest,
    background_tasks: BackgroundTasks,
    import_service: ImportService = Depends(get_import_service)
):
    """
    Main import endpoint - import directory
    """
    import sys
    print("🔥 API ENDPOINT HIT - import_directory called", file=sys.stderr, flush=True)
    print("🔥 API ENDPOINT HIT - import_directory called")
    debug_info = {"endpoint_hit": True, "source_directory": request.source_directory}
    try:
        response = await import_service.start_import(request)
        debug_info["service_called"] = True
        
        # Start background import task using threading - return debug info in response
        import threading
        
        debug_info = {
            "threading_approach": True,
            "import_id": response.import_id,
            "source_directory": request.source_directory
        }
        
        try:
            # Start simple test in thread
            test_thread = threading.Thread(target=simple_background_test)
            test_thread.daemon = True
            test_thread.start()
            debug_info["test_thread_started"] = True
            
            # Start actual import in thread
            import_thread = threading.Thread(
                target=run_import_background_service,
                args=(response.import_id, request.source_directory)
            )
            import_thread.daemon = True
            import_thread.start()
            debug_info["import_thread_started"] = True
            
        except Exception as e:
            debug_info["thread_error"] = str(e)
        
        # Add debug info to response object
        if hasattr(response, 'debug_info'):
            response.debug_info = debug_info
        else:
            # If we can't add to response, at least we know threading was attempted
            pass
            
        return response
        
    except Exception as e:
        if "does not exist" in str(e) or "must be a directory" in str(e):
            raise HTTPException(status_code=400, detail=str(e))
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.post("/start", response_model=ImportStartResponse)
async def start_import(
    request: ImportStartRequest,
    background_tasks: BackgroundTasks,
    import_service: ImportService = Depends(get_import_service)
):
    """
    Start an import process for a directory
    """
    print("🔥 /start ENDPOINT HIT - start_import called")
    try:
        response = await import_service.start_import(request)
        
        # Start background import task
        background_tasks.add_task(
            import_directory_background,
            response.import_id,
            request.source_path,
            request.source_description
        )
        
        return response
        
    except Exception as e:
        if "does not exist" in str(e) or "must be a directory" in str(e):
            raise HTTPException(status_code=400, detail=str(e))
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.get("/status/{import_id}", response_model=ImportResponse)
async def get_import_status(
    import_id: int, 
    import_service: ImportService = Depends(get_import_service)
):
    """
    Get status of an Import
    """
    try:
        return await import_service.get_import_status(import_id)
    except Exception as e:
        if "not found" in str(e):
            raise HTTPException(status_code=404, detail="Import not found")
        raise HTTPException(status_code=500, detail=f"Error getting status: {str(e)}")


@router.get("/", response_model=ImportListResponse)
async def list_imports(
    import_service: ImportService = Depends(get_import_service)
):
    """
    List all import imports
    """
    try:
        return await import_service.list_imports()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing imports: {str(e)}")


def import_directory_background(import_id: int, source_path: str, source_description: str):
    """
    Background task to import all images from a directory
    """
    db = None
    try:
        print(f"🚀 BACKGROUND TASK STARTED - session {import_id}, path: {source_path}")
        
        from database.connection import get_db_sync
        from datetime import datetime
        from pathlib import Path
        import hashlib
        from models import Import, Image
        
        print(f"📦 Imports completed, getting database connection...")
        
        # Get database connection
        db = get_db_sync()
        print(f"✅ Database connection obtained")
        
        # Get database connection
        db = get_db_sync()
        
        # Get the Import
        session = db.query(Import).filter(Import.id == import_id).first()
        if not session:
            print(f"Import {import_id} not found")
            return
        
        # Update session status to processing
        session.status = "processing"
        db.commit()
        
        # Check if directory exists
        source_dir = Path(source_path)
        if not source_dir.exists():
            print(f"Source directory does not exist: {source_path}")
            session.status = "failed"
            session.error_message = f"Source directory does not exist: {source_path}"
            db.commit()
            return
            
        # Find image files
        image_files = []
        for ext in ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp']:
            image_files.extend(source_dir.rglob(f"*{ext}"))
            image_files.extend(source_dir.rglob(f"*{ext.upper()}"))
        
        print(f"Found {len(image_files)} image files in {source_path}")
        
        # Update session with total files found
        session.total_files_found = len(image_files)
        session.images_imported = 0
        session.duplicates_skipped = 0
        session.errors_count = 0
        db.commit()
        
        # Process each image file
        for i, image_file in enumerate(image_files):
            try:
                # Check if already exists (simple filename check for now)
                existing = db.query(Image).filter(Image.original_filename == image_file.name).first()
                if existing:
                    session.duplicates_skipped += 1
                    print(f"Skipping duplicate: {image_file.name}")
                else:
                    # Create new image record with proper hash and EXIF data
                    try:
                        from PIL import Image as PILImage, ImageOps
                        import json
                        
                        file_size = image_file.stat().st_size
                        
                        # Generate unique hash from file content
                        with open(image_file, 'rb') as f:
                            file_content = f.read()
                            unique_hash = hashlib.md5(file_content).hexdigest()
                        
                        # Extract image dimensions, EXIF data, date taken, and GPS coordinates
                        width, height = 0, 0
                        exif_data = None
                        taken_at = None
                        gps_latitude = None
                        gps_longitude = None
                        
                        try:
                            with PILImage.open(image_file) as img:
                                # Get dimensions from properly rotated image
                                img_rotated = ImageOps.exif_transpose(img)
                                width, height = img_rotated.size
                                
                                # Extract EXIF data
                                exif = img.getexif()
                                if exif:
                                    # Store EXIF as JSON
                                    exif_dict = {}
                                    for tag_id, value in exif.items():
                                        try:
                                            tag = PILImage.ExifTags.TAGS.get(tag_id, tag_id)
                                            exif_dict[str(tag)] = str(value)
                                        except:
                                            pass
                                    
                                    if exif_dict:
                                        exif_data = json.dumps(exif_dict).encode('utf-8')
                                    
                                    # Try to extract date taken
                                    date_taken = exif.get(36867) or exif.get(306)  # DateTimeOriginal or DateTime
                                    if date_taken:
                                        try:
                                            taken_at = dt.datetime.strptime(date_taken, '%Y:%m:%d %H:%M:%S')
                                        except:
                                            pass
                                    
                                    # Extract GPS coordinates if available - use GPS IFD
                                    try:
                                        gps_ifd = exif.get_ifd(0x8825)  # GPS IFD tag
                                        if gps_ifd and len(gps_ifd) > 0:
                                            from PIL.ExifTags import GPSTAGS
                                            gps_data = {}
                                            for key in gps_ifd.keys():
                                                name = GPSTAGS.get(key, key)
                                                gps_data[name] = gps_ifd[key]
                                            
                                            # Convert GPS coordinates to decimal degrees
                                            def convert_to_degrees(value):
                                                d, m, s = value
                                                return d + (m / 60.0) + (s / 3600.0)
                                            
                                            if 'GPSLatitude' in gps_data and 'GPSLatitudeRef' in gps_data:
                                                lat = convert_to_degrees(gps_data['GPSLatitude'])
                                                if gps_data['GPSLatitudeRef'] == 'S':
                                                    lat = -lat
                                                gps_latitude = lat
                                            
                                            if 'GPSLongitude' in gps_data and 'GPSLongitudeRef' in gps_data:
                                                lon = convert_to_degrees(gps_data['GPSLongitude'])
                                                if gps_data['GPSLongitudeRef'] == 'W':
                                                    lon = -lon
                                                gps_longitude = lon
                                    except Exception as gps_error:
                                        # GPS extraction failed, but that's OK - not all images have GPS
                                        pass
                        except Exception as exif_error:
                            print(f"Could not extract EXIF from {image_file.name}: {exif_error}")
                        
                        new_image = Image(
                            original_filename=image_file.name,
                            file_path=str(image_file),
                            file_size=file_size,
                            file_format=image_file.suffix.lower(),
                            import_source="directory_import",
                            width=width,
                            height=height,
                            image_hash=unique_hash,
                            exif_data=exif_data,
                            taken_at=taken_at,
                            gps_latitude=gps_latitude,
                            gps_longitude=gps_longitude
                        )
                        db.add(new_image)
                        session.images_imported += 1
                        print(f"Imported: {image_file.name} (hash: {unique_hash[:8]}...)")
                        
                    except Exception as img_error:
                        session.errors_count += 1
                        print(f"Error creating image record for {image_file.name}: {img_error}")
                        continue
                
                # Update progress every 10 files
                if (i + 1) % 10 == 0:
                    db.commit()
                    progress = ((i + 1) / len(image_files)) * 100
                    print(f"Progress: {progress:.1f}% ({i + 1}/{len(image_files)})")
                
            except Exception as e:
                session.errors_count += 1
                print(f"Error processing {image_file.name}: {e}")
        
        # Final update - mark as completed
        session.status = "completed"
        session.completed_at = datetime.utcnow()
        db.commit()
        
        print(f"Background import completed for session {import_id}")
        print(f"Summary: {session.images_imported} imported, {session.duplicates_skipped} duplicates, {session.errors_count} errors")
        
    except Exception as e:
        print(f"Background import failed for session {import_id}: {e}")
        import traceback
        traceback.print_exc()
        
        # Try to mark session as failed
        if db and import_id:
            try:
                session = db.query(Import).filter(Import.id == import_id).first()
                if session:
                    session.status = "failed"
                    session.error_message = str(e)
                    db.commit()
            except:
                print("Could not update session status to failed")
    
    finally:
        if db:
            db.close()


@router.post("/test-single", response_model=ImportTestResponse)  
async def test_single_image(
    request: ImportTestRequest,
    import_service: ImportService = Depends(get_import_service)
):
    """
    Test importing a single image file (for development/testing)
    """
    try:
        return await import_service.test_single_file(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test import failed: {str(e)}")


