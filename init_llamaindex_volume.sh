#!/bin/bash

# Initialize LlamaIndex Vector Store Volume
# This script sets up the necessary directories and permissions for LlamaIndex

echo "🚀 Initializing LlamaIndex Vector Store Volume..."

# Create vector store directory
VECTOR_STORE_DIR="./vector_store"
if [ ! -d "$VECTOR_STORE_DIR" ]; then
    echo "📁 Creating vector store directory: $VECTOR_STORE_DIR"
    mkdir -p "$VECTOR_STORE_DIR"
    mkdir -p "$VECTOR_STORE_DIR/chroma_db"
    mkdir -p "$VECTOR_STORE_DIR/faiss_index"
    mkdir -p "$VECTOR_STORE_DIR/index"
else
    echo "✅ Vector store directory already exists: $VECTOR_STORE_DIR"
fi

# Set permissions
echo "🔐 Setting permissions..."
chmod -R 755 "$VECTOR_STORE_DIR"

# Create .gitkeep files to preserve empty directories
touch "$VECTOR_STORE_DIR/.gitkeep"
touch "$VECTOR_STORE_DIR/chroma_db/.gitkeep"
touch "$VECTOR_STORE_DIR/faiss_index/.gitkeep"
touch "$VECTOR_STORE_DIR/index/.gitkeep"

echo "✅ LlamaIndex vector store volume initialized successfully!"
echo "📊 Directory structure:"
tree "$VECTOR_STORE_DIR" -a

echo ""
echo "🔧 Next steps:"
echo "1. Add your markdown files to the knowledge_base directory"
echo "2. Start the Docker containers: docker-compose up -d"
echo "3. The LlamaIndex will automatically build on first startup"
echo "4. Monitor the logs: docker-compose logs -f backend"
