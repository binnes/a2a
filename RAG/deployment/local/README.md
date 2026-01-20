# Local Deployment

Deploy RAG agents locally using Podman for development and testing.

## Quick Start

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env with your Watsonx.ai credentials

# 2. Deploy all services
./deploy.sh

# 3. Test the deployment
curl http://localhost:8000/health
curl http://localhost:8001/health
```

## What Gets Deployed

This local deployment includes:

- **Milvus Vector Database** (with etcd and MinIO dependencies)
  - Port 19530: Milvus gRPC
  - Port 9091: Milvus metrics
  - Port 9001: MinIO console
  
- **MCP Server** 
  - Port 8000: REST API
  - Provides RAG tools via HTTP endpoints
  
- **A2A Agent**
  - Port 8001: Agent API
  - Orchestrates RAG workflows
  
- **Data Loader** (one-time job)
  - Automatically loads Shakespeare text into Milvus
  - Runs once during deployment

## Prerequisites

- **Podman**: Container runtime (replaces Docker)
  - Install: https://podman.io/getting-started/installation
  
- **podman-compose**: Compose tool for Podman
  - Install: `pip3 install podman-compose`
  
- **Python 3.10+**: For local development
  
- **Watsonx.ai Credentials**: API key and project ID

## Configuration

Edit `.env` file with your credentials:

```bash
# Required
WATSONX_API_KEY=your-api-key-here
WATSONX_PROJECT_ID=your-project-id-here

# Optional (defaults provided)
WATSONX_URL=https://us-south.ml.cloud.ibm.com
EMBEDDING_MODEL=ibm/granite-embedding-278m-multilingual
LLM_MODEL=openai/gpt-oss-120b
```

## Deployment Commands

### Full Deployment

```bash
./deploy.sh
```

This will:
1. Start Milvus and dependencies
2. Build and start MCP Server
3. Build and start A2A Agent
4. Load Shakespeare text into Milvus

### Shutdown and Cleanup

#### Interactive Shutdown

```bash
./shutdown.sh
```

This interactive script will:
1. Stop all running containers
2. Remove stopped containers
3. Optionally remove data volumes
4. Optionally clean up unused images

**Options:**
- **Option 1**: Stop containers only (preserves data)
- **Option 2**: Stop containers and remove volumes (deletes all data)

#### Automated Shutdown

For automation and CI/CD:

```bash
# Stop containers only (preserve data)
./shutdown-auto.sh

# Stop and remove all data
./shutdown-auto.sh --remove-volumes

# Full cleanup including images
./shutdown-auto.sh --remove-volumes --remove-images

# Show help
./shutdown-auto.sh --help
```

### Individual Services

```bash
# Start only Milvus
podman-compose up -d milvus

# Start only MCP Server
podman-compose up -d --build mcp-server

# Start only A2A Agent
podman-compose up -d --build a2a-agent

# Run data loader manually
podman-compose up --build data-loader
```

## Management Commands

### View Logs

```bash
# All services
podman-compose logs -f

# Specific service
podman-compose logs -f mcp-server
podman-compose logs -f a2a-agent
podman-compose logs -f milvus
```

### Check Status

```bash
# List running containers
podman-compose ps

# Check health
curl http://localhost:8000/health
curl http://localhost:8001/health
```

### Stop Services

```bash
# Recommended: Use shutdown script (interactive)
./shutdown.sh

# Quick stop (preserves data)
podman-compose down

# Stop and remove volumes (clears all data)
podman-compose down -v
```

### Restart Services

```bash
# Restart all
podman-compose restart

# Restart specific service
podman-compose restart mcp-server
```

## Testing

### Test MCP Server

```bash
# Health check
curl http://localhost:8000/health

# Query RAG (example)
curl -X POST http://localhost:8000/tools/rag_query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the meaning of life in Shakespeare?"}'

# Get stats
curl -X POST http://localhost:8000/tools/rag_stats
```

### Test A2A Agent

```bash
# Health check
curl http://localhost:8001/health

# Agent status
curl http://localhost:8001/status
```

### Access MinIO Console

Open http://localhost:9001 in your browser:
- Username: `minioadmin`
- Password: `minioadmin`

## Troubleshooting

### Milvus Won't Start

```bash
# Check logs
podman-compose logs milvus

# Ensure dependencies are running
podman-compose ps

# Restart with fresh volumes
podman-compose down -v
podman-compose up -d milvus
```

### MCP Server Connection Issues

```bash
# Check if Milvus is accessible
podman exec -it rag-mcp-server curl http://milvus:9091/healthz

# Check environment variables
podman exec -it rag-mcp-server env | grep MILVUS
```

### Data Loader Fails

```bash
# View logs
podman-compose logs data-loader

# Run manually with verbose output
podman-compose up data-loader

# Check if Shakespeare file exists
ls -la ../../data/reference/
```

### Port Conflicts

If ports are already in use, edit `podman-compose.yml` to change port mappings:

```yaml
ports:
  - "8080:8000"  # Change 8000 to 8080
```

## Development Workflow

### Rebuild After Code Changes

```bash
# Rebuild and restart specific service
podman-compose up -d --build mcp-server

# Rebuild all services
podman-compose up -d --build
```

### Access Container Shell

```bash
# MCP Server
podman exec -it rag-mcp-server /bin/bash

# A2A Agent
podman exec -it rag-a2a-agent /bin/bash

# Milvus
podman exec -it milvus-standalone /bin/bash
```

### View Container Resources

```bash
# Resource usage
podman stats

# Inspect container
podman inspect rag-mcp-server
```

## Data Persistence

Data is persisted in Podman volumes:

- `etcd_data`: etcd configuration
- `minio_data`: Object storage
- `milvus_data`: Vector database

To clear all data:

```bash
podman-compose down -v
```

## Network

All containers run on the `rag_network` bridge network, allowing them to communicate using service names:

- `milvus`: Milvus database
- `mcp-server`: MCP Server
- `a2a-agent`: A2A Agent

## Documentation

For complete documentation, see:

**[RAG Agent Documentation](../../../docs/docs/rag/overview.md)**

Includes:
- Architecture overview
- API reference
- Configuration guide
- Testing guide
- Troubleshooting

## Made with Bob