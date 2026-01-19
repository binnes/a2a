#!/bin/bash

# Master Build and Deployment Script for RAG Agents
# Builds containers and deploys Milvus (optional), MCP Server, and A2A Agent to IBM Code Engine

set -e

echo '==========================================================='
echo 'RAG Agents - Build and Deploy to IBM Code Engine'
echo '==========================================================='
echo ''

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found"
    echo "Please copy .env.example to .env and configure it"
    exit 1
fi

# Load environment to show configuration
source .env

# Determine deployment steps
DEPLOY_STEPS=()
STEP_NUM=1

if [ "$DEPLOY_MILVUS_LOCAL" = "true" ]; then
    DEPLOY_STEPS+=("Deploy Milvus to Code Engine")
fi
DEPLOY_STEPS+=("Build and Deploy MCP Server")
DEPLOY_STEPS+=("Build and Deploy A2A Agent")
DEPLOY_STEPS+=("Deploy Data Loader Job")
DEPLOY_STEPS+=("Load Shakespeare Data")

echo 'This script will:'
for i in "${!DEPLOY_STEPS[@]}"; do
    echo "  $((i+1)). ${DEPLOY_STEPS[$i]}"
done
echo ''

echo "Configuration:"
echo "  Resource Group: $IBM_RESOURCE_GROUP"
echo "  Region: $IBM_REGION"
echo "  Registry: $IBM_ICR"
echo "  Namespace: $IBM_NAMESPACE"
echo "  Code Engine Project: $IBM_ICE_PROJECT"
echo "  Deploy Milvus Locally: $DEPLOY_MILVUS_LOCAL"
if [ "$DEPLOY_MILVUS_LOCAL" != "true" ]; then
    echo "  External Milvus: $MILVUS_HOST:$MILVUS_PORT"
fi
echo ''

read -p "Continue with deployment? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled"
    exit 0
fi

# Deploy Milvus if requested
if [ "$DEPLOY_MILVUS_LOCAL" = "true" ]; then
    echo ''
    echo '==========================================================='
    echo "Step $STEP_NUM/${#DEPLOY_STEPS[@]}: Deploying Milvus"
    echo '==========================================================='
    cd milvus
    chmod +x deploy.sh
    ./deploy.sh
    MILVUS_EXIT_CODE=$?
    cd ..
    
    if [ $MILVUS_EXIT_CODE -ne 0 ]; then
        echo "Error: Milvus deployment failed"
        exit 1
    fi
    
    # Wait for Milvus to be ready
    echo ''
    echo 'Waiting for Milvus to be fully operational...'
    sleep 30
    
    STEP_NUM=$((STEP_NUM + 1))
fi

# Build and Deploy MCP Server
echo ''
echo '==========================================================='
echo "Step $STEP_NUM/${#DEPLOY_STEPS[@]}: Building and Deploying MCP Server"
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

STEP_NUM=$((STEP_NUM + 1))

# Build and Deploy A2A Agent
echo ''
echo '==========================================================='
echo "Step $STEP_NUM/${#DEPLOY_STEPS[@]}: Building and Deploying A2A Agent"
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

STEP_NUM=$((STEP_NUM + 1))

# Deploy Data Loader Job
echo ''
echo '==========================================================='
echo "Step $STEP_NUM/${#DEPLOY_STEPS[@]}: Deploying Data Loader Job"
echo '==========================================================='
cd data-loader
chmod +x deploy.sh
./deploy.sh
LOADER_EXIT_CODE=$?
cd ..

if [ $LOADER_EXIT_CODE -ne 0 ]; then
    echo "Error: Data Loader job deployment failed"
    exit 1
fi

STEP_NUM=$((STEP_NUM + 1))

# Run Data Loader Job
echo ''
echo '==========================================================='
echo "Step $STEP_NUM/${#DEPLOY_STEPS[@]}: Loading Shakespeare Data"
echo '==========================================================='
echo 'Submitting data loader job...'
JOB_RUN_NAME="rag-data-loader-run-$(date +%s)"
ibmcloud ce jobrun submit --job rag-data-loader --name "$JOB_RUN_NAME" --wait

# Check job run status
JOB_STATUS=$(ibmcloud ce jobrun get --name "$JOB_RUN_NAME" -o json | grep -o '"status":"[^"]*' | cut -d'"' -f4)
if [ "$JOB_STATUS" = "Succeeded" ]; then
    echo "✓ Shakespeare data loaded successfully"
else
    echo "⚠ Data loader job completed with status: $JOB_STATUS"
    echo "Check logs with: ibmcloud ce jobrun logs --name $JOB_RUN_NAME"
fi

echo ''
echo '==========================================================='
echo '✓ Build and Deployment Complete!'
echo '==========================================================='
echo ''
echo 'Services deployed to IBM Code Engine:'
echo ''

if [ "$DEPLOY_MILVUS_LOCAL" = "true" ]; then
    echo '  ✓ Milvus'
    echo '    - Container built and pushed to registry'
    echo '    - Deployed to Code Engine'
    echo '    - Vector database for RAG'
    echo ''
fi

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
echo '  ✓ Data Loader'
echo '    - Job created in Code Engine'
echo '    - Shakespeare text loaded into Milvus'
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
if [ "$DEPLOY_MILVUS_LOCAL" = "true" ]; then
    echo '     ibmcloud ce application logs -n rag-milvus'
fi
echo '     ibmcloud ce application logs -n rag-mcp-server'
echo '     ibmcloud ce application logs -n rag-a2a-agent'
echo ''
echo '  4. Test the API:'
echo '     curl -X POST $(ibmcloud ce application get -n rag-mcp-server -o json | grep -o "\"url\":\"[^\"]*" | cut -d"\"" -f4)/tools/rag_stats'
echo ''

# Made with Bob
