#!/usr/bin/env python3
"""
Test script for the new file operation tools
Demonstrates how to use the MCP-style file tools integrated into the Flask backend
"""

import requests
import json

# Backend URL
BACKEND_URL = "http://localhost:5557"

def test_list_files():
    """Test listing files in the knowledge base"""
    print("🔍 Testing list_files...")
    
    # List all files in root
    response = requests.post(f"{BACKEND_URL}/tools/list-files", 
                           json={"directory": "", "sort_by": "modified", "reverse": True})
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Found {data['count']} files in {data['directory']}")
        
        # Show first 5 files
        for i, file_info in enumerate(data['files'][:5]):
            print(f"  {i+1}. {file_info['filename']} ({file_info['size_human']}, {file_info['modified_human']})")
    else:
        print(f"❌ Error: {response.text}")

def test_find_latest_medscribe():
    """Test finding the latest Medscribe file"""
    print("\n🕒 Testing find_latest_file for Medscribe...")
    
    response = requests.post(f"{BACKEND_URL}/tools/find-latest-file", 
                           json={"directory": "Medscribe", "pattern": "*.md"})
    
    if response.status_code == 200:
        data = response.json()
        latest_file = data['latest_file']
        print(f"✅ Latest Medscribe file: {latest_file['filename']}")
        print(f"   Path: {latest_file['path']}")
        print(f"   Size: {latest_file['size_human']}")
        print(f"   Modified: {latest_file['modified_human']}")
        
        # Get the content of the latest file
        return latest_file['filename']
    else:
        print(f"❌ Error: {response.text}")
        return None

def test_get_file_content(filename):
    """Test getting file content"""
    if not filename:
        return
    
    print(f"\n📄 Testing get_file_content for {filename}...")
    
    response = requests.post(f"{BACKEND_URL}/tools/get-file-content", 
                           json={"filename": filename, "directory": "Medscribe"})
    
    if response.status_code == 200:
        data = response.json()
        content = data['content']
        print(f"✅ File content (first 200 chars):")
        print(f"   {content[:200]}...")
    else:
        print(f"❌ Error: {response.text}")

def test_search_files():
    """Test searching for files by name"""
    print("\n🔍 Testing search_files...")
    
    response = requests.post(f"{BACKEND_URL}/tools/search-files", 
                           json={"query": "Medscribe", "directory": "", "case_sensitive": False})
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Found {data['count']} files matching '{data['query']}'")
        
        # Show first 3 results
        for i, file_info in enumerate(data['files'][:3]):
            print(f"  {i+1}. {file_info['filename']} ({file_info['path']})")
    else:
        print(f"❌ Error: {response.text}")

def test_grep_content():
    """Test searching file contents"""
    print("\n🔍 Testing grep_content...")
    
    response = requests.post(f"{BACKEND_URL}/tools/grep-content", 
                           json={"search_term": "patient", "directory": "Medscribe", "max_results": 3})
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Found '{data['search_term']}' in {data['count']} files")
        
        for result in data['results']:
            print(f"  📄 {result['filename']} ({len(result['matches'])} matches)")
            for match in result['matches'][:1]:  # Show first match per file
                print(f"    Line {match['line']}: {match['matched_line'][:80]}...")
    else:
        print(f"❌ Error: {response.text}")

def test_medscribe_example():
    """Test the specific example: When was my last note added to Medscribe and what was it"""
    print("\n🎯 Testing the specific example: Latest Medscribe note...")
    
    # Step 1: Find the latest file
    response = requests.post(f"{BACKEND_URL}/tools/find-latest-file", 
                           json={"directory": "Medscribe", "pattern": "*.md"})
    
    if response.status_code == 200:
        data = response.json()
        latest_file = data['latest_file']
        
        print(f"📅 Last Medscribe note was added on: {latest_file['modified_human']}")
        print(f"📄 File: {latest_file['filename']}")
        
        # Step 2: Get the content
        content_response = requests.post(f"{BACKEND_URL}/tools/get-file-content", 
                                       json={"filename": latest_file['filename'], "directory": "Medscribe"})
        
        if content_response.status_code == 200:
            content_data = content_response.json()
            content = content_data['content']
            
            print(f"📝 Content:")
            print(f"   {content}")
        else:
            print(f"❌ Error getting content: {content_response.text}")
    else:
        print(f"❌ Error finding latest file: {response.text}")

if __name__ == "__main__":
    print("🚀 Testing File Operation Tools")
    print("=" * 50)
    
    try:
        # Test all tools
        test_list_files()
        latest_filename = test_find_latest_medscribe()
        test_get_file_content(latest_filename)
        test_search_files()
        test_grep_content()
        
        # Test the specific example
        test_medscribe_example()
        
        print("\n✅ All tests completed!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to backend server.")
        print("   Make sure the backend is running on http://localhost:5557")
        print("   Run: docker-compose up -d")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
