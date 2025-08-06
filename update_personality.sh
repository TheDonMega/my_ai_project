#!/bin/bash

# Script to reload personality and knowledge base in the container (bind mount version)

echo "🔄 Reloading personality in backend..."

# Reload the personality in the backend
curl -X POST http://localhost:5557/personality/reload -H "Content-Type: application/json" | jq '.message'

echo ""
echo "🔄 Reloading knowledge base..."

# Reload the knowledge base
curl -X POST http://localhost:5557/knowledge-base/reload -H "Content-Type: application/json" | jq '.message'

echo ""
echo "✅ Personality and knowledge base reloaded!"
echo ""
echo "📝 You can now edit ./knowledge_base/behavior.md and run this script again to reload the personality."
echo "📁 New documents added to ./knowledge_base/ will be automatically detected."
echo "🔄 Or use: curl -X POST http://localhost:5557/personality/reload"
echo "🔄 Or use: curl -X POST http://localhost:5557/knowledge-base/reload"
echo ""
echo "💡 Since we're using a bind mount, your local files are directly accessible in the container!" 