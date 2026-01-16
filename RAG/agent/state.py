"""Agent state definitions for LangGraph."""

from typing import TypedDict, List, Dict, Any, Optional, Annotated
from operator import add


class AgentState(TypedDict):
    """State for the A2A RAG agent.

    This state is passed between nodes in the LangGraph workflow.
    """

    # Input
    query: str
    """User query or input message"""

    # Conversation history
    messages: Annotated[List[Dict[str, str]], add]
    """List of conversation messages"""

    # Retrieved context
    context: Optional[List[str]]
    """Retrieved context chunks from RAG"""

    sources: Optional[List[Dict[str, Any]]]
    """Source information for retrieved context"""

    # Generated response
    response: Optional[str]
    """Generated response from the agent"""

    # Metadata
    metadata: Optional[Dict[str, Any]]
    """Additional metadata for the interaction"""

    # Error handling
    error: Optional[str]
    """Error message if any step fails"""

    # Control flow
    next_action: Optional[str]
    """Next action to take in the workflow"""


class A2AMessage(TypedDict):
    """A2A protocol message format."""

    agent_id: str
    """ID of the sending agent"""

    message_type: str
    """Type of message (query, response, error, etc.)"""

    content: Dict[str, Any]
    """Message content"""

    timestamp: str
    """ISO format timestamp"""

    correlation_id: Optional[str]
    """ID to correlate request/response pairs"""

# Made with Bob
