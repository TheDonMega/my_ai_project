#!/bin/bash

echo "🐳 Building Docker containers for AI Knowledge Base..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

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
echo "🚀 To start the application:"
echo "   docker-compose up"
echo ""
echo "🔧 To run in background:"
echo "   docker-compose up -d"
echo ""
echo "📊 To view logs:"
echo "   docker-compose logs -f"
echo ""
echo "🧹 To clean up:"
echo "   docker-compose down" 