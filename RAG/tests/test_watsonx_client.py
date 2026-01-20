"""Unit tests for Watsonx Client."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import List

from services.watsonx_client import WatsonxClient
from config.settings import Settings


@pytest.fixture
def mock_settings():
    """Create mock settings."""
    settings = Mock(spec=Settings)
    settings.watsonx_url = "https://us-south.ml.cloud.ibm.com"
    settings.watsonx_api_key = "test_api_key"
    settings.watsonx_project_id = "test_project_id"
    settings.embedding_model = "ibm/granite-embedding-278m-multilingual"
    settings.llm_model = "openai/gpt-oss-120b"
    settings.embedding_dimension = 768
    settings.llm_max_tokens = 512
    settings.llm_temperature = 0.7
    return settings


@pytest.fixture
def mock_api_client():
    """Create mock API client."""
    client = MagicMock()
    client.set.default_project = Mock()
    return client


@pytest.fixture
def mock_embeddings():
    """Create mock embeddings model."""
    embeddings = MagicMock()
    embeddings.embed_documents = Mock(return_value=[[0.1] * 768, [0.2] * 768])
    return embeddings


@pytest.fixture
def mock_llm():
    """Create mock LLM model."""
    llm = MagicMock()
    llm.generate_text = Mock(return_value="Generated response")
    return llm


class TestWatsonxClientInitialization:
    """Test Watsonx client initialization."""

    @patch('services.watsonx_client.ModelInference')
    @patch('services.watsonx_client.Embeddings')
    @patch('services.watsonx_client.APIClient')
    @patch('services.watsonx_client.Credentials')
    def test_successful_initialization(
        self, mock_credentials, mock_api_client_class, 
        mock_embeddings_class, mock_llm_class, mock_settings
    ):
        """Test successful client initialization."""
        # Setup
        mock_api_client = MagicMock()
        mock_api_client_class.return_value = mock_api_client
        mock_embeddings = MagicMock()
        mock_embeddings_class.return_value = mock_embeddings
        mock_llm = MagicMock()
        mock_llm_class.return_value = mock_llm
        
        # Execute
        client = WatsonxClient(mock_settings)
        
        # Verify
        mock_credentials.assert_called_once_with(
            url="https://us-south.ml.cloud.ibm.com",
            api_key="test_api_key",
        )
        mock_api_client_class.assert_called_once()
        mock_embeddings_class.assert_called_once()
        mock_llm_class.assert_called_once()
        assert client._api_client is not None
        assert client._embeddings is not None
        assert client._llm is not None

    @patch('services.watsonx_client.APIClient')
    @patch('services.watsonx_client.Credentials')
    def test_initialization_failure(self, mock_credentials, mock_api_client_class, mock_settings):
        """Test handling of initialization failure."""
        # Setup
        mock_api_client_class.side_effect = Exception("API initialization failed")
        
        # Execute & Verify
        with pytest.raises(Exception, match="API initialization failed"):
            WatsonxClient(mock_settings)


class TestWatsonxClientEmbeddings:
    """Test embedding generation."""

    @patch('services.watsonx_client.ModelInference')
    @patch('services.watsonx_client.Embeddings')
    @patch('services.watsonx_client.APIClient')
    @patch('services.watsonx_client.Credentials')
    def test_generate_embeddings_success(
        self, mock_credentials, mock_api_client_class,
        mock_embeddings_class, mock_llm_class, mock_settings
    ):
        """Test successful embedding generation."""
        # Setup
        mock_embeddings = MagicMock()
        mock_embeddings.embed_documents.return_value = [[0.1] * 768, [0.2] * 768]
        mock_embeddings_class.return_value = mock_embeddings
        mock_api_client_class.return_value = MagicMock()
        mock_llm_class.return_value = MagicMock()
        
        client = WatsonxClient(mock_settings)
        
        # Execute
        texts = ["text1", "text2"]
        embeddings = client.generate_embeddings(texts)
        
        # Verify
        assert len(embeddings) == 2
        assert len(embeddings[0]) == 768
        mock_embeddings.embed_documents.assert_called_once_with(texts)

    @patch('services.watsonx_client.ModelInference')
    @patch('services.watsonx_client.Embeddings')
    @patch('services.watsonx_client.APIClient')
    @patch('services.watsonx_client.Credentials')
    def test_generate_single_embedding(
        self, mock_credentials, mock_api_client_class,
        mock_embeddings_class, mock_llm_class, mock_settings
    ):
        """Test single embedding generation."""
        # Setup
        mock_embeddings = MagicMock()
        mock_embeddings.embed_documents.return_value = [[0.1] * 768]
        mock_embeddings_class.return_value = mock_embeddings
        mock_api_client_class.return_value = MagicMock()
        mock_llm_class.return_value = MagicMock()
        
        client = WatsonxClient(mock_settings)
        
        # Execute
        embedding = client.generate_embedding("test text")
        
        # Verify
        assert len(embedding) == 768
        mock_embeddings.embed_documents.assert_called_once_with(["test text"])

    @patch('services.watsonx_client.ModelInference')
    @patch('services.watsonx_client.Embeddings')
    @patch('services.watsonx_client.APIClient')
    @patch('services.watsonx_client.Credentials')
    def test_generate_embeddings_without_model(
        self, mock_credentials, mock_api_client_class,
        mock_embeddings_class, mock_llm_class, mock_settings
    ):
        """Test embedding generation fails without model."""
        # Setup
        mock_embeddings_class.return_value = MagicMock()
        mock_api_client_class.return_value = MagicMock()
        mock_llm_class.return_value = MagicMock()
        
        client = WatsonxClient(mock_settings)
        client._embeddings = None
        
        # Execute & Verify - expect RetryError wrapping RuntimeError
        with pytest.raises(Exception):  # Will be RetryError
            client.generate_embeddings(["test"])

    @patch('services.watsonx_client.ModelInference')
    @patch('services.watsonx_client.Embeddings')
    @patch('services.watsonx_client.APIClient')
    @patch('services.watsonx_client.Credentials')
    def test_generate_embeddings_retry_on_failure(
        self, mock_credentials, mock_api_client_class,
        mock_embeddings_class, mock_llm_class, mock_settings
    ):
        """Test embedding generation retries on failure."""
        # Setup
        mock_embeddings = MagicMock()
        # Fail twice, then succeed
        mock_embeddings.embed_documents.side_effect = [
            Exception("Temporary failure"),
            Exception("Temporary failure"),
            [[0.1] * 768],
        ]
        mock_embeddings_class.return_value = mock_embeddings
        mock_api_client_class.return_value = MagicMock()
        mock_llm_class.return_value = MagicMock()
        
        client = WatsonxClient(mock_settings)
        
        # Execute
        embeddings = client.generate_embeddings(["test"])
        
        # Verify - should succeed after retries
        assert len(embeddings) == 1
        assert mock_embeddings.embed_documents.call_count == 3


class TestWatsonxClientTextGeneration:
    """Test text generation."""

    @patch('services.watsonx_client.ModelInference')
    @patch('services.watsonx_client.Embeddings')
    @patch('services.watsonx_client.APIClient')
    @patch('services.watsonx_client.Credentials')
    def test_generate_text_success(
        self, mock_credentials, mock_api_client_class,
        mock_embeddings_class, mock_llm_class, mock_settings
    ):
        """Test successful text generation."""
        # Setup
        mock_llm = MagicMock()
        mock_llm.generate_text.return_value = "Generated response"
        mock_llm_class.return_value = mock_llm
        mock_embeddings_class.return_value = MagicMock()
        mock_api_client_class.return_value = MagicMock()
        
        client = WatsonxClient(mock_settings)
        
        # Execute
        response = client.generate_text("Test prompt")
        
        # Verify
        assert response == "Generated response"
        mock_llm.generate_text.assert_called_once()

    @patch('services.watsonx_client.ModelInference')
    @patch('services.watsonx_client.Embeddings')
    @patch('services.watsonx_client.APIClient')
    @patch('services.watsonx_client.Credentials')
    def test_generate_text_with_custom_params(
        self, mock_credentials, mock_api_client_class,
        mock_embeddings_class, mock_llm_class, mock_settings
    ):
        """Test text generation with custom parameters."""
        # Setup
        mock_llm = MagicMock()
        mock_llm.generate_text.return_value = "Generated response"
        mock_llm_class.return_value = mock_llm
        mock_embeddings_class.return_value = MagicMock()
        mock_api_client_class.return_value = MagicMock()
        
        client = WatsonxClient(mock_settings)
        
        # Execute
        response = client.generate_text(
            "Test prompt",
            max_tokens=256,
            temperature=0.5,
        )
        
        # Verify
        assert response == "Generated response"
        call_args = mock_llm.generate_text.call_args
        assert call_args[1]["params"]["max_new_tokens"] == 256
        assert call_args[1]["params"]["temperature"] == 0.5

    @patch('services.watsonx_client.ModelInference')
    @patch('services.watsonx_client.Embeddings')
    @patch('services.watsonx_client.APIClient')
    @patch('services.watsonx_client.Credentials')
    def test_generate_text_without_model(
        self, mock_credentials, mock_api_client_class,
        mock_embeddings_class, mock_llm_class, mock_settings
    ):
        """Test text generation fails without model."""
        # Setup
        mock_llm_class.return_value = MagicMock()
        mock_embeddings_class.return_value = MagicMock()
        mock_api_client_class.return_value = MagicMock()
        
        client = WatsonxClient(mock_settings)
        client._llm = None
        
        # Execute & Verify - expect RetryError wrapping RuntimeError
        with pytest.raises(Exception):  # Will be RetryError
            client.generate_text("test")


class TestWatsonxClientChatGeneration:
    """Test chat response generation."""

    @patch('services.watsonx_client.ModelInference')
    @patch('services.watsonx_client.Embeddings')
    @patch('services.watsonx_client.APIClient')
    @patch('services.watsonx_client.Credentials')
    def test_generate_chat_response(
        self, mock_credentials, mock_api_client_class,
        mock_embeddings_class, mock_llm_class, mock_settings
    ):
        """Test chat response generation."""
        # Setup
        mock_llm = MagicMock()
        mock_llm.generate_text.return_value = "Chat response"
        mock_llm_class.return_value = mock_llm
        mock_embeddings_class.return_value = MagicMock()
        mock_api_client_class.return_value = MagicMock()
        
        client = WatsonxClient(mock_settings)
        
        # Execute
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"},
        ]
        response = client.generate_chat_response(messages)
        
        # Verify
        assert response == "Chat response"
        mock_llm.generate_text.assert_called_once()

    @patch('services.watsonx_client.ModelInference')
    @patch('services.watsonx_client.Embeddings')
    @patch('services.watsonx_client.APIClient')
    @patch('services.watsonx_client.Credentials')
    def test_format_chat_prompt(
        self, mock_credentials, mock_api_client_class,
        mock_embeddings_class, mock_llm_class, mock_settings
    ):
        """Test chat prompt formatting."""
        # Setup
        mock_llm_class.return_value = MagicMock()
        mock_embeddings_class.return_value = MagicMock()
        mock_api_client_class.return_value = MagicMock()
        
        client = WatsonxClient(mock_settings)
        
        # Execute
        messages = [
            {"role": "system", "content": "System message"},
            {"role": "user", "content": "User message"},
            {"role": "assistant", "content": "Assistant message"},
        ]
        prompt = client._format_chat_prompt(messages)
        
        # Verify
        assert "System: System message" in prompt
        assert "User: User message" in prompt
        assert "Assistant: Assistant message" in prompt
        assert prompt.endswith("Assistant:")


class TestWatsonxClientHealth:
    """Test health check."""

    @patch('services.watsonx_client.ModelInference')
    @patch('services.watsonx_client.Embeddings')
    @patch('services.watsonx_client.APIClient')
    @patch('services.watsonx_client.Credentials')
    def test_health_check_healthy(
        self, mock_credentials, mock_api_client_class,
        mock_embeddings_class, mock_llm_class, mock_settings
    ):
        """Test health check when healthy."""
        # Setup
        mock_embeddings = MagicMock()
        mock_embeddings.embed_documents.return_value = [[0.1] * 768]
        mock_embeddings_class.return_value = mock_embeddings
        mock_llm_class.return_value = MagicMock()
        mock_api_client_class.return_value = MagicMock()
        
        client = WatsonxClient(mock_settings)
        
        # Execute
        is_healthy = client.health_check()
        
        # Verify
        assert is_healthy is True

    @patch('services.watsonx_client.ModelInference')
    @patch('services.watsonx_client.Embeddings')
    @patch('services.watsonx_client.APIClient')
    @patch('services.watsonx_client.Credentials')
    def test_health_check_unhealthy(
        self, mock_credentials, mock_api_client_class,
        mock_embeddings_class, mock_llm_class, mock_settings
    ):
        """Test health check when unhealthy."""
        # Setup
        mock_embeddings = MagicMock()
        mock_embeddings.embed_documents.side_effect = Exception("Connection failed")
        mock_embeddings_class.return_value = mock_embeddings
        mock_llm_class.return_value = MagicMock()
        mock_api_client_class.return_value = MagicMock()
        
        client = WatsonxClient(mock_settings)
        
        # Execute
        is_healthy = client.health_check()
        
        # Verify
        assert is_healthy is False

    @patch('services.watsonx_client.ModelInference')
    @patch('services.watsonx_client.Embeddings')
    @patch('services.watsonx_client.APIClient')
    @patch('services.watsonx_client.Credentials')
    def test_health_check_wrong_dimension(
        self, mock_credentials, mock_api_client_class,
        mock_embeddings_class, mock_llm_class, mock_settings
    ):
        """Test health check fails with wrong embedding dimension."""
        # Setup
        mock_embeddings = MagicMock()
        mock_embeddings.embed_documents.return_value = [[0.1] * 512]  # Wrong dimension
        mock_embeddings_class.return_value = mock_embeddings
        mock_llm_class.return_value = MagicMock()
        mock_api_client_class.return_value = MagicMock()
        
        client = WatsonxClient(mock_settings)
        
        # Execute
        is_healthy = client.health_check()
        
        # Verify
        assert is_healthy is False


# Made with Bob