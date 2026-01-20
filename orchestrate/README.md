# IBM watsonx Orchestrate Configuration

This directory contains the configuration for integrating the Shakespeare Knowledge Agent (RAG) with IBM watsonx Orchestrate Developer Edition.

## Quick Start

### Start Orchestrate

```bash
cd orchestrate
bash scripts/startOrchestrate.sh
```

This will start the local Orchestrate instance with document processing enabled.

### Create and Import the Shakespeare RAG Agent

Once Orchestrate is running, create and import the Shakespeare knowledge agent:

```bash
# Activate the orchestrate virtual environment
source .venv/bin/activate

# Create and import the agent (this also generates rag-agent-config.yml)
orchestrate agents create \
-n shakespeare-rag-agent \
-t "Shakespeare Knowledge Agent" \
-k external \
--description "RAG agent with complete works of Shakespeare. Use for questions about Shakespeare's plays, sonnets, characters, quotes, and literary analysis." \
--api http://host.lima.internal:8001 \
--provider external_chat/A2A/0.3.0 \
-o rag-agent-config.yml
```

**Important**: Use `host.lima.internal` to access the host machine from Lima VM where Orchestrate runs.

**Knowledge Base**: This agent has access to the complete works of William Shakespeare, making it ideal for:
- Questions about Shakespeare's plays and sonnets
- Character analysis and quotes
- Literary analysis and themes
- Historical context of Shakespeare's works

**Note**: The agent configuration is automatically saved to `rag-agent-config.yml` for future reference and can be re-imported using:
```bash
orchestrate agents import -f rag-agent-config.yml
```

## Configuration Files

- **rag-agent-config.yml**: Agent configuration for IBM watsonx Orchestrate
- **.env**: Environment variables for Orchestrate (API keys, credentials)
- **scripts/startOrchestrate.sh**: Script to start Orchestrate Developer Edition

## Prerequisites

Before registering the agent, ensure:

1. **RAG Agent is Running**: The A2A agent must be running on `http://localhost:8001`
   ```bash
   cd RAG/deployment/local
   bash deploy.sh
   ```

2. **Orchestrate is Running**: Start Orchestrate using the script above

3. **Environment Variables**: Ensure `.env` file contains required credentials:
   - `WATSONX_APIKEY`: Your watsonx.ai API key
   - `WATSONX_SPACE_ID`: Your watsonx.ai space ID
   - `WO_ENTITLEMENT_KEY`: Orchestrate entitlement key

## Agent Capabilities

The Shakespeare Knowledge Agent provides the following capabilities:

- **rag_query**: Query Shakespeare's complete works with natural language
- **knowledge_search**: Search for specific plays, sonnets, characters, or quotes
- **document_qa**: Answer questions about Shakespeare's literature and themes

**Knowledge Base Content**:
- All of Shakespeare's plays (tragedies, comedies, histories)
- Complete collection of sonnets
- Character information and relationships
- Famous quotes and passages
- Literary themes and analysis

## Endpoints

- **Agent Card**: `http://localhost:8001/.well-known/agent-card.json`
- **A2A Messages (JSONRPC)**: `http://localhost:8001/` (POST with JSONRPC payload)

## Verification

After importing, verify the agent is available:

```bash
# Activate virtual environment
source .venv/bin/activate

# List imported agents
orchestrate agents list

# Test agent health
curl http://localhost:8001/health
```

## Documentation

For complete documentation, see:
- [Orchestrate Architecture](../docs/docs/architecture/orchestrate.md)
- [A2A Protocol](../docs/docs/protocols/a2a.md)
- [RAG Agent Overview](../docs/docs/rag/overview.md)

## Troubleshooting

### Agent Not Responding

Check if the RAG agent is running:
```bash
curl http://localhost:8001/health
```

### Registration Failed

Verify Orchestrate is running:
```bash
orchestrate server status
```

### Connection Issues

Ensure the agent endpoint is accessible from Orchestrate. If running in containers, check network configuration.

## Made with Bob