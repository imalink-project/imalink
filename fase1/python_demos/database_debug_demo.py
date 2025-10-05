#!/usr/bin/env python3
"""
Database Debug Demo

Demo all debug endpoints to inspect database structure and contents.
"""

import requests
import sys
import json
from datetime import datetime


def print_section(title):
    """Print a section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def main():
    print("🔍 ImaLink Database Debug Demo")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    base_url = "http://localhost:8000/api/v1/debug"
    
    # Test connection first
    try:
        health_response = requests.get("http://localhost:8000/health", timeout=3)
        if not health_response.ok:
            print("❌ Server health check failed!")
            return 1
        print("✅ Server is running")
    except:
        print("❌ Cannot connect to server!")
        print("Start server: cd fase1/src && uv run python main.py")
        return 1
    
    try:
        # 1. Development Status
        print_section("1. DEVELOPMENT STATUS")
        response = requests.get(f"{base_url}/status")
        if response.ok:
            data = response.json()
            print("✅ Development Status:")
            print(f"   Development Mode: {data.get('development_mode', 'Unknown')}")
            print(f"   Database URL: {data.get('database_url', 'Unknown')}")
            print(f"   Data Directory: {data.get('data_directory', 'Unknown')}")
            print(f"   Environment: {data.get('environment', 'Unknown')}")
        else:
            print(f"❌ Status check failed: {response.status_code}")
        
        # 2. Database Statistics
        print_section("2. DATABASE STATISTICS")
        response = requests.get(f"{base_url}/database-stats")
        if response.ok:
            data = response.json()
            print("✅ Database Statistics:")
            table_counts = data.get('table_counts', {})
            
            for table, count in table_counts.items():
                print(f"   📊 {table}: {count} rows")
            
            total_rows = sum(v for v in table_counts.values() if isinstance(v, int))
            print(f"   📈 Total rows: {total_rows}")
        else:
            print(f"❌ Database stats failed: {response.status_code}")
        
        # 3. Database Schema
        print_section("3. DATABASE SCHEMA")
        response = requests.get(f"{base_url}/database-schema")
        if response.ok:
            data = response.json()
            print("✅ Database Schema:")
            tables = data.get('tables', {})
            
            for table_name, table_info in tables.items():
                print(f"\n   📋 Table: {table_name} ({table_info.get('row_count', 0)} rows)")
                columns = table_info.get('columns', [])
                
                for col in columns:
                    pk_marker = " 🔑" if col.get('primary_key') else ""
                    nn_marker = " ⚠️" if col.get('not_null') else ""
                    print(f"     • {col.get('name', 'unknown')}: {col.get('type', 'unknown')}{pk_marker}{nn_marker}")
            
            print(f"\n   📊 Total tables: {data.get('total_tables', 0)}")
        else:
            print(f"❌ Database schema failed: {response.status_code}")
            print(f"   Error: {response.text}")
        
        # 4. Available Routes
        print_section("4. AVAILABLE DEBUG ROUTES")
        debug_response = requests.get("http://localhost:8000/debug/routes")
        if debug_response.ok:
            print("✅ Available Routes:")
            routes = debug_response.json()
            debug_routes = [r for r in routes if 'debug' in r.get('path', '')]
            
            for route in debug_routes:
                print(f"   🔗 {route.get('method', 'GET')} {route.get('path', 'unknown')}")
        else:
            print("❌ Could not fetch routes")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1
    
    print_section("🎉 DEBUG DEMO COMPLETED")
    print("Database inspection demo completed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())