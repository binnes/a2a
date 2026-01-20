"""A2A Shakespeare RAG Agent Server.

This server uses the official a2a-server framework to provide a standards-compliant
A2A 0.3.0 protocol implementation for IBM watsonx Orchestrate integration.
"""

import logging
import sys

import httpx
import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import (
    BasePushNotificationSender,
    InMemoryPushNotificationConfigStore,
    InMemoryTaskStore,
)
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)

from agent.agent_executor import ShakespeareAgentExecutor
from config.settings import Settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_agent_card(settings: Settings, host: str, port: int) -> AgentCard:
    """Create the agent card describing Shakespeare RAG agent capabilities.
    
    Args:
        settings: Application settings
        host: Server host
        port: Server port
        
    Returns:
        AgentCard with agent metadata and capabilities
    """
    capabilities = AgentCapabilities(
        streaming=False,  # We don't support streaming yet
        push_notifications=False,
    )
    
    skill = AgentSkill(
        id='shakespeare_knowledge',
        name='Shakespeare Knowledge Base',
        description='Search and answer questions about Shakespeare\'s complete works',
        tags=[
            'shakespeare',
            'literature',
            'plays',
            'sonnets',
            'poetry',
            'drama',
            'elizabethan',
        ],
        examples=[
            'Who is Hamlet?',
            'What are the main characters in Othello?',
            'Tell me about Romeo and Juliet',
            'What happens in Macbeth?',
            'Who wrote "To be or not to be"?',
        ],
    )
    
    agent_card = AgentCard(
        name=settings.a2a_agent_name,
        description=settings.a2a_agent_description,
        url=f'http://{host}:{port}/',
        version='1.0.0',
        default_input_modes=['text', 'text/plain'],
        default_output_modes=['text', 'text/plain'],
        capabilities=capabilities,
        skills=[skill],
    )
    
    return agent_card


def main():
    """Start the Shakespeare RAG Agent server."""
    try:
        # Load settings
        settings = Settings()
        
        # Server configuration
        host = settings.a2a_host
        port = settings.a2a_port
        
        logger.info(f"Starting Shakespeare RAG Agent on {host}:{port}")
        logger.info(f"Agent ID: {settings.a2a_agent_id}")
        logger.info(f"Agent Name: {settings.a2a_agent_name}")
        
        # Create agent card
        agent_card = create_agent_card(settings, host, port)
        
        # Set up A2A server components
        httpx_client = httpx.AsyncClient()
        push_config_store = InMemoryPushNotificationConfigStore()
        push_sender = BasePushNotificationSender(
            httpx_client=httpx_client,
            config_store=push_config_store,
        )
        
        # Create request handler with our agent executor
        request_handler = DefaultRequestHandler(
            agent_executor=ShakespeareAgentExecutor(),
            task_store=InMemoryTaskStore(),
            push_config_store=push_config_store,
            push_sender=push_sender,
        )
        
        # Create A2A Starlette application
        server = A2AStarletteApplication(
            agent_card=agent_card,
            http_handler=request_handler,
        )
        
        # Start server
        logger.info("Server initialized successfully")
        uvicorn.run(server.build(), host=host, port=port)
        
    except Exception as e:
        logger.error(f"Failed to start server: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

# Made with Bob
