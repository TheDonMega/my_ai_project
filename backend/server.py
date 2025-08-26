# server.py
import os
import json
from dotenv import load_dotenv
from datetime import datetime
import time # Added for fast_llamaindex_query

# CrewAI removed - using ModelManager instead
CREWAI_AVAILABLE = False

# Feedback system removed - not used in current interface
FEEDBACK_AVAILABLE = False

# Import Ollama trainer
try:
    from ollama_trainer import OllamaTrainer
    OLLAMA_AVAILABLE = True
    print("✅ Ollama trainer available")
except ImportError as e:
    OLLAMA_AVAILABLE = False
    print(f"⚠️  Ollama trainer not available: {e}")

# Import Model Manager
try:
    from model_manager import model_manager, ModelManager
    MODEL_MANAGER_AVAILABLE = True
    print("✅ Model manager available")
except ImportError as e:
    MODEL_MANAGER_AVAILABLE = False
    print(f"⚠️  Model manager not available: {e}")

# Hybrid search system removed - not used in current interface
HYBRID_SEARCH_AVAILABLE = False

# Global variables for performance optimization
OLLAMA_AVAILABLE = False
OLLAMA_TRAINER = None
HYBRID_SEARCH_SYSTEM = None
MODEL_PRELOADED = False
PERSONALITY_PROMPT = ""
kb = []  # Global knowledge base variable

def load_personality_prompt(behavior_filename: str = "behavior.md"):
    """Load personality/behavior prompt from specified behavior file"""
    global PERSONALITY_PROMPT
    
    try:
        behavior_file = f"/app/behavior_model/{behavior_filename}"
        if os.path.exists(behavior_file):
            with open(behavior_file, 'r', encoding='utf-8') as f:
                PERSONALITY_PROMPT = f.read().strip()
                print(f"✅ Loaded personality prompt from {behavior_filename} ({len(PERSONALITY_PROMPT)} characters)")
        else:
            print(f"⚠️ No {behavior_filename} file found. Using default personality.")
            PERSONALITY_PROMPT = "You are a helpful AI assistant. Provide accurate, clear, and helpful responses."
    except Exception as e:
        print(f"❌ Error loading personality prompt: {e}")
        PERSONALITY_PROMPT = "You are a helpful AI assistant. Provide accurate, clear, and helpful responses."

def get_personality_prompt():
    """Get the current personality prompt"""
    global PERSONALITY_PROMPT
    return PERSONALITY_PROMPT

def preload_ollama_model():
    """Preload the best available Ollama model for faster responses"""
    global OLLAMA_TRAINER, MODEL_PRELOADED
    
    try:
        if OLLAMA_TRAINER and not MODEL_PRELOADED:
            print("🚀 Preloading Ollama model for faster responses...")
            success = OLLAMA_TRAINER.keep_model_loaded()
            if success:
                MODEL_PRELOADED = True
                print("✅ Model preloaded successfully")
            else:
                print("⚠️ Model preloading failed, but continuing...")
    except Exception as e:
        print(f"❌ Error preloading model: {e}")

# Initialize Ollama trainer on startup
try:
    from ollama_trainer import OllamaTrainer
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_TRAINER = OllamaTrainer(ollama_url)
    if OLLAMA_TRAINER.check_ollama_status():
        OLLAMA_AVAILABLE = True
        print("✅ Ollama trainer available")
        # Preload the model after a short delay
        import threading
        def delayed_preload():
            import time
            time.sleep(5)  # Wait 5 seconds for everything to start
            preload_ollama_model()
        
        threading.Thread(target=delayed_preload, daemon=True).start()
    else:
        print("⚠️ Ollama trainer not available: Ollama is not running or accessible")
except ImportError as e:
    print(f"⚠️ Ollama trainer not available: {e}")

# Hybrid search system removed - not used in current interface
HYBRID_SEARCH_SYSTEM = None

# Load personality prompt on startup
load_personality_prompt()

# Load environment variables from .env file
load_dotenv()

# --- 1. Load the Knowledge Base ---
def load_knowledge_base(folder_path="/app/knowledge_base"):
    """Loads all .md files from a folder and its subfolders recursively into a list of dictionaries."""
    knowledge = []
    print(f"Loading documents from {folder_path} and subfolders...")
    
    def load_recursive(current_path, base_path):
        """Recursively load markdown files from current path and subdirectories."""
        try:
            for item in os.listdir(current_path):
                item_path = os.path.join(current_path, item)
                
                if os.path.isdir(item_path):
                    # Recursively search subdirectories
                    load_recursive(item_path, base_path)
                elif item.endswith(".md"):
                    # Calculate relative path from base knowledge_base directory
                    relative_path = os.path.relpath(item_path, base_path)
                    
                    with open(item_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        knowledge.append({
                            "filename": relative_path,  # Include folder path
                            "content": content,
                            "full_path": item_path
                        })
        except PermissionError:
            print(f"Permission denied accessing: {current_path}")
        except Exception as e:
            print(f"Error accessing {current_path}: {e}")
    
    # Start recursive search from the base folder
    load_recursive(folder_path, folder_path)
    print(f"Loaded {len(knowledge)} documents from {folder_path} and subfolders.")
    return knowledge

def reload_knowledge_base():
    """Reload the knowledge base from disk"""
    global kb
    kb = load_knowledge_base()
    return len(kb)

# --- 2. Search for Relevant Context ---
def search_knowledge_base(query, knowledge_base, num_results=5):  # Increased to 5 results for better coverage
    """
    Search for relevant sections in markdown files and extract the most relevant paragraphs.
    """
    def split_into_sections(content):
        """Split markdown content into sections based on headers and paragraphs."""
        sections = []
        current_section = []
        current_header = ""
        
        lines = content.split('\n')
        for line in lines:
            if line.strip().startswith('#'):  # New header
                if current_section:
                    sections.append({
                        'header': current_header,
                        'content': '\n'.join(current_section)
                    })
                current_section = []
                current_header = line.strip()
            else:
                if line.strip() or current_section:  # Keep empty lines only if we have content
                    current_section.append(line)
        
        # Add the last section
        if current_section:
            sections.append({
                'header': current_header,
                'content': '\n'.join(current_section)
            })
        return sections

    query_words = set(query.lower().split())
    results = []
    
    # Feedback enhancement removed - not used in current interface
    
    for doc in knowledge_base:
        # Extract folder path from filename (everything before the last '/')
        filename_parts = doc['filename'].split('/')
        folder_path = '/'.join(filename_parts[:-1]) if len(filename_parts) > 1 else 'root'
        filename = filename_parts[-1] if len(filename_parts) > 0 else doc['filename']
        
        # Check if query matches filename or folder path (high priority)
        filename_lower = filename.lower()
        folder_lower = folder_path.lower()
        query_lower = query.lower()
        
        # High score for filename/folder matches
        filename_match_score = 0
        if any(word in filename_lower for word in query_words):
            filename_match_score = 15  # Higher priority for filename matches
        if any(word in folder_lower for word in query_words):
            filename_match_score = 12   # Higher priority for folder matches
        
        # Extra bonus for exact folder name matches (like "QA" folder)
        if query_lower in folder_lower or folder_lower in query_lower:
            filename_match_score += 10  # Significant bonus for exact folder matches
        
        sections = split_into_sections(doc['content'])
        
        for section in sections:
            content = section['content']
            if not content.strip():
                continue
            
            # Calculate relevance score based on query words in the section
            # Include both header and content in the search
            search_text = (section['header'] + ' ' + content).lower()
            section_words = set(search_text.split())
            common_words = query_words.intersection(section_words)
            
            # Score calculation: words found + bonus for header matches
            score = len(common_words)
            if any(word in section['header'].lower() for word in query_words):
                score += 5  # Higher bonus points for header matches
            
            # Bonus for content length (more detailed content gets higher score)
            content_length_bonus = min(len(content.split()) / 100, 3)  # Max 3 points for long content
            score += content_length_bonus
            
            # Add filename/folder match score
            score += filename_match_score
            
            # Feedback enhancement removed - not used in current interface
            
            # Only include sections with matches (including filename matches)
            if score > 0:
                results.append({
                    "score": score,
                    "section": content.strip(),
                    "header": section['header'],
                    "filename": doc['filename'],
                    "folder_path": folder_path,
                    "relevance": round((score / (len(query_words) + 2)) * 100, 2)  # Adjusted for header bonus
                })
    
    # Sort by relevance score
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:num_results]

# Feedback enhancement functions removed - not used in current interface

# --- 3. Query Ollama with Context ---
def ask_ollama_with_context(query, context_documents):
    """Formats a prompt with context and queries Ollama for analysis."""
    # Combine the content of the context documents
    context = "\n\n---\n\n".join([doc['content'] for doc in context_documents])
    
    print(f"DEBUG: ask_ollama_with_context called")
    print(f"DEBUG: Query: {query}")
    print(f"DEBUG: Context length: {len(context)}")
    print(f"DEBUG: Context preview: {context[:200]}...")

    # Create the prompt for the model
    prompt = f"""
    You are an AI assistant with access to local knowledge base content.

    LOCAL CONTEXT (from knowledge base):
    {context}

    USER'S QUESTION:
    {query}

    INSTRUCTIONS:
    1. Answer the question using the local context provided above.
    2. If the local context contains sufficient information to answer the question, provide a complete answer based on that context.
    3. If the local context is insufficient or doesn't contain the specific information needed, clearly state that you don't have enough information from the local knowledge base.
    4. Always structure your response to show:
       - What you found in the local context (if anything)
       - Whether the local context was sufficient
       - A comprehensive answer based on available information

    Please provide a detailed, well-structured response that addresses the user's question based on the available local context.
    """

    print("\n--- Asking Ollama with Context ---")
    
    # Try models in order of preference
    models_to_try = ["ollama-trained", "mistral-trained", "llama2-trained", "llama2", "mistral"]
    
    for model in models_to_try:
        try:
            import requests
            import json
            
            print(f"🔄 Trying model: {model}")
            
            # Prepare the request data for Ollama API
            request_data = {
                "model": model,
                "prompt": prompt,
                "stream": False
            }
            
            # Make request to Ollama
            ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            response = requests.post(
                f"{ollama_url}/api/generate",
                json=request_data,
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "No response from Ollama")
                print(f"✅ Successfully used model: {model}")
                return response_text
            else:
                error_data = response.json() if response.content else {}
                error_message = error_data.get("error", f"HTTP {response.status_code}")
                print(f"❌ Model {model} failed: {error_message}")
                
                # If it's a memory error, try the next model
                if "memory" in error_message.lower():
                    print(f"⚠️  Memory issue with {model}, trying next model...")
                    continue
                else:
                    # For other errors, continue to next model
                    continue
        
        except Exception as e:
            print(f"❌ Exception with model {model}: {e}")
            # Continue to next model
            continue
    
    # If all models failed
    print("❌ All models failed")
    return "Error: Unable to get response from any Ollama model. Please check if Ollama is running and has available models."

# --- Flask Web Server Setup ---
from flask import Flask, request, jsonify, Response, send_file
from flask_cors import CORS
import tempfile
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# Load knowledge base at startup
reload_knowledge_base()

@app.route('/status', methods=['GET'])
def status():
    """Get system status"""
    status_data = {
        'status': 'running',
        'documents_loaded': reload_knowledge_base(),
        'knowledge_base_documents': len(kb),

        'ollama_available': OLLAMA_AVAILABLE,
        'feedback_available': FEEDBACK_AVAILABLE,
        'personality_loaded': bool(PERSONALITY_PROMPT),
        'model_preloaded': MODEL_PRELOADED
    }
    
    return jsonify(status_data)

@app.route('/ask', methods=['POST'])
def ask():
    if not kb:
        return jsonify({
            'error': 'Knowledge base is empty or not found. Please add .md files to the /app/knowledge_base folder.'
        }), 500

    data = request.json
    if not data or 'question' not in data:
        return jsonify({'error': 'No question provided'}), 400

    user_question = data['question']
    steps = []
    
    # Handle the initial question - use AI analysis by default
    if 'step' not in data or data['step'] == 'initial':
        steps.append(f"Searching knowledge base with {len(kb)} documents...")
        
        method = data.get('method', 'ai_analysis')
        
        if method == 'ai_analysis':
            # AI analysis method removed - use /query-with-model-stream instead
            return jsonify({
                'error': 'AI analysis method is deprecated. Please use the new CLI interface with /query-with-model-stream endpoint.',
                'method': 'deprecated'
            }), 400
            
            # Use traditional keyword search
            print("🔍 Using Traditional Keyword Search")
            relevant_docs = search_knowledge_base(user_question, kb)
            
            if not relevant_docs:
                steps.append("No relevant documents found in knowledge base.")
                return jsonify({
                    'answer': "I couldn't find any relevant information in the local knowledge base.",
                    'sources': [],
                    'next_step': None,
                    'steps': steps,
                    'method': 'simple_fallback'
                })

            # Found relevant docs in knowledge base
            steps.append(f"Found {len(relevant_docs)} relevant document sections")
            
            # Format the answer to show folder structure clearly
            answer_parts = []
            for doc in relevant_docs[:2]:
                if doc['folder_path'] == 'root':
                    location = f"From {doc['filename']}"
                else:
                    location = f"From {doc['folder_path']}/{doc['filename'].split('/')[-1]}"
                answer_parts.append(f"{location}:\n{doc['section']}")
            
            answer = "Based on the local knowledge base:\n\n" + "\n\n".join(answer_parts)
            
            sources = [{
                'filename': doc['filename'],
                'folder_path': doc['folder_path'],
                'relevance': doc['relevance'],
                'header': doc['header'] if doc['header'] else 'No header',
                'content': doc['section'],
                'full_document_available': True
            } for doc in relevant_docs]

            return jsonify({
                'answer': answer,
                'sources': sources,
                'next_step': None,
                'steps': steps,
                'method': 'simple_fallback'
            })
        
        else:
            # If method is not ai_analysis, return error
            return jsonify({
                'error': 'Invalid method. Only ai_analysis is supported.',
                'sources': [],
                'next_step': None,
                'steps': steps
            }), 400

    # Handle AI analysis confirmation
    elif data['step'] == 'ask_ai':
        if not data.get('confirm') or data['confirm'].lower() != 'y':
            # User chose not to use AI analysis, just remove the step prompt
            # Keep the original local search answer that was already displayed
            return jsonify({
                'next_step': None,
                'steps': steps
            })
        
        # User wants AI analysis, ask about message modification
        return jsonify({
            'next_step': 'ask_modify_message',
            'prompt': 'Do you want to update your message or keep it the same? (Y to update/N to keep)',
            'current_message': data['question'],
            'steps': steps
        })

    # Handle message modification choice
    elif data['step'] == 'ask_modify_message':
        steps.append("Checking if message needs modification...")
        if data.get('confirm', '').lower() == 'y':
            return jsonify({
                'next_step': 'enter_new_message',
                'prompt': 'Enter your updated message:',
                'current_message': data['question'],
                'steps': steps
            })
        else:
            # Keep original message and move to markdown selection
            return jsonify({
                'next_step': 'ask_include_markdown',
                'prompt': 'Would you like to include markdown files in the request? (Y/N)',
                'message_to_send': data['question'],
                'steps': steps
            })

    # Handle new message entry
    elif data['step'] == 'enter_new_message':
        new_message = data.get('new_message', data['question'])
        return jsonify({
            'next_step': 'ask_include_markdown',
            'prompt': 'Would you like to include markdown files in the request? (Y/N)',
            'message_to_send': new_message,
            'steps': steps
        })

    # Handle markdown inclusion choice
    elif data['step'] == 'ask_include_markdown':
        message_to_send = data.get('message_to_send', data['question'])
        if not data.get('confirm') or data['confirm'].lower() != 'y':
            # No markdown files to include, show final confirmation
            return jsonify({
                'next_step': 'confirm_request',
                'prompt': 'Review and confirm your request:',
                'message_to_send': message_to_send,
                'files_to_include': [],
                'steps': steps
            })
        
        # User wants to include markdown files, show selection
        # Use the already-loaded knowledge base to show all files with folder structure
        md_files = [doc['filename'] for doc in kb]  # This includes folder paths
        numbered_files = [f"{i+1}. {file}" for i, file in enumerate(md_files)]
        numbered_files.append(f"{len(md_files) + 1}. All files")
        
        return jsonify({
            'next_step': 'select_markdown_files',
            'prompt': 'Select the markdown files to include (comma-separated numbers):',
            'available_files': md_files,
            'display_files': numbered_files,
            'all_files_index': str(len(md_files) + 1),
            'message_to_send': message_to_send,
            'steps': steps
        })

    # Handle markdown file selection
    elif data['step'] == 'select_markdown_files':
        message_to_send = data.get('message_to_send', data['question'])
        selected_files = data.get('selected_files', [])
        
        return jsonify({
            'next_step': 'confirm_request',
            'prompt': 'Review and confirm your request:',
            'message_to_send': message_to_send,
            'files_to_include': selected_files,
            'steps': steps
        })

    # Handle final confirmation
    elif data['step'] == 'confirm_request':
        if not data.get('confirm') or data['confirm'].lower() != 'y':
            return jsonify({
                'answer': 'Request cancelled.',
                'next_step': None,
                'steps': steps
            })
            
        # Process the actual request with selected files and message
        message_to_send = data.get('message_to_send', data['question'])
        files_to_include = data.get('files_to_include', [])
        
        print(f"DEBUG: Processing confirm_request")
        print(f"DEBUG: message_to_send: {message_to_send}")
        print(f"DEBUG: files_to_include: {files_to_include}")
        
        # Build context from selected files
        context_docs = []
        if files_to_include:
            for filename in files_to_include:
                try:
                    # Find the file in the knowledge base to get its full path
                    file_doc = next((doc for doc in kb if doc['filename'] == filename), None)
                    if file_doc:
                        # Use the full_path from the knowledge base
                        file_path = file_doc['full_path']
                        print(f"DEBUG: Reading file: {file_path}")
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            print(f"DEBUG: File {filename} content length: {len(content)}")
                            context_docs.append({"content": content})
                    else:
                        print(f"DEBUG: File {filename} not found in knowledge base")
                        steps.append(f"File {filename} not found in knowledge base")
                except Exception as e:
                    print(f"Error reading file {filename}: {e}")
                    steps.append(f"Error reading file {filename}: {e}")
        else:
            print("DEBUG: No files to include")
        
        print(f"DEBUG: Context docs count: {len(context_docs)}")
        
        steps.append("Processing request with AI...")
        answer = ask_ollama_with_context(message_to_send, context_docs)
        steps.append("AI response received")
        
        return jsonify({
            'answer': answer,
            'next_step': None,
            'steps': steps,
            'sources': [{'filename': f, 'content': 'Included in AI analysis'} for f in files_to_include]
        })
    
    return jsonify({'error': 'Invalid step'}), 400

@app.route('/document/<path:filename>', methods=['GET'])
def get_document(filename):
    """Get the full content of a specific document"""
    try:
        # Find the file in the knowledge base to get its full path
        file_doc = next((doc for doc in kb if doc['filename'] == filename), None)
        if file_doc:
            # Use the full_path from the knowledge base
            file_path = file_doc['full_path']
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                return jsonify({
                    'filename': filename,
                    'content': content
                })
        else:
            return jsonify({'error': 'Document not found'}), 404
    except Exception as e:
        return jsonify({'error': f'Error reading document: {str(e)}'}), 500

# Feedback endpoints removed - not used in current interface











@app.route('/ask-ollama', methods=['POST'])
def ask_ollama():
    """Ask question using Ollama with knowledge base context"""
    if not OLLAMA_AVAILABLE:
        return jsonify({
            'error': 'Ollama trainer not available'
        }), 500

    if not kb:
        return jsonify({
            'error': 'Knowledge base is empty or not found. Please add .md files to the /app/knowledge_base folder.'
        }), 500

    data = request.json
    if not data or 'question' not in data:
        return jsonify({'error': 'No question provided'}), 400

    user_question = data['question']
    
    try:
        # Search knowledge base for relevant context
        relevant_docs = search_knowledge_base(user_question, kb, num_results=3)
        
        if not relevant_docs:
            return jsonify({
                'answer': "I couldn't find any relevant information in the knowledge base for your question.",
                'sources': [],
                'method': 'ollama_no_context'
            })
        
        # Prepare context from relevant documents
        context = "\n\n---\n\n".join([doc['section'] for doc in relevant_docs])
        
        # Query Ollama with context
        global OLLAMA_TRAINER
        
        if OLLAMA_TRAINER:
            ollama_response = OLLAMA_TRAINER.query_ollama(user_question, context)
        else:
            # Fallback to creating a new instance
            ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            ollama_trainer = OllamaTrainer(ollama_url)
            ollama_response = ollama_trainer.query_ollama(user_question, context)
        
        if ollama_response:
            print("✅ Ollama query successful - using AI-generated response")
            # Format sources
            sources = [{
                'filename': doc['filename'],
                'folder_path': doc['folder_path'],
                'relevance': doc['relevance'],
                'header': doc['header'] if doc['header'] else 'No header',
                'content': doc['section'],
                'full_document_available': True
            } for doc in relevant_docs]
            
            return jsonify({
                'answer': ollama_response,
                'sources': sources,
                'method': 'ollama_with_context',
                'ai_used': True,
                'fallback_used': False
            })
        else:
            print("⚠️  Ollama query failed - falling back to local search")
            # Fallback to simple search if Ollama fails
            answer_parts = []
            for doc in relevant_docs[:2]:
                if doc['folder_path'] == 'root':
                    location = f"From {doc['filename']}"
                else:
                    location = f"From {doc['folder_path']}/{doc['filename'].split('/')[-1]}"
                answer_parts.append(f"{location}:\n{doc['section']}")
            
            answer = "Based on the knowledge base:\n\n" + "\n\n".join(answer_parts)
            
            sources = [{
                'filename': doc['filename'],
                'folder_path': doc['folder_path'],
                'relevance': doc['relevance'],
                'header': doc['header'] if doc['header'] else 'No header',
                'content': doc['section'],
                'full_document_available': True
            } for doc in relevant_docs]
            
            return jsonify({
                'answer': answer,
                'sources': sources,
                'method': 'ollama_fallback',
                'ai_used': False,
                'fallback_used': True,
                'fallback_reason': 'Ollama AI service unavailable or failed to respond'
            })
            
    except Exception as e:
        print(f"Error in Ollama query: {e}")
        return jsonify({
            'error': f'Error processing Ollama query: {str(e)}'
        }), 500

@app.route('/ask-ollama-stream', methods=['POST'])
def ask_ollama_stream():
    """Stream question using Ollama with knowledge base context"""
    if not OLLAMA_AVAILABLE:
        return jsonify({
            'error': 'Ollama trainer not available'
        }), 500

    if not kb:
        return jsonify({
            'error': 'Knowledge base is empty or not found. Please add .md files to the /app/knowledge_base folder.'
        }), 500

    data = request.json
    if not data or 'question' not in data:
        return jsonify({'error': 'No question provided'}), 400

    user_question = data['question']
    
    def generate():
        try:
            # Search knowledge base for relevant context
            relevant_docs = search_knowledge_base(user_question, kb, num_results=3)
            
            if not relevant_docs:
                yield f"data: {{\"error\": \"I couldn't find any relevant information in the knowledge base for your question.\"}}\n\n"
                return
            
            # Prepare context from relevant documents
            context = "\n\n---\n\n".join([doc['section'] for doc in relevant_docs])
            
            # Send sources info first
            sources = [{
                'filename': doc['filename'],
                'folder_path': doc['folder_path'],
                'relevance': doc['relevance'],
                'header': doc['header'] if doc['header'] else 'No header',
                'content': doc['section'],
                'full_document_available': True
            } for doc in relevant_docs]
            
            yield f"data: {{\"sources\": {json.dumps(sources)}}}\n\n"
            
            # Query Ollama with streaming
            global OLLAMA_TRAINER
            
            if OLLAMA_TRAINER:
                for chunk in OLLAMA_TRAINER.query_ollama_stream(user_question, context):
                    yield chunk
            else:
                # Fallback to creating a new instance
                ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
                ollama_trainer = OllamaTrainer(ollama_url)
                for chunk in ollama_trainer.query_ollama_stream(user_question, context):
                    yield chunk
                    
        except Exception as e:
            print(f"Error in streaming Ollama query: {e}")
            yield f"data: {{\"error\": \"Error processing streaming Ollama query: {str(e)}\"}}\n\n"
    
    return Response(generate(), mimetype='text/plain')

@app.route('/train-ollama', methods=['POST'])
def train_ollama():
    """Train Ollama model on selected knowledge base files with custom naming"""
    if not OLLAMA_AVAILABLE:
        return jsonify({
            'error': 'Ollama trainer not available'
        }), 500

    try:
        data = request.json
        if not data or data.get('action') != 'train_ollama':
            return jsonify({'error': 'Invalid training action'}), 400
        
        # Get required parameters
        selected_model = data.get('selected_model')
        if not selected_model:
            return jsonify({
                'success': False,
                'error': 'No model selected. Please select a model from the dropdown before training.'
            }), 400
        
        # Get selected files/folders for training
        selected_files = data.get('selected_files', [])
        if not selected_files:
            return jsonify({
                'success': False,
                'error': 'No files selected for training. Please select at least one file or folder.'
            }), 400
        
        # Get custom model name suffix
        custom_name = data.get('custom_name', '').strip()
        if not custom_name:
            return jsonify({
                'success': False,
                'error': 'Custom model name is required.'
            }), 400
        
        # Get selected behavior file
        behavior_filename = data.get('behavior_filename', 'behavior.md')
        
        # Validate custom name (alphanumeric, hyphens, underscores only)
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', custom_name):
            return jsonify({
                'success': False,
                'error': 'Custom name can only contain letters, numbers, hyphens, and underscores.'
            }), 400
        
        # Initialize Ollama trainer
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        ollama_trainer = OllamaTrainer(ollama_url)
        
        # Train the model with selected files, custom name, and behavior
        result = ollama_trainer.train_with_custom_selection(
            base_model=selected_model,
            selected_files=selected_files,
            custom_name=custom_name,
            behavior_filename=behavior_filename
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': f'Ollama model training completed successfully',
                'base_model': selected_model,
                'trained_model': result.get('trained_model_name'),
                'custom_name': custom_name,
                'selected_files': selected_files,
                'training_examples': result.get('training_examples', 0),
                'kb_examples': result.get('kb_examples', 0),
                'duration': result.get('duration', 0),
                'training_time': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Training failed')
            }), 500
        
    except Exception as e:
        print(f"Ollama training error: {e}")
        return jsonify({
            'success': False,
            'error': f'Ollama training failed: {str(e)}'
        }), 500

@app.route('/knowledge-base/structure', methods=['GET'])
def get_knowledge_base_structure():
    """Get the structure of the knowledge base for training selection"""
    try:
        knowledge_base_path = "/app/knowledge_base"
        structure = []
        
        if not os.path.exists(knowledge_base_path):
            return jsonify({
                'success': True,
                'structure': [],
                'message': 'Knowledge base directory not found'
            })
        
        def scan_directory(path, base_path):
            items = []
            try:
                for item in sorted(os.listdir(path)):
                    if item.startswith('.'):
                        continue
                    
                    item_path = os.path.join(path, item)
                    relative_path = os.path.relpath(item_path, base_path)
                    
                    if os.path.isdir(item_path):
                        # Directory
                        children = scan_directory(item_path, base_path)
                        items.append({
                            'name': item,
                            'type': 'directory',
                            'path': relative_path,
                            'children': children,
                            'file_count': sum(1 for child in children if child['type'] == 'file')
                        })
                    elif item.endswith('.md'):
                        # Markdown file
                        try:
                            stat = os.stat(item_path)
                            size = stat.st_size
                            modified = datetime.fromtimestamp(stat.st_mtime).isoformat()
                            
                            items.append({
                                'name': item,
                                'type': 'file',
                                'path': relative_path,
                                'size': size,
                                'modified': modified
                            })
                        except OSError:
                            continue
            except PermissionError:
                pass
            
            return items
        
        structure = scan_directory(knowledge_base_path, knowledge_base_path)
        
        total_files = 0
        def count_files(items):
            nonlocal total_files
            for item in items:
                if item['type'] == 'file':
                    total_files += 1
                elif item['type'] == 'directory':
                    count_files(item['children'])
        
        count_files(structure)
        
        return jsonify({
            'success': True,
            'structure': structure,
            'total_files': total_files
        })
        
    except Exception as e:
        print(f"❌ Error getting knowledge base structure: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/performance', methods=['GET'])
def get_performance_stats():
    """Get performance statistics"""
    global OLLAMA_TRAINER
    
    stats = {
        "ollama_available": OLLAMA_AVAILABLE,
        "model_preloaded": MODEL_PRELOADED,
        "cache_size": len(OLLAMA_TRAINER.response_cache) if OLLAMA_TRAINER else 0,
        "cache_hits": getattr(OLLAMA_TRAINER, 'cache_hits', 0) if OLLAMA_TRAINER else 0,
        "cache_misses": getattr(OLLAMA_TRAINER, 'cache_misses', 0) if OLLAMA_TRAINER else 0
    }
    
    return jsonify(stats)

@app.route('/personality', methods=['GET'])
def get_personality():
    """Get current personality prompt"""
    return jsonify({
        'personality_prompt': get_personality_prompt(),
        'has_behavior_file': os.path.exists('/app/behavior_model/behavior.md'),
        'behavior_file_path': '/app/behavior_model/behavior.md'
    })

@app.route('/personality/reload', methods=['POST'])
def reload_personality():
    """Reload personality prompt from behavior.md file"""
    try:
        load_personality_prompt()
        return jsonify({
            'success': True,
            'message': 'Personality prompt reloaded successfully',
            'personality_prompt': get_personality_prompt(),
            'has_behavior_file': os.path.exists('/app/behavior_model/behavior.md')
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to reload personality: {str(e)}'
        }), 500

@app.route('/behaviors', methods=['GET'])
def get_behaviors():
    """Get list of available behavior files"""
    try:
        behavior_dir = "/app/behavior_model"
        behaviors = []
        
        if os.path.exists(behavior_dir):
            for filename in os.listdir(behavior_dir):
                if filename.endswith('.md'):
                    filepath = os.path.join(behavior_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                        # Extract name from first header or use filename
                        lines = content.split('\n')
                        name = filename.replace('.md', '').replace('_', ' ').replace('-', ' ').title()
                        description = "Custom behavior profile"
                        preview = ""
                        
                        for line in lines:
                            if line.startswith('# '):
                                name = line[2:].strip()
                                if ' - ' in name:
                                    parts = name.split(' - ', 1)
                                    name = parts[1]
                                    description = f"{parts[0]} behavior"
                                break
                        
                        # Get a preview from the content
                        for line in lines:
                            if line.strip() and not line.startswith('#') and not line.startswith('##'):
                                preview = line.strip()[:100] + "..." if len(line.strip()) > 100 else line.strip()
                                break
                        
                        behaviors.append({
                            'name': name,
                            'filename': filename,
                            'description': description,
                            'preview': preview
                        })
                        
                    except Exception as e:
                        print(f"Error reading behavior file {filename}: {e}")
                        
        return jsonify({
            'success': True,
            'behaviors': behaviors
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get behaviors: {str(e)}'
        }), 500

@app.route('/behaviors/select', methods=['POST'])
def select_behavior():
    """Select a behavior file to use"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Request data is required'
            }), 400
            
        behavior_filename = data.get('behavior_filename', 'behavior.md')
        
        # Load the selected behavior
        load_personality_prompt(behavior_filename)
        
        return jsonify({
            'success': True,
            'message': f'Behavior {behavior_filename} selected successfully',
            'selected_behavior': behavior_filename,
            'personality_prompt': get_personality_prompt()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to select behavior: {str(e)}'
        }), 500

@app.route('/knowledge-base/reload', methods=['POST'])
def reload_knowledge_base_endpoint():
    """Reload knowledge base from disk"""
    try:
        document_count = reload_knowledge_base()
        return jsonify({
            'success': True,
            'message': f'Knowledge base reloaded successfully with {document_count} documents',
            'documents_loaded': document_count
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to reload knowledge base: {str(e)}'
        }), 500

# LlamaIndex and Hybrid Search endpoints removed - not used in current interface

# --- Model Management Endpoints ---

@app.route('/models', methods=['GET'])
def get_models():
    """Get list of available models"""
    if not MODEL_MANAGER_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Model manager not available'
        }), 500
    
    try:
        models = model_manager.get_available_models()
        model_data = []
        
        for model in models:
            model_data.append({
                'name': model.name,
                'size': model.size,
                'size_mb': round(model.size / (1024**2), 1),
                'size_gb': round(model.size / (1024**3), 2),
                'modified_at': model.modified_at,
                'is_running': model.is_running,
                'is_trained': model.is_trained,
                'base_model': model.base_model,
                'description': model.description
            })
        
        return jsonify({
            'success': True,
            'models': model_data,
            'total_models': len(model_data),
            'selected_model': model_manager.get_selected_model()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/models/running', methods=['GET'])
def get_running_models():
    """Get list of currently running models"""
    if not MODEL_MANAGER_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Model manager not available'
        }), 500
    
    try:
        running_models = model_manager.get_running_models()
        return jsonify({
            'success': True,
            'running_models': running_models,
            'count': len(running_models)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/models/select', methods=['POST'])
def select_model():
    """Select a model for queries"""
    if not MODEL_MANAGER_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Model manager not available'
        }), 500
    
    try:
        data = request.get_json()
        if not data or 'model_name' not in data:
            return jsonify({
                'success': False,
                'error': 'Model name is required'
            }), 400
        
        model_name = data['model_name']
        success = model_manager.set_selected_model(model_name)
        
        if success:
            return jsonify({
                'success': True,
                'selected_model': model_name,
                'message': f'Model {model_name} selected successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Model {model_name} not available'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/models/<model_name>/start', methods=['POST'])
def start_model(model_name):
    """Start/load a model"""
    if not MODEL_MANAGER_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Model manager not available'
        }), 500
    
    try:
        success = model_manager.start_model(model_name)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Model {model_name} started successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to start model {model_name}'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/models/<model_name>/stop', methods=['POST'])
def stop_model(model_name):
    """Stop/unload a model"""
    if not MODEL_MANAGER_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Model manager not available'
        }), 500
    
    try:
        success = model_manager.stop_model(model_name)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Model {model_name} stopped successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to stop model {model_name}'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/models/stats', methods=['GET'])
def get_model_stats():
    """Get model statistics"""
    if not MODEL_MANAGER_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Model manager not available'
        }), 500
    
    try:
        stats = model_manager.get_model_stats()
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/models/pull', methods=['POST'])
def pull_model():
    """Pull/download a new model"""
    if not MODEL_MANAGER_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Model manager not available'
        }), 500
    
    try:
        data = request.get_json()
        if not data or 'model_name' not in data:
            return jsonify({
                'success': False,
                'error': 'Model name is required'
            }), 400
        
        model_name = data['model_name']
        success = model_manager.pull_model(model_name)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Model {model_name} pulled successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to pull model {model_name}'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/models/<model_name>/delete', methods=['DELETE'])
def delete_model(model_name):
    """Delete a model"""
    if not MODEL_MANAGER_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Model manager not available'
        }), 500
    
    try:
        # Check if it's a trained model before deletion for better response
        is_trained = model_manager._is_trained_model(model_name)
        
        success = model_manager.delete_model(model_name)
        
        if success:
            message = f'Model {model_name} deleted successfully'
            if is_trained:
                message += ' (including associated training files)'
            
            return jsonify({
                'success': True,
                'message': message,
                'was_trained_model': is_trained
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to delete model {model_name}'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/models/cleanup-orphaned-files', methods=['POST'])
def cleanup_orphaned_files():
    """Clean up orphaned training files that don't correspond to existing models"""
    if not MODEL_MANAGER_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Model manager not available'
        }), 500
    
    try:
        import os
        from pathlib import Path
        
        local_models_dir = "/app/local_models"
        if not os.path.exists(local_models_dir):
            return jsonify({
                'success': True,
                'message': 'No local_models directory found',
                'deleted_files': []
            })
        
        # Get all existing models
        existing_models = [model.name for model in model_manager.get_available_models()]
        print(f"🔍 Existing models: {existing_models}")
        
        # Get all files in local_models directory
        all_files = []
        for filename in os.listdir(local_models_dir):
            file_path = os.path.join(local_models_dir, filename)
            if os.path.isfile(file_path):
                all_files.append(filename)
        
        print(f"🔍 All files in local_models: {all_files}")
        
        # Find orphaned files (files that don't correspond to existing models)
        orphaned_files = []
        for filename in all_files:
            is_orphaned = True
            
            # Check if this file corresponds to any existing model
            for model_name in existing_models:
                # Extract base model and custom name
                base_model = model_manager._get_base_model(model_name)
                safe_base_model = base_model.replace(':', '_').replace('/', '_')
                
                # Check various patterns
                patterns_to_check = [
                    f"Modelfile_{safe_base_model}",
                    f"ollama_training_{safe_base_model}",
                    f"ollama_training_data_{safe_base_model}",
                ]
                
                # Add custom name patterns if model has custom name
                if '-' in model_name and not model_name.endswith('-trained'):
                    parts = model_name.split('-')
                    if len(parts) >= 2:
                        custom_name = '-'.join(parts[1:])
                        patterns_to_check.extend([
                            f"Modelfile_{safe_base_model}_{custom_name}",
                            f"ollama_training_{safe_base_model}_{custom_name}",
                            f"ollama_training_data_{safe_base_model}_{custom_name}",
                        ])
                        
                        # Also check truncated versions
                        for i in range(3, len(custom_name)):
                            short_name = custom_name[:i]
                            patterns_to_check.extend([
                                f"Modelfile_{safe_base_model}_{short_name}",
                                f"ollama_training_{safe_base_model}_{short_name}",
                                f"ollama_training_data_{safe_base_model}_{short_name}",
                            ])
                
                # Check if filename matches any pattern
                for pattern in patterns_to_check:
                    if filename.startswith(pattern):
                        is_orphaned = False
                        print(f"✅ File {filename} matches pattern {pattern} for model {model_name}")
                        break
                
                if not is_orphaned:
                    break
            
            if is_orphaned:
                orphaned_files.append(filename)
                print(f"❌ File {filename} is orphaned (no matching model found)")
        
        print(f"🔍 Orphaned files found: {orphaned_files}")
        
        # Delete orphaned files
        deleted_files = []
        for filename in orphaned_files:
            file_path = os.path.join(local_models_dir, filename)
            try:
                os.remove(file_path)
                deleted_files.append(filename)
                print(f"🗑️ Deleted orphaned file: {filename}")
            except OSError as e:
                print(f"⚠️ Could not delete {filename}: {e}")
        
        return jsonify({
            'success': True,
            'message': f'Cleaned up {len(deleted_files)} orphaned files',
            'deleted_files': deleted_files,
            'total_orphaned_found': len(orphaned_files)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500



@app.route('/query-with-model-stream', methods=['POST'])
def query_with_model_stream():
    """Stream query with selected model and optional file inclusion"""
    if not MODEL_MANAGER_AVAILABLE:
        return jsonify({
            'error': 'Model manager not available'
        }), 500
    
    data = request.get_json()
    if not data or 'question' not in data:
        return jsonify({'error': 'Question is required'}), 400
    
    question = data['question']
    include_files = data.get('include_files', True)
    model_name = data.get('model_name')  # Optional override
    
    def generate():
        try:
            # Set model if specified
            if model_name:
                model_manager.set_selected_model(model_name)
            
            # Get context if including files
            context = ""
            sources = []
            if include_files and kb:
                relevant_docs = search_knowledge_base(question, kb, num_results=8)  # Increased for better coverage
                if relevant_docs:
                    context = "\n\n---\n\n".join([doc['section'] for doc in relevant_docs])
                    sources = [{
                        'filename': doc['filename'],
                        'folder_path': doc['folder_path'],
                        'relevance': doc['relevance'],
                        'header': doc['header'] if doc['header'] else 'No header',
                        'content': doc['section'],
                        'full_document_available': True
                    } for doc in relevant_docs]
            
            # Send metadata first
            yield f"data: {{\"sources\": {json.dumps(sources)}, \"model_used\": \"{model_manager.get_selected_model()}\", \"include_files\": {json.dumps(include_files)}}}\n\n"
            
            # Stream the response
            response_obj = model_manager.query_with_selected_model(
                prompt=question,
                stream=True,
                include_files=include_files,
                context=context,
                personality_prompt=get_personality_prompt()
            )
            
            if response_obj:
                # Process Ollama's streaming response
                response_count = 0
                for line in response_obj.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        try:
                            data = json.loads(line_str)
                            
                            # Handle Ollama's streaming format
                            if 'response' in data:
                                # Escape any quotes in the response text
                                response_text = data['response'].replace('"', '\\"').replace('\n', '\\n')
                                yield f"data: {{\"response\": \"{response_text}\"}}\n\n"
                                response_count += 1
                            
                            # Check if done - break out of the loop when done
                            if data.get('done', False):
                                print(f"✅ Streaming completed with {response_count} response chunks")
                                # Send done signal and break
                                yield f"data: {{\"done\": true}}\n\n"
                                break
                                
                        except json.JSONDecodeError:
                            # Skip invalid JSON lines
                            continue
                            
                # Ensure we send a final done signal if we didn't already
                if response_count == 0:
                    print("⚠️ No response chunks received from Ollama")
                yield f"data: {{\"done\": true}}\n\n"
            else:
                yield f"data: {{\"error\": \"Failed to get response from model\"}}\n\n"
                
        except Exception as e:
            print(f"❌ Streaming error: {e}")
            yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"
    
    # Return proper Server-Sent Events response
    return Response(
        generate(), 
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Cache-Control'
        }
    )


@app.route('/convert-docx-to-markdown', methods=['POST'])
def convert_docx_to_markdown():
    """Convert uploaded DOCX files to Markdown format"""
    try:
        # Check if files were uploaded
        if 'files' not in request.files:
            return jsonify({'error': 'No files uploaded'}), 400
        
        files = request.files.getlist('files')
        
        # Check if files were selected
        if not files or all(file.filename == '' for file in files):
            return jsonify({'error': 'No files selected'}), 400
        
        # Check if all files are DOCX files
        invalid_files = [file.filename for file in files if not file.filename.lower().endswith('.docx')]
        if invalid_files:
            return jsonify({'error': f'All files must be DOCX files. Invalid files: {", ".join(invalid_files)}'}), 400
        
        # Create a temporary directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            converted_files = []
            
            # Process each file
            for file in files:
                if file.filename == '':
                    continue
                    
                # Secure the filename
                filename = secure_filename(file.filename)
                
                # Save the uploaded file temporarily
                docx_path = os.path.join(temp_dir, filename)
                file.save(docx_path)
                
                # Convert DOCX to Markdown using markitdown
                try:
                    from markitdown import MarkItDown
                    
                    # Create MarkItDown instance and convert the file
                    converter = MarkItDown()
                    result = converter.convert_local(docx_path)
                    markdown_content = result.text_content
                    
                    # Create the output filename (replace .docx with .md)
                    base_name = os.path.splitext(filename)[0]
                    markdown_filename = f"{base_name}.md"
                    markdown_path = os.path.join(temp_dir, markdown_filename)
                    
                    # Write the markdown content to file
                    with open(markdown_path, 'w', encoding='utf-8') as f:
                        f.write(markdown_content)
                    
                    converted_files.append((markdown_path, markdown_filename))
                    
                except ImportError:
                    return jsonify({'error': 'markitdown library not available'}), 500
                except Exception as e:
                    return jsonify({'error': f'Conversion failed for {filename}: {str(e)}'}), 500
            
            # Return single file or create zip for multiple files
            if len(converted_files) == 1:
                # Single file - return directly
                markdown_path, markdown_filename = converted_files[0]
                return send_file(
                    markdown_path,
                    as_attachment=True,
                    download_name=markdown_filename,
                    mimetype='text/markdown'
                )
            else:
                # Multiple files - create zip
                import zipfile
                zip_path = os.path.join(temp_dir, 'converted_files.zip')
                
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for markdown_path, markdown_filename in converted_files:
                        zipf.write(markdown_path, markdown_filename)
                
                # Create zip filename based on first file
                first_filename = os.path.splitext(secure_filename(files[0].filename))[0]
                zip_filename = f"{first_filename}_and_{len(converted_files) - 1}_more_files.zip"
                
                return send_file(
                    zip_path,
                    as_attachment=True,
                    download_name=zip_filename,
                    mimetype='application/zip'
                )
                
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500


if __name__ == "__main__":
    # Initialize knowledge base at startup
    reload_knowledge_base()
    print(f"Starting server... Knowledge base loaded with {len(kb)} documents.")
    app.run(host='0.0.0.0', port=5557)