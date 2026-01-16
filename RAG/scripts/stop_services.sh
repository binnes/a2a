#!/bin/bash
# Stop all RAG services

cd "$(dirname "$0")/.."

echo "=========================================="
echo "Stopping RAG Services"
echo "=========================================="
echo ""

# Stop MCP Server
echo "1. Stopping MCP Server..."
pkill -f "uvicorn mcp_server.server:app" 2>/dev/null && echo "✓ MCP Server stopped" || echo "ℹ MCP Server not running"
echo ""

# Stop Milvus (if using podman-compose)
echo "2. Stopping Milvus..."
if command -v podman-compose &> /dev/null; then
    cd deployment
    podman-compose down
    cd ..
    echo "✓ Milvus stopped"
else
    echo "ℹ podman-compose not found, skipping Milvus shutdown"
fi
echo ""

echo "=========================================="
echo "✓ All services stopped"
echo "=========================================="

# Made with Bob
