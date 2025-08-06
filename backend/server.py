import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS

# Import the new SearchManager
from search_manager import SearchManager

# Load environment variables
load_dotenv()

# --- Global Variables ---
SEARCH_MANAGER = None
PERSONALITY_PROMPT = ""

# --- Personality Management ---
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

# --- Flask App Initialization ---
app = Flask(__name__)
CORS(app)

# --- App Initialization ---
def initialize_app():
    """Initialize the search manager and load personality prompt."""
    global SEARCH_MANAGER
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    embedding_model = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
    llm_model = os.getenv("LLM_MODEL", "llama2")
    use_chroma = os.getenv("USE_CHROMA", "true").lower() == "true"

    SEARCH_MANAGER = SearchManager(
        knowledge_base_path="/app/knowledge_base",
        vector_store_path="/app/vector_store",
        ollama_base_url=ollama_url,
        embedding_model=embedding_model,
        llm_model=llm_model,
        use_chroma=use_chroma
    )
    load_personality_prompt()

# --- Flask Routes ---
@app.route('/status', methods=['GET'])
def status():
    """Get system status"""
    if not SEARCH_MANAGER:
        return jsonify({'status': 'initializing'}), 503

    stats = SEARCH_MANAGER.get_system_stats()
    return jsonify({
        'status': 'running',
        'llamaindex_available': stats.get('llamaindex_available', False),
        'llamaindex_stats': stats.get('llamaindex_stats', {}),
        'personality_loaded': bool(PERSONALITY_PROMPT)
    })

@app.route('/ask', methods=['POST'])
def ask():
    """Handle a user's question"""
    if not SEARCH_MANAGER or not SEARCH_MANAGER.llamaindex_available:
        return jsonify({'error': 'LlamaIndex is not available or not initialized.'}), 503

    data = request.json
    if not data or 'question' not in data:
        return jsonify({'error': 'No question provided'}), 400

    user_question = data['question']
    
    # Add personality prompt to the query
    full_query = f"{get_personality_prompt()}\n\nUser question: {user_question}"

    try:
        result = SEARCH_MANAGER.query_with_llamaindex(query=full_query)
        
        if result['success']:
            return jsonify({
                'answer': result['response'],
                'sources': result['sources'],
                'method': 'llamaindex_rag',
                'ai_used': True,
                'fallback_used': False
            })
        else:
            return jsonify({
                'error': result.get('error', 'An unknown error occurred.'),
                'answer': 'I could not process your request.',
                'sources': []
            }), 500
            
    except Exception as e:
        print(f"Error in /ask endpoint: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/llamaindex/rebuild', methods=['POST'])
def rebuild_llamaindex():
    """Rebuild LlamaIndex"""
    if not SEARCH_MANAGER:
        return jsonify({'error': 'Search manager not initialized.'}), 503
        
    data = request.get_json() or {}
    force_rebuild = data.get('force_rebuild', True)
    
    result = SEARCH_MANAGER.rebuild_index(force_rebuild=force_rebuild)
    
    return jsonify(result)

@app.route('/personality/reload', methods=['POST'])
def reload_personality():
    """Reload personality prompt from behavior.md file"""
    try:
        load_personality_prompt()
        return jsonify({
            'success': True,
            'message': 'Personality prompt reloaded successfully',
            'personality_prompt': get_personality_prompt()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to reload personality: {str(e)}'
        }), 500

if __name__ == "__main__":
    initialize_app()
    app.run(host='0.0.0.0', port=5557)