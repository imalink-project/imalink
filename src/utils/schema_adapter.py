"""
Adapter for converting old PhotoCreateSchema (imalink-core v1) to new structure (imalink-schemas v2).

Old structure (from imalink-core v1):
- hotpreview_base64, primary_filename, camera_make at root level
- No user_id, rating, visibility
- No image_file_list

New structure (imalink-schemas v2):
- hotpreview_base64, image_file_list
- exif_dict contains camera_make, iso, etc.
- user_id, rating, category, visibility included
"""
from typing import Dict, Any


def adapt_old_photo_create_schema(
    old_schema: Dict[str, Any],
    rating: int = 0,
    category: str | None = None,
    visibility: str = "private",
    import_session_id: int | None = None,
    author_id: int | None = None,
) -> Dict[str, Any]:
    """
    Convert old PhotoCreateSchema to new structure.
    
    IMPORTANT: user_id is NOT included - backend sets it from JWT token.
    
    Args:
        old_schema: Old format from imalink-core v1
        rating: Star rating
        category: Photo category
        visibility: Visibility level
        import_session_id: Import session ID
        author_id: Author ID
        
    Returns:
        New PhotoCreateSchema format (without user_id)
    """
    # Build exif_dict from flat fields
    exif_dict = old_schema.get("exif_dict", {}).copy()
    
    # Move camera fields into exif_dict if they're at root
    for field in ["camera_make", "camera_model", "iso", "aperture", "shutter_speed", 
                  "focal_length", "lens_model", "lens_make"]:
        if field in old_schema and field not in exif_dict:
            exif_dict[field] = old_schema[field]
    
    # Build image_file_list from primary_filename
    image_file_list = []
    if "primary_filename" in old_schema:
        image_file_list.append({
            "filename": old_schema["primary_filename"],
            "file_size": old_schema.get("file_size_bytes", 0),
        })
    
    # Build new schema (WITHOUT user_id - backend adds it)
    new_schema = {
        "hothash": old_schema["hothash"],
        "hotpreview_base64": old_schema["hotpreview_base64"],
        "exif_dict": exif_dict if exif_dict else None,
        "width": old_schema["width"],
        "height": old_schema["height"],
        "taken_at": old_schema.get("taken_at"),
        "gps_latitude": old_schema.get("gps_latitude"),
        "gps_longitude": old_schema.get("gps_longitude"),
        "rating": rating,
        "category": category,
        "visibility": visibility,
        "import_session_id": import_session_id,
        "author_id": author_id,
        "stack_id": None,
        "timeloc_correction": None,
        "view_correction": None,
        "image_file_list": image_file_list,
    }
    
    # Optional coldpreview
    if "coldpreview_base64" in old_schema:
        new_schema["coldpreview_base64"] = old_schema["coldpreview_base64"]
    
    return new_schema
