#!/bin/bash

echo "🚀 Setting up Ollama for local use..."

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama is not installed. Please install it first:"
    echo "   macOS: brew install ollama"
    echo "   Linux: curl -fsSL https://ollama.ai/install.sh | sh"
    echo "   Windows: Download from https://ollama.ai/download"
    exit 1
fi

echo "✅ Ollama is installed"

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
    echo "⚠️  Ollama is not running. Starting Ollama..."
    echo "   Please run 'ollama serve' in a separate terminal and keep it running"
    echo "   Then run this script again"
    exit 1
fi

echo "✅ Ollama is running"

# Check if llama2 model is available
if ! ollama list | grep -q "llama2"; then
    echo "📥 Pulling llama2 model (this may take a while)..."
    ollama pull llama2
else
    echo "✅ llama2 model is already available"
fi

# Create local_models directory if it doesn't exist
mkdir -p local_models

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Keep 'ollama serve' running in a terminal"
echo "2. Run './build_docker.sh' to start the application"
echo "3. Access the app at http://localhost:5556"
