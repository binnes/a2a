#!/bin/bash

# Milvus Deployment Script for IBM Code Engine
# This script builds and deploys Milvus container

set -e

# Load environment variables
if [ -f ../.env ]; then
    source ../.env
else
    echo "Error: .env file not found in parent directory"
    exit 1
fi

# Check if Milvus should be deployed locally
if [ "$DEPLOY_MILVUS_LOCAL" != "true" ]; then
    echo "DEPLOY_MILVUS_LOCAL is not set to 'true'"
    echo "Skipping Milvus deployment - using external Milvus at $MILVUS_HOST:$MILVUS_PORT"
    exit 0
fi

# Validate required environment variables
REQUIRED_VARS=(
    "IBM_RESOURCE_GROUP"
    "IBM_REGION"
    "IBM_ICR"
    "IBM_NAMESPACE"
    "IBM_ICE_PROJECT"
    "IBM_API_KEY"
)

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo "Error: Required environment variable $var is not set"
        exit 1
    fi
done

# Generate timestamp for image tagging
TIMESTAMP=$(date +"%Y%m%d%H%M%S")
IMAGE_NAME="rag-milvus"
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

# Select Code Engine project to check for existing deployment
ibmcloud ce project select --name "$IBM_ICE_PROJECT"

# Check if Milvus application already exists and is running
if [[ ! $(ibmcloud ce application get -n rag-milvus 2>&1 | grep 'Resource not found') ]]; then
    echo '-----------------------------------------------------------'
    echo 'Milvus application already exists'
    echo '-----------------------------------------------------------'
    
    # Get application status
    APP_STATUS=$(ibmcloud ce application get -n rag-milvus -o json | grep -o '"status":"[^"]*' | cut -d'"' -f4)
    
    echo "Current status: $APP_STATUS"
    echo "Skipping rebuild and redeployment"
    echo "To force redeployment, delete the application first:"
    echo "  ibmcloud ce application delete -n rag-milvus -f"
    
    # Get cluster-local URL from address.url field
    CLUSTER_LOCAL_URL=$(ibmcloud ce app get --name rag-milvus --output json | grep -A1 '"address"' | grep '"url"' | head -1 | grep -o 'http://[^"]*')
    
    # Extract hostname from cluster-local URL
    if [ -n "$CLUSTER_LOCAL_URL" ]; then
        MILVUS_INTERNAL_HOST=$(echo "$CLUSTER_LOCAL_URL" | sed 's|http://||' | sed 's|https://||' | cut -d':' -f1)
        echo "Retrieved cluster-local URL: $CLUSTER_LOCAL_URL"
    else
        # Fallback to simple hostname if cluster-local URL not available
        MILVUS_INTERNAL_HOST="rag-milvus"
        echo "Using fallback hostname: $MILVUS_INTERNAL_HOST"
    fi
    MILVUS_INTERNAL_PORT="19530"
    
    ENV_FILE="../.env"
    if [ -f "$ENV_FILE" ]; then
        # Check if .env already has the correct configuration
        if grep -q "^MILVUS_HOST=$MILVUS_INTERNAL_HOST" "$ENV_FILE" && \
           grep -q "^MILVUS_PORT=$MILVUS_INTERNAL_PORT" "$ENV_FILE"; then
            echo "✓ .env file already has correct Milvus configuration"
        else
            echo "Updating .env file with Milvus configuration..."
            # Create backup
            cp "$ENV_FILE" "${ENV_FILE}.backup"
            
            # Comment out existing MILVUS_HOST and MILVUS_PORT lines and add new ones
            sed -i.tmp '/^MILVUS_HOST=/s/^/# (Original) /' "$ENV_FILE"
            sed -i.tmp '/^MILVUS_PORT=/s/^/# (Original) /' "$ENV_FILE"
            
            # Add new configuration above the commented lines
            sed -i.tmp "/^# (Original) MILVUS_HOST=/i\\
# Milvus deployed to Code Engine\\
MILVUS_HOST=$MILVUS_INTERNAL_HOST\\
MILVUS_PORT=$MILVUS_INTERNAL_PORT\\
" "$ENV_FILE"
            
            # Clean up temp file
            rm -f "${ENV_FILE}.tmp"
            
            echo "✓ Updated $ENV_FILE with:"
            echo "  MILVUS_HOST=$MILVUS_INTERNAL_HOST"
            echo "  MILVUS_PORT=$MILVUS_INTERNAL_PORT"
        fi
    fi
    
    exit 0
fi

ibmcloud cr namespace-list
ibmcloud cr login --client podman

echo '-----------------------------------------------------------'
echo 'Building Milvus container'
echo '-----------------------------------------------------------'

# Build container image
podman build -f Containerfile \
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
echo 'Creating/Updating Milvus Application'
echo '-----------------------------------------------------------'

# Check if application exists
if [[ $(ibmcloud ce application get -n rag-milvus 2>&1 | grep 'Resource not found') ]]; then
    echo 'Creating IBM Code Engine Application: rag-milvus'
    ibmcloud ce application create \
        --name rag-milvus \
        --port 19530 \
        --min-scale 1 --max-scale 1 \
        --cpu 2 --memory 4G \
        --image "private.$FULL_IMAGE_TAG" \
        --registry-secret rag-registry-secret \
        --env ETCD_USE_EMBED=true \
        --env COMMON_STORAGETYPE=local
else
    echo 'Updating IBM Code Engine Application: rag-milvus'
    ibmcloud ce application update \
        --name rag-milvus \
        --image "private.$FULL_IMAGE_TAG" \
        --registry-secret rag-registry-secret
fi

echo '-----------------------------------------------------------'
echo 'Deployment Complete'
echo '-----------------------------------------------------------'

# Get application URLs
APP_URL=$(ibmcloud ce application get -n rag-milvus -o json | grep -o '"url":"[^"]*' | cut -d'"' -f4)

# Get cluster-local URL from address.url field
CLUSTER_LOCAL_URL=$(ibmcloud ce app get --name rag-milvus --output json | grep -A1 '"address"' | grep '"url"' | head -1 | grep -o 'http://[^"]*')

# Extract hostname from cluster-local URL (remove http:// and port if present)
if [ -n "$CLUSTER_LOCAL_URL" ]; then
    MILVUS_INTERNAL_HOST=$(echo "$CLUSTER_LOCAL_URL" | sed 's|http://||' | sed 's|https://||' | cut -d':' -f1)
else
    # Fallback to simple hostname if cluster-local URL not available
    MILVUS_INTERNAL_HOST="rag-milvus"
fi
MILVUS_INTERNAL_PORT="19530"

echo "Milvus External URL: $APP_URL"
echo "Milvus Cluster Local URL: $CLUSTER_LOCAL_URL"
echo "Milvus Internal Host: $MILVUS_INTERNAL_HOST"
echo "Milvus Port: $MILVUS_INTERNAL_PORT"

echo '-----------------------------------------------------------'
echo 'Updating .env file with Milvus configuration'
echo '-----------------------------------------------------------'

# Update .env file with correct Milvus settings
ENV_FILE="../.env"
if [ -f "$ENV_FILE" ]; then
    # Create backup
    cp "$ENV_FILE" "${ENV_FILE}.backup"
    
    # Comment out existing MILVUS_HOST and MILVUS_PORT lines and add new ones
    sed -i.tmp '/^MILVUS_HOST=/s/^/# (Original) /' "$ENV_FILE"
    sed -i.tmp '/^MILVUS_PORT=/s/^/# (Original) /' "$ENV_FILE"
    
    # Add new configuration above the commented lines
    sed -i.tmp "/^# (Original) MILVUS_HOST=/i\\
# Milvus deployed to Code Engine\\
MILVUS_HOST=$MILVUS_INTERNAL_HOST\\
MILVUS_PORT=$MILVUS_INTERNAL_PORT\\
" "$ENV_FILE"
    
    # Clean up temp file
    rm -f "${ENV_FILE}.tmp"
    
    echo "✓ Updated $ENV_FILE with:"
    echo "  MILVUS_HOST=$MILVUS_INTERNAL_HOST"
    echo "  MILVUS_PORT=$MILVUS_INTERNAL_PORT"
    echo "  (Original values commented out)"
else
    echo "Warning: .env file not found at $ENV_FILE"
fi

echo '-----------------------------------------------------------'
echo 'Testing deployment'
echo '-----------------------------------------------------------'

# Wait for application to be ready
echo "Waiting for Milvus to be ready..."
sleep 30

echo '-----------------------------------------------------------'
echo 'Deployment successful!'
echo '-----------------------------------------------------------'

# Made with Bob