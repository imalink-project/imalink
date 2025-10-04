"""
System Statistics Demo - ImaLink Streamlit Demo
===============================================

Overvåk system helse, ytelse og statistikker i real-time.
"""

import streamlit as st
import requests
import json
from pathlib import Path
from datetime import datetime, timedelta
import sys
import time

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Konfigurasjon
API_BASE = "http://localhost:8000/api/v1"

def main():
    st.header("📊 System Statistics Demo")
    st.markdown("Overvåk ImaLink system helse og ytelse i real-time")
    
    # Sidebar for konfigurasjon
    st.sidebar.header("⚙️ Monitoring Settings")
    api_base = st.sidebar.text_input("API Base URL", value=API_BASE)
    auto_refresh = st.sidebar.checkbox("Auto-refresh (30s)", value=False)
    
    # Refresh button
    if st.sidebar.button("🔄 Refresh Now") or auto_refresh:
        refresh_data(api_base)
    
    # Main dashboard
    tab1, tab2, tab3 = st.tabs(["🎯 Overview", "📈 Detailed Stats", "🔍 System Health"])
    
    with tab1:
        show_overview_dashboard(api_base)
    
    with tab2:
        show_detailed_statistics(api_base)
    
    with tab3:
        show_system_health(api_base)
    
    # Auto-refresh logic
    if auto_refresh:
        time.sleep(30)
        st.rerun()


def refresh_data(api_base):
    """Refresh all cached data"""
    st.session_state['last_refresh'] = datetime.now()
    # Clear any cached data to force refresh
    for key in list(st.session_state.keys()):
        if isinstance(key, str) and key.startswith('cache_'):
            del st.session_state[key]


def show_overview_dashboard(api_base):
    """Display main overview dashboard"""
    st.subheader("🎯 System Overview")
    
    # Key metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    # Get image statistics
    try:
        response = requests.get(f"{api_base}/images/statistics/overview", timeout=10)
        if response.status_code == 200:
            img_stats = response.json()
            
            with col1:
                st.metric(
                    "📷 Total Images", 
                    img_stats.get('total_images', 0),
                    delta=img_stats.get('images_today', 0)
                )
            
            with col2:
                total_size = img_stats.get('total_size_gb', 0)
                st.metric(
                    "💾 Storage Used", 
                    f"{total_size:.1f} GB"
                )
            
            with col3:
                unique_hashes = img_stats.get('unique_hashes', 0)
                total_images = img_stats.get('total_images', 0)
                if total_images > 0:
                    uniqueness = (unique_hashes / total_images) * 100
                    st.metric("🔗 Uniqueness", f"{uniqueness:.1f}%")
                else:
                    st.metric("🔗 Uniqueness", "N/A")
                    
        else:
            st.error("❌ Failed to load image statistics")
            
    except requests.exceptions.RequestException:
        st.error("❌ Cannot connect to API")
    
    # Get import session statistics  
    try:
        response = requests.get(f"{api_base}/import_sessions/", timeout=10)
        if response.status_code == 200:
            sessions_data = response.json()
            sessions = sessions_data.get('data', []) if isinstance(sessions_data, dict) else sessions_data
            
            with col4:
                active_imports = len([s for s in sessions if s.get('status') == 'in_progress'])
                st.metric(
                    "🔄 Active Imports", 
                    active_imports,
                    delta=len(sessions)
                )
    except:
        with col4:
            st.metric("🔄 Active Imports", "N/A")
    
    # Recent activity
    st.markdown("---")
    st.subheader("📈 Recent Activity")
    
    try:
        # Get recent images
        response = requests.get(f"{api_base}/images/recent?limit=5", timeout=10)
        if response.status_code == 200:
            recent_images = response.json()
            
            if recent_images:
                st.markdown("**🖼️ Recently Imported Images:**")
                for img in recent_images[:5]:
                    col1, col2, col3 = st.columns([3, 2, 2])
                    
                    with col1:
                        st.text(f"📄 {img.get('original_filename', 'Unknown')}")
                    with col2:
                        if img.get('width') and img.get('height'):
                            st.text(f"📐 {img['width']}×{img['height']}")
                    with col3:
                        if img.get('created_at'):
                            st.text(f"⏰ {img['created_at'][:19]}")
            else:
                st.info("📭 No recent images found")
                
    except requests.exceptions.RequestException:
        st.error("❌ Failed to load recent activity")


def show_detailed_statistics(api_base):
    """Show detailed system statistics"""
    st.subheader("📈 Detailed Statistics")
    
    # Authors statistics
    try:
        response = requests.get(f"{api_base}/authors/statistics/", timeout=10)
        if response.status_code == 200:
            author_stats = response.json()
            
            st.markdown("**👥 Author Statistics:**")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Authors", author_stats.get('total_authors', 0))
            with col2:
                st.metric("Active Authors", author_stats.get('authors_with_images', 0))
            with col3:
                avg_images = author_stats.get('average_images_per_author', 0)
                st.metric("Avg Images/Author", f"{avg_images:.1f}")
                
    except requests.exceptions.RequestException:
        st.warning("⚠️ Author statistics not available")
    
    # Import sessions breakdown
    try:
        response = requests.get(f"{api_base}/import_sessions/", timeout=10)
        if response.status_code == 200:
            sessions_data = response.json()
            sessions = sessions_data.get('data', []) if isinstance(sessions_data, dict) else sessions_data
            
            st.markdown("**📥 Import Sessions Breakdown:**")
            
            status_counts = {}
            total_files = 0
            total_imported = 0
            
            for session in sessions:
                status = session.get('status', 'unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
                total_files += session.get('total_files_found', 0)
                total_imported += session.get('images_imported', 0)
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("✅ Completed", status_counts.get('completed', 0))
            with col2:
                st.metric("🔄 In Progress", status_counts.get('in_progress', 0))
            with col3:
                st.metric("❌ Failed", status_counts.get('failed', 0))
            with col4:
                if total_files > 0:
                    success_rate = (total_imported / total_files) * 100
                    st.metric("Success Rate", f"{success_rate:.1f}%")
                else:
                    st.metric("Success Rate", "N/A")
            
            # Session details table
            if sessions:
                st.markdown("**📋 Recent Sessions:**")
                session_table_data = []
                
                for session in sessions[-10:]:  # Last 10 sessions
                    session_table_data.append({
                        "ID": session.get('id'),
                        "Status": session.get('status', 'Unknown'),
                        "Files": session.get('total_files_found', 0),
                        "Imported": session.get('images_imported', 0),
                        "Started": session.get('started_at', 'N/A')[:19] if session.get('started_at') else 'N/A'
                    })
                
                st.dataframe(session_table_data, use_container_width=True)
                
    except requests.exceptions.RequestException:
        st.warning("⚠️ Import session data not available")


def show_system_health(api_base):
    """Show system health and connectivity"""
    st.subheader("🔍 System Health Monitor")
    
    # API connectivity test
    endpoints_to_test = [
        ("Health Check", "/health"),
        ("Images API", "/images/?limit=1"),
        ("Authors API", "/authors/?limit=1"),
        ("Import Sessions", "/import_sessions/?limit=1"),
        ("Debug Routes", "/debug/routes")
    ]
    
    st.markdown("**🌐 API Endpoint Status:**")
    
    for name, endpoint in endpoints_to_test:
        col1, col2, col3 = st.columns([2, 1, 2])
        
        with col1:
            st.text(name)
        
        try:
            start_time = time.time()
            response = requests.get(f"{api_base}{endpoint}", timeout=5)
            response_time = (time.time() - start_time) * 1000
            
            with col2:
                if response.status_code == 200:
                    st.success("✅ OK")
                else:
                    st.error(f"❌ {response.status_code}")
            
            with col3:
                st.text(f"⏱️ {response_time:.0f}ms")
                
        except requests.exceptions.RequestException as e:
            with col2:
                st.error("❌ FAIL")
            with col3:
                st.text(f"💥 {str(e)[:30]}...")
    
    # System information
    st.markdown("---")
    st.markdown("**ℹ️ System Information:**")
    
    try:
        response = requests.get(f"{api_base}/debug/routes", timeout=10)
        if response.status_code == 200:
            routes_data = response.json()
            routes = routes_data.get('routes', [])
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("🛣️ Total Routes", len(routes))
                
            with col2:
                methods = set()
                for route in routes:
                    methods.update(route.get('methods', []))
                st.metric("📡 HTTP Methods", len(methods))
            
            # Route listing
            with st.expander("🔍 All Available Routes"):
                for route in routes:
                    methods_str = ", ".join(route.get('methods', []))
                    st.text(f"{methods_str:15} {route.get('path', 'Unknown')}")
                    
    except requests.exceptions.RequestException:
        st.warning("⚠️ Route information not available")
    
    # Last refresh time
    if 'last_refresh' in st.session_state:
        st.info(f"🕒 Last updated: {st.session_state['last_refresh'].strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()