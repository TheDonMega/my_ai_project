#!/usr/bin/env python3
"""
MCP Server for Local File Operations
Provides tools for searching and managing files in the knowledge base directory
"""

import os
import re
import glob
from datetime import datetime
from typing import Any, List, Dict, Optional
from pathlib import Path
import logging

# Configure logging to stderr (required for MCP servers)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    logger.error("MCP SDK not installed. Install with: pip install 'mcp[cli]'")
    exit(1)

# Initialize FastMCP server
mcp = FastMCP("knowledge-base-tools")

# Constants
KNOWLEDGE_BASE_PATH = "/app/knowledge_base"  # Docker container path
LOCAL_KNOWLEDGE_BASE_PATH = "./knowledge_base"  # Local development path

def get_knowledge_base_path() -> str:
    """Get the appropriate knowledge base path"""
    if os.path.exists(KNOWLEDGE_BASE_PATH):
        return KNOWLEDGE_BASE_PATH
    elif os.path.exists(LOCAL_KNOWLEDGE_BASE_PATH):
        return LOCAL_KNOWLEDGE_BASE_PATH
    else:
        raise FileNotFoundError("Knowledge base directory not found")

def format_file_info(file_path: str, relative_path: str) -> Dict[str, Any]:
    """Format file information for display"""
    try:
        stat = os.stat(file_path)
        return {
            "filename": os.path.basename(file_path),
            "path": relative_path,
            "size": stat.st_size,
            "size_human": format_file_size(stat.st_size),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "modified_human": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            "is_file": os.path.isfile(file_path),
            "is_dir": os.path.isdir(file_path)
        }
    except Exception as e:
        logger.error(f"Error getting file info for {file_path}: {e}")
        return {"filename": os.path.basename(file_path), "path": relative_path, "error": str(e)}

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0B"
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.1f}{size_names[i]}"

@mcp.tool()
async def list_files(directory: str = "", sort_by: str = "modified", reverse: bool = True) -> str:
    """List files in the knowledge base directory with detailed information.
    
    Args:
        directory: Subdirectory to list (e.g., "Medscribe", "QA"). Leave empty for root.
        sort_by: Sort by "name", "size", or "modified" (default: modified)
        reverse: Sort in reverse order (default: True for newest first)
    """
    try:
        kb_path = get_knowledge_base_path()
        target_path = os.path.join(kb_path, directory) if directory else kb_path
        
        if not os.path.exists(target_path):
            return f"❌ Directory not found: {directory}"
        
        files = []
        for item in os.listdir(target_path):
            item_path = os.path.join(target_path, item)
            relative_path = os.path.relpath(item_path, kb_path)
            file_info = format_file_info(item_path, relative_path)
            files.append(file_info)
        
        # Sort files
        if sort_by == "name":
            files.sort(key=lambda x: x["filename"], reverse=reverse)
        elif sort_by == "size":
            files.sort(key=lambda x: x.get("size", 0), reverse=reverse)
        else:  # modified
            files.sort(key=lambda x: x.get("modified", ""), reverse=reverse)
        
        # Format output
        result = f"📁 Files in {directory or 'knowledge_base'} ({len(files)} items):\n\n"
        
        for file_info in files:
            if file_info.get("is_dir"):
                result += f"📂 {file_info['filename']}/ ({file_info['modified_human']})\n"
            else:
                result += f"📄 {file_info['filename']} ({file_info['size_human']}, {file_info['modified_human']})\n"
        
        return result
        
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        return f"❌ Error listing files: {str(e)}"

@mcp.tool()
async def find_latest_file(directory: str = "", pattern: str = "*.md") -> str:
    """Find the most recently modified file in a directory.
    
    Args:
        directory: Subdirectory to search (e.g., "Medscribe"). Leave empty for root.
        pattern: File pattern to match (default: "*.md" for markdown files)
    """
    try:
        kb_path = get_knowledge_base_path()
        target_path = os.path.join(kb_path, directory) if directory else kb_path
        
        if not os.path.exists(target_path):
            return f"❌ Directory not found: {directory}"
        
        # Find all files matching pattern
        search_pattern = os.path.join(target_path, "**", pattern)
        matching_files = glob.glob(search_pattern, recursive=True)
        
        if not matching_files:
            return f"❌ No files found matching pattern '{pattern}' in {directory or 'knowledge_base'}"
        
        # Get file info for all matching files
        files = []
        for file_path in matching_files:
            relative_path = os.path.relpath(file_path, kb_path)
            file_info = format_file_info(file_path, relative_path)
            files.append(file_info)
        
        # Sort by modification time (newest first)
        files.sort(key=lambda x: x.get("modified", ""), reverse=True)
        
        latest_file = files[0]
        
        result = f"🕒 Latest file in {directory or 'knowledge_base'}:\n\n"
        result += f"📄 {latest_file['filename']}\n"
        result += f"📍 Path: {latest_file['path']}\n"
        result += f"📏 Size: {latest_file['size_human']}\n"
        result += f"🕐 Modified: {latest_file['modified_human']}\n"
        
        return result
        
    except Exception as e:
        logger.error(f"Error finding latest file: {e}")
        return f"❌ Error finding latest file: {str(e)}"

@mcp.tool()
async def search_files(query: str, directory: str = "", case_sensitive: bool = False) -> str:
    """Search for files by name or pattern.
    
    Args:
        query: Search query (filename or pattern)
        directory: Subdirectory to search (e.g., "Medscribe"). Leave empty for root.
        case_sensitive: Whether search should be case sensitive (default: False)
    """
    try:
        kb_path = get_knowledge_base_path()
        target_path = os.path.join(kb_path, directory) if directory else kb_path
        
        if not os.path.exists(target_path):
            return f"❌ Directory not found: {directory}"
        
        # Convert query to regex pattern
        if not case_sensitive:
            query = query.lower()
        
        # Search recursively
        matching_files = []
        for root, dirs, files in os.walk(target_path):
            for file in files:
                filename = file if case_sensitive else file.lower()
                if query in filename:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, kb_path)
                    file_info = format_file_info(file_path, relative_path)
                    matching_files.append(file_info)
        
        if not matching_files:
            return f"❌ No files found matching '{query}' in {directory or 'knowledge_base'}"
        
        # Sort by modification time (newest first)
        matching_files.sort(key=lambda x: x.get("modified", ""), reverse=True)
        
        result = f"🔍 Found {len(matching_files)} files matching '{query}':\n\n"
        
        for file_info in matching_files:
            result += f"📄 {file_info['filename']}\n"
            result += f"📍 Path: {file_info['path']}\n"
            result += f"📏 Size: {file_info['size_human']}\n"
            result += f"🕐 Modified: {file_info['modified_human']}\n\n"
        
        return result
        
    except Exception as e:
        logger.error(f"Error searching files: {e}")
        return f"❌ Error searching files: {str(e)}"

@mcp.tool()
async def grep_content(search_term: str, directory: str = "", case_sensitive: bool = False, max_results: int = 10) -> str:
    """Search file contents for a specific term (like grep).
    
    Args:
        search_term: Text to search for in file contents
        directory: Subdirectory to search (e.g., "Medscribe"). Leave empty for root.
        case_sensitive: Whether search should be case sensitive (default: False)
        max_results: Maximum number of results to return (default: 10)
    """
    try:
        kb_path = get_knowledge_base_path()
        target_path = os.path.join(kb_path, directory) if directory else kb_path
        
        if not os.path.exists(target_path):
            return f"❌ Directory not found: {directory}"
        
        if not case_sensitive:
            search_term = search_term.lower()
        
        results = []
        
        # Search recursively through markdown files
        for root, dirs, files in os.walk(target_path):
            for file in files:
                if file.endswith('.md'):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, kb_path)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Search in content
                        content_to_search = content if case_sensitive else content.lower()
                        if search_term in content_to_search:
                            # Find line numbers and context
                            lines = content.split('\n')
                            matches = []
                            
                            for i, line in enumerate(lines, 1):
                                line_to_search = line if case_sensitive else line.lower()
                                if search_term in line_to_search:
                                    # Get context (previous and next lines)
                                    start = max(0, i - 2)
                                    end = min(len(lines), i + 1)
                                    context = lines[start:end]
                                    
                                    matches.append({
                                        "line": i,
                                        "context": context,
                                        "matched_line": line
                                    })
                            
                            if matches:
                                results.append({
                                    "file": relative_path,
                                    "filename": file,
                                    "matches": matches[:3]  # Limit matches per file
                                })
                    
                    except Exception as e:
                        logger.warning(f"Error reading file {file_path}: {e}")
                        continue
        
        if not results:
            return f"❌ No files found containing '{search_term}' in {directory or 'knowledge_base'}"
        
        # Sort by number of matches (most matches first)
        results.sort(key=lambda x: len(x["matches"]), reverse=True)
        results = results[:max_results]
        
        result = f"🔍 Found '{search_term}' in {len(results)} files:\n\n"
        
        for file_result in results:
            result += f"📄 {file_result['filename']} ({file_result['file']})\n"
            result += f"📊 {len(file_result['matches'])} matches\n"
            
            for match in file_result['matches']:
                result += f"   Line {match['line']}: {match['matched_line'][:100]}...\n"
            
            result += "\n"
        
        return result
        
    except Exception as e:
        logger.error(f"Error grepping content: {e}")
        return f"❌ Error searching content: {str(e)}"

@mcp.tool()
async def get_file_content(filename: str, directory: str = "") -> str:
    """Get the full content of a specific file.
    
    Args:
        filename: Name of the file to retrieve
        directory: Subdirectory containing the file (e.g., "Medscribe"). Leave empty for root.
    """
    try:
        kb_path = get_knowledge_base_path()
        file_path = os.path.join(kb_path, directory, filename) if directory else os.path.join(kb_path, filename)
        
        if not os.path.exists(file_path):
            return f"❌ File not found: {filename}"
        
        if not os.path.isfile(file_path):
            return f"❌ Path is not a file: {filename}"
        
        # Get file info
        relative_path = os.path.relpath(file_path, kb_path)
        file_info = format_file_info(file_path, relative_path)
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        result = f"📄 File: {filename}\n"
        result += f"📍 Path: {file_info['path']}\n"
        result += f"📏 Size: {file_info['size_human']}\n"
        result += f"🕐 Modified: {file_info['modified_human']}\n"
        result += f"📝 Content:\n\n"
        result += "---\n"
        result += content
        result += "\n---\n"
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting file content: {e}")
        return f"❌ Error reading file: {str(e)}"

@mcp.tool()
async def get_file_info(filename: str, directory: str = "") -> str:
    """Get detailed information about a specific file.
    
    Args:
        filename: Name of the file to get info for
        directory: Subdirectory containing the file (e.g., "Medscribe"). Leave empty for root.
    """
    try:
        kb_path = get_knowledge_base_path()
        file_path = os.path.join(kb_path, directory, filename) if directory else os.path.join(kb_path, filename)
        
        if not os.path.exists(file_path):
            return f"❌ File not found: {filename}"
        
        relative_path = os.path.relpath(file_path, kb_path)
        file_info = format_file_info(file_path, relative_path)
        
        result = f"📄 File Information: {filename}\n\n"
        result += f"📍 Path: {file_info['path']}\n"
        result += f"📏 Size: {file_info['size_human']} ({file_info['size']} bytes)\n"
        result += f"🕐 Modified: {file_info['modified_human']}\n"
        result += f"📅 Modified (ISO): {file_info['modified']}\n"
        result += f"📁 Type: {'Directory' if file_info['is_dir'] else 'File'}\n"
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting file info: {e}")
        return f"❌ Error getting file info: {str(e)}"

if __name__ == "__main__":
    # Initialize and run the server
    logger.info("🚀 Starting Knowledge Base MCP Server...")
    logger.info(f"📁 Knowledge base path: {get_knowledge_base_path()}")
    mcp.run(transport='stdio')
