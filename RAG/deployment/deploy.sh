#!/bin/bash

# Unified Deployment Script for RAG Agents
# Supports both local (Podman) and IBM Code Engine deployments

set -e

echo '==========================================================='
echo 'RAG Agents - Unified Deployment Script'
echo '==========================================================='
echo ''

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Display usage
usage() {
    echo "Usage: $0 [local|ibm-code-engine]"
    echo ""
    echo "Deployment options:"
    echo "  local              Deploy locally using Podman"
    echo "  ibm-code-engine    Deploy to IBM Code Engine"
    echo ""
    echo "Examples:"
    echo "  $0 local"
    echo "  $0 ibm-code-engine"
    exit 1
}

# Check arguments
if [ $# -eq 0 ]; then
    echo -e "${RED}Error: No deployment target specified${NC}"
    echo ""
    usage
fi

DEPLOYMENT_TARGET=$1

case $DEPLOYMENT_TARGET in
    local)
        echo -e "${BLUE}Selected: Local Deployment with Podman${NC}"
        echo ""
        echo "This will deploy:"
        echo "  • Milvus vector database (with etcd and MinIO)"
        echo "  • MCP Server"
        echo "  • A2A Agent"
        echo "  • Automatic Shakespeare data loading"
        echo ""
        echo "All services will run in containers on your local machine."
        echo ""
        
        # Check if local deployment directory exists
        if [ ! -d "local" ]; then
            echo -e "${RED}Error: local deployment directory not found${NC}"
            exit 1
        fi
        
        # Run local deployment
        cd local
        if [ ! -f "deploy.sh" ]; then
            echo -e "${RED}Error: local/deploy.sh not found${NC}"
            exit 1
        fi
        
        chmod +x deploy.sh
        ./deploy.sh
        ;;
        
    ibm-code-engine)
        echo -e "${BLUE}Selected: IBM Code Engine Deployment${NC}"
        echo ""
        echo "This will deploy:"
        echo "  • Milvus (optional, based on .env configuration)"
        echo "  • MCP Server"
        echo "  • A2A Agent"
        echo "  • Data Loader Job (for Shakespeare text)"
        echo ""
        echo "All services will be deployed to IBM Code Engine."
        echo ""
        
        # Check if IBM Code Engine deployment directory exists
        if [ ! -d "ibm-code-engine" ]; then
            echo -e "${RED}Error: ibm-code-engine deployment directory not found${NC}"
            exit 1
        fi
        
        # Run IBM Code Engine deployment
        cd ibm-code-engine
        if [ ! -f "deploy-all.sh" ]; then
            echo -e "${RED}Error: ibm-code-engine/deploy-all.sh not found${NC}"
            exit 1
        fi
        
        chmod +x deploy-all.sh
        ./deploy-all.sh
        ;;
        
    *)
        echo -e "${RED}Error: Invalid deployment target '${DEPLOYMENT_TARGET}'${NC}"
        echo ""
        usage
        ;;
esac

# Made with Bob