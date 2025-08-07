#!/bin/bash

echo "🐳 Building Docker containers for AI Knowledge Base..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if Ollama is running locally
if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
    echo "❌ Ollama is not running locally. Please start Ollama first:"
    echo "   ollama serve"
    echo "   Then run this script again."
    exit 1
fi

echo "✅ Ollama is running locally"

# Build the backend container
echo "🔨 Building backend container..."
docker-compose build backend

if [ $? -eq 0 ]; then
    echo "✅ Backend container built successfully"
else
    echo "❌ Backend container build failed"
    echo "💡 Try running: docker-compose build --no-cache backend"
    exit 1
fi

# Build the frontend container
echo "🔨 Building frontend container..."
docker-compose build frontend

if [ $? -eq 0 ]; then
    echo "✅ Frontend container built successfully"
else
    echo "❌ Frontend container build failed"
    echo "💡 Try running: docker-compose build --no-cache frontend"
    exit 1
fi

echo "🎉 All containers built successfully!"
echo ""
echo "🚀 Starting services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to start..."
sleep 10

echo ""
echo "🎉 Setup completed!"
echo ""
echo "📊 To view logs:"
echo "   docker-compose logs -f"
echo ""
echo "🔧 To stop services:"
echo "   docker-compose down"
echo ""
echo "💡 To check Ollama models:"
echo "   ollama list"
echo ""
echo "💡 To check if Ollama is running:"
echo "   curl -s http://localhost:11434/api/tags" 