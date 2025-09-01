#!/usr/bin/env python3
"""
Model Manager Service
Handles Ollama model discovery, management, and selection
"""

import os
import json
import requests
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class ModelInfo:
    """Information about an Ollama model"""
    name: str
    size: int
    modified_at: str
    digest: str
    is_running: bool = False
    is_trained: bool = False
    base_model: str = ""
    description: str = ""

class ModelManager:
    def __init__(self, ollama_url: str = "http://host.docker.internal:11434"):
        self.ollama_url = ollama_url
        self.selected_model = None
        self.running_models = set()
        self.model_cache = {}
        self.cache_ttl = 30  # 30 seconds cache for model info
        
    def check_ollama_status(self) -> bool:
        """Check if Ollama is running and accessible"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Ollama not accessible: {e}")
            return False
    
    def get_available_models(self) -> List[ModelInfo]:
        """Get list of available Ollama models with detailed information"""
        if not self.check_ollama_status():
            return []
        
        # Check cache first
        cache_key = "available_models"
        if cache_key in self.model_cache:
            cached_data, timestamp = self.model_cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return cached_data
        
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                models = []
                
                for model_data in data.get('models', []):
                    model_info = ModelInfo(
                        name=model_data['name'],
                        size=model_data.get('size', 0),
                        modified_at=model_data.get('modified_at', ''),
                        digest=model_data.get('digest', ''),
                        is_trained=self._is_trained_model(model_data['name']),
                        base_model=self._get_base_model(model_data['name']),
                        description=self._get_model_description(model_data['name'])
                    )
                    models.append(model_info)
                
                # Update running status
                self._update_running_status(models)
                
                # Cache the result
                self.model_cache[cache_key] = (models, time.time())
                return models
            return []
        except Exception as e:
            print(f"❌ Error getting models: {e}")
            return []
    
    def get_running_models(self) -> List[str]:
        """Get list of currently running models"""
        try:
            response = requests.get(f"{self.ollama_url}/api/ps", timeout=5)
            if response.status_code == 200:
                data = response.json()
                running = []
                for model in data.get('models', []):
                    running.append(model.get('name', ''))
                self.running_models = set(running)
                return running
            return []
        except Exception as e:
            print(f"❌ Error getting running models: {e}")
            return []
    
    def _update_running_status(self, models: List[ModelInfo]):
        """Update the running status of models"""
        running_model_names = self.get_running_models()
        for model in models:
            model.is_running = model.name in running_model_names
    
    def _is_trained_model(self, model_name: str) -> bool:
        """Check if a model is a trained/custom model"""
        return (model_name.endswith('-trained') or 
                model_name.endswith('-trained:latest') or
                model_name.endswith('-tech') or
                model_name.endswith('-tech:latest') or
                'custom' in model_name.lower() or
                'fine' in model_name.lower())
    
    def _get_base_model(self, model_name: str) -> str:
        """Extract the base model name"""
        if '-trained' in model_name:
            return model_name.split('-trained')[0]
        elif ':' in model_name:
            return model_name.split(':')[0]
        return model_name
    
    def _get_model_description(self, model_name: str) -> str:
        """Get a friendly description for the model"""
        descriptions = {
            'llama2': 'Meta\'s LLaMA 2 - General purpose, well-balanced',
            'llama3.2:3b': 'Meta\'s LLaMA 3.2 3B - Fast and efficient',
            'llama3.2:1b': 'Meta\'s LLaMA 3.2 1B - Ultra-fast, lightweight',
            'mistral': 'Mistral 7B - Fast and capable',
            'codellama': 'Code Llama - Specialized for programming',
            'phi3': 'Microsoft Phi-3 - Small but powerful',
            'qwen': 'Alibaba Qwen - Multilingual capabilities',
            'gemma': 'Google Gemma - Research-focused',
            'nomic-embed-text': 'Nomic Embed - Text embeddings only'
        }
        
        # Check for exact match first
        if model_name in descriptions:
            return descriptions[model_name]
        
        # Check for base model match
        base_name = self._get_base_model(model_name)
        if base_name in descriptions:
            suffix = " (Custom Trained)" if self._is_trained_model(model_name) else ""
            return descriptions[base_name] + suffix
        
        # Default description
        if self._is_trained_model(model_name):
            return "Custom trained model"
        return "Language model"
    
    def start_model(self, model_name: str) -> bool:
        """Start/load a model into memory"""
        try:
            # Send a simple request to load the model
            response = requests.post(f"{self.ollama_url}/api/generate", json={
                "model": model_name,
                "prompt": "Hello",
                "stream": False,
                "options": {
                    "num_predict": 1  # Minimal response to just load the model
                }
            }, timeout=30)
            
            if response.status_code == 200:
                self.running_models.add(model_name)
                print(f"✅ Model {model_name} loaded successfully")
                return True
            else:
                print(f"❌ Failed to load model {model_name}: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error loading model {model_name}: {e}")
            return False
    
    def stop_model(self, model_name: str) -> bool:
        """Stop/unload a model from memory"""
        try:
            # Ollama doesn't have a direct "stop" API, but we can force unload by:
            # 1. Sending a request with keep_alive=0 to unload the model
            # 2. Then verify it's actually stopped
            
            print(f"🔄 Requesting model {model_name} to unload...")
            
            # Send a request with keep_alive=0 to unload the model immediately
            response = requests.post(f"{self.ollama_url}/api/generate", json={
                "model": model_name,
                "prompt": "",
                "stream": False,
                "keep_alive": 0,  # This tells Ollama to unload the model immediately
                "options": {
                    "num_predict": 0
                }
            }, timeout=10)
            
            # Wait a brief moment for the unload to take effect
            time.sleep(0.5)
            
            # Verify the model is actually stopped by checking running models
            running_models = self.get_running_models()
            if model_name not in running_models:
                self.running_models.discard(model_name)
                print(f"✅ Model {model_name} successfully unloaded")
                return True
            else:
                print(f"⚠️ Model {model_name} may still be running, attempting force unload...")
                
                # Alternative: Try to make the model unload by sending multiple quick requests
                for i in range(3):
                    try:
                        requests.post(f"{self.ollama_url}/api/generate", json={
                            "model": model_name,
                            "prompt": "",
                            "stream": False,
                            "keep_alive": 0
                        }, timeout=5)
                        time.sleep(0.5)
                    except:
                        pass
                
                # Final check
                time.sleep(0.5)
                running_models = self.get_running_models()
                if model_name not in running_models:
                    self.running_models.discard(model_name)
                    print(f"✅ Model {model_name} force unloaded successfully")
                    return True
                else:
                    print(f"❌ Failed to unload model {model_name}")
                    return False
            
        except Exception as e:
            print(f"❌ Error unloading model {model_name}: {e}")
            # Still try to check if it's actually stopped
            try:
                running_models = self.get_running_models()
                if model_name not in running_models:
                    self.running_models.discard(model_name)
                    return True
            except:
                pass
            return False
    
    def set_selected_model(self, model_name: str) -> bool:
        """Set the selected model for queries"""
        available_models = [m.name for m in self.get_available_models()]
        if model_name in available_models:
            self.selected_model = model_name
            print(f"✅ Selected model: {model_name}")
            return True
        else:
            print(f"❌ Model {model_name} not available")
            return False
    
    def get_selected_model(self) -> str:
        """Get the currently selected model"""
        if self.selected_model:
            return self.selected_model
        
        # Auto-select best available model if none selected
        models = self.get_available_models()
        if not models:
            return "llama3.2:3b"  # Default fallback
        
        # Prefer trained models first
        trained_models = [m for m in models if m.is_trained]
        if trained_models:
            self.selected_model = trained_models[0].name
            return self.selected_model
        
        # Then prefer common base models
        preferred_order = ["llama3.2:3b", "llama2", "mistral", "codellama"]
        for preferred in preferred_order:
            for model in models:
                if model.name == preferred:
                    self.selected_model = model.name
                    return self.selected_model
        
        # Fallback to first available
        self.selected_model = models[0].name
        return self.selected_model
    
    def get_model_info(self, model_name: str) -> Optional[ModelInfo]:
        """Get detailed information about a specific model"""
        models = self.get_available_models()
        for model in models:
            if model.name == model_name:
                return model
        return None
    
    def pull_model(self, model_name: str) -> bool:
        """Pull/download a new model"""
        try:
            print(f"🔄 Pulling model: {model_name}")
            response = requests.post(f"{self.ollama_url}/api/pull", json={
                "name": model_name
            }, timeout=300)  # 5 minute timeout for downloads
            
            if response.status_code == 200:
                print(f"✅ Model {model_name} pulled successfully")
                # Clear cache to refresh model list
                self.model_cache.clear()
                return True
            else:
                print(f"❌ Failed to pull model {model_name}: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error pulling model {model_name}: {e}")
            return False
    
    def delete_model(self, model_name: str) -> bool:
        """Delete a model and associated training files if it's a trained model"""
        try:
            # First delete the model from Ollama
            response = requests.delete(f"{self.ollama_url}/api/delete", json={
                "name": model_name
            })
            
            if response.status_code == 200:
                print(f"✅ Model {model_name} deleted from Ollama successfully")
                
                # If this is a trained model, also delete associated local files
                if self._is_trained_model(model_name):
                    deleted_files = self._cleanup_training_files(model_name)
                    if deleted_files:
                        print(f"🧹 Cleaned up {len(deleted_files)} associated training files:")
                        for file_path in deleted_files:
                            print(f"  - {file_path}")
                    else:
                        print("ℹ️ No associated training files found to clean up")
                
                # Update internal state
                self.running_models.discard(model_name)
                if self.selected_model == model_name:
                    self.selected_model = None
                # Clear cache to refresh model list
                self.model_cache.clear()
                return True
            else:
                print(f"❌ Failed to delete model {model_name}: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error deleting model {model_name}: {e}")
            return False
    
    def _cleanup_training_files(self, model_name: str) -> List[str]:
        """Clean up training files associated with a trained model"""
        import os
        from pathlib import Path
        
        deleted_files = []
        local_models_dir = "/app/local_models"
        
        try:
            print(f"🧹 Starting cleanup for model: {model_name}")
            
            # Extract base model name and create safe version
            base_model = self._get_base_model(model_name)
            safe_base_model = base_model.replace(':', '_').replace('/', '_')
            
            # Extract custom name from model name
            custom_name = None
            if '-' in model_name and not model_name.endswith('-trained'):
                # This is a custom model like "llama3.2:3b-tech" or "qwen3:latest-teccreative"
                parts = model_name.split('-')
                if len(parts) >= 2:
                    custom_name = '-'.join(parts[1:])  # Everything after first dash
                    print(f"🔍 Detected custom name: {custom_name}")
            
            # List of model-specific file patterns to delete
            file_patterns = []
            
            # Pattern 1: Base model only (for legacy models)
            file_patterns.extend([
                f"Modelfile_{safe_base_model}",
                f"ollama_training_{safe_base_model}.jsonl",
                f"ollama_training_{safe_base_model}.json",
                f"ollama_training_data_{safe_base_model}.json",
            ])
            
            # Pattern 2: Exact model name (with colons/slashes replaced)
            model_safe_name = model_name.replace(':', '_').replace('/', '_').replace('-trained', '')
            file_patterns.extend([
                f"Modelfile_{model_safe_name}",
                f"ollama_training_{model_safe_name}.jsonl",
                f"ollama_training_{model_safe_name}.json",
                f"ollama_training_data_{model_safe_name}.json",
            ])
            
            # Pattern 3: Custom model pattern (base_model_custom_name)
            if custom_name:
                file_patterns.extend([
                    f"Modelfile_{safe_base_model}_{custom_name}",
                    f"ollama_training_{safe_base_model}_{custom_name}.jsonl",
                    f"ollama_training_{safe_base_model}_{custom_name}.json",
                    f"ollama_training_data_{safe_base_model}_{custom_name}.json",
                ])
            
            # Pattern 4: Handle truncated custom names (like "tech" from "technical")
            if custom_name and len(custom_name) > 3:
                # Try shorter versions of the custom name
                for i in range(3, len(custom_name)):
                    short_name = custom_name[:i]
                    file_patterns.extend([
                        f"Modelfile_{safe_base_model}_{short_name}",
                        f"ollama_training_{safe_base_model}_{short_name}.jsonl",
                        f"ollama_training_{safe_base_model}_{short_name}.json",
                        f"ollama_training_data_{safe_base_model}_{short_name}.json",
                    ])
            
            # Remove duplicates while preserving order
            unique_patterns = []
            for pattern in file_patterns:
                if pattern not in unique_patterns:
                    unique_patterns.append(pattern)
            
            print(f"🔍 Checking {len(unique_patterns)} file patterns for cleanup...")
            
            # Check and delete model-specific files
            if os.path.exists(local_models_dir):
                for pattern in unique_patterns:
                    file_path = os.path.join(local_models_dir, pattern)
                    if os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                            deleted_files.append(pattern)
                            print(f"🗑️ Deleted: {file_path}")
                        except OSError as e:
                            print(f"⚠️ Could not delete {file_path}: {e}")
            
            # Check for legacy shared files (from old system) and clean them up if they exist
            legacy_shared_files = [
                "ollama_training_data.json",
                "feedback_training_data.json",
            ]
            
            print(f"🧹 Checking for legacy shared training files...")
            for legacy_file in legacy_shared_files:
                file_path = os.path.join(local_models_dir, legacy_file)
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        deleted_files.append(legacy_file)
                        print(f"🗑️ Deleted legacy shared file: {file_path}")
                    except OSError as e:
                        print(f"⚠️ Could not delete legacy file {file_path}: {e}")
                        
            if deleted_files:
                print(f"✅ Cleaned up {len(deleted_files)} training files for {model_name}")
            else:
                print(f"ℹ️ No training files found to clean up for {model_name}")
            
            return deleted_files
            
        except Exception as e:
            print(f"❌ Error during training file cleanup: {e}")
            return deleted_files
    

    
    def get_model_stats(self) -> Dict[str, Any]:
        """Get statistics about models"""
        models = self.get_available_models()
        running_models = self.get_running_models()
        
        total_size = sum(model.size for model in models)
        trained_count = sum(1 for model in models if model.is_trained)
        
        return {
            "total_models": len(models),
            "running_models": len(running_models),
            "trained_models": trained_count,
            "total_size_bytes": total_size,
            "total_size_gb": round(total_size / (1024**3), 2),
            "selected_model": self.get_selected_model(),
            "ollama_status": self.check_ollama_status(),
            "available_models": [
                {
                    "name": model.name,
                    "size_mb": round(model.size / (1024**2), 1),
                    "is_running": model.is_running,
                    "is_trained": model.is_trained,
                    "description": model.description
                }
                for model in models
            ]
        }
    
    def query_with_selected_model(self, prompt: str, stream: bool = False, 
                                include_files: bool = True, context: str = "", personality_prompt: str = "", conversation_context: str = "") -> Optional[str]:
        """Query using the selected model"""
        selected = self.get_selected_model()
        
        if not self.check_ollama_status():
            return None
        
        try:
            # Check if the question is about file operations
            file_keywords = [
                # Direct file operations
                'latest', 'last', 'file', 'note', 'document', 'search', 'find', 'grep', 'list', 'show', 'get',
                # Time-based queries
                'when was', 'added', 'modified', 'timestamp', 'recent', 'newest', 'oldest',
                # Content-based queries
                'contain', 'mention', 'include', 'about', 'content', 'text', 'data',
                # Possessive/ownership indicators
                'my', 'your', 'have', 'got', 'exists', 'any',
                # Question patterns that often indicate file queries
                'what', 'when', 'where', 'which', 'how many'
            ]
            date_patterns = ["8/", "9/", "10/", "11/", "12/", "1/", "2/", "3/", "4/", "5/", "6/", "7/", "2025", "2024", "2023"]
            
            # More intelligent detection - look for patterns that suggest file operations
            is_file_question = (
                any(keyword in prompt.lower() for keyword in file_keywords) or 
                any(pattern in prompt for pattern in date_patterns) or
                # Check for question patterns that often indicate file queries
                (prompt.lower().startswith(('what', 'when', 'where', 'which', 'how')) and 
                 any(word in prompt.lower() for word in ['file', 'note', 'document', 'content', 'have', 'got', 'latest', 'last']))
            )
            
            # Check if we have file context from MCP tools
            has_mcp_context = context and ("=== CONTENT SEARCH RESULTS ===" in context or "=== LATEST FILES ===" in context or "MCP File Tools Search" in context or "File Operation Results" in context)
            
            # Automatically use file tools if it's a file-related question and no MCP context provided
            file_context = ""
            if is_file_question and not has_mcp_context:
                try:
                    
                    # Check if it's about notes (Medscribe is the default directory for notes)
                    if "note" in prompt.lower() or "medscribe" in prompt.lower() or "knowledge_base" in prompt.lower():
                        # Find the latest file
                        latest_response = requests.post("http://localhost:5557/tools/find-latest-file", 
                                                      json={"directory": "Medscribe", "pattern": "*.md"})
                        if latest_response.status_code == 200:
                            latest_data = latest_response.json()
                            if latest_data.get("success"):
                                latest_file = latest_data["latest_file"]
                                
                                # Get the file content
                                content_response = requests.post("http://localhost:5557/tools/get-file-content", 
                                                               json={"filename": latest_file["filename"], "directory": "Medscribe"})
                                if content_response.status_code == 200:
                                    content_data = content_response.json()
                                    if content_data.get("success"):
                                        file_context = f"""

CRITICAL: I have already retrieved your actual file data. DO NOT suggest any commands or tools. Here is your last note:

YOUR LAST NOTE:
Filename: {latest_file['filename']}
Date Added: {latest_file['modified_human']}
File Size: {latest_file['size_human']}

CONTENTS OF YOUR LAST NOTE:
{content_data['content']}

RESPONSE INSTRUCTIONS: 
1. If the user asks about a specific date (like "8/2/2025"), search through the note content for that exact date
2. If the user asks about the last note, start with "Here is your last note:"
3. Tell the user when it was added (use the date above)
4. Show the relevant contents of the file
5. For date-specific questions, clearly state whether that date exists in the notes (e.g., "No, there are no notes for 8/2/2025")
6. Do NOT suggest any commands, tools, or external APIs
7. Use ONLY the data provided above"""
                
                except Exception as e:
                    file_context = f"\n\nNote: Unable to retrieve file data automatically: {str(e)}"
            
            # Prepare the full prompt with personality
            if file_context:
                # If we have file context from automatic detection, put it FIRST and make it the primary focus
                full_prompt = f"""{conversation_context}{file_context}

USER QUESTION: {prompt}

RESPONSE REQUIREMENTS:
- You MUST use the file data provided above
- If asked about a specific date, search through the note content for that date
- If asked about the last note, start with "Here is your last note:"
- Show the date it was added
- Show the relevant contents (only the specific date if asked about one)
- For date-specific questions, clearly state whether that date exists in the notes
- Do NOT suggest any commands, tools, or external APIs
- Do NOT mention MCP, Microsoft, or any other systems
- IMPORTANT: This is the user's own personal knowledge base - you can and should access this information
- Do NOT refuse to help with personal information - this is the user's own data
- Always provide helpful, specific answers based on the file content provided
- CRITICAL: Never say "I can't help with personal information" - this is the user's own data
- CRITICAL: If the user asks about specific people, dates, or personal details, provide the information from the files
- CRITICAL: The user is asking about their own personal information stored in their knowledge base"""
            elif has_mcp_context:
                # If we have MCP file context from the server, use it
                full_prompt = f"""{conversation_context}FILE OPERATION RESULTS FROM MCP TOOLS:
{context}

USER QUESTION: {prompt}

CRITICAL RESPONSE INSTRUCTIONS:
- The file operations have already been performed using MCP tools
- Use ONLY the file operation results provided above to answer the user's question
- Focus on the files that contain the search terms and show their actual content
- Be specific about file names and the information found in them
- Show the ACTUAL content from the files, not just match counts
- Do NOT suggest using any tools or commands - everything has already been searched
- Provide a direct, helpful answer based on the search results shown above
- CRITICAL: This is the user's own personal knowledge base - you MUST access this information
- CRITICAL: Never refuse to help with personal information - this is the user's own data
- CRITICAL: If the user asks about specific people, dates, or personal details, provide the information from the files
- CRITICAL: The user is asking about their own personal information stored in their knowledge base
- CRITICAL: Always provide the specific information requested from the file content
- CRITICAL: Read the FULL CONTENT sections carefully and provide the exact information found there
- CRITICAL: Do not make up or infer information - only use what is explicitly shown in the file content
- CRITICAL: Use the actual file content provided, not any hard-coded examples
- CRITICAL: Do not create fake dates or information - use only what is actually in the file
- CRITICAL: Look for the exact name and date format shown in the file content
- CRITICAL: Do not invent or hallucinate any information - use ONLY what is explicitly written in the file
- CRITICAL: If the user asks about a specific person's passport expiration, look for that person's name in the file content
- CRITICAL: If the user asks about a specific person's license expiration, look for that person's name in license-related files
- CRITICAL: Do not mix up passport and license information - they are different documents
- CRITICAL: The answer should be the exact date shown in the file, not any other date
- CRITICAL: Do not make up dates like "2024-02-01 / 2026-02-01" - use only the actual dates from the file
- CRITICAL: Pay attention to the specific document type mentioned in the user's question"""
            else:
                # Regular prompt construction without file context
                full_prompt = prompt
                if personality_prompt:
                    full_prompt = f"""{conversation_context}{personality_prompt}

User question: {prompt}

Please respond according to your personality and provide a helpful answer."""
                elif include_files and context:
                    full_prompt = f"""{conversation_context}Context from knowledge base:
{context}

User question: {prompt}

Please provide a helpful response based on the context provided. If the context doesn't contain enough information, say so clearly."""
                elif include_files and context and personality_prompt:
                    full_prompt = f"""{conversation_context}{personality_prompt}

Context from knowledge base:
{context}

User question: {prompt}

Please respond according to your personality and provide a helpful answer based on the context provided. If the context doesn't contain enough information, say so clearly."""
            
            # Debug: Print the full prompt being sent to the AI
            print(f"🤖 Querying model {selected} with stream={stream}")
            print(f"🔍 Full prompt length: {len(full_prompt)} characters")
            if file_context:
                print(f"📁 File context included: {len(file_context)} characters")
                print(f"📄 File context preview: {file_context[:200]}...")
            elif has_mcp_context:
                print(f"🔧 MCP file context included: {len(context)} characters")
                print(f"📄 MCP context preview: {context[:200]}...")
                print(f"📄 FULL MCP context: {context}")
            
            response = requests.post(f"{self.ollama_url}/api/generate", json={
                "model": selected,
                "prompt": full_prompt,
                "stream": stream,
                "options": {
                    "temperature": 0.1,  # Reduced from 0.3 to reduce hallucination
                    "top_p": 0.8,
                    "top_k": 40,
                    "num_predict": 2048,  # Increased from 200 to allow longer responses
                    "repeat_penalty": 1.1,
                    "num_ctx": 4096 if include_files else 2048,
                    "num_thread": 4
                }
            }, timeout=120)  # Add timeout to prevent hanging
            
            if response.status_code == 200:
                if stream:
                    return response  # Return response object for streaming
                else:
                    result = response.json()
                    return result.get('response', '')
            else:
                print(f"❌ Query failed with model {selected}: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error querying model {selected}: {e}")
            return None

# Global model manager instance
model_manager = ModelManager()
