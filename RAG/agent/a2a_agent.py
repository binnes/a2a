"""A2A RAG Agent implementation using LangGraph."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from langgraph.graph import StateGraph, END  # type: ignore
from langchain_core.messages import HumanMessage, AIMessage  # type: ignore

from agent.state import AgentState, A2AMessage
from agent.tools import MCPToolClient
from config.settings import Settings

logger = logging.getLogger(__name__)


class A2ARAGAgent:
    """A2A-based RAG agent using LangGraph for orchestration."""

    def __init__(self, settings: Settings):
        """Initialize the A2A RAG agent.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.agent_id = settings.a2a_agent_id
        self.agent_name = settings.a2a_agent_name
        self.mcp_client = MCPToolClient(settings)
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow.

        Returns:
            Compiled state graph
        """
        # Create workflow graph
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("process_input", self._process_input)
        workflow.add_node("retrieve_context", self._retrieve_context)
        workflow.add_node("generate_response", self._generate_response)
        workflow.add_node("handle_error", self._handle_error)

        # Set entry point
        workflow.set_entry_point("process_input")

        # Add edges
        workflow.add_conditional_edges(
            "process_input",
            self._route_after_input,
            {
                "retrieve": "retrieve_context",
                "error": "handle_error",
            },
        )

        workflow.add_conditional_edges(
            "retrieve_context",
            self._route_after_retrieval,
            {
                "generate": "generate_response",
                "error": "handle_error",
            },
        )

        workflow.add_edge("generate_response", END)
        workflow.add_edge("handle_error", END)

        # Compile graph
        return workflow.compile()

    async def _process_input(self, state: AgentState) -> AgentState:
        """Process user input and prepare for retrieval.

        Args:
            state: Current agent state

        Returns:
            Updated agent state
        """
        try:
            logger.info(f"Processing input: {state['query']}")

            # Add user message to conversation
            if "messages" not in state:
                state["messages"] = []

            state["messages"].append({
                "role": "user",
                "content": state["query"],
            })

            # Initialize metadata
            if "metadata" not in state or state["metadata"] is None:
                state["metadata"] = {}

            state["metadata"]["agent_id"] = self.agent_id
            state["metadata"]["timestamp"] = datetime.utcnow().isoformat()

            state["next_action"] = "retrieve"
            logger.info("Input processed successfully")

        except Exception as e:
            logger.error(f"Error processing input: {e}")
            state["error"] = str(e)
            state["next_action"] = "error"

        return state

    async def _retrieve_context(self, state: AgentState) -> AgentState:
        """Retrieve relevant context from RAG knowledge base.

        Args:
            state: Current agent state

        Returns:
            Updated agent state with context
        """
        try:
            logger.info("Retrieving context from RAG")

            # Call MCP RAG query tool
            result = await self.mcp_client.rag_query(
                query=state["query"],
                top_k=self.settings.rag_top_k,
                include_sources=True,
            )

            # Store context and sources
            state["context"] = result.get("context", [])
            state["sources"] = result.get("sources", [])
            state["response"] = result.get("answer", "")

            state["next_action"] = "generate"
            logger.info(f"Retrieved {len(state['context'])} context chunks")

        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            state["error"] = str(e)
            state["next_action"] = "error"

        return state

    async def _generate_response(self, state: AgentState) -> AgentState:
        """Generate final response (already done by RAG query).

        Args:
            state: Current agent state

        Returns:
            Updated agent state with response
        """
        try:
            logger.info("Finalizing response")

            # Add assistant message to conversation
            response_content = state.get("response") or ""
            state["messages"].append({
                "role": "assistant",
                "content": response_content,
            })

            # Update metadata
            metadata = state.get("metadata")
            if metadata is not None:
                metadata["response_generated"] = True
                sources = state.get("sources")
                metadata["num_sources"] = len(sources) if sources else 0

            logger.info("Response generated successfully")

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            state["error"] = str(e)

        return state

    async def _handle_error(self, state: AgentState) -> AgentState:
        """Handle errors in the workflow.

        Args:
            state: Current agent state

        Returns:
            Updated agent state with error response
        """
        logger.error(f"Handling error: {state.get('error', 'Unknown error')}")

        state["response"] = (
            f"I encountered an error while processing your request: "
            f"{state.get('error', 'Unknown error')}"
        )

        state["messages"].append({
            "role": "assistant",
            "content": state["response"],
        })

        return state

    def _route_after_input(self, state: AgentState) -> str:
        """Route after input processing.

        Args:
            state: Current agent state

        Returns:
            Next node name
        """
        next_action = state.get("next_action")
        return next_action if next_action else "error"

    def _route_after_retrieval(self, state: AgentState) -> str:
        """Route after context retrieval.

        Args:
            state: Current agent state

        Returns:
            Next node name
        """
        next_action = state.get("next_action")
        return next_action if next_action else "error"

    async def process_query(self, query: str) -> Dict[str, Any]:
        """Process a user query through the agent workflow.

        Args:
            query: User query string

        Returns:
            Response dictionary with answer and metadata

        Raises:
            Exception: If processing fails
        """
        try:
            logger.info(f"Agent {self.agent_id} processing query")

            # Initialize state
            initial_state: AgentState = {
                "query": query,
                "messages": [],
                "context": None,
                "sources": None,
                "response": None,
                "metadata": None,
                "error": None,
                "next_action": None,
            }

            # Run workflow
            final_state = await self.graph.ainvoke(initial_state)

            # Prepare response
            response = {
                "agent_id": self.agent_id,
                "query": query,
                "response": final_state.get("response", ""),
                "context": final_state.get("context", []),
                "sources": final_state.get("sources", []),
                "metadata": final_state.get("metadata", {}),
            }

            if final_state.get("error"):
                response["error"] = final_state["error"]

            logger.info("Query processed successfully")
            return response

        except Exception as e:
            logger.error(f"Failed to process query: {e}")
            raise

    async def handle_a2a_message(self, message: A2AMessage) -> A2AMessage:
        """Handle incoming A2A protocol message.

        Args:
            message: Incoming A2A message

        Returns:
            Response A2A message

        Raises:
            Exception: If message handling fails
        """
        try:
            logger.info(f"Handling A2A message from {message['agent_id']}")

            message_type = message.get("message_type", "query")
            content = message.get("content", {})

            if message_type == "query":
                # Process query
                query = content.get("query", "")
                result = await self.process_query(query)

                # Create response message
                response_message: A2AMessage = {
                    "agent_id": self.agent_id,
                    "message_type": "response",
                    "content": result,
                    "timestamp": datetime.utcnow().isoformat(),
                    "correlation_id": message.get("correlation_id"),
                }

                return response_message

            else:
                raise ValueError(f"Unsupported message type: {message_type}")

        except Exception as e:
            logger.error(f"Failed to handle A2A message: {e}")
            
            # Return error message
            error_message: A2AMessage = {
                "agent_id": self.agent_id,
                "message_type": "error",
                "content": {"error": str(e)},
                "timestamp": datetime.utcnow().isoformat(),
                "correlation_id": message.get("correlation_id"),
            }
            
            return error_message

    def get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities for A2A registration.

        Returns:
            Dictionary describing agent capabilities
        """
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "description": self.settings.a2a_agent_description,
            "capabilities": [
                "rag_query",
                "knowledge_search",
                "document_qa",
            ],
            "tools": [
                "rag_query",
                "rag_search",
                "rag_index",
            ],
            "version": "0.1.0",
        }

    async def health_check(self) -> Dict[str, bool]:
        """Check health of agent and dependencies.

        Returns:
            Dictionary with health status
        """
        return {
            "agent": True,
            "mcp_server": await self.mcp_client.health_check(),
        }

    async def close(self):
        """Clean up resources."""
        await self.mcp_client.close()

# Made with Bob
