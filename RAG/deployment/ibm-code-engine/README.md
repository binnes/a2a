# IBM Code Engine Deployment

Deploy RAG agents (MCP Server and A2A Agent) to IBM Code Engine.

## Quick Start

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env with your credentials

# 2. Deploy both services
./deploy-all.sh

# 3. Verify
ibmcloud ce application list
curl https://rag-mcp-server.your-region.codeengine.appdomain.cloud/health
```

## Individual Deployments

```bash
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