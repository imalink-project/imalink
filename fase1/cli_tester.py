#!/usr/bin/env python3
"""
ImaLink CLI Tester - Command Line Interface for quick API testing
No HTML editing needed, just run Python commands!
"""

import requests
import json
import time
import sys
from datetime import datetime
from pathlib import Path

# Configuration
API_BASE = "http://localhost:8000/api/v1"
DEFAULT_TEST_DIR = "C:/temp/PHOTOS_SRC_TEST_MICRO"

class ImaLinkTester:
    def __init__(self, api_base=API_BASE):
        self.api_base = api_base
        self.last_session_id = None
    
    def test_connection(self):
        """Test API connection"""
        try:
            response = requests.get(f"{self.api_base}/import_sessions/test")
            if response.ok:
                print("✅ API Connection OK!")
                return True
            else:
                print(f"❌ Connection failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return False
    
    def storage_info(self, subfolder=None):
        """Get storage information"""
        try:
            url = f"{self.api_base}/import_sessions/storage-info"
            if subfolder:
                url += f"?subfolder={subfolder}"
            
            response = requests.get(url)
            if response.ok:
                data = response.json()
                print("📁 Storage Info:")
                for key, value in data.items():
                    print(f"  {key}: {value}")
                return data
            else:
                print(f"❌ Failed: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return None
    
    def start_import(self, source_dir=DEFAULT_TEST_DIR, description=None, 
                    storage_subfolder=None, copy_files=True):
        """Start unified import (database + file copy)"""
        
        if description is None:
            description = f"CLI Test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        payload = {
            "source_directory": source_dir,
            "source_description": description,
            "copy_files": copy_files
        }
        
        if storage_subfolder:
            payload["storage_subfolder"] = storage_subfolder
        
        try:
            print(f"🚀 Starting import...")
            print(f"  Source: {source_dir}")
            print(f"  Description: {description}")
            print(f"  Copy files: {copy_files}")
            
            response = requests.post(
                f"{self.api_base}/import_sessions/",
                json=payload
            )
            
            if response.ok:
                result = response.json()
                session_id = result["import_id"]
                self.last_session_id = session_id
                print(f"✅ Import started! Session ID: {session_id}")
                return session_id
            else:
                print(f"❌ Import failed: {response.status_code}")
                print(response.text)
                return None
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return None
    
    def status(self, session_id=None):
        """Get import status"""
        if session_id is None:
            session_id = self.last_session_id
        
        if session_id is None:
            print("❌ No session ID provided or available")
            return None
        
        try:
            response = requests.get(f"{self.api_base}/import_sessions/status/{session_id}")
            
            if response.ok:
                data = response.json()
                
                print(f"\n📊 Status for Session {session_id}:")
                print(f"  Status: {data.get('status')}")
                print(f"  Progress: {data.get('progress_percentage', 0)}%")
                print(f"  Files Found: {data.get('total_files_found', 0)}")
                print(f"  Images Imported: {data.get('images_imported', 0)}")
                print(f"  Duplicates Skipped: {data.get('duplicates_skipped', 0)}")
                print(f"  Files Copied: {data.get('files_copied', 0)}")
                print(f"  Storage Path: {data.get('storage_path', 'N/A')}")
                
                return data
            else:
                print(f"❌ Failed to get status: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return None
    
    def monitor(self, session_id=None, max_wait=300):
        """Monitor import until completion"""
        if session_id is None:
            session_id = self.last_session_id
        
        if session_id is None:
            print("❌ No session ID provided or available")
            return None
        
        print(f"🔄 Monitoring session {session_id} until completion...")
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            status_data = self.status(session_id)
            
            if not status_data:
                break
                
            status = status_data.get('status')
            progress = status_data.get('progress_percentage', 0)
            
            print(f"⏱️  {datetime.now().strftime('%H:%M:%S')} - Status: {status}, Progress: {progress}%")
            
            if status in ['completed', 'failed']:
                print(f"\n🎉 Import {status}!")
                return status_data
                
            time.sleep(5)
        
        print(f"⏰ Timeout after {max_wait} seconds")
        return self.status(session_id)
    
    def list_imports(self, limit=10):
        """List recent import sessions"""
        try:
            response = requests.get(f"{self.api_base}/import_sessions/")
            
            if response.ok:
                data = response.json()
                imports = data.get('imports', [])
                
                print(f"📋 Found {len(imports)} import sessions (showing last {limit}):")
                
                for imp in imports[-limit:]:
                    print(f"\n  ID: {imp.get('id')}")
                    print(f"    Status: {imp.get('status')}")
                    print(f"    Source: {Path(imp.get('source_path', '')).name}")
                    print(f"    Images: {imp.get('images_imported', 0)}")
                    print(f"    Files Copied: {imp.get('files_copied', 0)}")
                    print(f"    Started: {imp.get('started_at')}")
                
                return imports
            else:
                print(f"❌ Failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return None
    
    def quick_test(self, source_dir=DEFAULT_TEST_DIR):
        """Run a complete test cycle"""
        print("🎯 Quick Test Cycle")
        
        # 1. Test connection
        if not self.test_connection():
            return None
        
        # 2. Get storage info
        self.storage_info("cli_test")
        
        # 3. Start import
        session_id = self.start_import(
            source_dir, 
            "CLI Quick Test", 
            "cli_test"
        )
        
        if session_id:
            print(f"\n✅ Started session {session_id}")
            print("Run .status() or .monitor() to check progress")
        
        return session_id

# Interactive CLI
def main():
    print("🚀 ImaLink CLI Tester")
    print("=" * 50)
    
    tester = ImaLinkTester()
    
    if len(sys.argv) > 1:
        # Command line arguments
        command = sys.argv[1].lower()
        
        if command == "test":
            tester.test_connection()
        elif command == "quick":
            tester.quick_test()
        elif command == "start":
            source = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_TEST_DIR
            tester.start_import(source)
        elif command == "status":
            session_id = int(sys.argv[2]) if len(sys.argv) > 2 else None
            tester.status(session_id)
        elif command == "monitor":
            session_id = int(sys.argv[2]) if len(sys.argv) > 2 else None
            tester.monitor(session_id)
        elif command == "list":
            tester.list_imports()
        else:
            print(f"Unknown command: {command}")
            print_help()
    else:
        # Interactive mode
        print("\n💡 Available commands:")
        print("  tester.test_connection() - Test API")
        print("  tester.quick_test() - Full test cycle")
        print("  tester.start_import(path) - Start import")
        print("  tester.status() - Check last import")
        print("  tester.monitor() - Monitor until complete")
        print("  tester.list_imports() - Show recent imports")
        
        # Make tester available globally
        globals()['tester'] = tester
        
        print(f"\n🎯 Quick start: tester.quick_test()")
        print(f"📂 Default test dir: {DEFAULT_TEST_DIR}")

def print_help():
    print("\nUsage:")
    print("  python cli_tester.py test          - Test connection")
    print("  python cli_tester.py quick         - Quick test cycle")
    print("  python cli_tester.py start [path]  - Start import")
    print("  python cli_tester.py status [id]   - Check status")
    print("  python cli_tester.py monitor [id]  - Monitor progress")
    print("  python cli_tester.py list          - List imports")
    print("  python cli_tester.py               - Interactive mode")

if __name__ == "__main__":
    main()