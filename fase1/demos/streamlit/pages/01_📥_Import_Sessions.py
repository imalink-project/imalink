"""
Import Sessions Demo - ImaLink Streamlit Demo
============================================

Interaktiv testing av import-funksjonalitet med arkivering og real-time status.
"""

import streamlit as st
import requests
import json
from pathlib import Path
import time
import sys

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Konfigurasjon
API_BASE = "http://localhost:8000/api/v1"

def main():
    st.header("📥 Import Sessions Demo")
    st.markdown("Test bildeimport med arkivering og real-time progress tracking")
    
    # Sidebar for konfigurasjon
    st.sidebar.header("⚙️ Konfigurasjon")
    api_base = st.sidebar.text_input("API Base URL", value=API_BASE)

    # Main content
    tab1, tab2, tab3 = st.tabs(["🚀 Import Test", "📊 Status", "🔍 API Explorer"])

    with tab1:
        st.subheader("Start Import Session")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📂 Import Configuration**")
            source_dir = st.text_input(
                "Source Directory", 
                value="C:/temp/PHOTOS_SRC_TEST_MICRO",
                help="Sti til mappen med bilder"
            )
            
            description = st.text_input(
                "Beskrivelse", 
                value="Streamlit Test Import"
            )
            
            # Storage options (fra integrert import_once)
            st.markdown("**🗃️ Archive Options**")
            archive_base_path = st.text_input(
                "Archive Base Path (valgfri)",
                value="C:/temp/00imalink_data",
                placeholder="Base mappe for arkiv - det lages automatisk unik undermappe med imalink_YYYYMMDD_uuid format"
            )
            
            storage_subfolder = st.text_input(
                "Storage Subfolder (valgfri)",
                placeholder="f.eks. 2025-10-04_test"
            )
            
            copy_files = st.checkbox("Copy Files to Archive", value=True, help="Kopiér filer til arkiv (anbefalt)")
        
        with col2:
            st.markdown("**🎛️ Import Controls**")
            
            if st.button("🚀 Start Import", type="primary", use_container_width=True):
                if not source_dir:
                    st.error("❌ Source directory kan ikke være tom!")
                elif not Path(source_dir).exists():
                    st.error(f"❌ Directory '{source_dir}' finnes ikke!")
                else:
                    # Build request payload
                    payload = {
                        "source_directory": source_dir,
                        "source_description": description,
                        "copy_files": copy_files
                    }
                    
                    if archive_base_path:
                        payload["archive_base_path"] = archive_base_path
                    
                    if storage_subfolder:
                        payload["storage_subfolder"] = storage_subfolder
                    
                    # Make API call
                    try:
                        with st.spinner("🔄 Starter import..."):
                            response = requests.post(f"{api_base}/import_sessions/", json=payload, timeout=30)
                        
                        if response.status_code == 200:
                            result = response.json()
                            st.success(f"✅ Import startet! Session ID: {result.get('import_id')}")
                            st.session_state['current_import_id'] = result.get('import_id')
                            st.json(result)
                        else:
                            st.error(f"❌ Import feilet: {response.status_code}")
                            st.code(response.text)
                    
                    except requests.exceptions.RequestException as e:
                        st.error(f"❌ Nettverksfeil: {str(e)}")
                        st.info("💡 Sjekk at API serveren kjører på localhost:8000")

    with tab2:
        st.subheader("📊 Import Status & Progress")
        
        # Manual session ID input
        col1, col2 = st.columns([2, 1])
        with col1:
            session_id = st.number_input(
                "Session ID", 
                value=st.session_state.get('current_import_id', 1),
                min_value=1,
                help="ID for import session å sjekke"
            )
        with col2:
            auto_refresh = st.checkbox("Auto-refresh", value=False)
        
        if st.button("🔄 Refresh Status") or auto_refresh:
            try:
                response = requests.get(f"{api_base}/import_sessions/status/{session_id}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Status overview
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Status", data.get('status', 'Unknown'))
                    with col2:  
                        st.metric("Files Found", data.get('total_files_found', 0))
                    with col3:
                        st.metric("Imported", data.get('images_imported', 0))
                    with col4:
                        st.metric("Files Copied", data.get('files_copied', 0))
                    
                    # Progress bar
                    total = data.get('total_files_found', 0)
                    imported = data.get('images_imported', 0)
                    if total > 0:
                        progress = imported / total
                        st.progress(progress, text=f"Import Progress: {imported}/{total} ({progress:.1%})")
                    
                    # Archive information
                    if data.get('storage_name'):
                        st.info(f"📁 Archive: {data.get('archive_base_path', 'N/A')}/{data.get('storage_name')}")
                    
                    # Detailed status
                    with st.expander("📋 Detailed Status"):
                        st.json(data)
                    
                    # Copy completion check
                    if data.get('status') == 'completed' and data.get('copy_files', False):
                        files_copied = data.get('files_copied', 0)
                        if files_copied > 0:
                            st.success(f"✅ Storage Copy fullført! {files_copied} filer kopiert til arkiv")
                        else:
                            st.warning("⚠️ Import fullført, men ingen filer ble kopiert til storage")
                
                else:
                    st.error(f"❌ Kunne ikke hente status: {response.status_code}")
                    st.code(response.text)
            
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Nettverksfeil: {str(e)}")
        
        if auto_refresh:
            time.sleep(2)
            st.rerun()

    with tab3:
        st.subheader("🔍 API Explorer")
        st.markdown("Test andre API endepunkter direkte")
        
        endpoint_option = st.selectbox(
            "Velg endpoint",
            [
                "GET /import_sessions/",
                "GET /images/",
                "GET /authors/",
                "GET /images/statistics/overview"
            ]
        )
        
        if st.button("📡 Call API"):
            endpoint_map = {
                "GET /import_sessions/": f"{api_base}/import_sessions/",
                "GET /images/": f"{api_base}/images/",  
                "GET /authors/": f"{api_base}/authors/",
                "GET /images/statistics/overview": f"{api_base}/images/statistics/overview"
            }
            
            try:
                url = endpoint_map[endpoint_option]
                response = requests.get(url)
                
                st.code(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    st.json(data)
                else:
                    st.error(f"Error: {response.text}")
            
            except requests.exceptions.RequestException as e:
                st.error(f"Request failed: {str(e)}")

if __name__ == "__main__":
    main()