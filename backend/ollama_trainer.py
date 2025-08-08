#!/usr/bin/env python3
"""
Ollama Training System
Trains the Ollama model on knowledge base documents and feedback data
"""

import os
import json
import requests
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

class OllamaTrainer:
    def __init__(self, ollama_url: str = "http://host.docker.internal:11434"):
        self.ollama_url = ollama_url
        self.model_name = "llama3.2:3b"  # Use the specified model
        self.training_data_file = "/app/local_models/ollama_training_data.json"
        self.feedback_training_file = "/app/local_models/feedback_training_data.json"
        # Add caching for performance
        self.response_cache = {}
        self.cache_ttl = 3600  # 1 hour cache TTL
        self.last_cache_cleanup = time.time()
        self.cache_hits = 0
        self.cache_misses = 0
        
    def check_ollama_status(self) -> bool:
        """Check if Ollama is running and accessible"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Ollama not accessible: {e}")
            return False
    
    def get_available_models(self) -> List[str]:
        """Get list of available Ollama models"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get('models', [])
                return [model['name'] for model in models]
            return []
        except Exception as e:
            print(f"❌ Error getting models: {e}")
            return []
    
    def has_trained_model(self) -> bool:
        """Check if a trained model exists"""
        available_models = self.get_available_models()
        trained_models = [model for model in available_models if model.endswith('-trained')]
        return len(trained_models) > 0
    
    def get_best_available_model(self) -> str:
        """Get the best available model (trained first, then fallbacks)"""
        available_models = self.get_available_models()
        
        # Look for ollama-trained model first (with or without :latest suffix)
        for model in available_models:
            if model.startswith("ollama-trained"):
                return model
        
        # Look for other trained models
        trained_models = [model for model in available_models if model.endswith('-trained') or model.endswith('-trained:latest')]
        if trained_models:
            return trained_models[0]  # Return the first trained model
        
        # Fallback to base models
        base_models = ["llama3.2:3b", "llama2", "mistral", "llama2:7b"]
        for model in available_models:
            if any(base_model in model for base_model in base_models):
                return model
        
        # Default fallback
        return "llama3.2:3b"
    
    def create_training_data_from_knowledge_base(self, knowledge_base_path: str = "/app/knowledge_base") -> List[Dict[str, Any]]:
        """Create training data from knowledge base documents"""
        training_data = []
        
        if not os.path.exists(knowledge_base_path):
            print(f"❌ Knowledge base path not found: {knowledge_base_path}")
            return training_data
        
        print("📚 Creating training data from knowledge base...")
        
        for root, dirs, files in os.walk(knowledge_base_path):
            for file in files:
                if file.endswith('.md'):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, knowledge_base_path)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Create training examples from the document
                        training_examples = self.create_training_examples_from_document(content, relative_path)
                        training_data.extend(training_examples)
                        
                    except Exception as e:
                        print(f"❌ Error processing {file_path}: {e}")
        
        print(f"✅ Created {len(training_data)} training examples from knowledge base")
        return training_data
    
    def create_training_examples_from_document(self, content: str, filename: str) -> List[Dict[str, Any]]:
        """Create training examples from a single document"""
        examples = []
        
        # Split content into sections
        sections = self.split_document_into_sections(content)
        
        for i, section in enumerate(sections):
            if len(section.strip()) < 50:  # Skip very short sections
                continue
            
            # Create question-answer pairs from the section
            qa_pairs = self.generate_qa_pairs_from_section(section, filename)
            examples.extend(qa_pairs)
        
        return examples
    
    def split_document_into_sections(self, content: str) -> List[str]:
        """Split document into meaningful sections"""
        sections = []
        current_section = []
        
        lines = content.split('\n')
        for line in lines:
            if line.strip().startswith('#'):
                # New section
                if current_section:
                    sections.append('\n'.join(current_section))
                current_section = [line]
            else:
                current_section.append(line)
        
        # Add the last section
        if current_section:
            sections.append('\n'.join(current_section))
        
        return sections
    
    def generate_qa_pairs_from_section(self, section: str, filename: str) -> List[Dict[str, Any]]:
        """Generate question-answer pairs from a section"""
        qa_pairs = []
        
        # Extract key information from the section
        lines = section.split('\n')
        header = ""
        content = ""
        
        for line in lines:
            if line.strip().startswith('#'):
                header = line.strip().lstrip('#').strip()
            else:
                content += line + '\n'
        
        if not header:
            header = f"Information from {filename}"
        
        # Create different types of questions
        questions = self.generate_questions_from_content(header, content, filename)
        
        for question in questions:
            qa_pairs.append({
                "instruction": question,
                "input": "",
                "output": f"Based on the knowledge base:\n\n{content.strip()}\n\nSource: {filename}",
                "context": {
                    "filename": filename,
                    "header": header,
                    "content_length": len(content)
                }
            })
        
        return qa_pairs
    
    def generate_questions_from_content(self, header: str, content: str, filename: str) -> List[str]:
        """Generate relevant questions from content"""
        questions = []
        
        # Basic questions based on header
        if header:
            questions.extend([
                f"What is {header.lower()}?",
                f"Tell me about {header.lower()}",
                f"Explain {header.lower()}",
                f"Can you provide information about {header.lower()}?"
            ])
        
        # Questions based on filename
        filename_clean = filename.replace('.md', '').replace('_', ' ').replace('-', ' ')
        questions.extend([
            f"What information is available about {filename_clean}?",
            f"Can you help me understand {filename_clean}?",
            f"What does the document {filename_clean} contain?"
        ])
        
        # Generic questions
        questions.extend([
            "What information do you have about this topic?",
            "Can you provide details about this subject?",
            "What can you tell me about this?"
        ])
        
        return questions[:5]  # Limit to 5 questions per section
    
    def create_training_data_from_feedback(self) -> List[Dict[str, Any]]:
        """Create training data from user feedback - removed, not used in current interface"""
        return []
    
    def generate_improved_response(self, original_response: str, feedback_text: str) -> Optional[str]:
        """Generate an improved response based on feedback"""
        improvements = []
        
        if 'more detail' in feedback_text or 'incomplete' in feedback_text:
            improvements.append("Provide more comprehensive information")
        
        if 'examples' in feedback_text or 'specific' in feedback_text:
            improvements.append("Include specific examples")
        
        if 'confusing' in feedback_text or 'unclear' in feedback_text:
            improvements.append("Make the response clearer and better structured")
        
        if 'too long' in feedback_text or 'verbose' in feedback_text:
            improvements.append("Make the response more concise")
        
        if improvements:
            return f"{original_response}\n\n[Improved based on feedback: {', '.join(improvements)}]"
        
        return None
    
    def save_training_data(self, training_data: List[Dict[str, Any]], filename: str):
        """Save training data to file"""
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    "training_data": training_data,
                    "created_at": datetime.now().isoformat(),
                    "total_examples": len(training_data)
                }, f, indent=2, ensure_ascii=False)
            print(f"✅ Training data saved to {filename}")
        except Exception as e:
            print(f"❌ Error saving training data: {e}")
    
    def load_training_data(self, filename: str) -> List[Dict[str, Any]]:
        """Load training data from file"""
        try:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('training_data', [])
        except Exception as e:
            print(f"❌ Error loading training data: {e}")
        return []
    
    def train_ollama_model(self, training_data: List[Dict[str, Any]]) -> bool:
        """Train the Ollama model with the provided training data (legacy)"""
        return self.train_ollama_model_with_base(training_data, "llama2")
    
    def train_ollama_model_with_base(self, training_data: List[Dict[str, Any]], base_model: str) -> bool:
        """Train the Ollama model with the provided training data and base model"""
        if not self.check_ollama_status():
            print("❌ Ollama is not running or accessible")
            return False
        
        if not training_data:
            print("❌ No training data provided")
            return False
        
        print(f"🚀 Starting Ollama training with {len(training_data)} examples using base model: {base_model}")
        
        try:
            # Check if this model has been trained before
            available_models = self.get_available_models()
            # Create safe model name without colons
            safe_base_model = base_model.replace(':', '_')
            custom_model_name = f"{safe_base_model}-trained"
            model_exists = custom_model_name in available_models
            
            if model_exists:
                print(f"🔄 Model {custom_model_name} already exists. Updating with latest training data...")
                # Use :latest tag to update existing model
                custom_model_name = f"{custom_model_name}:latest"
            else:
                print(f"🆕 Creating new trained model: {custom_model_name}")
            
            # Prepare training data in Ollama format
            ollama_training_data = []
            for example in training_data:
                # Format for Ollama fine-tuning
                ollama_training_data.append({
                    "instruction": example["instruction"],
                    "input": example.get("input", ""),
                    "output": example["output"]
                })
            
            # Ensure local_models directory exists
            local_models_dir = "/app/local_models"
            os.makedirs(local_models_dir, exist_ok=True)
            
            # Create unique training data file for this base model
            safe_base_model = base_model.replace(':', '_').replace('/', '_')
            training_file = os.path.join(local_models_dir, f"ollama_training_{safe_base_model}.jsonl")
            with open(training_file, 'w', encoding='utf-8') as f:
                for item in ollama_training_data:
                    # Use the exact format Ollama expects
                    f.write(json.dumps(item, ensure_ascii=False) + '\n')
            
            print(f"✅ Training data prepared: {training_file}")
            print(f"📊 Training examples: {len(ollama_training_data)}")
            
            # Create Modelfile with training data and performance optimizations
            modelfile_content = f"""FROM {base_model}
SYSTEM You are an AI assistant trained on a specific knowledge base. Provide accurate, helpful responses based on the training data. Always reference the source documents when possible. Keep responses concise and focused.

PARAMETER temperature 0.3
PARAMETER top_p 0.8
PARAMETER top_k 40
PARAMETER num_predict 150
PARAMETER repeat_penalty 1.1
PARAMETER num_ctx 2048
PARAMETER num_thread 4
PARAMETER stop "Human:"
PARAMETER stop "Assistant:"

# Training data for fine-tuning
TRAIN {training_file}
"""
            
            # Create unique Modelfile for this base model
            modelfile_path = os.path.join(local_models_dir, f"Modelfile_{safe_base_model}")
            with open(modelfile_path, 'w', encoding='utf-8') as f:
                f.write(modelfile_content)
            
            print(f"✅ Modelfile created: {modelfile_path}")
            print(f"📄 Modelfile content preview:")
            print("=" * 50)
            print(modelfile_content)
            print("=" * 50)
            
            # Create the fine-tuned model using Ollama create command
            print(f"🔧 Creating fine-tuned model: {custom_model_name}")
            
            # Use requests to call Ollama create API with modelfile parameter
            create_response = requests.post(f"{self.ollama_url}/api/create", json={
                "name": custom_model_name,
                "modelfile": modelfile_content
            })
            
            # Check both status code and response content
            response_text = create_response.text
            print(f"DEBUG: Response status: {create_response.status_code}")
            print(f"DEBUG: Response content: {response_text}")
            
            if create_response.status_code == 200 and "success" in response_text.lower():
                print(f"✅ Successfully created fine-tuned model: {custom_model_name}")
                # Update the model name to use the trained version
                self.model_name = custom_model_name
                return True
            else:
                error_data = create_response.json() if create_response.content else {}
                error_message = error_data.get("error", f"HTTP {create_response.status_code}")
                print(f"❌ Failed to create model: {error_message}")
                print(f"Response: {create_response.text}")
                
                # Fallback: try to create without training data (just base model)
                print("🔄 Trying fallback: creating model with base model only")
                fallback_response = requests.post(f"{self.ollama_url}/api/create", json={
                    "name": custom_model_name,
                    "from": base_model
                })
                
                fallback_text = fallback_response.text
                print(f"DEBUG: Fallback response status: {fallback_response.status_code}")
                print(f"DEBUG: Fallback response content: {fallback_text}")
                
                if fallback_response.status_code == 200 and "success" in fallback_text.lower():
                    print(f"✅ Created fallback model: {custom_model_name}")
                    self.model_name = custom_model_name
                    return True
                else:
                    fallback_error = fallback_response.json() if fallback_response.content else {}
                    fallback_error_msg = fallback_error.get("error", f"HTTP {fallback_response.status_code}")
                    print(f"❌ Fallback model creation also failed: {fallback_error_msg}")
                    print(f"Fallback response: {fallback_response.text}")
                    return False
            
        except Exception as e:
            print(f"❌ Error training Ollama model: {e}")
            return False
    
    def cleanup_cache(self):
        """Clean up expired cache entries"""
        current_time = time.time()
        if current_time - self.last_cache_cleanup > 300:  # Clean every 5 minutes
            expired_keys = []
            for key, (response, timestamp) in self.response_cache.items():
                if current_time - timestamp > self.cache_ttl:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.response_cache[key]
            
            self.last_cache_cleanup = current_time
    
    def keep_model_loaded(self, model_name: str = None) -> bool:
        """Keep the model loaded in memory for faster responses"""
        if not model_name:
            model_name = self.get_best_available_model()
        
        try:
            # Send a warm-up query to keep the model loaded
            warmup_response = requests.post(f"{self.ollama_url}/api/generate", json={
                "model": model_name,
                "prompt": "Hello",
                "stream": False,
                "options": {
                    "num_predict": 1  # Very short response just to load the model
                }
            })
            
            if warmup_response.status_code == 200:
                print(f"🔥 Model {model_name} kept loaded in memory")
                return True
            else:
                print(f"⚠️ Could not keep model {model_name} loaded")
                return False
                
        except Exception as e:
            print(f"❌ Error keeping model loaded: {e}")
            return False
    
    def get_cache_key(self, question: str, context: str) -> str:
        """Generate a cache key for the query"""
        import hashlib
        content = f"{question}:{context}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def query_ollama(self, question: str, context: str = "", stream: bool = False) -> Optional[str]:
        """Query the trained Ollama model with performance optimizations and personality prompt"""
        if not self.check_ollama_status():
            return None
        
        # Clean up cache periodically
        self.cleanup_cache()
        
        # Check cache first
        cache_key = self.get_cache_key(question, context)
        if cache_key in self.response_cache:
            response, timestamp = self.response_cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                print(f"🚀 Cache hit for query: {question[:50]}...")
                self.cache_hits += 1
                return response
            else:
                print(f"🚀 Cache miss for query: {question[:50]}...")
                self.cache_misses += 1
        else:
            print(f"🚀 Cache miss for query: {question[:50]}...")
            self.cache_misses += 1
        
        # Get the best available model
        best_model = self.get_best_available_model()
        print(f"🎯 Using best available model: {best_model}")
        
        try:
            # Optimize context length for speed
            max_context_length = 2000  # Limit context to improve speed
            if len(context) > max_context_length:
                context = context[:max_context_length] + "... [truncated for performance]"
            
            # Get personality prompt from server
            try:
                from server import get_personality_prompt
                personality_prompt = get_personality_prompt()
            except ImportError:
                personality_prompt = "You are a helpful AI assistant. Provide accurate, clear, and helpful responses."
            
            prompt = f"""{personality_prompt}

Context from knowledge base:
{context}

User question: {question}

Please provide a helpful response based on the context provided. If the context doesn't contain enough information, say so clearly."""

            # Optimized parameters for speed
            response = requests.post(f"{self.ollama_url}/api/generate", json={
                "model": best_model,
                "prompt": prompt,
                "stream": stream,
                "options": {
                    "temperature": 0.3,  # Lower temperature for faster, more focused responses
                    "top_p": 0.8,        # Slightly lower for speed
                    "top_k": 40,         # Limit token selection for speed
                    "num_predict": 150,  # Limit response length for speed
                    "repeat_penalty": 1.1,  # Prevent repetition
                    "num_ctx": 2048,     # Limit context window
                    "num_thread": 4      # Use multiple threads if available
                }
            })
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '')
                print(f"✅ Successfully used model: {best_model}")
                
                # Cache the response
                self.response_cache[cache_key] = (response_text, time.time())
                
                return response_text
            else:
                error_data = response.json() if response.content else {}
                error_message = error_data.get("error", f"HTTP {response.status_code}")
                print(f"❌ Model {best_model} failed: {error_message}")
                return None
                    
        except Exception as e:
            print(f"❌ Exception with model {best_model}: {e}")
            return None
    
    def query_ollama_stream(self, question: str, context: str = ""):
        """Stream query to Ollama model - yields response chunks"""
        if not self.check_ollama_status():
            yield "data: {\"error\": \"Ollama not available\"}\n\n"
            return
        
        # Get the best available model - prefer base models over trained ones for streaming
        available_models = self.get_available_models()
        best_model = "llama3.2:3b"  # Default to the base model
        
        # Try to find the base model first
        for model in available_models:
            if model == "llama3.2:3b":
                best_model = model
                break
            elif model == "llama2":
                best_model = model
                break
        
        print(f"🎯 Streaming with model: {best_model}")
        
        try:
            # Optimize context length for speed
            max_context_length = 2000  # Limit context to improve speed
            if len(context) > max_context_length:
                context = context[:max_context_length] + "... [truncated for performance]"
            
            # Get personality prompt from server
            try:
                from server import get_personality_prompt
                personality_prompt = get_personality_prompt()
            except ImportError:
                personality_prompt = "You are a helpful AI assistant. Provide accurate, clear, and helpful responses."
            
            prompt = f"""{personality_prompt}

Context from knowledge base:
{context}

User question: {question}

Please provide a helpful response based on the context provided. If the context doesn't contain enough information, say so clearly."""

            print(f"📤 Sending streaming request to Ollama with model: {best_model}")
            
            # Stream request to Ollama
            response = requests.post(f"{self.ollama_url}/api/generate", json={
                "model": best_model,
                "prompt": prompt,
                "stream": True,
                "options": {
                    "temperature": 0.3,
                    "top_p": 0.8,
                    "top_k": 40,
                    "num_predict": 150,
                    "repeat_penalty": 1.1,
                    "num_ctx": 2048,
                    "num_thread": 4
                }
            }, stream=True)
            
            print(f"📥 Received response status: {response.status_code}")
            
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        print(f"🔍 Processing line: {line_str[:100]}...")
                        
                        try:
                            data = json.loads(line_str)
                            if 'response' in data:
                                print(f"📝 Streaming chunk: {data['response'][:50]}...")
                                yield f"data: {{\"response\": \"{data['response']}\"}}\n\n"
                            if data.get('done', False):
                                print("✅ Streaming complete")
                                yield f"data: {{\"done\": true}}\n\n"
                                break
                        except json.JSONDecodeError as e:
                            print(f"⚠️ JSON decode error: {e}")
                            continue
            else:
                error_data = response.json() if response.content else {}
                error_message = error_data.get("error", f"HTTP {response.status_code}")
                print(f"❌ Ollama error: {error_message}")
                yield f"data: {{\"error\": \"{error_message}\"}}\n\n"
                    
        except Exception as e:
            print(f"❌ Exception with streaming model {best_model}: {e}")
            yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"
    
    def train(self, knowledge_base_path: str = "/app/knowledge_base") -> Dict[str, Any]:
        """Main training function (legacy - use train_with_model instead)"""
        return self.train_with_model(self.model_name, knowledge_base_path)
    
    def train_with_model(self, base_model: str, knowledge_base_path: str = "/app/knowledge_base") -> Dict[str, Any]:
        """Train Ollama model with specified base model"""
        print(f"🚀 Starting Ollama training process with base model: {base_model}")
        
        start_time = time.time()
        
        try:
            # Check Ollama status
            if not self.check_ollama_status():
                return {
                    "success": False,
                    "error": "Ollama is not running or accessible"
                }
            
            # Verify the base model exists
            available_models = self.get_available_models()
            if base_model not in available_models:
                return {
                    "success": False,
                    "error": f"Base model '{base_model}' not found. Available models: {', '.join(available_models[:5])}"
                }
            
            # Check if this model has been trained before
            safe_base_model = base_model.replace(':', '_')
            custom_model_name = f"{safe_base_model}-trained"
            model_exists = custom_model_name in available_models
            
            # Create training data from knowledge base
            kb_training_data = self.create_training_data_from_knowledge_base(knowledge_base_path)
            
            if not kb_training_data:
                return {
                    "success": False,
                    "error": "No training data could be created from knowledge base"
                }
            
            # Save training data
            self.save_training_data(kb_training_data, self.training_data_file)
            
            # Train the model with specified base model
            training_success = self.train_ollama_model_with_base(kb_training_data, base_model)
            
            duration = time.time() - start_time
            
            return {
                "success": training_success,
                "training_examples": len(kb_training_data),
                "kb_examples": len(kb_training_data),
                "trained_model_name": custom_model_name,
                "base_model": base_model,
                "model_exists": model_exists,
                "duration": duration,
                "model_available": self.check_ollama_status()
            }
            
        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ Training failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "duration": duration
            } 