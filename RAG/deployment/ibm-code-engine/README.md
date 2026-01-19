# IBM Code Engine Deployment

Deploy RAG agents (MCP Server, A2A Agent, and optionally Milvus) to IBM Code Engine.

## Quick Start

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env with your credentials

# 2. Deploy all services
./deploy-all.sh

# 3. Test deployment
./test-deployment.sh
```

## Testing the Deployment

After deployment, run the comprehensive test script:

```bash
./test-deployment.sh
```

This will verify:
- ✅ All applications are deployed and running
- ✅ Cluster-local URLs are configured correctly
- ✅ Environment variables are set properly
- ✅ Health endpoints are responding
- ✅ Service-to-service communication is working

### Manual Testing

```bash
# Check application status
ibmcloud ce application list

# View application details
ibmcloud ce app get --name rag-milvus
ibmcloud ce app get --name rag-mcp-server
ibmcloud ce app get --name rag-a2a-agent

# Check logs
ibmcloud ce app logs -n rag-mcp-server --tail 50
ibmcloud ce app logs -n rag-a2a-agent --tail 50

# Test health endpoints
MCP_URL=$(ibmcloud ce app get --name rag-mcp-server -o json | grep -o '"url":"[^"]*' | cut -d'"' -f4)
curl $MCP_URL/health

A2A_URL=$(ibmcloud ce app get --name rag-a2a-agent -o json | grep -o '"url":"[^"]*' | cut -d'"' -f4)
curl $A2A_URL/health
```

## Individual Deployments

```bash
# Milvus only (if DEPLOY_MILVUS_LOCAL=true)
cd milvus && ./deploy.sh

# MCP Server only
cd mcp-server && ./deploy.sh

# A2A Agent only
cd a2a-agent && ./deploy.sh
```

## Directory Structure

```
ibm-code-engine/
├── .env.example          # Configuration template
├── deploy-all.sh         # Deploy both services
├── mcp-server/
│   ├── Containerfile     # MCP Server container
│   └── deploy.sh         # MCP Server deployment
└── a2a-agent/
    ├── Containerfile     # A2A Agent container
    └── deploy.sh         # A2A Agent deployment
```

## Documentation

For complete deployment documentation, see:

**[IBM Code Engine Deployment Guide](../../../docs/docs/deployment/ibm-code-engine.md)**

Includes:
- Prerequisites and setup
- Configuration reference
- Deployment process
- Monitoring and troubleshooting
- Security best practices
- Cost optimization