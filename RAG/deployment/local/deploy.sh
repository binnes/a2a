#!/bin/bash

# Local Deployment Script for RAG Agents
# Deploys Milvus, MCP Server, A2A Agent, and loads Shakespeare data using Podman

set -e

echo '==========================================================='
echo 'RAG Agents - Local Deployment with Podman'
echo '==========================================================='
echo ''

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Warning: .env file not found${NC}"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo -e "${YELLOW}⚠ Please edit .env with your Watsonx.ai credentials${NC}"
    echo -e "${YELLOW}  Required: WATSONX_API_KEY, WATSONX_PROJECT_ID${NC}"
    echo ""
    read -p "Press Enter after updating .env file to continue..."
fi

# Load environment
source .env

# Check required variables
if [ -z "$WATSONX_API_KEY" ] || [ "$WATSONX_API_KEY" = "your-api-key-here" ]; then
    echo -e "${RED}Error: WATSONX_API_KEY not set in .env${NC}"
    exit 1
fi

if [ -z "$WATSONX_PROJECT_ID" ] || [ "$WATSONX_PROJECT_ID" = "your-project-id-here" ]; then
    echo -e "${RED}Error: WATSONX_PROJECT_ID not set in .env${NC}"
    exit 1
fi

# Check if Podman is installed
echo "Checking Podman..."
if ! command -v podman &> /dev/null; then
    echo -e "${RED}Error: Podman is not installed${NC}"
    echo "Please install Podman: https://podman.io/getting-started/installation"
    exit 1
fi
echo -e "${GREEN}✓ Podman found${NC}"

# Check if podman-compose is installed
echo "Checking podman-compose..."
if ! command -v podman-compose &> /dev/null; then
    echo -e "${YELLOW}Warning: podman-compose is not installed${NC}"
    echo "Installing podman-compose..."
    pip3 install podman-compose
fi
echo -e "${GREEN}✓ podman-compose found${NC}"

echo ''
echo 'This script will:'
echo '  1. Start Milvus vector database'
echo '  2. Build and start MCP Server'
echo '  3. Build and start A2A Agent'
echo '  4. Load Shakespeare text into Milvus'
echo ''

read -p "Continue with deployment? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled"
    exit 0
fi

echo ''
echo '==========================================================='
echo 'Step 1/4: Starting Milvus'
echo '==========================================================='

# Check if Milvus services are already running
MILVUS_RUNNING=$(podman ps --filter "name=milvus-standalone" --format "{{.Names}}" 2>/dev/null || echo "")
ETCD_RUNNING=$(podman ps --filter "name=milvus-etcd" --format "{{.Names}}" 2>/dev/null || echo "")
MINIO_RUNNING=$(podman ps --filter "name=milvus-minio" --format "{{.Names}}" 2>/dev/null || echo "")

if [ -n "$MILVUS_RUNNING" ] && [ -n "$ETCD_RUNNING" ] && [ -n "$MINIO_RUNNING" ]; then
    echo -e "${YELLOW}⚠ Milvus services are already running${NC}"
    echo "  - milvus-standalone: running"
    echo "  - milvus-etcd: running"
    echo "  - milvus-minio: running"
    echo ""
    read -p "Do you want to restart Milvus services? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Restarting Milvus services..."
        podman-compose restart etcd minio milvus
        echo ''
        echo 'Waiting for Milvus to be ready...'
        sleep 30
    else
        echo "Using existing Milvus services..."
    fi
else
    if [ -n "$MILVUS_RUNNING" ] || [ -n "$ETCD_RUNNING" ] || [ -n "$MINIO_RUNNING" ]; then
        echo -e "${YELLOW}⚠ Some Milvus services are running but not all${NC}"
        [ -n "$MILVUS_RUNNING" ] && echo "  - milvus-standalone: running"
        [ -n "$ETCD_RUNNING" ] && echo "  - milvus-etcd: running"
        [ -n "$MINIO_RUNNING" ] && echo "  - milvus-minio: running"
        echo ""
        echo "Stopping partial services and starting fresh..."
        podman-compose down etcd minio milvus 2>/dev/null || true
        sleep 5
    fi
    
    echo 'Starting Milvus and dependencies (etcd, minio)...'
    podman-compose up -d etcd minio milvus
    
    echo ''
    echo 'Waiting for Milvus to be ready...'
    sleep 30
fi

# Check if Milvus is running
if podman ps | grep -q milvus-standalone; then
    echo -e "${GREEN}✓ Milvus is running${NC}"
else
    echo -e "${RED}Error: Milvus failed to start${NC}"
    echo "Check logs with: podman-compose logs milvus"
    exit 1
fi

echo ''
echo '==========================================================='
echo 'Step 2/4: Building and Starting MCP Server'
echo '==========================================================='

# Check if MCP Server is already running
MCP_RUNNING=$(podman ps --filter "name=rag-mcp-server" --format "{{.Names}}" 2>/dev/null || echo "")

if [ -n "$MCP_RUNNING" ]; then
    echo -e "${YELLOW}⚠ MCP Server is already running${NC}"
    echo ""
    read -p "Do you want to rebuild and restart MCP Server? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Stopping MCP Server..."
        podman stop rag-mcp-server 2>/dev/null || true
        podman rm rag-mcp-server 2>/dev/null || true
        echo "Rebuilding and starting MCP Server..."
        podman-compose up -d --build --no-deps mcp-server
        echo ''
        echo 'Waiting for MCP Server to be ready...'
        sleep 20
    else
        echo "Using existing MCP Server..."
    fi
else
    echo "Building and starting MCP Server..."
    podman-compose up -d --build --no-deps mcp-server
    
    echo ''
    echo 'Waiting for MCP Server to be ready...'
    sleep 20
fi

# Check if MCP Server is running
if podman ps | grep -q rag-mcp-server; then
    echo -e "${GREEN}✓ MCP Server is running${NC}"
else
    echo -e "${RED}Error: MCP Server failed to start${NC}"
    echo "Check logs with: podman-compose logs mcp-server"
    exit 1
fi

echo ''
echo '==========================================================='
echo 'Step 3/4: Building and Starting A2A Agent'
echo '==========================================================='

# Check if A2A Agent is already running
A2A_RUNNING=$(podman ps --filter "name=rag-a2a-agent" --format "{{.Names}}" 2>/dev/null || echo "")

if [ -n "$A2A_RUNNING" ]; then
    echo -e "${YELLOW}⚠ A2A Agent is already running${NC}"
    echo ""
    read -p "Do you want to rebuild and restart A2A Agent? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Stopping A2A Agent..."
        podman stop rag-a2a-agent 2>/dev/null || true
        podman rm rag-a2a-agent 2>/dev/null || true
        echo "Rebuilding and starting A2A Agent..."
        podman-compose up -d --build --no-deps a2a-agent
        echo ''
        echo 'Waiting for A2A Agent to be ready...'
        sleep 20
    else
        echo "Using existing A2A Agent..."
    fi
else
    echo "Building and starting A2A Agent..."
    podman-compose up -d --build --no-deps a2a-agent
    
    echo ''
    echo 'Waiting for A2A Agent to be ready...'
    sleep 20
fi

# Check if A2A Agent is running
if podman ps | grep -q rag-a2a-agent; then
    echo -e "${GREEN}✓ A2A Agent is running${NC}"
else
    echo -e "${RED}Error: A2A Agent failed to start${NC}"
    echo "Check logs with: podman-compose logs a2a-agent"
    exit 1
fi

echo ''
echo '==========================================================='
echo 'Step 4/4: Loading Shakespeare Data'
echo '==========================================================='
echo 'Building and running data loader...'
# Stop and remove any existing data loader container
podman stop rag-data-loader 2>/dev/null || true
podman rm rag-data-loader 2>/dev/null || true
# Run data loader without recreating dependencies
podman-compose up --build --no-deps data-loader

# Check data loader exit code
DATA_LOADER_EXIT=$(podman inspect rag-data-loader --format='{{.State.ExitCode}}' 2>/dev/null || echo "1")
if [ "$DATA_LOADER_EXIT" = "0" ]; then
    echo -e "${GREEN}✓ Shakespeare data loaded successfully${NC}"
else
    echo -e "${YELLOW}⚠ Data loader completed with warnings (exit code: $DATA_LOADER_EXIT)${NC}"
    echo "Check logs with: podman-compose logs data-loader"
fi

echo ''
echo '==========================================================='
echo '✓ Local Deployment Complete!'
echo '==========================================================='
echo ''
echo 'Services running:'
echo ''
echo '  ✓ Milvus Vector Database'
echo '    - Port: 19530'
echo '    - MinIO Console: http://localhost:9001'
echo ''
echo '  ✓ MCP Server'
echo '    - Port: 8000'
echo '    - Health: http://localhost:8000/health'
echo ''
echo '  ✓ A2A Agent'
echo '    - Port: 8001'
echo '    - Health: http://localhost:8001/health'
echo ''
echo 'Useful commands:'
echo '  - View all logs: podman-compose logs -f'
echo '  - View specific service: podman-compose logs -f mcp-server'
echo '  - Stop all services: podman-compose down'
echo '  - Restart services: podman-compose restart'
echo '  - Check status: podman-compose ps'
echo ''
echo 'Test the deployment:'
echo '  curl http://localhost:8000/health'
echo '  curl http://localhost:8001/health'
echo ''

# Made with Bob