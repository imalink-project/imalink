"""
Image Gallery Demo - ImaLink Streamlit Demo
===========================================

Bla gjennom og søk i importerte bilder med metadata visning.
"""

import streamlit as st
import requests
import json
from pathlib import Path
from datetime import datetime
import sys

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Konfigurasjon
API_BASE = "http://localhost:8000/api/v1"

def main():
    st.header("🖼️ Image Gallery Demo")
    st.markdown("Bla gjennom importerte bilder og utforsk metadata")
    
    # Sidebar for konfigurasjon
    st.sidebar.header("⚙️ Gallery Settings")
    api_base = st.sidebar.text_input("API Base URL", value=API_BASE)
    
    # Image listing controls
    st.sidebar.subheader("🔍 Search & Filter")
    author_filter = st.sidebar.selectbox("Filter by Author", ["All Authors"] + get_authors(api_base))
    limit = st.sidebar.slider("Images per page", 5, 50, 20)
    show_metadata = st.sidebar.checkbox("Show detailed metadata", value=True)
    
    # Main content
    tab1, tab2 = st.tabs(["📷 Image Grid", "📊 Statistics"])
    
    with tab1:
        st.subheader("Image Collection")
        
        # Load images
        try:
            params = {"limit": limit}
            if author_filter != "All Authors":
                # In a real implementation, you'd need author ID
                pass
                
            response = requests.get(f"{api_base}/images/", params=params)
            
            if response.status_code == 200:
                data = response.json()
                images = data.get('data', []) if isinstance(data, dict) else data
                
                if images:
                    st.info(f"📸 Found {len(images)} images")
                    
                    # Display images in grid
                    cols = 3
                    rows = (len(images) + cols - 1) // cols
                    
                    for row in range(rows):
                        columns = st.columns(cols)
                        
                        for col_idx in range(cols):
                            img_idx = row * cols + col_idx
                            if img_idx < len(images):
                                image = images[img_idx]
                                
                                with columns[col_idx]:
                                    # Image card
                                    st.markdown(f"**{image.get('original_filename', 'Unknown')}**")
                                    
                                    # Basic info
                                    if image.get('width') and image.get('height'):
                                        st.caption(f"📐 {image['width']} × {image['height']}")
                                    
                                    if image.get('file_size'):
                                        size_mb = image['file_size'] / (1024 * 1024)
                                        st.caption(f"💾 {size_mb:.1f} MB")
                                    
                                    # Hash info
                                    hash_short = image.get('image_hash', '')[:12] + "..." if image.get('image_hash') else 'N/A'
                                    st.caption(f"🔗 {hash_short}")
                                    
                                    # Metadata expander
                                    if show_metadata:
                                        with st.expander(f"🔍 Details #{image.get('id', 'N/A')}"):
                                            # EXIF info
                                            if image.get('taken_at'):
                                                st.text(f"📅 Taken: {image['taken_at']}")
                                            
                                            # GPS info  
                                            if image.get('gps_latitude') and image.get('gps_longitude'):
                                                st.text(f"🌍 GPS: {image['gps_latitude']:.6f}, {image['gps_longitude']:.6f}")
                                            
                                            # File info
                                            st.text(f"📂 Path: {image.get('file_path', 'N/A')}")
                                            st.text(f"🏷️ Format: {image.get('file_format', 'N/A')}")
                                            
                                            # Import info
                                            if image.get('import_session_id'):
                                                st.text(f"📥 Import ID: {image['import_session_id']}")
                                            
                                            # Raw JSON
                                            with st.expander("📋 Raw JSON"):
                                                st.json(image)
                else:
                    st.info("📭 No images found. Try importing some images first!")
                    if st.button("🚀 Go to Import Demo"):
                        st.switch_page("01_📥_Import_Sessions.py")
                    
            else:
                st.error(f"❌ Failed to load images: {response.status_code}")
                st.code(response.text)
                
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Network error: {str(e)}")
            st.info("💡 Make sure API server is running on localhost:8000")
    
    with tab2:
        st.subheader("📊 Image Statistics")
        
        # Load statistics
        try:
            response = requests.get(f"{api_base}/images/statistics/overview")
            
            if response.status_code == 200:
                stats = response.json()
                
                # Key metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Images", stats.get('total_images', 0))
                with col2:
                    st.metric("Total Size", f"{stats.get('total_size_gb', 0):.1f} GB")
                with col3:
                    st.metric("Unique Hashes", stats.get('unique_hashes', 0))
                with col4:
                    st.metric("Authors", stats.get('total_authors', 0))
                
                # Recent activity
                if stats.get('recent_imports'):
                    st.subheader("📈 Recent Activity")
                    st.json(stats['recent_imports'])
                
                # Detailed stats
                with st.expander("📋 Detailed Statistics"):
                    st.json(stats)
                    
            else:
                st.error(f"❌ Failed to load statistics: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Network error: {str(e)}")


def get_authors(api_base):
    """Fetch available authors for filtering"""
    try:
        response = requests.get(f"{api_base}/authors/")
        if response.status_code == 200:
            data = response.json()
            authors = data.get('data', []) if isinstance(data, dict) else data
            return [author.get('name', f"ID {author.get('id')}") for author in authors]
    except:
        pass
    return []


if __name__ == "__main__":
    main()