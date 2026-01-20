#!/bin/bash

# MCP Server Deployment Script for IBM Code Engine
# This script builds and deploys the MCP Server container

set -e

# Load environment variables
if [ -f ../.env ]; then
    source ../.env
else
    echo "Error: .env file not found in parent directory"
    exit 1
fi

# Validate required environment variables
REQUIRED_VARS=(
    "IBM_RESOURCE_GROUP"
    "IBM_REGION"
    "IBM_ICR"
    "IBM_NAMESPACE"
    "IBM_ICE_PROJECT"
    "IBM_API_KEY"
    "WATSONX_API_KEY"
    "WATSONX_PROJECT_ID"
    "WATSONX_URL"
    "MILVUS_HOST"
    "MILVUS_PORT"
)

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo "Error: Required environment variable $var is not set"
        exit 1
    fi
done

# Generate timestamp for image tagging
TIMESTAMP=$(date +"%Y%m%d%H%M%S")
IMAGE_NAME="rag-mcp-server"
FULL_IMAGE_TAG="$IBM_ICR/$IBM_NAMESPACE/$IMAGE_NAME:$TIMESTAMP"
LATEST_TAG="$IBM_ICR/$IBM_NAMESPACE/$IMAGE_NAME:latest"

echo '-----------------------------------------------------------'
echo 'Setting up IBM Cloud access'
echo '-----------------------------------------------------------'

# Check if logged in to IBM Cloud
if [[ $(ibmcloud target | grep login) ]]; then
    echo 'Please login to ibmcloud cli before running this script'
    exit 1
fi

# Set target resource group and region
ibmcloud target -g "$IBM_RESOURCE_GROUP"
ibmcloud cr region-set "$IBM_REGION"
ibmcloud cr namespace-list
ibmcloud cr login --client podman

echo '-----------------------------------------------------------'
echo 'Building MCP Server container'
echo '-----------------------------------------------------------'

# Navigate to RAG directory
cd ../../../

# Build container image
podman build -f deployment/ibm-code-engine/mcp-server/Containerfile \
    --tag "$FULL_IMAGE_TAG" \
    --tag "$LATEST_TAG" \
    --platform linux/amd64 \
    .

echo '-----------------------------------------------------------'
echo "Pushing container to registry: $FULL_IMAGE_TAG"
echo '-----------------------------------------------------------'

# Push both tags
podman push "$FULL_IMAGE_TAG"
podman push "$LATEST_TAG"

echo '-----------------------------------------------------------'
echo 'Configuring IBM Code Engine'
echo '-----------------------------------------------------------'

# Select Code Engine project
ibmcloud ce project select --name "$IBM_ICE_PROJECT"

# Create registry secret if it doesn't exist
if [[ $(ibmcloud ce secret get -n rag-registry-secret 2>&1 | grep 'Resource not found') ]]; then
    echo 'Creating IBM Code Engine registry secret'
    ibmcloud ce secret create \
        --format registry \
        --name rag-registry-secret \
        --server "private.$IBM_ICR" \
        --username iamapikey \
        --password "$IBM_API_KEY"
else
    echo 'Registry secret already exists'
fi

echo '-----------------------------------------------------------'
echo 'Configuring Milvus Connection'
echo '-----------------------------------------------------------'

# Reload .env to get any updates from Milvus deployment
if [ -f ../.env ]; then
    source ../.env
    echo "✓ Reloaded environment variables from .env"
else
    echo "Warning: .env file not found at ../.env"
    echo "Using environment variables from initial load"
fi

# Determine Milvus host based on deployment mode
if [ "$DEPLOY_MILVUS_LOCAL" = "true" ]; then
    # Get cluster-local URL from Milvus application (address.url field)
    echo "Retrieving Milvus cluster-local URL..."
    CLUSTER_LOCAL_URL=$(ibmcloud ce app get --name rag-milvus --output json 2>/dev/null | grep -A1 '"address"' | grep '"url"' | head -1 | grep -o 'http://[^"]*')
    
    if [ -n "$CLUSTER_LOCAL_URL" ]; then
        # Extract hostname from cluster-local URL (remove http:// and port if present)
        MILVUS_HOST_CONFIG=$(echo "$CLUSTER_LOCAL_URL" | sed 's|http://||' | sed 's|https://||' | cut -d':' -f1)
        echo "✓ Retrieved cluster-local URL: $CLUSTER_LOCAL_URL"
    else
        # Fallback to simple hostname if cluster-local URL not available
        MILVUS_HOST_CONFIG="rag-milvus"
        echo "⚠ Could not retrieve cluster-local URL, using fallback: $MILVUS_HOST_CONFIG"
    fi
    
    MILVUS_PORT_CONFIG="19530"
    echo "Using local Milvus deployment:"
    echo "  Host: $MILVUS_HOST_CONFIG"
    echo "  Port: $MILVUS_PORT_CONFIG"
else
    # Use values from .env for external Milvus
    MILVUS_HOST_CONFIG="$MILVUS_HOST"
    MILVUS_PORT_CONFIG="$MILVUS_PORT"
    echo "Using external Milvus:"
    echo "  Host: $MILVUS_HOST_CONFIG"
    echo "  Port: $MILVUS_PORT_CONFIG"
fi

echo '-----------------------------------------------------------'
echo 'Creating/Updating MCP Server Application'
echo '-----------------------------------------------------------'

# Check if application exists
if [[ $(ibmcloud ce application get -n rag-mcp-server 2>&1 | grep 'Resource not found') ]]; then
    echo 'Creating IBM Code Engine Application: rag-mcp-server'
    ibmcloud ce application create \
        --name rag-mcp-server \
        --port 8000 \
        --min-scale 1 --max-scale 3 \
        --cpu 1 --memory 2G \
        --image "private.$FULL_IMAGE_TAG" \
        --registry-secret rag-registry-secret \
        --env WATSONX_API_KEY="$WATSONX_API_KEY" \
        --env WATSONX_PROJECT_ID="$WATSONX_PROJECT_ID" \
        --env WATSONX_URL="$WATSONX_URL" \
        --env MILVUS_HOST="$MILVUS_HOST_CONFIG" \
        --env MILVUS_PORT="$MILVUS_PORT_CONFIG" \
        --env MILVUS_COLLECTION_NAME="${MILVUS_COLLECTION_NAME:-rag_knowledge_base}" \
        --env MILVUS_METRIC_TYPE="${MILVUS_METRIC_TYPE:-COSINE}" \
        --env MCP_SERVER_HOST="0.0.0.0" \
        --env MCP_SERVER_PORT="8000" \
        --env MCP_SERVER_RELOAD="false" \
        --env EMBEDDING_MODEL="${EMBEDDING_MODEL:-ibm/granite-embedding-278m-multilingual}" \
        --env EMBEDDING_DIMENSION="${EMBEDDING_DIMENSION:-768}" \
        --env LLM_MODEL="${LLM_MODEL:-ibm/granite-13b-chat-v2}" \
        --env LLM_MAX_TOKENS="${LLM_MAX_TOKENS:-2048}" \
        --env LLM_TEMPERATURE="${LLM_TEMPERATURE:-0.7}" \
        --env RAG_CHUNK_SIZE="${RAG_CHUNK_SIZE:-512}" \
        --env RAG_CHUNK_OVERLAP="${RAG_CHUNK_OVERLAP:-50}" \
        --env RAG_TOP_K="${RAG_TOP_K:-5}" \
        --env RAG_SCORE_THRESHOLD="${RAG_SCORE_THRESHOLD:-0.7}" \
        --env LOG_LEVEL="${LOG_LEVEL:-INFO}" \
        --env LOG_FORMAT="${LOG_FORMAT:-json}"
else
    echo 'Updating IBM Code Engine Application: rag-mcp-server'
    ibmcloud ce application update \
        --name rag-mcp-server \
        --image "private.$FULL_IMAGE_TAG" \
        --registry-secret rag-registry-secret
fi

echo '-----------------------------------------------------------'
echo 'Deployment Complete'
echo '-----------------------------------------------------------'

# Get application URL
APP_URL=$(ibmcloud ce application get -n rag-mcp-server -o json | grep -o '"url":"[^"]*' | cut -d'"' -f4)
echo "MCP Server URL: $APP_URL"
echo "Health Check: $APP_URL/health"
echo "API Docs: $APP_URL/docs"

echo '-----------------------------------------------------------'
echo 'Testing deployment'
echo '-----------------------------------------------------------'

# Wait for application to be ready
echo "Waiting for application to be ready..."
sleep 10

# Test health endpoint
if curl -f -s "$APP_URL/health" > /dev/null; then
    echo "✓ Health check passed"
else
    echo "✗ Health check failed"
    exit 1
fi

echo '-----------------------------------------------------------'
echo 'Deployment successful!'
echo '-----------------------------------------------------------'

# Made with Bob
