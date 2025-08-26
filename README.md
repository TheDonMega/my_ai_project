# AI Knowledge Base Analyzer

An intelligent knowledge base analyzer that uses AI to search through markdown files and provide comprehensive answers using local Ollama models. Features a dynamic personality system for customizable AI behavior, real-time knowledge base management, and advanced model training capabilities.

## Features

- **🤖 Advanced Model Management**: Select and switch between available Ollama models dynamically
  - View all available models with detailed information (size, type, running status)
  - Start/stop models on demand for memory optimization
  - Auto-detect trained vs. base models with visual indicators
  - Real-time model status monitoring and statistics
  - Compact dropdown interface for easy model selection
  - Model caching for improved performance
- **🎭 Dynamic Behavior System**: Switch between multiple AI personalities instantly
  - Multiple pre-built personality profiles (Friendly, Technical, Storyteller, Creative)
  - Custom personality creation through markdown files
  - Real-time personality switching without model retraining
  - Behavior preview and selection interface
  - Personality-specific response formatting
- **📁 Smart File Inclusion Control**: Choose whether to include knowledge base files in AI responses
  - Toggle knowledge base search on/off
  - General knowledge mode for faster responses
  - Context-aware mode for document-specific queries
- **🚀 Streaming Responses**: Real-time streaming responses with selected models
  - Word-by-word streaming like Ollama CLI
  - Interactive CLI interface in the frontend
  - Real-time response generation with personality applied
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
- **📄 Sources Display**: View found documents with relevant information
  - Shows filename, folder path, relevance score, and content preview
  - "View" button to see full document content in modal
  - Displays sources below CLI when files are included
  - Real-time source capture from streaming responses
- **📄 DOCX to Markdown Conversion**: Convert Word documents to Markdown format
  - Upload multiple DOCX files and convert them to Markdown instantly
  - Drag & drop or click to select multiple files
  - Preserves original filenames with .md extension
  - Single file downloads as .md, multiple files as zip
  - Automatic file download after conversion
  - Uses Microsoft's open-source markitdown library
  - Clean, modern conversion interface
- **Local Knowledge Base Search**: Searches through markdown files recursively, including subfolders
- **Local AI Processing**: Uses Ollama for local AI model inference
- **Real-time Knowledge Base Management**: Add documents without restarting containers
- **Model Training**: Train custom Ollama models on your knowledge base
- **Folder Structure Support**: Displays folder paths for better organization
- **Modal Document Viewer**: View full documents with proper overlay

## 🎭 Behavior System

The AI assistant's personality and behavior can be customized using multiple personality files in the `behavior_model` directory. This allows you to:

- **Switch personalities instantly** without retraining models
- **Test different communication styles** (professional, casual, academic, creative)
- **Customize response formats** and tone
- **Apply domain-specific behaviors** (medical, technical, educational)

### Available Personalities

The system comes with several pre-built personality profiles:

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

#### **Creative Storyteller** (`storyteller.md`)
- **Imaginative and creative**: Loves exploring new ideas and narratives
- **Enthusiastic about stories**: Shows excitement for plot development
- **Narrative-focused**: Uses storytelling techniques when relevant
- **Inspiring**: Helps users see creative potential in situations

### Quick Personality Setup

1. **Select from existing personalities:**
   - Use the Behavior Selector dropdown in the frontend
   - Choose from available personality files
   - Switch personalities instantly without restarting

2. **Create a custom personality:**
   ```bash
   nano ./behavior_model/my_custom_personality.md
   ```

3. **Example custom personality:**
   ```markdown
   # AI Assistant Personality - Medical Expert
   
   You are a professional, medical-focused AI assistant:
   
   ## Core Personality
   - **Professional and formal**: Use medical terminology appropriately
   - **Patient and thorough**: Take time to explain concepts clearly
   - **Encouraging**: Support users in their learning journey
   
   ## Communication Style
   - **Clear and concise**: Provide well-structured responses
   - **Use medical terminology**: When appropriate and accurate
   - **Include context**: Always reference source documents
   ```

4. **Reload personalities:**
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

# Reload personality changes
curl -X POST http://localhost:5557/personality/reload

# Use the convenience script (reloads both personality and knowledge base)
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

#### **Real-World Example:**
When you train on QA documentation:
- **"What is llamaindex?"** → Uses general knowledge + your personality
- **"What is QA?"** → Uses general knowledge + your personality  
- **"What is 2+2?"** → Uses general knowledge + your personality
- **"Explain quantum physics"** → Uses general knowledge + your personality

**Result**: You get the best of both worlds - all original capabilities plus your preferred communication style!

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

# Train with custom file selection and behavior
curl -X POST http://localhost:5557/train-ollama \
  -H "Content-Type: application/json" \
  -d '{
    "action": "train_with_custom_selection",
    "base_model": "llama3.2:3b",
    "selected_files": ["QA/", "Llamaindex/"],
    "custom_name": "tech",
    "behavior_filename": "technical.md"
  }'
```

### Training Workflow

1. **Select Base Model**: Choose from available Ollama models in the dropdown
2. **Choose Files**: Select specific directories or files to train on
3. **Pick Behavior**: Select personality file for the trained model
4. **Custom Name**: Provide a unique suffix for your trained model
5. **Train**: System creates fine-tuned model with your personality
6. **Use**: Switch to your trained model for enhanced responses

## 🤖 Model Management System

The AI Knowledge Base Analyzer includes a comprehensive model management system that allows you to:

### **Features**
- **View Available Models**: See all Ollama models installed on your system with detailed information
- **Model Selection**: Choose which model to use for queries dynamically
- **Start/Stop Models**: Control which models are loaded in memory for performance optimization
- **Model Information**: View model size, type (trained vs. base), and running status
- **File Inclusion Control**: Toggle whether AI responses should include knowledge base files
- **Compact Dropdown Interface**: Easy model selection with detailed information
- **Model Caching**: Performance optimization with intelligent caching
- **Model Statistics**: Detailed usage and performance metrics

### **Model Types**
- **Base Models**: Original Ollama models (llama2, llama3.2:3b, mistral, etc.)
- **Trained Models**: Custom models trained on your knowledge base (marked with `-trained` suffix)
- **Running Models**: Models currently loaded in memory for faster responses

### **Query Modes**
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

# Pull a new model
curl -X POST http://localhost:5557/models/pull \
  -H "Content-Type: application/json" \
  -d '{"model_name": "llama3.2:3b"}'

# Delete a model
curl -X DELETE http://localhost:5557/models/llama3.2:3b-trained/delete

# Cleanup orphaned training files
curl -X POST http://localhost:5557/models/cleanup-orphaned-files
```

### **New Query Endpoints**
```bash
# Stream responses with model selection (recommended)
curl -X POST http://localhost:5557/query-with-model-stream \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is this knowledge base about?",
    "include_files": true,
    "model_name": "llama3.2:3b-trained"
  }'

# Stream responses with sources display
curl -X POST http://localhost:5557/query-with-model-stream \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Explain the main concepts",
    "include_files": true
  }' --no-buffer

# Get full document content
curl -X GET http://localhost:5557/document/filename.md
```

## 💻 Interactive CLI Interface

The frontend now features an interactive CLI-style interface:

### **Features:**
- **Command-Line Style**: Type questions and hit Enter for responses
- **Real-Time Streaming**: Word-by-word streaming like Ollama CLI
- **Command History**: View previous questions and responses
- **Visual Cursor**: Animated cursor for authentic CLI feel
- **Response Streaming**: See responses generate in real-time
- **Sources Display**: View found documents below CLI when files are included

### **Usage:**
1. Type your question in the CLI input field
2. Press Enter to submit
3. Watch the response stream word-by-word
4. View found sources below (if files included)
5. Click "View" to see full document content
6. View command history below

## 📂 Collapsible Interface

The interface now includes collapsible sections for better organization:

### **Collapsible Sections:**
- **Ollama Model Training**: Training controls and information
- **Query Options**: File inclusion toggle and model info
- **Persistent State**: UI state saved in localStorage
- **Clean Interface**: Focus on what matters most

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
9. **Behavior not switching**: Use the Behavior Selector dropdown in the frontend
10. **Model management issues**: Check model status with `/models` endpoint
11. **Sources not displaying**: Check browser console for debugging messages
12. **Trained model not detected**: Verify model naming convention (should end with `-tech`, `-trained`, etc.)
13. **File inclusion not working**: Ensure "Include Files" toggle is enabled in Query Options
14. **DOCX conversion fails**: Ensure markitdown library is installed with docx extras
15. **Downloaded file has wrong name**: Check that the original filename is preserved with .md extension
16. **Multiple files not working**: Ensure files are being sent as 'files' parameter, not 'file'
17. **Zip file not downloading**: Check that zipfile module is available in Python environment

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

# List available behaviors
curl -s http://localhost:5557/behaviors

# Check model statistics
curl -s http://localhost:5557/models/stats

# Test sources display
curl -X POST http://localhost:5557/query-with-model-stream \
  -H "Content-Type: application/json" \
  -d '{"question": "What is QA?", "include_files": true}' --no-buffer | head -5

# Test DOCX conversion endpoint (single file)
curl -X POST http://localhost:5557/convert-docx-to-markdown -F "files=@README.md" -v

# Test DOCX conversion endpoint (multiple files)
curl -X POST http://localhost:5557/convert-docx-to-markdown -F "files=@README.md" -F "files=@package.json" -v
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
│   ├── server.py           # Main server with personality, model management, and DOCX conversion
│   ├── ollama_trainer.py   # Model training and management
│   ├── model_manager.py    # Model management and selection
│   ├── train_knowledge_base.py  # Knowledge base indexing
│   └── requirements.txt    # Python dependencies including markitdown[docx]
├── frontend/               # Next.js React application
│   ├── pages/index.tsx     # Main interface with CLI and behavior selector
│   ├── pages/convert-docx.tsx  # DOCX to Markdown conversion page
│   ├── components/         # React components
│   │   ├── BehaviorSelector.tsx  # Personality selection component
│   │   ├── ModelSelector.tsx     # Model selection component
│   │   └── ...              # Other UI components
│   ├── styles/            # CSS modules
│   │   ├── ConvertDocx.module.css  # DOCX conversion page styles
│   │   └── ...             # Other CSS modules
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

## 📄 DOCX to Markdown Conversion

The AI Knowledge Base Analyzer now includes a powerful DOCX to Markdown conversion feature that allows you to easily convert Word documents to Markdown format for use in your knowledge base.

### Features

- **📤 Multiple File Upload**: Drag & drop or click to select multiple DOCX files
- **🔒 File Validation**: Only accepts .docx files for security
- **📝 Preserved Filenames**: Keeps original filenames with .md extension
- **📦 Smart Download**: Single file downloads as .md, multiple files as zip
- **⚡ Instant Conversion**: Fast conversion using Microsoft's markitdown library
- **💾 Automatic Download**: Converted files are automatically downloaded
- **🎨 Modern Interface**: Clean, responsive design that matches the app theme

### How to Use

1. **Access the Converter**:
   - Click the "📄 Convert Notes to Markdown" button in the top-right corner of the main page
   - Or navigate directly to `/convert-docx`

2. **Upload Your Files**:
   - Click the upload area or drag and drop your DOCX files
   - Select multiple files by holding Ctrl/Cmd while clicking
   - Only .docx files are accepted
   - File sizes and names are displayed for confirmation

3. **Convert and Download**:
   - Click "Convert to Markdown" button
   - Files are processed using the markitdown library
   - Single file: downloads as .md file
   - Multiple files: downloads as zip file with all converted files
   - Original filenames are preserved with .md extension

### Examples

- **Single File**: 
  - Input: `My Document.docx`
  - Output: `My Document.md` (automatically downloaded)

- **Multiple Files**:
  - Input: `Report.docx`, `Notes.docx`, `Summary.docx`
  - Output: `Report_and_2_more_files.zip` (contains all converted .md files)

### Technical Details

- **Library**: Uses Microsoft's open-source [markitdown](https://github.com/microsoft/markitdown) library
- **Dependencies**: Includes python-docx and mammoth for DOCX processing
- **Format Support**: Converts DOCX formatting to clean Markdown
- **Error Handling**: Comprehensive error messages for invalid files or conversion failures

### API Endpoint

```bash
# Convert DOCX to Markdown (single or multiple files)
POST /convert-docx-to-markdown
Content-Type: multipart/form-data

# Single file response: Markdown file download
Content-Disposition: attachment; filename="original_name.md"

# Multiple files response: Zip file download
Content-Disposition: attachment; filename="firstfile_and_X_more_files.zip"
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
POST /models/pull                     # Pull a new model
DELETE /models/{model_name}/delete    # Delete a model

# Behavior Management
GET /behaviors                        # List available behaviors
POST /behaviors/select                # Select a behavior

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

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with Docker: `./build_docker.sh && docker-compose up`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.
