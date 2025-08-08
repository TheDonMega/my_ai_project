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
            # Ollama doesn't have a direct "stop" API, but we can try to unload it
            # by making a request with a very short context
            response = requests.delete(f"{self.ollama_url}/api/generate", json={
                "model": model_name
            })
            
            # Remove from running models regardless of response
            self.running_models.discard(model_name)
            print(f"✅ Model {model_name} unload requested")
            return True
            
        except Exception as e:
            print(f"❌ Error unloading model {model_name}: {e}")
            self.running_models.discard(model_name)
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
        """Delete a model"""
        try:
            response = requests.delete(f"{self.ollama_url}/api/delete", json={
                "name": model_name
            })
            
            if response.status_code == 200:
                print(f"✅ Model {model_name} deleted successfully")
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
                                include_files: bool = True, context: str = "") -> Optional[str]:
        """Query using the selected model"""
        selected = self.get_selected_model()
        
        if not self.check_ollama_status():
            return None
        
        try:
            # Prepare the full prompt
            full_prompt = prompt
            if include_files and context:
                full_prompt = f"""Context from knowledge base:
{context}

User question: {prompt}

Please provide a helpful response based on the context provided. If the context doesn't contain enough information, say so clearly."""
            
            response = requests.post(f"{self.ollama_url}/api/generate", json={
                "model": selected,
                "prompt": full_prompt,
                "stream": stream,
                "options": {
                    "temperature": 0.3,
                    "top_p": 0.8,
                    "top_k": 40,
                    "num_predict": 200,
                    "repeat_penalty": 1.1,
                    "num_ctx": 4096 if include_files else 2048,
                    "num_thread": 4
                }
            })
            
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
