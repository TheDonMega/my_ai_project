# server.py
import os
import json
from dotenv import load_dotenv
from datetime import datetime
import time # Added for fast_llamaindex_query

# Import CrewAI analyzer
try:
    from crewai_analyzer import get_crewai_analyzer
    CREWAI_AVAILABLE = True
    print("✅ CrewAI integration available")
except ImportError as e:
    CREWAI_AVAILABLE = False
    print(f"⚠️  CrewAI not available: {e}")

# Import feedback system
try:
    from feedback_system import save_user_feedback, get_feedback_insights
    FEEDBACK_AVAILABLE = True
    print("✅ Feedback system available")
except ImportError as e:
    FEEDBACK_AVAILABLE = False
    print(f"⚠️  Feedback system not available: {e}")

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

# Import LlamaIndex hybrid search system
try:
    import hybrid_search
    HYBRID_SEARCH_AVAILABLE = True
    print("✅ Hybrid search system available")
except ImportError as e:
    HYBRID_SEARCH_AVAILABLE = False
    print(f"⚠️  Hybrid search system not available: {e}")

# Global variables for performance optimization
OLLAMA_AVAILABLE = False
OLLAMA_TRAINER = None
HYBRID_SEARCH_SYSTEM = None
MODEL_PRELOADED = False
PERSONALITY_PROMPT = ""
kb = []  # Global knowledge base variable

def load_personality_prompt():
    """Load personality/behavior prompt from behavior.md file"""
    global PERSONALITY_PROMPT
    
    try:
        behavior_file = "/app/knowledge_base/behavior.md"
        if os.path.exists(behavior_file):
            with open(behavior_file, 'r', encoding='utf-8') as f:
                PERSONALITY_PROMPT = f.read().strip()
                print(f"✅ Loaded personality prompt from behavior.md ({len(PERSONALITY_PROMPT)} characters)")
        else:
            print("⚠️ No behavior.md file found. Using default personality.")
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

# Initialize Hybrid Search System on startup
try:
    if HYBRID_SEARCH_AVAILABLE:
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        embedding_model = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
        llm_model = os.getenv("LLM_MODEL", "llama3.2:3b")
        use_chroma = os.getenv("USE_CHROMA", "true").lower() == "true"
        hybrid_weight = float(os.getenv("HYBRID_WEIGHT", "0.7"))
        
        HYBRID_SEARCH_SYSTEM = hybrid_search.HybridSearchSystem(
            knowledge_base_path="/app/knowledge_base",
            vector_store_path="/app/vector_store",
            ollama_base_url=ollama_url,
            embedding_model=embedding_model,
            llm_model=llm_model,
            use_chroma=use_chroma,
            hybrid_weight=hybrid_weight
        )
        print("✅ Hybrid search system initialized")
    else:
        print("⚠️ Hybrid search system not available")
except Exception as e:
    print(f"⚠️ Error initializing hybrid search system: {e}")
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
def search_knowledge_base(query, knowledge_base, num_results=3):  # Increased default results
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
    
    # Load feedback learning data for enhanced search
    feedback_enhancement = load_feedback_enhancement()
    
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
            filename_match_score = 10  # High priority for filename matches
        if any(word in folder_lower for word in query_words):
            filename_match_score = 8   # High priority for folder matches
        
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
                score += 2  # Bonus points for header matches
            
            # Add filename/folder match score
            score += filename_match_score
            
            # Apply feedback-based enhancements
            if feedback_enhancement:
                score = apply_feedback_enhancement(score, query, section, feedback_enhancement)
            
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

def load_feedback_enhancement():
    """Load feedback learning data for search enhancement"""
    try:
        from train_knowledge_base import KnowledgeBaseTrainer
        trainer = KnowledgeBaseTrainer()
        learning_data = trainer.load_feedback_learning_data()
        return learning_data.get('feedback_patterns', {})
    except Exception as e:
        print(f"⚠️  Error loading feedback enhancement: {e}")
        return {}

def apply_feedback_enhancement(score, query, section, feedback_patterns):
    """Apply feedback-based enhancements to search scores"""
    enhanced_score = score
    
    # Get query type for pattern matching
    query_lower = query.lower()
    query_type = categorize_query(query_lower)
    
    # Check if this query type has successful patterns
    successful_patterns = feedback_patterns.get('successful_patterns', [])
    for pattern in successful_patterns:
        if pattern.get('query_type') == query_type:
            # Boost score for queries that match successful patterns
            enhanced_score += 1
    
    # Check for common issues to avoid
    common_issues = feedback_patterns.get('common_issues', [])
    if 'irrelevant_response' in common_issues:
        # Be more strict with relevance scoring
        if enhanced_score < 2:
            enhanced_score *= 0.5
    
    # Check query improvements
    query_improvements = feedback_patterns.get('query_improvements', {})
    if query_lower in query_improvements:
        # Apply specific improvements for this query
        improvements = query_improvements[query_lower].get('suggested_improvements', [])
        if 'add_more_details' in improvements:
            # Boost sections with more detailed content
            if len(section['content']) > 200:
                enhanced_score += 1
    
    return enhanced_score

def categorize_query(query):
    """Categorize query type for pattern matching"""
    if any(word in query for word in ['how', 'what', 'why', 'when', 'where']):
        return 'question'
    elif any(word in query for word in ['explain', 'describe', 'tell me about']):
        return 'explanation'
    elif any(word in query for word in ['find', 'search', 'look for']):
        return 'search'
    elif any(word in query for word in ['compare', 'difference', 'vs']):
        return 'comparison'
    else:
        return 'general'

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
from flask import Flask, request, jsonify, Response
from flask_cors import CORS

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
        'crewai_available': CREWAI_AVAILABLE,
        'ollama_available': OLLAMA_AVAILABLE,
        'feedback_available': FEEDBACK_AVAILABLE,
        'personality_loaded': bool(PERSONALITY_PROMPT),
        'model_preloaded': MODEL_PRELOADED,
        'hybrid_search_available': HYBRID_SEARCH_AVAILABLE
    }
    
    # Add LlamaIndex status if available
    if HYBRID_SEARCH_SYSTEM:
        llamaindex_stats = HYBRID_SEARCH_SYSTEM.get_system_stats()
        status_data.update({
            'llamaindex_available': llamaindex_stats['llamaindex_available'],
            'llamaindex_stats': llamaindex_stats
        })
    
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
            # Use CrewAI for AI analysis
            if CREWAI_AVAILABLE:
                try:
                    print("🤖 Using CrewAI for local knowledge base analysis...")
                    # Use the correct knowledge base path for Docker container
                    crewai_analyzer = get_crewai_analyzer("/app/knowledge_base")
                    crewai_result = crewai_analyzer.analyze_query(user_question)
                    
                    if crewai_result and crewai_result.get('answer'):
                        steps.append("CrewAI multi-agent analysis completed")
                        return jsonify({
                            'answer': crewai_result['answer'],
                            'sources': crewai_result.get('sources', []),
                            'next_step': None,  # No further steps for AI analysis
                            'steps': steps,
                            'method': crewai_result.get('method', 'crewai')
                        })
                    else:
                        print("⚠️  CrewAI returned no results, falling back to hybrid search")
                except Exception as e:
                    print(f"⚠️  CrewAI analysis failed: {e}, falling back to hybrid search")
            
            # Use hybrid search if available, otherwise fallback to simple search
            if HYBRID_SEARCH_SYSTEM and HYBRID_SEARCH_SYSTEM.llamaindex_available:
                print("🔍 Using Hybrid Search System")
                search_results = HYBRID_SEARCH_SYSTEM.search(
                    query=user_question,
                    knowledge_base=kb,
                    search_mode='hybrid',
                    num_results=5,
                    similarity_threshold=0.6
                )
                
                if search_results['results']:
                    relevant_docs = []
                    for result in search_results['results']:
                        relevant_docs.append({
                            'section': result['content'],
                            'filename': result['filename'],
                            'score': result['score'],
                            'relevance': result.get('relevance', result['score']),
                            'folder_path': result.get('folder_path', ''),
                            'header': result.get('header', ''),
                            'source_type': result.get('source_type', 'hybrid')
                        })
                    steps.append(f"Hybrid search found {len(relevant_docs)} relevant sections")
                else:
                    print("❌ No relevant content found with hybrid search, falling back to keyword search")
                    relevant_docs = search_knowledge_base(user_question, kb)
                    steps.append("Falling back to keyword search")
            else:
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

@app.route('/feedback', methods=['POST'])
def submit_feedback():
    """Submit user feedback for an AI response"""
    if not FEEDBACK_AVAILABLE:
        return jsonify({'error': 'Feedback system not available'}), 500
    
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No feedback data provided'}), 400
        
        required_fields = ['user_question', 'ai_response', 'rating', 'feedback_type']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate rating
        rating = data['rating']
        if not isinstance(rating, int) or rating < 1 or rating > 5:
            return jsonify({'error': 'Rating must be an integer between 1 and 5'}), 400
        
        # Validate feedback type
        feedback_type = data['feedback_type']
        if feedback_type not in ['thumbs_up', 'thumbs_down', 'neutral']:
            return jsonify({'error': 'Invalid feedback type'}), 400
        
        # Save feedback
        success = save_user_feedback(
            user_question=data['user_question'],
            ai_response=data['ai_response'],
            rating=rating,
            feedback_type=feedback_type,
            feedback_text=data.get('feedback_text', ''),
            search_method=data.get('search_method', 'unknown'),
            sources_used=data.get('sources_used', []),
            relevance_score=data.get('relevance_score', 0.0),
            user_session_id=data.get('user_session_id', '')
        )
        
        if success:
            # Generate learning insights based on the feedback
            learning_insights = generate_feedback_insights(rating, feedback_type, data.get('feedback_text', ''))
            
            return jsonify({
                'success': True,
                'message': 'Feedback submitted successfully',
                'rating': rating,
                'feedback_type': feedback_type,
                'learning_insights': learning_insights,
                'will_improve': True,
                'next_steps': [
                    'Your feedback has been saved for learning',
                    'The system will analyze patterns from your feedback',
                    'Future responses will be improved based on your input',
                    'You can retrain the system to apply changes immediately'
                ]
            })
        else:
            return jsonify({'error': 'Failed to save feedback'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Error submitting feedback: {str(e)}'}), 500

def generate_feedback_insights(rating: int, feedback_type: str, feedback_text: str) -> list:
    """Generate learning insights based on feedback"""
    insights = []
    
    # Rating-based insights
    if rating >= 4:
        insights.append("✅ This response pattern will be reinforced for similar queries")
        insights.append("🎯 Future searches will prioritize this type of content")
    elif rating <= 2:
        insights.append("🔍 The system will avoid similar response patterns")
        insights.append("📈 Search relevance will be adjusted for better results")
    
    # Feedback text analysis
    feedback_lower = feedback_text.lower()
    
    if 'more detail' in feedback_lower or 'incomplete' in feedback_lower:
        insights.append("📝 Future responses will include more comprehensive information")
    
    if 'irrelevant' in feedback_lower or 'not helpful' in feedback_lower:
        insights.append("🎯 Search relevance thresholds will be improved")
    
    if 'confusing' in feedback_lower or 'unclear' in feedback_lower:
        insights.append("💡 Response clarity and structure will be enhanced")
    
    if 'too long' in feedback_lower or 'verbose' in feedback_lower:
        insights.append("✂️ Future responses will be more concise")
    
    if 'examples' in feedback_lower or 'specific' in feedback_lower:
        insights.append("📋 Responses will include more specific examples")
    
    if 'wrong' in feedback_lower or 'incorrect' in feedback_lower:
        insights.append("🔍 Information accuracy will be improved")
    
    if 'structure' in feedback_lower or 'organize' in feedback_lower:
        insights.append("📊 Response organization will be enhanced")
    
    return insights

@app.route('/feedback/insights', methods=['GET'])
def get_feedback_insights_endpoint():
    """Get insights from feedback data"""
    if not FEEDBACK_AVAILABLE:
        return jsonify({'error': 'Feedback system not available'}), 500
    
    try:
        insights = get_feedback_insights()
        return jsonify(insights)
    except Exception as e:
        return jsonify({'error': f'Error getting insights: {str(e)}'}), 500

@app.route('/feedback/stats', methods=['GET'])
def get_feedback_stats():
    """Get feedback statistics"""
    if not FEEDBACK_AVAILABLE:
        return jsonify({'error': 'Feedback system not available'}), 500
    
    try:
        from feedback_system import feedback_system
        stats = feedback_system.get_feedback_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': f'Error getting stats: {str(e)}'}), 500











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
    """Train Ollama model on knowledge base and feedback"""
    if not OLLAMA_AVAILABLE:
        return jsonify({
            'error': 'Ollama trainer not available'
        }), 500

    try:
        data = request.json
        if not data or data.get('action') != 'train_ollama':
            return jsonify({'error': 'Invalid training action'}), 400
        
        # Initialize Ollama trainer
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        ollama_trainer = OllamaTrainer(ollama_url)
        
        # Train the model
        result = ollama_trainer.train()
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Ollama model training completed successfully',
                'training_examples': result.get('training_examples', 0),
                'kb_examples': result.get('kb_examples', 0),
                'feedback_examples': result.get('feedback_examples', 0),
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
        'has_behavior_file': os.path.exists('/app/knowledge_base/behavior.md'),
        'behavior_file_path': '/app/knowledge_base/behavior.md'
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
            'has_behavior_file': os.path.exists('/app/knowledge_base/behavior.md')
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to reload personality: {str(e)}'
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

# --- LlamaIndex and Hybrid Search Endpoints ---

@app.route('/llamaindex/status', methods=['GET'])
def llamaindex_status():
    """Get LlamaIndex system status"""
    try:
        if not HYBRID_SEARCH_SYSTEM:
            return jsonify({
                'success': False,
                'error': 'Hybrid search system not available'
            })
        
        stats = HYBRID_SEARCH_SYSTEM.get_system_stats()
        return jsonify({
            'success': True,
            'llamaindex_available': stats['llamaindex_available'],
            'stats': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/llamaindex/rebuild', methods=['POST'])
def rebuild_llamaindex():
    """Rebuild LlamaIndex"""
    try:
        if not HYBRID_SEARCH_SYSTEM:
            return jsonify({
                'success': False,
                'error': 'Hybrid search system not available'
            })
        
        data = request.get_json() or {}
        force_rebuild = data.get('force_rebuild', True)
        
        result = HYBRID_SEARCH_SYSTEM.rebuild_index(force_rebuild=force_rebuild)
        
        return jsonify({
            'success': True,
            'result': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/search/hybrid', methods=['POST'])
def hybrid_search():
    """Perform hybrid search using LlamaIndex and keyword search"""
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({
                'success': False,
                'error': 'Query is required'
            }), 400
        
        query = data['query']
        search_mode = data.get('search_mode', 'hybrid')  # hybrid, llamaindex, keyword, fallback
        num_results = data.get('num_results', 5)
        similarity_threshold = data.get('similarity_threshold', 0.6)
        
        if not HYBRID_SEARCH_SYSTEM:
            return jsonify({
                'success': False,
                'error': 'Hybrid search system not available'
            })
        
        # Perform hybrid search
        search_results = HYBRID_SEARCH_SYSTEM.search(
            query=query,
            knowledge_base=kb,
            search_mode=search_mode,
            num_results=num_results,
            similarity_threshold=similarity_threshold
        )
        
        return jsonify({
            'success': True,
            'search_results': search_results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/search/llamaindex', methods=['POST'])
def llamaindex_query():
    """Query using LlamaIndex RAG pipeline"""
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({
                'success': False,
                'error': 'Query is required'
            }), 400
        
        query = data['query']
        use_cache = data.get('use_cache', True)
        similarity_threshold = data.get('similarity_threshold', 0.7)
        top_k = data.get('top_k', 5)
        
        if not HYBRID_SEARCH_SYSTEM:
            return jsonify({
                'success': False,
                'error': 'Hybrid search system not available'
            })
        
        # Query using LlamaIndex
        result = HYBRID_SEARCH_SYSTEM.query_with_llamaindex(
            query=query,
            use_cache=use_cache,
            similarity_threshold=similarity_threshold,
            top_k=top_k
        )
        
        return jsonify({
            'success': True,
            'result': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/search/stats', methods=['GET'])
def get_search_stats():
    """Get search system statistics"""
    try:
        if not HYBRID_SEARCH_SYSTEM:
            return jsonify({
                'success': False,
                'error': 'Hybrid search system not available'
            })
        
        stats = HYBRID_SEARCH_SYSTEM.get_system_stats()
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/llamaindex/query', methods=['POST'])
def pure_llamaindex_query():
    """Pure LlamaIndex query - fast RAG with your knowledge base"""
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({
                'success': False,
                'error': 'Query is required'
            }), 400
        
        query = data['query']
        use_cache = data.get('use_cache', True)
        similarity_threshold = data.get('similarity_threshold', 0.5)  # Lower threshold for more results
        top_k = data.get('top_k', 8)  # More results for better coverage
        
        if not HYBRID_SEARCH_SYSTEM:
            return jsonify({
                'success': False,
                'error': 'LlamaIndex system not available'
            }), 503
        
        # Check and update LlamaIndex availability
        if not HYBRID_SEARCH_SYSTEM.check_llamaindex_availability():
            return jsonify({
                'success': False,
                'error': 'LlamaIndex not available. Please train the knowledge base first.'
            }), 503
        
        # Query using pure LlamaIndex
        result = HYBRID_SEARCH_SYSTEM.query_with_llamaindex(
            query=query,
            use_cache=use_cache,
            similarity_threshold=similarity_threshold,
            top_k=top_k
        )
        
        if not result['success']:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Query failed')
            }), 500
        
        # Format the response for better readability
        response = {
            'success': True,
            'query': query,
            'answer': result['response'],
            'sources': [],
            'query_time': result['query_time'],
            'total_sources_found': result['total_sources'],
            'sources_used': result['filtered_sources']
        }
        
        # Format sources with file information
        for source in result['sources']:
            formatted_source = {
                'content': source['content'][:300] + '...' if len(source['content']) > 300 else source['content'],
                'filename': source['filename'],
                'relevance_score': round(source['score'], 3),
                'file_path': source['filename']
            }
            response['sources'].append(formatted_source)
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/llamaindex/fast-query', methods=['POST'])
def fast_llamaindex_query():
    """Fast LlamaIndex query - returns retrieved documents without LLM response generation"""
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({
                'success': False,
                'error': 'Query is required'
            }), 400
        
        query = data['query']
        top_k = data.get('top_k', 8)
        similarity_threshold = data.get('similarity_threshold', 0.0)
        
        if not HYBRID_SEARCH_SYSTEM:
            return jsonify({
                'success': False,
                'error': 'LlamaIndex system not available'
            }), 503
        
        # Check and update LlamaIndex availability
        if not HYBRID_SEARCH_SYSTEM.check_llamaindex_availability():
            return jsonify({
                'success': False,
                'error': 'LlamaIndex not available. Please train the knowledge base first.'
            }), 503
        
        start_time = time.time()
        
        # Get similar documents directly
        similar_docs = HYBRID_SEARCH_SYSTEM.llamaindex_manager.get_similar_documents(
            query=query,
            top_k=top_k,
            similarity_threshold=similarity_threshold
        )
        
        query_time = time.time() - start_time
        
        # Format the response
        response = {
            'success': True,
            'query': query,
            'query_time': query_time,
            'documents_found': len(similar_docs),
            'answer': f"Found {len(similar_docs)} relevant documents from your knowledge base.",
            'sources': []
        }
        
        # Format sources with file information
        for doc in similar_docs:
            formatted_source = {
                'content': doc['content'][:500] + '...' if len(doc['content']) > 500 else doc['content'],
                'filename': doc['filename'],
                'relevance_score': round(doc['score'], 6),
                'file_path': doc['filename'],
                'full_content': doc['content']  # Include full content for reference
            }
            response['sources'].append(formatted_source)
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/llamaindex/train', methods=['POST'])
def train_llamaindex():
    """Train/rebuild LlamaIndex on your knowledge base"""
    try:
        data = request.get_json() or {}
        force_rebuild = data.get('force_rebuild', True)
        
        if not HYBRID_SEARCH_SYSTEM:
            return jsonify({
                'success': False,
                'error': 'LlamaIndex system not available'
            }), 503
        
        # Rebuild the index
        result = HYBRID_SEARCH_SYSTEM.rebuild_index(force_rebuild=force_rebuild)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'LlamaIndex trained successfully!',
                'stats': {
                    'documents_processed': result['documents_processed'],
                    'chunks_created': result['chunks_created'],
                    'training_time': round(result['indexing_time'], 2),
                    'index_size_mb': result.get('index_size_mb', 0)
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Training failed')
            }), 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/llamaindex/debug', methods=['POST'])
def debug_llamaindex():
    """Debug endpoint to test document retrieval without LLM response"""
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({
                'success': False,
                'error': 'Query is required'
            }), 400
        
        query = data['query']
        top_k = data.get('top_k', 10)
        similarity_threshold = data.get('similarity_threshold', 0.0)
        
        if not HYBRID_SEARCH_SYSTEM:
            return jsonify({
                'success': False,
                'error': 'LlamaIndex system not available'
            }), 503
        
        # Check and update LlamaIndex availability
        if not HYBRID_SEARCH_SYSTEM.check_llamaindex_availability():
            return jsonify({
                'success': False,
                'error': 'LlamaIndex not available. Please train the knowledge base first.'
            }), 503
        
        # Get similar documents directly
        similar_docs = HYBRID_SEARCH_SYSTEM.llamaindex_manager.get_similar_documents(
            query=query,
            top_k=top_k,
            similarity_threshold=similarity_threshold
        )
        
        return jsonify({
            'success': True,
            'query': query,
            'documents_found': len(similar_docs),
            'documents': similar_docs
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

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
        
        return jsonify({
            'success': True,
            'message': f'Model {model_name} stop requested'
        })
            
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

@app.route('/query-with-model', methods=['POST'])
def query_with_model():
    """Query with selected model and optional file inclusion"""
    if not MODEL_MANAGER_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Model manager not available'
        }), 500
    
    try:
        data = request.get_json()
        if not data or 'question' not in data:
            return jsonify({
                'success': False,
                'error': 'Question is required'
            }), 400
        
        question = data['question']
        include_files = data.get('include_files', True)
        model_name = data.get('model_name')  # Optional override
        
        # Set model if specified
        if model_name:
            model_manager.set_selected_model(model_name)
        
        # Get context if including files
        context = ""
        sources = []
        if include_files and kb:
            relevant_docs = search_knowledge_base(question, kb, num_results=5)
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
        
        # Query the model
        response_text = model_manager.query_with_selected_model(
            prompt=question,
            stream=False,
            include_files=include_files,
            context=context
        )
        
        if response_text:
            return jsonify({
                'success': True,
                'answer': response_text,
                'sources': sources,
                'model_used': model_manager.get_selected_model(),
                'include_files': include_files,
                'method': 'model_manager'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to get response from model'
            }), 500
            
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
                relevant_docs = search_knowledge_base(question, kb, num_results=5)
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
                context=context
            )
            
            if response_obj:
                for line in response_obj.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        try:
                            data = json.loads(line_str)
                            if 'response' in data:
                                yield f"data: {{\"response\": \"{data['response']}\"}}\n\n"
                            if data.get('done', False):
                                yield f"data: {{\"done\": true}}\n\n"
                                break
                        except json.JSONDecodeError:
                            continue
            else:
                yield f"data: {{\"error\": \"Failed to get response from model\"}}\n\n"
                
        except Exception as e:
            yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"
    
    return Response(generate(), mimetype='text/plain')

if __name__ == "__main__":
    # Initialize knowledge base at startup
    reload_knowledge_base()
    print(f"Starting server... Knowledge base loaded with {len(kb)} documents.")
    app.run(host='0.0.0.0', port=5557)