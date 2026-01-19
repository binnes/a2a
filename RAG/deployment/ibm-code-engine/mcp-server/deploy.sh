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
    "TZ_RESOURCE_GROUP"
    "TZ_ICR"
    "TZ_NAMESPACE"
    "TZ_ICE_PROJECT"
    "TZ_API_KEY"
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
FULL_IMAGE_TAG="$TZ_ICR/$TZ_NAMESPACE/$IMAGE_NAME:$TIMESTAMP"
LATEST_TAG="$TZ_ICR/$TZ_NAMESPACE/$IMAGE_NAME:latest"

echo '-----------------------------------------------------------'
echo 'Setting up IBM Cloud access'
echo '-----------------------------------------------------------'

# Check if logged in to IBM Cloud
if [[ $(ibmcloud target | grep login) ]]; then
    echo 'Please login to ibmcloud cli before running this script'
    exit 1
fi

# Set target resource group and region
ibmcloud target -g "$TZ_RESOURCE_GROUP"
ibmcloud cr region-set eu-central
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
ibmcloud ce project select --name "$TZ_ICE_PROJECT"

# Create registry secret if it doesn't exist
if [[ $(ibmcloud ce secret get -n rag-registry-secret 2>&1 | grep 'Resource not found') ]]; then
    echo 'Creating IBM Code Engine registry secret'
    ibmcloud ce secret create \
        --format registry \
        --name rag-registry-secret \
        --server "private.$TZ_ICR" \
        --username iamapikey \
        --password "$TZ_API_KEY"
else
    echo 'Registry secret already exists'
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
        --env MILVUS_HOST="$MILVUS_HOST" \
        --env MILVUS_PORT="$MILVUS_PORT" \
        --env MILVUS_COLLECTION_NAME="${MILVUS_COLLECTION_NAME:-rag_knowledge_base}" \
        --env MILVUS_METRIC_TYPE="${MILVUS_METRIC_TYPE:-COSINE}" \
        --env MCP_SERVER_HOST="0.0.0.0" \
        --env MCP_SERVER_PORT="8000" \
        --env MCP_SERVER_RELOAD="false" \
        --env EMBEDDING_MODEL="${EMBEDDING_MODEL:-ibm/slate-125m-english-rtrvr}" \
        --env EMBEDDING_DIMENSION="${EMBEDDING_DIMENSION:-384}" \
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
