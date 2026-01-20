"""Shakespeare RAG Agent Executor for A2A Protocol."""

import logging
from typing import Any, Dict

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    InternalError,
    InvalidParamsError,
    Part,
    TaskState,
    TextPart,
    UnsupportedOperationError,
)
from a2a.utils import (
    new_agent_text_message,
    new_task,
)
from a2a.utils.errors import ServerError

from agent.a2a_agent import A2ARAGAgent
from config.settings import Settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ShakespeareAgentExecutor(AgentExecutor):
    """Shakespeare RAG Agent Executor for A2A Protocol.
    
    This executor handles requests from IBM watsonx Orchestrate and processes
    them through the Shakespeare RAG agent, providing streaming updates.
    """

    def __init__(self):
        """Initialize the executor with the RAG agent."""
        settings = Settings()
        self.agent = A2ARAGAgent(settings)
        logger.info(f"Initialized Shakespeare Agent Executor: {self.agent.agent_id}")

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Execute a query against the Shakespeare knowledge base.
        
        Args:
            context: Request context containing user input and task info
            event_queue: Queue for sending status updates and results
            
        Raises:
            ServerError: If validation fails or processing encounters an error
        """
        # Validate request
        error = self._validate_request(context)
        if error:
            raise ServerError(error=InvalidParamsError())

        # Extract query from user input
        query = context.get_user_input()
        if not query:
            raise ServerError(error=InvalidParamsError(message="No query provided"))

        # Get or create task
        task = context.current_task
        if not task:
            task = new_task(context.message)  # type: ignore
            await event_queue.enqueue_event(task)
        
        updater = TaskUpdater(event_queue, task.id, task.context_id)
        
        try:
            # Update status to working
            await updater.update_status(
                TaskState.working,
                new_agent_text_message(
                    "Searching Shakespeare's works for relevant information...",
                    task.context_id,
                    task.id,
                ),
            )
            
            # Process query through RAG agent
            logger.info(f"Processing query: {query}")
            result = await self.agent.process_query(query)
            
            # Check for errors
            if result.get("error"):
                await updater.update_status(
                    TaskState.input_required,
                    new_agent_text_message(
                        f"Error processing query: {result['error']}",
                        task.context_id,
                        task.id,
                    ),
                    final=True,
                )
                return
            
            # Extract response
            response_text = result.get("response", "")
            if not response_text:
                await updater.update_status(
                    TaskState.input_required,
                    new_agent_text_message(
                        "I couldn't find relevant information in Shakespeare's works. Please try rephrasing your question.",
                        task.context_id,
                        task.id,
                    ),
                    final=True,
                )
                return
            
            # Add artifact with the answer
            await updater.add_artifact(
                [Part(root=TextPart(text=response_text))],
                name="shakespeare_answer",
            )
            
            # Mark task as complete
            await updater.complete()
            logger.info("Query processed successfully")
            
        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            await updater.update_status(
                TaskState.input_required,
                new_agent_text_message(
                    f"An error occurred while processing your request: {str(e)}",
                    task.context_id,
                    task.id,
                ),
                final=True,
            )
            raise ServerError(error=InternalError()) from e

    def _validate_request(self, context: RequestContext) -> bool:
        """Validate the incoming request.
        
        Args:
            context: Request context to validate
            
        Returns:
            True if validation fails, False if valid
        """
        # Check if user input exists
        user_input = context.get_user_input()
        if not user_input or not user_input.strip():
            logger.error("No user input provided")
            return True
        
        return False

    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        """Cancel a running task.
        
        Args:
            context: Request context
            event_queue: Event queue
            
        Raises:
            ServerError: Cancellation not supported
        """
        raise ServerError(error=UnsupportedOperationError())

# Made with Bob
