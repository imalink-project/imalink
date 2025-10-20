#!/usr/bin/env python3
"""
Script to systematically fix API tests to use authentication
"""
import re
import os

def fix_api_test_file(filepath):
    """Fix a single API test file to use authentication"""
    print(f"Processing {filepath}...")
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Step 1: Replace test_client parameter with authenticated_client
    content = re.sub(r'def (test_[^(]+)\(self, test_client\)', r'def \1(self, authenticated_client)', content)
    
    # Step 2: Replace test_client.method calls
    methods = ['get', 'post', 'put', 'delete', 'patch']
    
    for method in methods:
        # Simple calls without parameters: client.get("/path")
        pattern = f'test_client\.{method}\("([^"]+)"\)'
        replacement = f'authenticated_client.{method}("\\1", headers=authenticated_client.auth_headers)'
        content = re.sub(pattern, replacement, content)
        
        # Calls with json parameter: client.post("/path", json=data)
        pattern = f'test_client\.{method}\("([^"]+)", json=([^)]+)\)'
        replacement = f'authenticated_client.{method}("\\1", json=\\2, headers=authenticated_client.auth_headers)'
        content = re.sub(pattern, replacement, content)
        
        # Calls with data parameter: client.post("/path", data=data)
        pattern = f'test_client\.{method}\("([^"]+)", data=([^)]+)\)'
        replacement = f'authenticated_client.{method}("\\1", data=\\2, headers=authenticated_client.auth_headers)'
        content = re.sub(pattern, replacement, content)
    
    with open(filepath, 'w') as f:
        f.write(content)
    print(f"Fixed {filepath}")

if __name__ == "__main__":
    test_dir = "/home/kjell/git_prosjekt/imalink/fase1/tests/api"
    
    test_files = [
        "test_authors_api.py",
        "test_photos_api.py", 
        "test_image_files_api.py",
        "test_import_sessions_api.py"
    ]
    
    for filename in test_files:
        filepath = os.path.join(test_dir, filename)
        if os.path.exists(filepath):
            fix_api_test_file(filepath)
        else:
            print(f"File not found: {filepath}")
    
    print("Done!")