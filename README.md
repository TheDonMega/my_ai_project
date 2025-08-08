# AI Knowledge Base Analyzer

An intelligent knowledge base analyzer that uses AI to search through markdown files and provide comprehensive answers using local Ollama models. Features a dynamic personality system for customizable AI behavior, real-time knowledge base management, and advanced model training capabilities.

## Features

- **🤖 Advanced Model Management**: Select and switch between available Ollama models dynamically
  - View all available models with detailed information (size, type, running status)
  - Start/stop models on demand
  - Auto-detect trained vs. base models
  - Real-time model status monitoring
  - Compact dropdown interface for easy model selection
- **📁 Smart File Inclusion Control**: Choose whether to include knowledge base files in AI responses
  - Toggle knowledge base search on/off
  - General knowledge mode for faster responses
  - Context-aware mode for document-specific queries
- **🚀 Streaming Responses**: Real-time streaming responses with selected models
  - Word-by-word streaming like Ollama CLI
  - Interactive CLI interface in the frontend
  - Real-time response generation
- **🎯 Multiple Trained Models**: Train and maintain multiple custom models
  - Train different base models on your knowledge base
  - Automatic model versioning with `:latest` tags
  - Unique Modelfiles and training data for each model
  - No overwriting - each base model gets its own trained version
- **💻 Interactive CLI Interface**: Command-line style interface for queries
  - Type questions and hit Enter for streaming responses
  - Command history display
  - Real-time streaming output
  - Ollama CLI-like experience in the browser
- **📂 Collapsible Sections**: Clean, organized interface
  - Collapsible training section
  - Collapsible query options section
  - Persistent UI state with localStorage
  - Focused, clutter-free interface
- **Local Knowledge Base Search**: Searches through markdown files recursively, including subfolders
- **Local AI Processing**: Uses Ollama for local AI model inference
- **Dynamic Personality System**: Customizable AI behavior through markdown files
- **Real-time Knowledge Base Management**: Add documents without restarting containers
- **Model Training**: Train custom Ollama models on your knowledge base
- **Folder Structure Support**: Displays folder paths for better organization
- **Modal Document Viewer**: View full documents with proper overlay

## 🚀 Model Training System

### Multiple Trained Models

The system now supports training and maintaining multiple custom models:

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

3. **Multiple Models**: Maintain separate trained models for different base models
   - `llama2_latest-trained:latest` (updated version)
   - `llama3.2_3b-trained:latest` (updated version)
   - Each model has its own training data and configuration

#### **Training Workflow:**
1. Select a model from the dropdown
2. Click "🔄 Train Ollama Model" button
3. System validates model selection
4. Creates training data from knowledge base
5. Saves unique Modelfile and training data to `local_models/`
6. Creates/updates trained model using selected base model
7. Shows success message with model details

#### **Files Created in `local_models/`:**
- **`Modelfile_{safe_model_name}`** - Unique Modelfile for each base model
- **`ollama_training_{safe_model_name}.jsonl`** - Training data for each model
- **`ollama_training_data.json`** - Combined training data

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

The AI Knowledge Base Analyzer includes a comprehensive model management system that allows you to:

### **Features**
- **View Available Models**: See all Ollama models installed on your system with detailed information
- **Model Selection**: Choose which model to use for queries dynamically
- **Start/Stop Models**: Control which models are loaded in memory for performance optimization
- **Model Information**: View model size, type (trained vs. base), and running status
- **File Inclusion Control**: Toggle whether AI responses should include knowledge base files
- **Compact Dropdown Interface**: Easy model selection with detailed information

### **Model Types**
- **Base Models**: Original Ollama models (llama2, llama3.2:3b, mistral, etc.)
- **Trained Models**: Custom models trained on your knowledge base (marked with `-trained` suffix)
- **Running Models**: Models currently loaded in memory for faster responses

### **Query Modes**
1. **Knowledge-Based Mode** (include_files: true)
   - AI searches your knowledge base for relevant context
   - Provides document-specific answers with source citations
   - Slower but more accurate for your content

2. **General Knowledge Mode** (include_files: false)
   - AI uses only its general training knowledge
   - Faster responses for general questions
   - No knowledge base search performed

### **Model Management Commands**
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
```

### **New Query Endpoints**
```bash
# Query with model selection and file inclusion control
curl -X POST http://localhost:5557/query-with-model \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is this knowledge base about?",
    "include_files": true,
    "model_name": "llama3.2:3b-trained"
  }'

# Stream responses with model selection
curl -X POST http://localhost:5557/query-with-model-stream \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Explain the main concepts",
    "include_files": true
  }'
```

## 💻 Interactive CLI Interface

The frontend now features an interactive CLI-style interface:

### **Features:**
- **Command-Line Style**: Type questions and hit Enter for responses
- **Real-Time Streaming**: Word-by-word streaming like Ollama CLI
- **Command History**: View previous questions and responses
- **Visual Cursor**: Animated cursor for authentic CLI feel
- **Response Streaming**: See responses generate in real-time

### **Usage:**
1. Type your question in the CLI input field
2. Press Enter to submit
3. Watch the response stream word-by-word
4. View command history below

## 📂 Collapsible Interface

The interface now includes collapsible sections for better organization:

### **Collapsible Sections:**
- **Ollama Model Training**: Training controls and information
- **Query Options**: File inclusion toggle and model info
- **Persistent State**: UI state saved in localStorage
- **Clean Interface**: Focus on what matters most

## 🎭 Personality System

The AI assistant's personality and behavior can be customized using a `behavior.md` file in your knowledge base. This allows you to:

- **Change AI personality instantly** without retraining models
- **Test different communication styles** (professional, casual, academic, creative)
- **Customize response formats** and tone
- **Apply domain-specific behaviors** (medical, technical, educational)

### Quick Personality Setup

1. **Create a personality file:**
   ```bash
   nano ./knowledge_base/behavior.md
   ```

2. **Example personality (Developer Mode):**
   ```markdown
   # AI Assistant Personality - Developer Mode
   
   You are a friendly, tech-savvy AI assistant with a developer-focused personality:
   
   ## Core Personality
   - **Casual and approachable**: Use a relaxed, conversational tone
   - **Tech-enthusiastic**: Show excitement about technical topics
   - **Pragmatic**: Focus on practical solutions
   
   ## Communication Style
   - **Use developer slang**: Feel free to use terms like "cool", "awesome"
   - **Include code examples**: When relevant, provide code snippets
   - **Be direct**: Get to the point quickly
   ```

3. **Reload the personality:**
   ```bash
   curl -X POST http://localhost:5557/personality/reload
   ```

### Personality Management Commands

```bash
# Check current personality
curl -s http://localhost:5557/personality

# Reload personality changes
curl -X POST http://localhost:5557/personality/reload

# Use the convenience script (reloads both personality and knowledge base)
./update_personality.sh
```

## 📚 Knowledge Base Management

### Adding New Documents

**No scripts or container restarts needed!** Simply add files to `./knowledge_base/` and reload:

```bash
# Add your .md files to ./knowledge_base/
# Then reload the knowledge base:
curl -X POST http://localhost:5557/knowledge-base/reload

# Check current document count:
curl -s http://localhost:5557/status

# Or use the convenience script:
./update_personality.sh
```

### Knowledge Base Commands

```bash
# Check current document count
curl -s http://localhost:5557/status

# Reload knowledge base (detects new files)
curl -X POST http://localhost:5557/knowledge-base/reload

# Get detailed knowledge base stats
curl -s http://localhost:5557/training/stats
```

### Real-time File Detection

- **Bind mount setup**: Your local `./knowledge_base/` folder is directly mounted to the container
- **Instant availability**: New files are immediately accessible
- **No volume management**: No need for scripts to copy files
- **Version control friendly**: Files stay in your local git repository

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
docker-compose down && docker-compose up -d --build
```

### 4. Add Your Knowledge Base

```bash
# Add your .md files to ./knowledge_base/
# The system will automatically detect them
```

### 5. Customize Personality (Optional)

```bash
# Edit the personality file
nano ./knowledge_base/behavior.md

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
│   ├── behavior.md          # AI personality configuration
│   ├── README.md
│   └── your-documents.md
├── local_models/            # Local trained models and training data
│   ├── Modelfile_llama2_latest          # Modelfile for llama2:latest
│   ├── Modelfile_llama3.2_3b            # Modelfile for llama3.2:3b
│   ├── ollama_training_llama2_latest.jsonl
│   ├── ollama_training_llama3.2_3b.jsonl
│   └── ollama_training_data.json
├── backend/                 # Python Flask server
│   ├── server.py           # Main server with personality system
│   ├── ollama_trainer.py   # Model training and management
│   ├── model_manager.py    # Model management and selection
│   └── train_knowledge_base.py  # Knowledge base indexing
├── frontend/               # Next.js React application
│   ├── pages/index.tsx     # Main interface with CLI
│   ├── components/         # React components
│   └── styles/            # CSS modules
├── docker-compose.yml      # Container orchestration
├── update_personality.sh   # Convenience script
└── init_volume.sh         # Setup verification script
```

## 🔧 Configuration

### Environment Variables

```bash
# Backend configuration
OLLAMA_BASE_URL=http://host.docker.internal:11434
PYTHONUNBUFFERED=1

# Local Ollama configuration (running on host)
# Ollama runs on localhost:11434 by default
```

### Docker Resources

The system is configured with optimized resource limits:

- **Backend**: 6GB memory, 3 CPUs  
- **Frontend**: 1GB memory, 0.5 CPUs
- **Ollama**: Running locally on host (not containerized)

## 🎨 Personality Examples

### Professional/Medical
```markdown
# AI Assistant Personality - Professional Mode

You are a professional, medical-focused AI assistant:

## Core Personality
- **Professional and formal**: Use medical terminology appropriately
- **Patient and thorough**: Take time to explain concepts clearly
- **Encouraging**: Support users in their learning journey
- **Humble**: Acknowledge limitations and be honest about what you don't know

## Communication Style
- **Clear and concise**: Provide well-structured responses
- **Use medical terminology**: When appropriate and accurate
- **Include context**: Always reference source documents
```

### Academic/Research
```markdown
# AI Assistant Personality - Academic Mode

You are a scholarly, research-oriented AI assistant:

## Core Personality
- **Scholarly and precise**: Use formal, academic language
- **Analytical**: Approach questions with systematic analysis
- **Thorough**: Provide comprehensive, well-researched responses
- **Objective**: Maintain neutrality and present balanced perspectives

## Communication Style
- **Formal tone**: Use professional, academic language
- **Structured responses**: Organize information with clear headings
- **Citations**: Reference sources and provide context
```

### Creative/Storytelling
```markdown
# AI Assistant Personality - Creative Mode

You are a creative, imaginative AI assistant:

## Core Personality
- **Imaginative and creative**: Use vivid language and metaphors
- **Storytelling approach**: Frame responses as narratives when appropriate
- **Enthusiastic and engaging**: Show excitement and passion for topics
- **Playful and fun**: Use humor while staying helpful

## Communication Style
- **Vivid descriptions**: Use colorful, descriptive language
- **Metaphors and analogies**: Explain concepts through creative comparisons
- **Storytelling elements**: Use narrative structure when helpful
```

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

# Query Endpoints
POST /query-with-model                # Query with selected model
POST /query-with-model-stream         # Stream with selected model

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

# Check local Ollama status
curl -s http://localhost:11434/api/tags

# List available Ollama models
ollama list

# Check trained models
curl -s http://localhost:5557/models | jq '.models[] | select(.is_trained==true)'
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with Docker: `./build_docker.sh && docker-compose up`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.
