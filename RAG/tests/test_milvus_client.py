"""Unit tests for Milvus Client."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import List

from services.milvus_client import MilvusClient
from config.settings import Settings


@pytest.fixture
def mock_settings():
    """Create mock settings."""
    settings = Mock(spec=Settings)
    settings.milvus_host = "localhost"
    settings.milvus_port = 19530
    settings.milvus_collection_name = "test_collection"
    settings.milvus_metric_type = "COSINE"
    settings.embedding_dimension = 768
    settings.rag_top_k = 5
    settings.rag_score_threshold = 0.7
    return settings


@pytest.fixture
def mock_collection():
    """Create mock Milvus collection."""
    collection = MagicMock()
    collection.num_entities = 100
    collection.load = Mock()
    collection.insert = Mock()
    collection.flush = Mock()
    collection.delete = Mock()
    collection.drop = Mock()
    collection.search = Mock()
    return collection


class TestMilvusClientInitialization:
    """Test Milvus client initialization."""

    @patch('services.milvus_client.connections')
    @patch('services.milvus_client.utility')
    @patch('services.milvus_client.Collection')
    def test_successful_initialization_existing_collection(
        self, mock_collection_class, mock_utility, mock_connections, mock_settings
    ):
        """Test successful initialization with existing collection."""
        # Setup
        mock_utility.has_collection.return_value = True
        mock_collection = MagicMock()
        mock_collection_class.return_value = mock_collection
        
        # Execute
        client = MilvusClient(mock_settings)
        
        # Verify
        mock_connections.connect.assert_called_once_with(
            alias="default",
            host="localhost",
            port=19530,
        )
        mock_utility.has_collection.assert_called_once_with("test_collection")
        mock_collection.load.assert_called_once()
        assert client.collection is not None

    @patch('services.milvus_client.connections')
    @patch('services.milvus_client.utility')
    @patch('services.milvus_client.Collection')
    def test_successful_initialization_new_collection(
        self, mock_collection_class, mock_utility, mock_connections, mock_settings
    ):
        """Test successful initialization creating new collection."""
        # Setup
        mock_utility.has_collection.return_value = False
        mock_collection = MagicMock()
        mock_collection_class.return_value = mock_collection
        
        # Execute
        client = MilvusClient(mock_settings)
        
        # Verify
        mock_connections.connect.assert_called_once()
        mock_utility.has_collection.assert_called_once()
        mock_collection.create_index.assert_called_once()
        mock_collection.load.assert_called_once()

    @patch('services.milvus_client.connections')
    def test_connection_failure(self, mock_connections, mock_settings):
        """Test handling of connection failure."""
        # Setup
        mock_connections.connect.side_effect = Exception("Connection failed")
        
        # Execute & Verify
        with pytest.raises(Exception, match="Connection failed"):
            MilvusClient(mock_settings)


class TestMilvusClientInsert:
    """Test document insertion."""

    @patch('services.milvus_client.connections')
    @patch('services.milvus_client.utility')
    @patch('services.milvus_client.Collection')
    def test_successful_insert(
        self, mock_collection_class, mock_utility, mock_connections, mock_settings
    ):
        """Test successful document insertion."""
        # Setup
        mock_utility.has_collection.return_value = True
        mock_collection = MagicMock()
        mock_collection_class.return_value = mock_collection
        
        client = MilvusClient(mock_settings)
        
        ids = ["id1", "id2"]
        texts = ["text1", "text2"]
        vectors = [[0.1] * 768, [0.2] * 768]
        sources = ["source1", "source2"]
        
        # Execute
        client.insert(ids, texts, vectors, sources)
        
        # Verify
        mock_collection.insert.assert_called_once()
        mock_collection.flush.assert_called_once()

    @patch('services.milvus_client.connections')
    @patch('services.milvus_client.utility')
    @patch('services.milvus_client.Collection')
    def test_insert_without_collection(
        self, mock_collection_class, mock_utility, mock_connections, mock_settings
    ):
        """Test insert fails when collection not initialized."""
        # Setup
        mock_utility.has_collection.return_value = True
        mock_collection_class.return_value = MagicMock()
        
        client = MilvusClient(mock_settings)
        client.collection = None
        
        # Execute & Verify
        with pytest.raises(RuntimeError, match="Collection not initialized"):
            client.insert(["id1"], ["text1"], [[0.1] * 768], ["source1"])

    @patch('services.milvus_client.connections')
    @patch('services.milvus_client.utility')
    @patch('services.milvus_client.Collection')
    def test_insert_failure(
        self, mock_collection_class, mock_utility, mock_connections, mock_settings
    ):
        """Test handling of insertion failure."""
        # Setup
        mock_utility.has_collection.return_value = True
        mock_collection = MagicMock()
        mock_collection.insert.side_effect = Exception("Insert failed")
        mock_collection_class.return_value = mock_collection
        
        client = MilvusClient(mock_settings)
        
        # Execute & Verify
        with pytest.raises(Exception, match="Insert failed"):
            client.insert(["id1"], ["text1"], [[0.1] * 768], ["source1"])


class TestMilvusClientSearch:
    """Test document search."""

    @patch('services.milvus_client.connections')
    @patch('services.milvus_client.utility')
    @patch('services.milvus_client.Collection')
    def test_successful_search(
        self, mock_collection_class, mock_utility, mock_connections, mock_settings
    ):
        """Test successful document search."""
        # Setup
        mock_utility.has_collection.return_value = True
        mock_collection = MagicMock()
        
        # Mock search results
        mock_hit = MagicMock()
        mock_hit.score = 0.9
        mock_hit.entity.get.side_effect = lambda key: {
            "id": "id1",
            "text": "test text",
            "source": "test.txt",
            "timestamp": 1234567890,
        }.get(key)
        
        mock_collection.search.return_value = [[mock_hit]]
        mock_collection_class.return_value = mock_collection
        
        client = MilvusClient(mock_settings)
        
        # Execute
        results = client.search([0.1] * 768, top_k=5)
        
        # Verify
        assert len(results) == 1
        assert results[0]["id"] == "id1"
        assert results[0]["text"] == "test text"
        assert results[0]["score"] == 0.9
        mock_collection.search.assert_called_once()

    @patch('services.milvus_client.connections')
    @patch('services.milvus_client.utility')
    @patch('services.milvus_client.Collection')
    def test_search_with_score_threshold(
        self, mock_collection_class, mock_utility, mock_connections, mock_settings
    ):
        """Test search filters by score threshold."""
        # Setup
        mock_utility.has_collection.return_value = True
        mock_collection = MagicMock()
        
        # Mock hits with different scores
        mock_hit1 = MagicMock()
        mock_hit1.score = 0.9
        mock_hit1.entity.get.side_effect = lambda key: {
            "id": "id1", "text": "text1", "source": "s1", "timestamp": 123
        }.get(key)
        
        mock_hit2 = MagicMock()
        mock_hit2.score = 0.5  # Below threshold
        mock_hit2.entity.get.side_effect = lambda key: {
            "id": "id2", "text": "text2", "source": "s2", "timestamp": 124
        }.get(key)
        
        mock_collection.search.return_value = [[mock_hit1, mock_hit2]]
        mock_collection_class.return_value = mock_collection
        
        client = MilvusClient(mock_settings)
        
        # Execute
        results = client.search([0.1] * 768, score_threshold=0.7)
        
        # Verify - only hit1 should be returned
        assert len(results) == 1
        assert results[0]["id"] == "id1"

    @patch('services.milvus_client.connections')
    @patch('services.milvus_client.utility')
    @patch('services.milvus_client.Collection')
    def test_search_without_collection(
        self, mock_collection_class, mock_utility, mock_connections, mock_settings
    ):
        """Test search fails when collection not initialized."""
        # Setup
        mock_utility.has_collection.return_value = True
        mock_collection_class.return_value = MagicMock()
        
        client = MilvusClient(mock_settings)
        client.collection = None
        
        # Execute & Verify
        with pytest.raises(RuntimeError, match="Collection not initialized"):
            client.search([0.1] * 768)


class TestMilvusClientDelete:
    """Test document deletion."""

    @patch('services.milvus_client.connections')
    @patch('services.milvus_client.utility')
    @patch('services.milvus_client.Collection')
    def test_successful_delete(
        self, mock_collection_class, mock_utility, mock_connections, mock_settings
    ):
        """Test successful document deletion."""
        # Setup
        mock_utility.has_collection.return_value = True
        mock_collection = MagicMock()
        mock_collection_class.return_value = mock_collection
        
        client = MilvusClient(mock_settings)
        
        # Execute
        client.delete(["id1", "id2"])
        
        # Verify
        mock_collection.delete.assert_called_once()
        mock_collection.flush.assert_called_once()


class TestMilvusClientStats:
    """Test statistics retrieval."""

    @patch('services.milvus_client.connections')
    @patch('services.milvus_client.utility')
    @patch('services.milvus_client.Collection')
    def test_get_stats(
        self, mock_collection_class, mock_utility, mock_connections, mock_settings
    ):
        """Test getting collection statistics."""
        # Setup
        mock_utility.has_collection.return_value = True
        mock_collection = MagicMock()
        mock_collection.num_entities = 100
        mock_collection_class.return_value = mock_collection
        
        client = MilvusClient(mock_settings)
        
        # Execute
        stats = client.get_stats()
        
        # Verify
        assert stats["collection_name"] == "test_collection"
        assert stats["num_entities"] == 100
        assert stats["metric_type"] == "COSINE"
        assert stats["dimension"] == 768


class TestMilvusClientClear:
    """Test collection clearing."""

    @patch('services.milvus_client.connections')
    @patch('services.milvus_client.utility')
    @patch('services.milvus_client.Collection')
    def test_clear_collection(
        self, mock_collection_class, mock_utility, mock_connections, mock_settings
    ):
        """Test clearing collection."""
        # Setup
        mock_utility.has_collection.return_value = True
        mock_collection = MagicMock()
        mock_collection_class.return_value = mock_collection
        
        client = MilvusClient(mock_settings)
        
        # Execute
        client.clear_collection()
        
        # Verify
        mock_collection.drop.assert_called_once()
        # Should create new collection
        assert mock_collection.create_index.call_count >= 1


class TestMilvusClientHealth:
    """Test health check."""

    @patch('services.milvus_client.connections')
    @patch('services.milvus_client.utility')
    @patch('services.milvus_client.Collection')
    def test_health_check_healthy(
        self, mock_collection_class, mock_utility, mock_connections, mock_settings
    ):
        """Test health check when healthy."""
        # Setup
        mock_utility.has_collection.return_value = True
        mock_collection = MagicMock()
        mock_collection.num_entities = 100
        mock_collection_class.return_value = mock_collection
        
        client = MilvusClient(mock_settings)
        
        # Execute
        is_healthy = client.health_check()
        
        # Verify
        assert is_healthy is True

    @patch('services.milvus_client.connections')
    @patch('services.milvus_client.utility')
    @patch('services.milvus_client.Collection')
    def test_health_check_unhealthy(
        self, mock_collection_class, mock_utility, mock_connections, mock_settings
    ):
        """Test health check when unhealthy."""
        # Setup
        mock_utility.has_collection.return_value = True
        mock_collection = MagicMock()
        type(mock_collection).num_entities = property(
            lambda self: (_ for _ in ()).throw(Exception("Connection lost"))
        )
        mock_collection_class.return_value = mock_collection
        
        client = MilvusClient(mock_settings)
        
        # Execute
        is_healthy = client.health_check()
        
        # Verify
        assert is_healthy is False


class TestMilvusClientDisconnect:
    """Test disconnection."""

    @patch('services.milvus_client.connections')
    @patch('services.milvus_client.utility')
    @patch('services.milvus_client.Collection')
    def test_disconnect(
        self, mock_collection_class, mock_utility, mock_connections, mock_settings
    ):
        """Test disconnecting from Milvus."""
        # Setup
        mock_utility.has_collection.return_value = True
        mock_collection_class.return_value = MagicMock()
        
        client = MilvusClient(mock_settings)
        
        # Execute
        client.disconnect()
        
        # Verify
        mock_connections.disconnect.assert_called_once_with("default")


# Made with Bob