#!/bin/bash

# Script to verify knowledge base bind mount setup

echo "🚀 Checking knowledge base bind mount setup..."

# Check if the knowledge base directory exists
if [ ! -d "./knowledge_base" ]; then
    echo "❌ Error: ./knowledge_base directory not found!"
    echo "Please create the knowledge_base directory and add your .md files."
    exit 1
fi

echo "✅ Knowledge base directory found: ./knowledge_base"
echo "📁 Contents:"
ls -la ./knowledge_base/

echo ""
echo "🎉 Bind mount setup complete!"
echo ""
echo "📝 You can now edit files directly in the ./knowledge_base folder."
echo "🔄 Changes will be immediately available in the container."
echo "🔄 Use the /personality/reload endpoint to reload personality changes."
echo ""
echo "To edit your personality:"
echo "  nano ./knowledge_base/behavior.md"
echo ""
echo "To reload personality changes:"
echo "  curl -X POST http://localhost:5557/personality/reload"
echo "  or run: ./update_personality.sh" 