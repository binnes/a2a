"""A2A Client Integration Tests.

Tests the refactored A2A agent using the official a2a-sdk client,
based on the sample client code pattern.
"""

import logging
import pytest
from typing import Any
from uuid import uuid4

import httpx

from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    AgentCard,
    MessageSendParams,
    SendMessageRequest,
    SendStreamingMessageRequest,
)
from a2a.utils.constants import (
    AGENT_CARD_WELL_KNOWN_PATH,
    EXTENDED_AGENT_CARD_PATH,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.fixture
def base_url():
    """Get A2A agent base URL."""
    return 'http://localhost:8001'


@pytest.fixture
async def httpx_client():
    """Create HTTP client for testing."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        yield client


@pytest.fixture
async def agent_card_resolver(httpx_client, base_url):
    """Create A2A card resolver."""
    resolver = A2ACardResolver(
        httpx_client=httpx_client,
        base_url=base_url,
    )
    return resolver


@pytest.fixture
async def agent_card(agent_card_resolver):
    """Fetch agent card."""
    card = await agent_card_resolver.get_agent_card()
    return card


@pytest.fixture
async def a2a_client(httpx_client, agent_card):
    """Create A2A client."""
    client = A2AClient(
        httpx_client=httpx_client,
        agent_card=agent_card
    )
    return client


class TestA2AAgentCard:
    """Test A2A agent card retrieval and validation."""

    @pytest.mark.asyncio
    async def test_fetch_public_agent_card(self, agent_card_resolver, base_url):
        """Test fetching public agent card from well-known path."""
        logger.info(
            f'Attempting to fetch public agent card from: {base_url}{AGENT_CARD_WELL_KNOWN_PATH}'
        )
        
        public_card = await agent_card_resolver.get_agent_card()
        
        assert public_card is not None
        logger.info('Successfully fetched public agent card')
        logger.info(
            public_card.model_dump_json(indent=2, exclude_none=True)
        )

    @pytest.mark.asyncio
    async def test_agent_card_structure(self, agent_card):
        """Test agent card has required fields."""
        assert agent_card.name == "Shakespeare Knowledge Agent"
        assert "Shakespeare" in agent_card.description
        assert agent_card.protocol_version == "0.3.0"
        assert agent_card.preferred_transport == "JSONRPC"
        
        logger.info(f"✓ Agent card structure valid: {agent_card.name}")

    @pytest.mark.asyncio
    async def test_agent_card_capabilities(self, agent_card):
        """Test agent card capabilities declaration."""
        assert agent_card.capabilities is not None
        assert agent_card.capabilities.streaming == False
        assert agent_card.capabilities.push_notifications == False
        
        logger.info("✓ Agent capabilities correctly declared")

    @pytest.mark.asyncio
    async def test_agent_card_skills(self, agent_card):
        """Test agent card skills definition."""
        assert agent_card.skills is not None
        assert len(agent_card.skills) > 0
        
        shakespeare_skill = next(
            (s for s in agent_card.skills if s.id == 'shakespeare_knowledge'),
            None
        )
        assert shakespeare_skill is not None
        assert shakespeare_skill.name == "Shakespeare Knowledge Base"
        assert len(shakespeare_skill.examples) > 0
        assert "shakespeare" in [tag.lower() for tag in shakespeare_skill.tags]
        
        logger.info(f"✓ Shakespeare skill found with {len(shakespeare_skill.examples)} examples")


class TestA2AMessageSending:
    """Test A2A message sending and response handling."""

    @pytest.mark.asyncio
    async def test_send_simple_message(self, a2a_client):
        """Test sending a simple message to the agent."""
        send_message_payload = {
            'message': {
                'role': 'user',
                'parts': [
                    {'kind': 'text', 'text': 'Who is Romeo?'}
                ],
                'message_id': uuid4().hex,
            },
        }
        
        request = SendMessageRequest(
            id=str(uuid4()),
            params=MessageSendParams(**send_message_payload)
        )

        logger.info("Sending message: Who is Romeo?")
        response = await a2a_client.send_message(request)
        
        assert response is not None
        assert response.root is not None
        assert response.root.result is not None
        assert response.root.result.id is not None  # Task ID
        
        logger.info(f"✓ Message sent successfully, task ID: {response.root.result.id}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

# Made with Bob