#!/bin/bash

# Setup script for A2A RAG Agent
# This script sets up the development environment and starts services

set -e

echo "=== A2A RAG Agent Setup ==="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python 3.10+ is installed
echo "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
REQUIRED_VERSION="3.10"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo -e "${RED}Error: Python 3.10 or higher is required (found $PYTHON_VERSION)${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"

# Check if Podman is installed
echo "Checking Podman..."
if ! command -v podman &> /dev/null; then
    echo -e "${YELLOW}Warning: Podman is not installed${NC}"
    echo "Please install Podman: https://podman.io/getting-started/installation"
    echo "Or use Docker instead by modifying the compose file"
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

# Create virtual environment
echo ""
echo "Creating Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${YELLOW}Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo -e "${GREEN}✓ Dependencies installed${NC}"

# Create .env file if it doesn't exist
echo ""
if [ ! -f "config/.env" ]; then
    echo "Creating .env file from template..."
    cp config/.env.example config/.env
    echo -e "${YELLOW}⚠ Please edit config/.env with your credentials${NC}"
    echo -e "${YELLOW}  Required: WATSONX_API_KEY, WATSONX_PROJECT_ID${NC}"
else
    echo -e "${GREEN}✓ .env file exists${NC}"
fi

# Start Milvus with Podman
echo ""
echo "Starting Milvus vector database..."
cd deployment
podman-compose up -d

echo ""
echo "Waiting for Milvus to be ready..."
sleep 10

# Check if Milvus is running
if podman ps | grep -q milvus-standalone; then
    echo -e "${GREEN}✓ Milvus is running${NC}"
else
    echo -e "${RED}Error: Milvus failed to start${NC}"
    echo "Check logs with: podman-compose logs"
    exit 1
fi

cd ..

# Create data directories
echo ""
echo "Creating data directories..."
mkdir -p data/documents
mkdir -p data/examples

echo -e "${GREEN}✓ Data directories created${NC}"

# Summary
echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Edit config/.env with your Watsonx.ai credentials"
echo "2. Add documents to data/documents/ for indexing"
echo "3. Start the MCP server: python -m mcp_server.server"
echo "4. Run the agent: python -m agent.a2a_agent"
echo ""
echo "Useful commands:"
echo "  - Start Milvus: cd deployment && podman-compose up -d"
echo "  - Stop Milvus: cd deployment && podman-compose down"
echo "  - View logs: cd deployment && podman-compose logs -f"
echo "  - Activate venv: source venv/bin/activate"
echo ""
echo -e "${GREEN}Happy coding!${NC}"

# Made with Bob
