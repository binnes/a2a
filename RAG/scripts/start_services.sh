#!/bin/bash
# Start all required services for RAG system

set -e
cd "$(dirname "$0")/.."

echo "=========================================="
echo "Starting RAG Services"
echo "=========================================="
echo ""

# Start Milvus (if using podman-compose)
echo "1. Starting Milvus..."
if command -v podman-compose &> /dev/null; then
    cd deployment
    podman-compose up -d
    cd ..
    echo "✓ Milvus started"
else
    echo "⚠ podman-compose not found, assuming Milvus is already running"
fi
echo ""

# Start MCP Server
echo "2. Starting MCP Server..."
source venv/bin/activate
pkill -f "uvicorn mcp_server.server:app" 2>/dev/null || true
sleep 2
nohup python -m uvicorn mcp_server.server:app --host 0.0.0.0 --port 8000 > logs/mcp_server.log 2>&1 &
MCP_PID=$!
sleep 5

# Verify MCP server is running
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✓ MCP Server started (PID: $MCP_PID)"
else
    echo "✗ MCP Server failed to start"
    exit 1
fi
echo ""

echo "=========================================="
echo "✓ All services started successfully"
echo "=========================================="
echo ""
echo "Service URLs:"
echo "  MCP Server: http://localhost:8000"
echo "  Milvus: localhost:19530"
echo ""
echo "Logs:"
echo "  MCP Server: logs/mcp_server.log"
echo ""

# Made with Bob
