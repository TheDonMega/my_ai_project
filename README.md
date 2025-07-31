# AI Knowledge Base Analyzer

An intelligent knowledge base analyzer that uses AI to search through markdown files and provide comprehensive answers with web search capabilities.

## Features

- **Local Knowledge Base Search**: Searches through markdown files recursively, including subfolders
- **AI-Powered Analysis**: Uses CrewAI for multi-agent analysis of local content
- **Web Search Integration**: Gemini AI with built-in web search capabilities
- **Folder Structure Support**: Displays folder paths for better organization
- **Modal Document Viewer**: View full documents with proper overlay
- **Multi-Step AI Flow**: Guided process for AI analysis with file selection

## Docker Setup

This application is containerized for easy deployment and consistent environments. The setup includes Ollama for local AI processing.

### Quick Start

1. **Build and start all services:**
   ```bash
   chmod +x build_docker.sh
   ./build_docker.sh
   ```

2. **Access the application:**
   - Frontend: http://localhost:5556
   - Backend: http://localhost:5557
   - Ollama: http://localhost:11434

### Manual Setup

If you prefer to build manually:

```bash
# Build all containers
docker-compose build

# Start services
docker-compose up -d

# Wait for Ollama to start, then pull models
python setup_docker_ollama.py
```

### Docker Architecture

The setup includes three services:

- **Ollama**: Local AI model server (llama2, mistral, etc.)
- **Backend**: Python Flask server with CrewAI integration
- **Frontend**: Next.js React application

### Ollama Models

The system uses Ollama for local AI processing:

- **llama2** (default): Good general-purpose model
- **mistral**: Faster, smaller alternative
- **codellama**: Specialized for code analysis

To change models, edit `crewai_analyzer.py` and update the `model_name` variable.

### Docker Features

- **Python 3.11**: Compatible with latest CrewAI versions
- **Ollama Integration**: Local AI models for privacy and speed
- **Flexible Dependencies**: Automatic fallback installation if bulk install fails
- **Graceful Degradation**: Falls back to simple search if CrewAI unavailable
- **Volume Mounting**: Knowledge base mounted as volume for easy updates
- **Persistent Models**: Ollama models stored in Docker volume

## Local Development Setup

### Prerequisites

- Python 3.11+
- Node.js 16+
- Ollama (optional, for local AI models)

### Backend Setup

1. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your GEMINI_API_KEY
   ```

4. **Start the backend:**
   ```bash
   python server.py
   ```

### Frontend Setup

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Start the frontend:**
   ```bash
   npm run dev
   ```

## Knowledge Base Structure

Place your markdown files in the `knowledge_base` folder:

```
knowledge_base/
├── general/
│   ├── overview.md
│   └── guidelines.md
├── technical/
│   ├── api-docs.md
│   └── setup.md
└── root-file.md
```

The system will:
- Recursively search all subfolders
- Display folder paths in search results
- Support nested organization

## AI Integration

### CrewAI Multi-Agent System

The application uses CrewAI for sophisticated local knowledge base analysis:

- **Research Agent**: Finds relevant information
- **Content Analyst**: Synthesizes and structures answers
- **Quality Assurance**: Validates accuracy and completeness

### 🔒 API Key Security

**Important**: Your Gemini API key is **NEVER** used during CrewAI operations:

- **CrewAI**: Uses only local Ollama models (no API calls)
- **Web Search**: Gemini API key is only used for web search functionality
- **Complete Separation**: CrewAI and web search are completely independent

This ensures your API key is only used when you explicitly choose web search, not during local knowledge base analysis.

### Fallback Options

If CrewAI is unavailable, the system gracefully falls back to:
1. Simple keyword search
2. Basic document matching
3. Manual file selection for AI analysis

### Web Search Integration

When local knowledge is insufficient, Gemini can:
- Search the web for additional information
- Provide citations and sources
- Combine local and web knowledge

## API Endpoints

- `POST /ask` - Main query endpoint
- `GET /document/<filename>` - Get full document content
- `GET /status` - Service status

## Troubleshooting

### Docker Issues

1. **Build failures**: Try `docker-compose build --no-cache`
2. **Permission issues**: Ensure Docker has access to the project directory
3. **Port conflicts**: Change ports in `docker-compose.yml`

### Dependency Issues

1. **Python version conflicts**: The Docker setup uses Python 3.11 for compatibility
2. **CrewAI installation**: The system includes fallback options if CrewAI fails
3. **Ollama setup**: Optional - Gemini is used as fallback

### Common Solutions

- **Clear Docker cache**: `docker system prune -a`
- **Rebuild containers**: `docker-compose down && docker-compose build --no-cache`
- **Check logs**: `docker-compose logs -f backend`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with Docker: `./build_docker.sh && docker-compose up`
5. Submit a pull request

## License

This project is licensed under the MIT License.
