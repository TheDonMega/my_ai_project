# server.py
import os
import google.generativeai as genai
from dotenv import load_dotenv

# Import CrewAI analyzer
try:
    from crewai_analyzer import get_crewai_analyzer
    CREWAI_AVAILABLE = True
    print("✅ CrewAI integration available")
except ImportError as e:
    CREWAI_AVAILABLE = False
    print(f"⚠️  CrewAI not available: {e}")

# --- Setup ---
# Load environment variables from .env file
load_dotenv()
# Configure the Gemini API key (only used for web search, not for CrewAI)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# --- 1. Load the Knowledge Base ---
def load_knowledge_base(folder_path="./knowledge_base"):
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
    
    for doc in knowledge_base:
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
            
            # Only include sections with matches
            if score > 0:
                # Extract folder path from filename (everything before the last '/')
                filename_parts = doc['filename'].split('/')
                folder_path = '/'.join(filename_parts[:-1]) if len(filename_parts) > 1 else 'root'
                
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

# --- 3. Query Gemini with Context ---
def ask_gemini_with_context(query, context_documents):
    """Formats a prompt with context and queries the Gemini API with web search capabilities."""
    # Combine the content of the context documents
    context = "\n\n---\n\n".join([doc['content'] for doc in context_documents])
    
    print(f"DEBUG: ask_gemini_with_context called")
    print(f"DEBUG: Query: {query}")
    print(f"DEBUG: Context length: {len(context)}")
    print(f"DEBUG: Context preview: {context[:200]}...")

    # Create the prompt for the model
    prompt = f"""
    You are an AI assistant with access to both local knowledge base content and web search capabilities.

    LOCAL CONTEXT (from knowledge base):
    {context}

    USER'S QUESTION:
    {query}

    INSTRUCTIONS:
    1. First, try to answer the question using ONLY the local context provided above.
    2. If the local context contains sufficient information to answer the question, provide a complete answer based on that context.
    3. If the local context is insufficient or doesn't contain the specific information needed, use web search to find additional information.
    4. When using web search, clearly indicate in your response that you searched the web for additional information.
    5. Always structure your response to show:
       - What you found in the local context (if anything)
       - Whether you needed to search the web
       - What additional information you found through web search (if applicable)
       - A comprehensive final answer combining both sources

    Please provide a detailed, well-structured response that addresses the user's question completely.
    """

    print("\n--- Asking Gemini with Web Search ---")
    try:
        # Use Gemini 1.5 Flash with web search capabilities
        # Note: Web search is automatically available in some Gemini models
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Create the generation config
        generation_config = genai.types.GenerationConfig(
            temperature=0.7,
            top_p=0.8,
            top_k=40
        )
        
        # Enhanced prompt that explicitly requests web search when needed
        enhanced_prompt = f"""
        {prompt}

        WEB SEARCH INSTRUCTION:
        If the local context above is insufficient to fully answer the user's question, you have access to web search capabilities. 
        Please search the web for current, accurate, and comprehensive information to supplement the local context.
        
        When you use web search, please:
        1. Clearly indicate that you searched the web for additional information
        2. Cite the sources you found
        3. Provide a comprehensive answer that combines local context with web search results
        4. If web search doesn't yield relevant results, clearly state this
        
        If the local context is sufficient, you may not need to search the web.
        """
        
        response = model.generate_content(
            enhanced_prompt,
            generation_config=generation_config,
            safety_settings=[
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                }
            ]
        )
        
        # Check if response was blocked
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'finish_reason') and candidate.finish_reason == 'SAFETY':
                print("DEBUG: Response blocked by safety filters")
                return "I apologize, but I cannot provide information on this topic due to safety concerns."
        
        return response.text
        
    except Exception as e:
        print(f"DEBUG: Error calling Gemini API: {e}")
        # Fallback to local context only if web search fails
        fallback_prompt = f"""
        Based on the following local context, please answer the user's question.
        If the context does not contain sufficient information, clearly state that you don't have enough information from the local knowledge base.

        LOCAL CONTEXT:
        {context}

        USER'S QUESTION:
        {query}

        Note: Web search is currently unavailable. This response is based only on local knowledge base content.
        """
        
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(fallback_prompt)
            return response.text
        except Exception as fallback_error:
            print(f"DEBUG: Fallback also failed: {fallback_error}")
            return f"Error: Unable to process your request. Please try again later. Error details: {str(e)}"

# --- Flask Web Server Setup ---
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Load knowledge base at startup
kb = load_knowledge_base()

@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        'status': 'running',
        'documents_loaded': len(kb)
    })

@app.route('/ask', methods=['POST'])
def ask():
    if not kb:
        return jsonify({
            'error': 'Knowledge base is empty or not found. Please add .md files to the ./knowledge_base folder.'
        }), 500

    data = request.json
    if not data or 'question' not in data:
        return jsonify({'error': 'No question provided'}), 400

    user_question = data['question']
    steps = []
    
    # Handle the initial question - search local markdown only
    if 'step' not in data or data['step'] == 'initial':
        steps.append(f"Searching knowledge base with {len(kb)} documents...")

    # Initial search in knowledge base
    if data.get('step') == 'initial' or 'step' not in data:
        # Try CrewAI first if available
        if CREWAI_AVAILABLE:
            try:
                print("🤖 Using CrewAI for local knowledge base analysis...")
                crewai_analyzer = get_crewai_analyzer()
                crewai_result = crewai_analyzer.analyze_query(user_question)
                
                if crewai_result and crewai_result.get('answer'):
                    steps.append("CrewAI multi-agent analysis completed")
                    return jsonify({
                        'answer': crewai_result['answer'],
                        'sources': crewai_result.get('sources', []),
                        'next_step': 'ask_ai',
                        'prompt': 'Would you like me to analyze this further using AI? (Y/N)',
                        'steps': steps,
                        'method': crewai_result.get('method', 'crewai')
                    })
                else:
                    print("⚠️  CrewAI returned no results, falling back to simple search")
            except Exception as e:
                print(f"⚠️  CrewAI analysis failed: {e}, falling back to simple search")
        
        # Fallback to original search method
        relevant_docs = search_knowledge_base(user_question, kb)
        
        if not relevant_docs:
            steps.append("No relevant documents found in knowledge base.")
            return jsonify({
                'answer': "I couldn't find any relevant information in the local knowledge base.",
                'sources': [],
                'next_step': 'ask_ai',
                'prompt': 'Would you like me to analyze your question using AI? (Y/N)',
                'steps': steps
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
            'next_step': 'ask_ai',
            'prompt': 'Would you like me to analyze this further using AI? (Y/N)',
            'steps': steps,
            'method': 'simple_search'
        })

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
        answer = ask_gemini_with_context(message_to_send, context_docs)
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
if __name__ == "__main__":
    print(f"Starting server... Knowledge base loaded with {len(kb)} documents.")
    app.run(host='0.0.0.0', port=5557)