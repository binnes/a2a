#!/bin/bash

# Master Build and Deployment Script for RAG Agents
# Builds containers and deploys both MCP Server and A2A Agent to IBM Code Engine

set -e

echo '==========================================================='
echo 'RAG Agents - Build and Deploy to IBM Code Engine'
echo '==========================================================='
echo ''
echo 'This script will:'
echo '  1. Build MCP Server container'
echo '  2. Push to IBM Container Registry'
echo '  3. Deploy MCP Server to Code Engine'
echo '  4. Build A2A Agent container'
echo '  5. Push to IBM Container Registry'
echo '  6. Deploy A2A Agent to Code Engine'
echo ''

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found"
    echo "Please copy .env.example to .env and configure it"
    exit 1
fi

# Load environment to show configuration
source .env
echo "Configuration:"
echo "  Resource Group: $TZ_RESOURCE_GROUP"
echo "  Registry: $TZ_ICR"
echo "  Namespace: $TZ_NAMESPACE"
echo "  Code Engine Project: $TZ_ICE_PROJECT"
echo ''

read -p "Continue with deployment? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled"
    exit 0
fi

# Build and Deploy MCP Server
echo ''
echo '==========================================================='
echo 'Step 1/2: Building and Deploying MCP Server'
echo '==========================================================='
cd mcp-server
chmod +x deploy.sh
./deploy.sh
MCP_EXIT_CODE=$?
cd ..

if [ $MCP_EXIT_CODE -ne 0 ]; then
    echo "Error: MCP Server deployment failed"
    exit 1
fi

# Wait for MCP Server to be ready
echo ''
echo 'Waiting for MCP Server to be fully operational...'
sleep 30

# Build and Deploy A2A Agent
echo ''
echo '==========================================================='
echo 'Step 2/2: Building and Deploying A2A Agent'
echo '==========================================================='
cd a2a-agent
chmod +x deploy.sh
./deploy.sh
A2A_EXIT_CODE=$?
cd ..

if [ $A2A_EXIT_CODE -ne 0 ]; then
    echo "Error: A2A Agent deployment failed"
    exit 1
fi

echo ''
echo '==========================================================='
echo '✓ Build and Deployment Complete!'
echo '==========================================================='
echo ''
echo 'Both services have been built and deployed to IBM Code Engine:'
echo ''
echo '  ✓ MCP Server'
echo '    - Container built and pushed to registry'
echo '    - Deployed to Code Engine'
echo '    - Provides RAG tools via REST API'
echo ''
echo '  ✓ A2A Agent'
echo '    - Container built and pushed to registry'
echo '    - Deployed to Code Engine'
echo '    - Orchestrates RAG workflows'
echo ''
echo 'Next steps:'
echo '  1. Verify deployments:'
echo '     ibmcloud ce application list'
echo ''
echo '  2. Check MCP Server health:'
echo '     ibmcloud ce application get -n rag-mcp-server'
echo '     curl $(ibmcloud ce application get -n rag-mcp-server -o json | grep -o "\"url\":\"[^\"]*" | cut -d"\"" -f4)/health'
echo ''
echo '  3. View logs:'
echo '     ibmcloud ce application logs -n rag-mcp-server'
echo '     ibmcloud ce application logs -n rag-a2a-agent'
echo ''
echo '  4. Test the API:'
echo '     curl -X POST $(ibmcloud ce application get -n rag-mcp-server -o json | grep -o "\"url\":\"[^\"]*" | cut -d"\"" -f4)/tools/rag_stats'
echo ''

# Made with Bob
