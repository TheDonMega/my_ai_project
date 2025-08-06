#!/bin/bash

# Script to reload personality in the container (bind mount version)

echo "🔄 Reloading personality in backend..."

# Reload the personality in the backend
curl -X POST http://localhost:5557/personality/reload -H "Content-Type: application/json" | jq '.message'

echo ""
echo "✅ Personality reloaded!"
echo ""
echo "📝 You can now edit ./knowledge_base/behavior.md and run this script again to reload the personality."
echo "🔄 Or use: curl -X POST http://localhost:5557/personality/reload"
echo ""
echo "💡 Since we're using a bind mount, your local files are directly accessible in the container!" 