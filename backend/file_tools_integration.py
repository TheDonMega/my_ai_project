#!/usr/bin/env python3
"""
File Tools Integration for Local Models
Shows how to integrate the file operation tools with your existing local Ollama models
"""

import requests
import json
from typing import Dict, Any, List, Optional

class FileToolsIntegration:
    """Integration class for file operation tools with local models"""
    
    def __init__(self, backend_url: str = "http://localhost:5557"):
        self.backend_url = backend_url
    
    def list_files(self, directory: str = "", sort_by: str = "modified", reverse: bool = True) -> Dict[str, Any]:
        """List files in the knowledge base directory"""
        response = requests.post(f"{self.backend_url}/tools/list-files", 
                               json={"directory": directory, "sort_by": sort_by, "reverse": reverse})
        return response.json() if response.status_code == 200 else {"error": response.text}
    
    def find_latest_file(self, directory: str = "", pattern: str = "*.md") -> Dict[str, Any]:
        """Find the most recently modified file in a directory"""
        response = requests.post(f"{self.backend_url}/tools/find-latest-file", 
                               json={"directory": directory, "pattern": pattern})
        return response.json() if response.status_code == 200 else {"error": response.text}
    
    def search_files(self, query: str, directory: str = "", case_sensitive: bool = False) -> Dict[str, Any]:
        """Search for files by name or pattern"""
        response = requests.post(f"{self.backend_url}/tools/search-files", 
                               json={"query": query, "directory": directory, "case_sensitive": case_sensitive})
        return response.json() if response.status_code == 200 else {"error": response.text}
    
    def grep_content(self, search_term: str, directory: str = "", case_sensitive: bool = False, max_results: int = 10) -> Dict[str, Any]:
        """Search file contents for a specific term"""
        response = requests.post(f"{self.backend_url}/tools/grep-content", 
                               json={"search_term": search_term, "directory": directory, "case_sensitive": case_sensitive, "max_results": max_results})
        return response.json() if response.status_code == 200 else {"error": response.text}
    
    def get_file_content(self, filename: str, directory: str = "") -> Dict[str, Any]:
        """Get the full content of a specific file"""
        response = requests.post(f"{self.backend_url}/tools/get-file-content", 
                               json={"filename": filename, "directory": directory})
        return response.json() if response.status_code == 200 else {"error": response.text}
    
    def get_file_info(self, filename: str, directory: str = "") -> Dict[str, Any]:
        """Get detailed information about a specific file"""
        response = requests.post(f"{self.backend_url}/tools/get-file-info", 
                               json={"filename": filename, "directory": directory})
        return response.json() if response.status_code == 200 else {"error": response.text}

def create_file_tools_prompt() -> str:
    """Create a prompt that explains the available file tools to the AI model"""
    return """
You have access to the following file operation tools for working with the knowledge base:

1. **list_files(directory, sort_by, reverse)** - List files in a directory
   - directory: Subdirectory to list (e.g., "Medscribe", "QA"). Leave empty for root.
   - sort_by: "name", "size", or "modified" (default: modified)
   - reverse: True for newest first (default: True)

2. **find_latest_file(directory, pattern)** - Find the most recently modified file
   - directory: Subdirectory to search (e.g., "Medscribe"). Leave empty for root.
   - pattern: File pattern to match (default: "*.md")

3. **search_files(query, directory, case_sensitive)** - Search for files by name
   - query: Search query (filename or pattern)
   - directory: Subdirectory to search. Leave empty for root.
   - case_sensitive: Whether search should be case sensitive (default: False)

4. **grep_content(search_term, directory, case_sensitive, max_results)** - Search file contents
   - search_term: Text to search for in file contents
   - directory: Subdirectory to search. Leave empty for root.
   - case_sensitive: Whether search should be case sensitive (default: False)
   - max_results: Maximum number of results (default: 10)

5. **get_file_content(filename, directory)** - Get full file content
   - filename: Name of the file to retrieve
   - directory: Subdirectory containing the file. Leave empty for root.

6. **get_file_info(filename, directory)** - Get file metadata
   - filename: Name of the file to get info for
   - directory: Subdirectory containing the file. Leave empty for root.

When a user asks about files, you can use these tools to:
- Find the latest files in a directory
- Search for specific files by name
- Search file contents for specific terms
- Get detailed file information
- Retrieve full file contents

Example: If someone asks "When was my last note added to Medscribe and what was it?", you would:
1. Use find_latest_file("Medscribe", "*.md") to find the latest file
2. Use get_file_content(filename, "Medscribe") to get the content
3. Provide the date and content to the user
"""

def example_usage():
    """Example of how to use the file tools integration"""
    tools = FileToolsIntegration()
    
    print("🎯 Example: Finding the latest Medscribe note")
    print("=" * 50)
    
    # Step 1: Find the latest file
    result = tools.find_latest_file("Medscribe", "*.md")
    
    if result.get("success"):
        latest_file = result["latest_file"]
        print(f"📅 Latest Medscribe file: {latest_file['filename']}")
        print(f"🕐 Modified: {latest_file['modified_human']}")
        
        # Step 2: Get the content
        content_result = tools.get_file_content(latest_file['filename'], "Medscribe")
        
        if content_result.get("success"):
            content = content_result["content"]
            print(f"📝 Content:")
            print(f"   {content}")
        else:
            print(f"❌ Error getting content: {content_result.get('error')}")
    else:
        print(f"❌ Error finding latest file: {result.get('error')}")

def integrate_with_query_system():
    """Example of how to integrate with your existing query system"""
    
    # This is how you could modify your existing query system to use file tools
    def enhanced_query_with_file_tools(question: str, model_name: str = "llama3.2:3b-trained") -> str:
        """
        Enhanced query function that can use file tools when needed
        """
        tools = FileToolsIntegration()
        
        # Check if the question is about files
        file_keywords = ["latest", "last", "file", "note", "document", "medscribe", "search", "find", "grep"]
        is_file_question = any(keyword in question.lower() for keyword in file_keywords)
        
        if is_file_question:
            # Use file tools to gather information
            context = ""
            
            if "medscribe" in question.lower() and ("latest" in question.lower() or "last" in question.lower()):
                # Find latest Medscribe file
                result = tools.find_latest_file("Medscribe", "*.md")
                if result.get("success"):
                    latest_file = result["latest_file"]
                    context += f"Latest Medscribe file: {latest_file['filename']} (modified: {latest_file['modified_human']})\n"
                    
                    # Get content
                    content_result = tools.get_file_content(latest_file['filename'], "Medscribe")
                    if content_result.get("success"):
                        context += f"Content: {content_result['content']}\n"
            
            # Add context to the question
            enhanced_question = f"Context from file tools: {context}\n\nUser question: {question}"
            
            # Now use your existing query system with the enhanced question
            # This would call your existing query endpoint
            return f"Enhanced query with file context: {enhanced_question}"
        else:
            # Use regular query system
            return f"Regular query: {question}"
    
    return enhanced_query_with_file_tools

if __name__ == "__main__":
    print("🚀 File Tools Integration Example")
    print("=" * 50)
    
    # Show the tools prompt
    print("📋 Available Tools:")
    print(create_file_tools_prompt())
    
    print("\n" + "=" * 50)
    
    # Show example usage
    example_usage()
    
    print("\n" + "=" * 50)
    
    # Show integration example
    print("🔧 Integration Example:")
    enhanced_query = integrate_with_query_system()
    result = enhanced_query("When was my last note added to Medscribe and what was it?")
    print(result)
