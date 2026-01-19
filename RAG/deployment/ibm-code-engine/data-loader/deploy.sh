#!/bin/bash

# Deploy Data Loader Job to IBM Code Engine
# Loads Shakespeare text into Milvus

set -e

echo '==========================================================='
echo 'Building and Deploying Data Loader Job'
echo '==========================================================='

# Load environment variables
if [ ! -f ../.env ]; then
    echo "Error: .env file not found in parent directory"
    exit 1
fi

source ../.env

# Set variables
IMAGE_NAME="rag-data-loader"
FULL_IMAGE_NAME="${IBM_ICR}/${IBM_NAMESPACE}/${IMAGE_NAME}:latest"
JOB_NAME="rag-data-loader"

echo "Image: ${FULL_IMAGE_NAME}"
echo "Job: ${JOB_NAME}"
echo ''

# Login to IBM Cloud
echo 'Logging in to IBM Cloud...'
ibmcloud login --apikey "${IBM_API_KEY}" -r "${IBM_REGION}" -g "${IBM_RESOURCE_GROUP}"

# Login to Container Registry
echo 'Logging in to IBM Container Registry...'
ibmcloud cr login

# Target Code Engine project
echo "Targeting Code Engine project: ${IBM_ICE_PROJECT}"
ibmcloud ce project select --name "${IBM_ICE_PROJECT}"

# Build container image
echo ''
echo 'Building container image...'
cd ../../..
podman build -f deployment/ibm-code-engine/data-loader/Containerfile -t "${FULL_IMAGE_NAME}" .

# Push to registry
echo ''
echo 'Pushing image to IBM Container Registry...'
podman push "${FULL_IMAGE_NAME}"

# Check if job exists
echo ''
if ibmcloud ce job get --name "${JOB_NAME}" &>/dev/null; then
    echo "Job ${JOB_NAME} exists, updating..."
    ibmcloud ce job update --name "${JOB_NAME}" \
        --image "${FULL_IMAGE_NAME}" \
        --env-from-secret watsonx-credentials \
        --env MILVUS_HOST="${MILVUS_HOST}" \
        --env MILVUS_PORT="${MILVUS_PORT}" \
        --env MILVUS_COLLECTION_NAME="${MILVUS_COLLECTION_NAME}" \
        --env EMBEDDING_MODEL="${EMBEDDING_MODEL}" \
        --env EMBEDDING_DIMENSION="${EMBEDDING_DIMENSION}" \
        --env LOG_LEVEL="${LOG_LEVEL}" \
        --cpu 1 \
        --memory 2G \
        --maxexecutiontime 1800 \
        --retrylimit 2
else
    echo "Creating new job ${JOB_NAME}..."
    ibmcloud ce job create --name "${JOB_NAME}" \
        --image "${FULL_IMAGE_NAME}" \
        --env-from-secret watsonx-credentials \
        --env MILVUS_HOST="${MILVUS_HOST}" \
        --env MILVUS_PORT="${MILVUS_PORT}" \
        --env MILVUS_COLLECTION_NAME="${MILVUS_COLLECTION_NAME}" \
        --env EMBEDDING_MODEL="${EMBEDDING_MODEL}" \
        --env EMBEDDING_DIMENSION="${EMBEDDING_DIMENSION}" \
        --env LOG_LEVEL="${LOG_LEVEL}" \
        --cpu 1 \
        --memory 2G \
        --maxexecutiontime 1800 \
        --retrylimit 2
fi

echo ''
echo '==========================================================='
echo '✓ Data Loader Job Deployed'
echo '==========================================================='
echo ''
echo 'To run the job:'
echo "  ibmcloud ce jobrun submit --job ${JOB_NAME} --name ${JOB_NAME}-run-\$(date +%s)"
echo ''
echo 'To view job runs:'
echo "  ibmcloud ce jobrun list --job ${JOB_NAME}"
echo ''
echo 'To view logs:'
echo "  ibmcloud ce jobrun logs --job ${JOB_NAME}"
echo ''

# Made with Bob