# AI Knowledge Base Analyzer

An intelligent knowledge base analyzer that uses AI to search through markdown files and provide comprehensive answers using local Ollama models. Features a dynamic personality system for customizable AI behavior, real-time knowledge base management, and advanced model training capabilities.

## 🚀 Features

### Core AI Capabilities
- **🤖 Local AI Processing**: Uses Ollama for local AI model inference
- **🎭 Dynamic Behavior System**: Switch between multiple AI personalities instantly
- **📁 Smart File Inclusion Control**: Choose whether to include knowledge base files in AI responses
- **🚀 Streaming Responses**: Real-time streaming responses with selected models
- **💻 Interactive CLI Interface**: Command-line style interface for queries

### Model Management
- **🤖 Advanced Model Management**: Select and switch between available Ollama models dynamically
- **🎯 Multiple Trained Models**: Train and maintain multiple custom models
- **📊 Model Statistics**: Detailed usage and performance metrics
- **⚡ Model Caching**: Performance optimization with intelligent caching

### Knowledge Base Management
- **🔧 MCP-Style File Operations**: Local file system tools for knowledge base management
- **📂 Real-time Knowledge Base Management**: Add documents without restarting containers
- **📄 Sources Display**: View found documents with relevant information
- **📂 Folder Structure Support**: Displays folder paths for better organization

### Document Conversion
- **📄 DOCX to Markdown Conversion**: Convert Word documents to Markdown format
- **🎵 Audio to Markdown Conversion**: Convert audio files to Markdown format using OpenAI Whisper
- **🔄 Complete Document Workflow**: Convert DOCX and audio files to Markdown for seamless knowledge base integration

### User Interface
- **🎨 Modern UI Layout**: Professional, responsive design
- **📂 Collapsible Sections**: Clean, organized interface
- **📱 Modal Document Viewer**: View full documents with proper overlay
- **🎯 Persistent UI State**: UI state saved in localStorage

## 🎭 Behavior System

The AI assistant's personality and behavior can be customized using multiple personality files in the `behavior_model` directory.

### Available Personalities

#### **Creative Storyteller** (`behavior.md`)
- **Imaginative and creative**: Uses vivid language and creative metaphors
- **Storytelling approach**: Frames responses as narratives when appropriate
- **Enthusiastic and engaging**: Shows excitement and passion for topics
- **Playful and fun**: Uses humor while staying helpful

#### **Friendly Helper** (`friendly.md`)
- **Warm and welcoming**: Creates a comfortable, non-intimidating environment
- **Patient and understanding**: Takes time to explain things clearly
- **Encouraging**: Supports users and celebrates their progress
- **Conversational tone**: Uses relaxed, friendly language

#### **Technical Expert** (`technical.md`)
- **Detail-oriented**: Pays close attention to technical specifications
- **Analytical**: Breaks down complex problems systematically
- **Practical**: Focuses on actionable, implementable solutions
- **Code examples**: Provides relevant code snippets and examples

### Quick Personality Setup

1. **Select from existing personalities:**
   - Use the Behavior Selector dropdown in the frontend
   - Choose from available personality files
   - Switch personalities instantly without restarting

2. **Create a custom personality:**
   ```bash
   nano ./behavior_model/my_custom_personality.md
   ```

3. **Reload personalities:**
   ```bash
   curl -X POST http://localhost:5557/personality/reload
   ```

### Behavior Management Commands

```bash
# List available behaviors
curl -s http://localhost:5557/behaviors

# Select a specific behavior
curl -X POST http://localhost:5557/behaviors/select \
  -H "Content-Type: application/json" \
  -d '{"behavior_filename": "technical.md"}'

# Check current personality
curl -s http://localhost:5557/personality

# Use the convenience script
./update_personality.sh
```

## 🚀 Model Training System

### Understanding Model Training

The system uses **fine-tuning with behavior enhancement**, which means:

#### **What Training Does:**
- **✅ Retains All Original Knowledge**: Your trained model keeps 100% of the base model's knowledge
- **✅ Adds Your Personality**: Applies your selected behavior/personality to responses
- **✅ Enhances Domain Expertise**: Improves responses about your specific content
- **✅ Optimizes Parameters**: Sets optimal response parameters for your use case

#### **Knowledge Distribution:**
- **Original Base Model Knowledge**: ~99.9% retained (general language, coding, math, etc.)
- **Your Personality/Behavior**: ~0.1% added (communication style, tone, approach)
- **Domain Expertise**: Enhanced through behavior prompts and parameter optimization

### Multiple Trained Models

The system supports training and maintaining multiple custom models:

#### **How It Works:**
1. **First Training**: Creates a new trained model with unique files
   - `Modelfile_{safe_model_name}` (e.g., `Modelfile_llama2_latest`)
   - `ollama_training_{safe_model_name}.jsonl` (e.g., `ollama_training_llama2_latest.jsonl`)
   - New trained model: `{safe_model_name}-trained` (e.g., `llama2_latest-trained`)

2. **Subsequent Training**: Updates existing models with latest data
   - Detects existing trained model
   - Updates with `:latest` tag (e.g., `llama2_latest-trained:latest`)
   - Overwrites existing Modelfile and training data
   - Shows "Updated" vs "Created" in success messages

#### **Training Workflow:**
1. Select a model from the dropdown
2. Click "🔄 Train Ollama Model" button
3. System validates model selection
4. Creates training data from knowledge base
5. Saves unique Modelfile and training data to `local_models/`
6. Creates/updates trained model using selected base model
7. Shows success message with model details

### Training Commands

```bash
# Train with selected model (requires model selection in frontend)
curl -X POST http://localhost:5557/train-ollama \
  -H "Content-Type: application/json" \
  -d '{"action": "train_ollama", "selected_model": "llama2:latest"}'

# Train with different base model
curl -X POST http://localhost:5557/train-ollama \
  -H "Content-Type: application/json" \
  -d '{"action": "train_ollama", "selected_model": "llama3.2:3b"}'
```

## 🤖 Model Management System

### Features
- **View Available Models**: See all Ollama models installed on your system with detailed information
- **Model Selection**: Choose which model to use for queries dynamically
- **Start/Stop Models**: Control which models are loaded in memory for performance optimization
- **Model Information**: View model size, type (trained vs. base), and running status
- **File Inclusion Control**: Toggle whether AI responses should include knowledge base files
- **Compact Dropdown Interface**: Easy model selection with detailed information

### Model Types
- **Base Models**: Original Ollama models (llama2, llama3.2:3b, mistral, etc.)
- **Trained Models**: Custom models trained on your knowledge base (marked with `-trained` suffix)
- **Running Models**: Models currently loaded in memory for faster responses

### Query Modes
1. **Knowledge-Based Mode** (include_files: true)
   - AI searches your knowledge base for relevant context
   - Provides document-specific answers with source citations
   - Shows found sources below CLI with relevance scores
   - "View" button to see full document content
   - Slower but more accurate for your content

2. **General Knowledge Mode** (include_files: false)
   - AI uses only its general training knowledge
   - Faster responses for general questions
   - No knowledge base search performed
   - No sources displayed

### Model Management Commands

```bash
# List all available models with details
curl http://localhost:5557/models

# Get currently running models
curl http://localhost:5557/models/running

# Select a specific model for queries
curl -X POST http://localhost:5557/models/select \
  -H "Content-Type: application/json" \
  -d '{"model_name": "llama3.2:3b-trained"}'

# Start a model (load into memory)
curl -X POST http://localhost:5557/models/llama3.2:3b/start

# Stop a model (unload from memory)
curl -X POST http://localhost:5557/models/llama3.2:3b/stop

# Get model statistics
curl http://localhost:5557/models/stats

# Pull a new model
curl -X POST http://localhost:5557/models/pull \
  -H "Content-Type: application/json" \
  -d '{"model_name": "llama3.2:3b"}'

# Delete a model
curl -X DELETE http://localhost:5557/models/llama3.2:3b-trained/delete
```

## 🔧 File Operation Tools

The AI Knowledge Base Analyzer includes powerful MCP-style file operation tools that allow your local AI models to perform file system operations through natural language queries.

### Key Features
- **Automatic File Detection**: The system automatically detects file-related questions and uses the appropriate tools
- **Date-Specific Searches**: Search for notes on specific dates (e.g., "Do I have any notes on 8/2/2025?")
- **Latest File Retrieval**: Find and display the most recently modified files
- **Content Search**: Search through file contents for specific terms
- **Real-time File Access**: Direct access to your knowledge base files without external APIs

### Available File Operations

#### 1. Find Latest File
**Example Questions:**
- "What is my last note?"
- "When was my last note added to Medscribe?"
- "Show me the latest file in the knowledge base"

#### 2. Date-Specific Searches
**Example Questions:**
- "Do I have any notes on 8/2/2025?"
- "What did I write on 8/11/2025?"
- "Show me notes from August 2025"

#### 3. File Content Retrieval
**Example Questions:**
- "What's in my latest Medscribe note?"
- "Show me the content of my last note"
- "What did I write in my most recent file?"

#### 4. File Listing and Search
**Example Questions:**
- "List all files in the Medscribe directory"
- "Show me all my notes"
- "What files do I have in the knowledge base?"

### File Operation API Endpoints

```bash
# Find latest file in directory
POST /tools/find-latest-file
{
  "directory": "Medscribe",
  "pattern": "*.md"
}

# List files with sorting options
POST /tools/list-files
{
  "directory": "Medscribe",
  "sort_by": "modified",
  "reverse": true
}

# Search files by name
POST /tools/search-files
{
  "query": "Medscribe",
  "directory": "",
  "case_sensitive": false
}

# Search file contents (grep-like)
POST /tools/grep-content
{
  "search_term": "patient",
  "directory": "Medscribe",
  "case_sensitive": false,
  "max_results": 10
}

# Get file content
POST /tools/get-file-content
{
  "filename": "8_14_2025 [Medscribe].md",
  "directory": "Medscribe"
}

# Get file information
POST /tools/get-file-info
{
  "filename": "8_14_2025 [Medscribe].md",
  "directory": "Medscribe"
}
```

## 📄 Document Conversion Features

### DOCX to Markdown Conversion
- **📤 Multiple File Upload**: Drag & drop or click to select multiple DOCX files
- **🔒 File Validation**: Only accepts .docx files for security
- **📝 Preserved Filenames**: Keeps original filenames with .md extension
- **📦 Smart Download**: Single file downloads as .md, multiple files as zip
- **⚡ Instant Conversion**: Fast conversion using Microsoft's markitdown library
- **💾 Automatic Download**: Converted files are automatically downloaded

### Audio to Markdown Conversion
- **📤 Multiple Audio Upload**: Drag & drop or click to select multiple audio files
- **🔒 Format Validation**: Only accepts supported audio formats for security
- **📝 Preserved Filenames**: Keeps original filenames with .md extension
- **📦 Smart Download**: Single file downloads as .md, multiple files as zip
- **⚡ CPU-Optimized**: Uses Whisper base model for efficient CPU processing
- **📋 Metadata Extraction**: Automatically extracts audio metadata (title, artist, album, duration, etc.)
- **💾 Automatic Download**: Transcribed files are automatically downloaded

### Supported Audio Formats
- MP3, WAV, M4A, FLAC, OGG, AAC, WMA

### How to Use Document Conversion

1. **Access the Converters**:
   - Click the "📄 Convert Notes to Markdown" button for DOCX conversion
   - Click the "🎵 Convert Audio to Markdown" button for audio transcription
   - Or navigate directly to `/convert-docx` or `/convert-audio`

2. **Upload Your Files**:
   - Click the upload area or drag and drop your files
   - Select multiple files by holding Ctrl/Cmd while clicking
   - File sizes and names are displayed for confirmation

3. **Convert and Download**:
   - Click the conversion button
   - Files are processed and automatically downloaded
   - Single file: downloads as .md file
   - Multiple files: downloads as zip file with all converted files

## 🔍 API Reference

### Core Endpoints

```bash
# Model Management
GET /models                           # List all available models
GET /models/running                   # List running models
POST /models/select                   # Select a model for queries
POST /models/{model_name}/start       # Start/load a model
POST /models/{model_name}/stop        # Stop/unload a model
GET /models/stats                     # Get model statistics
POST /models/pull                     # Pull a new model
DELETE /models/{model_name}/delete    # Delete a model

# Behavior Management
GET /behaviors                        # List available behaviors
POST /behaviors/select                # Select a behavior

# Query Endpoints
POST /query-with-model-stream         # Stream with selected model (recommended)
GET /document/{filename}              # Get full document content

# Training
POST /train-ollama                    # Train custom model (requires selected_model)

# Status and monitoring
GET /status
GET /performance

# Personality management
GET /personality
POST /personality/reload

# Knowledge base management
POST /knowledge-base/reload

# Document Conversion
POST /convert-docx-to-markdown        # Convert DOCX to Markdown
POST /convert-audio-to-text           # Convert Audio to Markdown
```

### Response Format

```json
{
  "answer": "AI response with personality applied",
  "sources": [
    {
      "filename": "document.md",
      "folder_path": "category",
      "relevance": 85.5,
      "content": "Relevant content excerpt"
    }
  ],
  "method": "model_manager",
  "model_used": "llama3.2:3b-trained",
  "include_files": true,
  "ai_used": true,
  "fallback_used": false
}
```

## 🚀 Quick Start

### 1. Install Ollama Locally

First, install Ollama on your local machine:

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows
# Download from https://ollama.ai/download
```

### 2. Start Ollama and Pull Base Models

```bash
# Start Ollama service
ollama serve

# In another terminal, pull the base model
ollama pull llama2
```

### 3. Build and Start the Application

```bash
# Build and start all services
chmod +x build_docker.sh
./build_docker.sh

# Or manually:
docker-compose down --rmi all && docker-compose up -d --build
```

### 4. Add Your Knowledge Base

```bash
# Add your .md files to ./knowledge_base/
# The system will automatically detect them
```

### 5. Select Personality (Optional)

```bash
# Use the Behavior Selector in the frontend to choose a personality
# Or edit/create personality files:
nano ./behavior_model/behavior.md

# Reload personality
./update_personality.sh
```

### 6. Train Custom Models (Optional)

1. Select a model from the dropdown in the frontend
2. Click "🔄 Train Ollama Model" button
3. Wait for training to complete
4. Use the trained model for better responses

### 7. Access the Application

- **Frontend**: http://localhost:5556
- **Backend**: http://localhost:5557
- **Ollama**: http://localhost:11434 (running locally)

## 📁 Project Structure

```
my_ai_project/
├── knowledge_base/           # Your markdown files (bind mounted)
├── behavior_model/           # AI personality configuration
│   ├── behavior.md           # Creative Storyteller personality (default)
│   ├── friendly.md           # Friendly Helper personality
│   ├── technical.md          # Technical Expert personality
│   └── storyteller.md        # Creative Storyteller personality
├── local_models/            # Local trained models and training data
│   ├── Modelfile_llama2_latest          # Modelfile for llama2:latest
│   ├── Modelfile_llama3.2_3b            # Modelfile for llama3.2:3b
│   ├── ollama_training_llama2_latest.jsonl
│   ├── ollama_training_llama3.2_3b.jsonl
│   └── ollama_training_data.json
├── backend/                 # Python Flask server
│   ├── server.py           # Main server with personality, model management, and file conversions
│   ├── ollama_trainer.py   # Model training and management
│   ├── model_manager.py    # Model management and selection
│   ├── train_knowledge_base.py  # Knowledge base indexing
│   ├── file_tools_integration.py # File operation tools
│   ├── mcp_server.py       # MCP server implementation
│   ├── llamaindex_manager.py # LlamaIndex integration
│   └── requirements.txt    # Python dependencies
├── frontend/               # Next.js React application
│   ├── pages/index.tsx     # Main interface with CLI and behavior selector
│   ├── pages/convert-docx.tsx  # DOCX to Markdown conversion page
│   ├── pages/convert-audio.tsx  # Audio to Markdown conversion page
│   ├── pages/manage-models.tsx  # Model management page
│   ├── components/         # React components
│   │   ├── BehaviorSelector.tsx  # Personality selection component
│   │   ├── ModelSelector.tsx     # Model selection component
│   │   ├── DocumentModal.tsx     # Document viewer modal
│   │   └── ...              # Other UI components
│   ├── styles/            # CSS modules
│   └── package.json       # Node.js dependencies
├── vector_store/          # Vector database storage
├── docker-compose.yml      # Container orchestration
├── build_docker.sh        # Build script
├── update_personality.sh   # Convenience script
└── init_volume.sh         # Setup verification script
```

## 🔧 Configuration

### Environment Variables

```bash
# Backend configuration
OLLAMA_BASE_URL=http://host.docker.internal:11434
PYTHONUNBUFFERED=1
EMBEDDING_MODEL=nomic-embed-text
LLM_MODEL=llama3.2:3b
USE_CHROMA=true
HYBRID_WEIGHT=0.7

# Local Ollama configuration (running on host)
# Ollama runs on localhost:11434 by default
```

### Docker Resources

The system is configured with optimized resource limits:

- **Backend**: 6GB memory, 3 CPUs  
- **Frontend**: 1GB memory, 0.5 CPUs
- **Ollama**: Running locally on host (not containerized)

## 🛠️ Troubleshooting

### Common Issues

1. **Personality not updating**: Run `./update_personality.sh`
2. **New documents not detected**: Call `/knowledge-base/reload` endpoint
3. **Container not starting**: Check logs with `docker logs my_ai_project-backend-1`
4. **Memory issues**: Increase Docker memory limits in `docker-compose.yml`
5. **Ollama connection issues**: Ensure Ollama is running locally with `ollama serve`
6. **Model not found**: Pull the base model with `ollama pull llama2`
7. **Training fails**: Make sure to select a model from the dropdown before training
8. **Streaming not working**: Check that the selected model is running
9. **Behavior not switching**: Use the Behavior Selector dropdown in the frontend
10. **Model management issues**: Check model status with `/models` endpoint
11. **Sources not displaying**: Check browser console for debugging messages
12. **File inclusion not working**: Ensure "Include Files" toggle is enabled in Query Options
13. **DOCX conversion fails**: Ensure markitdown library is installed with docx extras
14. **Audio conversion fails**: Ensure Whisper and FFmpeg are properly installed
15. **File operation tools not working**: Ensure the backend is running and check logs

### Debug Commands

```bash
# Check container status
docker ps

# View backend logs
docker logs my_ai_project-backend-1

# Check knowledge base files
docker exec my_ai_project-backend-1 ls -la /app/knowledge_base/

# Test personality system
curl -s http://localhost:5557/personality

# Test knowledge base
curl -s http://localhost:5557/status

# Test file operation tools
curl -X POST http://localhost:5557/tools/find-latest-file \
  -H "Content-Type: application/json" \
  -d '{"directory": "Medscribe", "pattern": "*.md"}'

# Check local Ollama status
curl -s http://localhost:11434/api/tags

# List available Ollama models
ollama list

# Check trained models
curl -s http://localhost:5557/models | jq '.models[] | select(.is_trained==true)'

# List available behaviors
curl -s http://localhost:5557/behaviors

# Test DOCX conversion endpoint
curl -X POST http://localhost:5557/convert-docx-to-markdown -F "files=@README.md" -v

# Test audio conversion endpoint
curl -X POST http://localhost:5557/convert-audio-to-text -F "files=@audio.mp3" -v
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with Docker: `./build_docker.sh && docker-compose up`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.
