"""
API Testing Demo - ImaLink Streamlit Demo
=========================================

Test alle API-endepunkter direkte med request/response visning.
"""

import streamlit as st
import requests
import json
from pathlib import Path
import sys

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Konfigurasjon
API_BASE = "http://localhost:8000/api/v1"

def main():
    st.header("🔗 API Testing Demo")
    st.markdown("Test alle ImaLink API-endepunkter og se request/response data")
    
    # Sidebar for konfigurasjon
    st.sidebar.header("⚙️ API Configuration")
    api_base = st.sidebar.text_input("API Base URL", value=API_BASE)
    
    # API endpoint selector
    st.sidebar.subheader("🎯 Select Endpoint")
    
    endpoints = {
        "Import Sessions": {
            "GET /import_sessions/": ("GET", "/import_sessions/", {}),
            "POST /import_sessions/": ("POST", "/import_sessions/", {
                "source_directory": "C:/temp/test",
                "source_description": "API Test Import",
                "copy_files": True
            }),
            "GET /import_sessions/{id}": ("GET", "/import_sessions/1", {}),
            "GET /import_sessions/status/{id}": ("GET", "/import_sessions/status/1", {})
        },
        "Images": {
            "GET /images/": ("GET", "/images/", {}),
            "GET /images/{id}": ("GET", "/images/1", {}),
            "GET /images/recent": ("GET", "/images/recent", {}),
            "GET /images/statistics/overview": ("GET", "/images/statistics/overview", {}),
            "GET /images/author/{id}": ("GET", "/images/author/1", {})
        },
        "Authors": {
            "GET /authors/": ("GET", "/authors/", {}),
            "POST /authors/": ("POST", "/authors/", {
                "name": "Test Author",
                "email": "test@example.com"
            }),
            "GET /authors/{id}": ("GET", "/authors/1", {}),
            "GET /authors/search/": ("GET", "/authors/search/?q=test", {}),
            "GET /authors/statistics/": ("GET", "/authors/statistics/", {})
        },
        "Debug": {
            "GET /debug/routes": ("GET", "/debug/routes", {}),
            "GET /health": ("GET", "/health", {})
        }
    }
    
    # Category selection
    category = st.sidebar.selectbox("API Category", list(endpoints.keys()))
    endpoint_name = st.sidebar.selectbox("Endpoint", list(endpoints[category].keys()))
    
    method, path, default_body = endpoints[category][endpoint_name]
    
    # Main content
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📤 Request")
        
        # Method and URL
        st.code(f"{method} {api_base}{path}")
        
        # Request body for POST/PUT
        if method in ["POST", "PUT"]:
            st.markdown("**Request Body:**")
            request_body = st.text_area(
                "JSON Body",
                value=json.dumps(default_body, indent=2),
                height=200,
                help="Edit the JSON request body"
            )
        else:
            request_body = "{}"
        
        # Query parameters
        st.markdown("**Query Parameters:**")
        query_params = st.text_input(
            "Parameters",
            placeholder="limit=10&offset=0",
            help="Add query parameters (format: key=value&key2=value2)"
        )
        
        # Execute button
        if st.button(f"🚀 Execute {method} Request", type="primary", use_container_width=True):
            execute_request(api_base, method, path, request_body, query_params)
    
    with col2:
        st.subheader("📥 Response")
        
        # Response will be shown here by execute_request function
        if 'response_data' not in st.session_state:
            st.info("👆 Select an endpoint and click Execute to see the response")
        else:
            show_response()
    
    # Quick actions
    st.markdown("---")
    st.subheader("⚡ Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Get System Status", use_container_width=True):
            quick_request("GET", "/health")
    
    with col2:
        if st.button("📈 Get Image Stats", use_container_width=True):
            quick_request("GET", "/images/statistics/overview")
    
    with col3:
        if st.button("📋 List Recent Imports", use_container_width=True):
            quick_request("GET", "/import_sessions/")


def execute_request(api_base, method, path, request_body, query_params):
    """Execute API request and store response in session state"""
    try:
        # Build URL
        url = f"{api_base}{path}"
        if query_params:
            separator = "&" if "?" in path else "?"
            url += f"{separator}{query_params}"
        
        # Prepare request
        headers = {"Content-Type": "application/json"}
        
        # Execute request
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=30)
        elif method == "POST":
            body = json.loads(request_body) if request_body.strip() else {}
            response = requests.post(url, json=body, headers=headers, timeout=30)
        elif method == "PUT":
            body = json.loads(request_body) if request_body.strip() else {}
            response = requests.put(url, json=body, headers=headers, timeout=30)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=30)
        else:
            st.error(f"❌ Unsupported method: {method}")
            return
        
        # Store response
        st.session_state['response_data'] = {
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'url': url,
            'method': method,
            'text': response.text
        }
        
        # Try to parse JSON
        try:
            st.session_state['response_data']['json'] = response.json()
        except:
            st.session_state['response_data']['json'] = None
        
        # Show success message
        if 200 <= response.status_code < 300:
            st.success(f"✅ Request successful: {response.status_code}")
        else:
            st.error(f"❌ Request failed: {response.status_code}")
            
    except json.JSONDecodeError:
        st.error("❌ Invalid JSON in request body")
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Network error: {str(e)}")
        st.info("💡 Make sure API server is running on localhost:8000")


def quick_request(method, path):
    """Quick request execution for buttons"""
    execute_request(API_BASE, method, path, "{}", "")


def show_response():
    """Display the stored response data"""
    if 'response_data' not in st.session_state:
        return
    
    response = st.session_state['response_data']
    
    # Status and basic info
    status_color = "🟢" if 200 <= response['status_code'] < 300 else "🔴"
    st.markdown(f"**Status:** {status_color} {response['status_code']}")
    st.markdown(f"**URL:** `{response['url']}`")
    
    # Response tabs
    resp_tab1, resp_tab2, resp_tab3 = st.tabs(["📄 JSON", "📋 Raw", "ℹ️ Headers"])
    
    with resp_tab1:
        if response.get('json'):
            st.json(response['json'])
        else:
            st.info("📝 Response is not valid JSON")
            st.code(response['text'])
    
    with resp_tab2:
        st.code(response['text'])
    
    with resp_tab3:
        st.json(response['headers'])


if __name__ == "__main__":
    main()