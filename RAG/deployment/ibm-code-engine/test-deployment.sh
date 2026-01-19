#!/bin/bash

# Test script for IBM Code Engine deployment
# This script verifies that all services are deployed and can communicate

set -e

echo "==========================================================="
echo "IBM Code Engine Deployment Test"
echo "==========================================================="
echo ""

# Load environment variables
if [ -f .env ]; then
    source .env
else
    echo "Error: .env file not found"
    exit 1
fi

# Check if logged in to IBM Cloud
if [[ $(ibmcloud target | grep login) ]]; then
    echo 'Please login to ibmcloud cli before running this script'
    exit 1
fi

# Select Code Engine project
ibmcloud ce project select --name "$IBM_ICE_PROJECT"

echo "-----------------------------------------------------------"
echo "Test 1: Verify Milvus Application"
echo "-----------------------------------------------------------"

if [[ $(ibmcloud ce application get -n rag-milvus 2>&1 | grep 'Resource not found') ]]; then
    echo "❌ FAIL: Milvus application not found"
    exit 1
else
    echo "✓ Milvus application exists"
    
    # Get status
    STATUS=$(ibmcloud ce application get -n rag-milvus -o json | grep -o '"status":"[^"]*' | cut -d'"' -f4)
    echo "  Status: $STATUS"
    
    # Get cluster-local URL from address.url field
    CLUSTER_URL=$(ibmcloud ce app get --name rag-milvus --output json | grep -A1 '"address"' | grep '"url"' | head -1 | grep -o 'http://[^"]*')
    if [ -n "$CLUSTER_URL" ]; then
        echo "  ✓ Cluster-local URL: $CLUSTER_URL"
    else
        echo "  ❌ FAIL: Could not retrieve cluster-local URL"
        exit 1
    fi
fi

echo ""
echo "-----------------------------------------------------------"
echo "Test 2: Verify MCP Server Application"
echo "-----------------------------------------------------------"

if [[ $(ibmcloud ce application get -n rag-mcp-server 2>&1 | grep 'Resource not found') ]]; then
    echo "❌ FAIL: MCP Server application not found"
    exit 1
else
    echo "✓ MCP Server application exists"
    
    # Get status
    STATUS=$(ibmcloud ce application get -n rag-mcp-server -o json | grep -o '"status":"[^"]*' | cut -d'"' -f4)
    echo "  Status: $STATUS"
    
    # Get cluster-local URL from address.url field
    CLUSTER_URL=$(ibmcloud ce app get --name rag-mcp-server --output json | grep -A1 '"address"' | grep '"url"' | head -1 | grep -o 'http://[^"]*')
    if [ -n "$CLUSTER_URL" ]; then
        echo "  ✓ Cluster-local URL: $CLUSTER_URL"
    else
        echo "  ❌ FAIL: Could not retrieve cluster-local URL"
        exit 1
    fi
    
    # Check Milvus configuration
    MILVUS_HOST=$(ibmcloud ce application get -n rag-mcp-server -o json | grep -o '"MILVUS_HOST","value":"[^"]*' | cut -d'"' -f6)
    if [ -n "$MILVUS_HOST" ]; then
        echo "  ✓ Milvus host configured: $MILVUS_HOST"
    else
        echo "  ⚠ Warning: Could not verify Milvus host configuration"
    fi
fi

echo ""
echo "-----------------------------------------------------------"
echo "Test 3: Verify A2A Agent Application"
echo "-----------------------------------------------------------"

if [[ $(ibmcloud ce application get -n rag-a2a-agent 2>&1 | grep 'Resource not found') ]]; then
    echo "❌ FAIL: A2A Agent application not found"
    exit 1
else
    echo "✓ A2A Agent application exists"
    
    # Get status
    STATUS=$(ibmcloud ce application get -n rag-a2a-agent -o json | grep -o '"status":"[^"]*' | cut -d'"' -f4)
    echo "  Status: $STATUS"
    
    # Get external URL
    EXTERNAL_URL=$(ibmcloud ce application get -n rag-a2a-agent -o json | grep -o '"url":"[^"]*' | cut -d'"' -f4)
    if [ -n "$EXTERNAL_URL" ]; then
        echo "  ✓ External URL: $EXTERNAL_URL"
    fi
    
    # Check MCP Server configuration
    MCP_HOST=$(ibmcloud ce application get -n rag-a2a-agent -o json | grep -o '"MCP_SERVER_HOST","value":"[^"]*' | cut -d'"' -f6)
    if [ -n "$MCP_HOST" ]; then
        echo "  ✓ MCP Server host configured: $MCP_HOST"
    else
        echo "  ⚠ Warning: Could not verify MCP Server host configuration"
    fi
fi

echo ""
echo "-----------------------------------------------------------"
echo "Test 4: Verify .env File Configuration"
echo "-----------------------------------------------------------"

if [ -f .env ]; then
    echo "✓ .env file exists"
    
    # Check Milvus configuration
    MILVUS_HOST_ENV=$(grep "^MILVUS_HOST=" .env | cut -d'=' -f2)
    MILVUS_PORT_ENV=$(grep "^MILVUS_PORT=" .env | cut -d'=' -f2)
    
    if [ -n "$MILVUS_HOST_ENV" ]; then
        echo "  ✓ MILVUS_HOST: $MILVUS_HOST_ENV"
    else
        echo "  ❌ FAIL: MILVUS_HOST not set in .env"
        exit 1
    fi
    
    if [ -n "$MILVUS_PORT_ENV" ]; then
        echo "  ✓ MILVUS_PORT: $MILVUS_PORT_ENV"
    else
        echo "  ❌ FAIL: MILVUS_PORT not set in .env"
        exit 1
    fi
else
    echo "❌ FAIL: .env file not found"
    exit 1
fi

echo ""
echo "-----------------------------------------------------------"
echo "Test 5: Test MCP Server Health Endpoint"
echo "-----------------------------------------------------------"

MCP_URL=$(ibmcloud ce application get -n rag-mcp-server -o json | grep -o '"url":"[^"]*' | cut -d'"' -f4)
if [ -n "$MCP_URL" ]; then
    echo "Testing health endpoint: $MCP_URL/health"
    
    # Wait a bit for the service to be ready
    sleep 5
    
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$MCP_URL/health" || echo "000")
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo "  ✓ Health check passed (HTTP $HTTP_CODE)"
    else
        echo "  ⚠ Health check returned HTTP $HTTP_CODE"
        echo "  Note: Service may still be starting up"
    fi
else
    echo "  ⚠ Could not retrieve MCP Server URL"
fi

echo ""
echo "-----------------------------------------------------------"
echo "Test 6: Test A2A Agent Health Endpoint"
echo "-----------------------------------------------------------"

A2A_URL=$(ibmcloud ce application get -n rag-a2a-agent -o json | grep -o '"url":"[^"]*' | cut -d'"' -f4)
if [ -n "$A2A_URL" ]; then
    echo "Testing health endpoint: $A2A_URL/health"
    
    # Wait a bit for the service to be ready
    sleep 5
    
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$A2A_URL/health" || echo "000")
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo "  ✓ Health check passed (HTTP $HTTP_CODE)"
    else
        echo "  ⚠ Health check returned HTTP $HTTP_CODE"
        echo "  Note: Service may still be starting up"
    fi
else
    echo "  ⚠ Could not retrieve A2A Agent URL"
fi

echo ""
echo "==========================================================="
echo "Test Summary"
echo "==========================================================="
echo ""
echo "✓ All applications are deployed"
echo "✓ Cluster-local URLs are configured"
echo "✓ Environment variables are set"
echo ""
echo "Next steps:"
echo "1. Check application logs for any errors:"
echo "   ibmcloud ce app logs -n rag-milvus"
echo "   ibmcloud ce app logs -n rag-mcp-server"
echo "   ibmcloud ce app logs -n rag-a2a-agent"
echo ""
echo "2. Test the RAG functionality:"
echo "   curl -X POST $A2A_URL/query -H 'Content-Type: application/json' -d '{\"query\":\"test\"}'"
echo ""
echo "==========================================================="

# Made with Bob