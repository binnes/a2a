"""Watsonx.ai client for embeddings and LLM services."""

import logging
from typing import List, Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential  # type: ignore

from ibm_watsonx_ai import APIClient, Credentials  # type: ignore
from ibm_watsonx_ai.foundation_models import Embeddings, ModelInference  # type: ignore

from config.settings import Settings

logger = logging.getLogger(__name__)


class WatsonxClient:
    """Client for interacting with IBM Watsonx.ai services."""

    def __init__(self, settings: Settings):
        """Initialize Watsonx.ai client.

        Args:
            settings: Application settings containing Watsonx.ai credentials
        """
        self.settings = settings
        self._api_client: Optional[APIClient] = None
        self._embeddings: Optional[Embeddings] = None
        self._llm: Optional[ModelInference] = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize Watsonx.ai API client and models."""
        try:
            # Create credentials
            credentials = Credentials(
                url=self.settings.watsonx_url,
                api_key=self.settings.watsonx_api_key,
            )

            # Initialize API client
            self._api_client = APIClient(credentials)
            if self._api_client:
                self._api_client.set.default_project(self.settings.watsonx_project_id)  # type: ignore

            # Initialize embeddings model
            self._embeddings = Embeddings(
                model_id=self.settings.embedding_model,
                api_client=self._api_client,
                project_id=self.settings.watsonx_project_id,
            )

            # Initialize LLM
            self._llm = ModelInference(
                model_id=self.settings.llm_model,
                api_client=self._api_client,
                project_id=self.settings.watsonx_project_id,
            )

            logger.info("Watsonx.ai client initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Watsonx.ai client: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors

        Raises:
            Exception: If embedding generation fails
        """
        try:
            if not self._embeddings:
                raise RuntimeError("Embeddings model not initialized")

            logger.debug(f"Generating embeddings for {len(texts)} texts")
            
            # Generate embeddings
            result = self._embeddings.embed_documents(texts)
            
            logger.info(f"Successfully generated {len(result)} embeddings")
            return result

        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text.

        Args:
            text: Text string to embed

        Returns:
            Embedding vector

        Raises:
            Exception: If embedding generation fails
        """
        embeddings = self.generate_embeddings([text])
        return embeddings[0]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def generate_text(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> str:
        """Generate text using the LLM.

        Args:
            prompt: Input prompt for text generation
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional generation parameters

        Returns:
            Generated text

        Raises:
            Exception: If text generation fails
        """
        try:
            if not self._llm:
                raise RuntimeError("LLM model not initialized")

            # Set generation parameters
            params = {
                "max_new_tokens": max_tokens or self.settings.llm_max_tokens,
                "temperature": temperature or self.settings.llm_temperature,
                **kwargs,
            }

            logger.debug(f"Generating text with params: {params}")

            # Generate text
            result = self._llm.generate_text(prompt=prompt, params=params)

            logger.info("Successfully generated text")
            return result

        except Exception as e:
            logger.error(f"Failed to generate text: {e}")
            raise

    def generate_chat_response(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> str:
        """Generate chat response using the LLM.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional generation parameters

        Returns:
            Generated response text

        Raises:
            Exception: If chat generation fails
        """
        try:
            # Convert messages to prompt format
            prompt = self._format_chat_prompt(messages)
            
            # Generate response
            return self.generate_text(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs,
            )

        except Exception as e:
            logger.error(f"Failed to generate chat response: {e}")
            raise

    def _format_chat_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Format chat messages into a prompt string.

        Args:
            messages: List of message dictionaries

        Returns:
            Formatted prompt string
        """
        prompt_parts = []
        
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        
        prompt_parts.append("Assistant:")
        return "\n\n".join(prompt_parts)

    def health_check(self) -> bool:
        """Check if the Watsonx.ai client is healthy.

        Returns:
            True if healthy, False otherwise
        """
        try:
            # Try to generate a simple embedding
            test_embedding = self.generate_embedding("health check")
            return len(test_embedding) == self.settings.embedding_dimension
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

# Made with Bob
