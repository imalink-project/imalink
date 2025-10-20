#!/usr/bin/env python3
"""
Script to fix API tests to use authentication headers
"""
import re
import os

def fix_api_test_file(filepath):
    """Fix a single API test file to use authentication"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Replace test_client with authenticated_client
    content = re.sub(r'\btest_client\)', 'authenticated_client)', content)
    content = re.sub(r'\btest_client\.', 'authenticated_client.', content)
    
    # Add headers to HTTP method calls
    # GET requests
    content = re.sub(r'authenticated_client\.get\("([^"]+)"\)', 
                     r'authenticated_client.get("\1", headers=authenticated_client.auth_headers)', content)
    
    # POST requests without headers
    content = re.sub(r'authenticated_client\.post\("([^"]+)", json=([^)]+)\)', 
                     r'authenticated_client.post("\1", json=\2, headers=authenticated_client.auth_headers)', content)
    
    # PUT requests
    content = re.sub(r'authenticated_client\.put\("([^"]+)", json=([^)]+)\)', 
                     r'authenticated_client.put("\1", json=\2, headers=authenticated_client.auth_headers)', content)
    
    # DELETE requests
    content = re.sub(r'authenticated_client\.delete\("([^"]+)"\)', 
                     r'authenticated_client.delete("\1", headers=authenticated_client.auth_headers)', content)
    
    with open(filepath, 'w') as f:
        f.write(content)

if __name__ == "__main__":
    test_dir = "/home/kjell/git_prosjekt/imalink/fase1/tests/api"
    
    for filename in os.listdir(test_dir):
        if filename.startswith("test_") and filename.endswith("_api.py"):
            filepath = os.path.join(test_dir, filename)
            print(f"Fixing {filename}...")
            fix_api_test_file(filepath)
    
    print("Done!")