"""Tests for embedding service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import numpy as np

from services.embedding_service import EmbeddingService
from models import EmbeddingModel, VectorDocument


class TestEmbeddingService:
    """Test embedding service."""

    @pytest.fixture
    def embedding_service(self):
        """Create embedding service instance."""
        return EmbeddingService()

    @pytest.fixture
    def mock_openai_client(self):
        """Mock OpenAI client."""
        with patch("services.embedding_service.openai.AsyncOpenAI") as mock:
            client = AsyncMock()
            mock.return_value = client
            yield client

    @pytest.fixture
    def mock_sentence_transformer(self):
        """Mock sentence transformer."""
        with patch("services.embedding_service.SentenceTransformer") as mock:
            transformer = MagicMock()
            mock.return_value = transformer
            yield transformer

    async def test_initialize(
        self, embedding_service, mock_openai_client, mock_sentence_transformer
    ):
        """Test service initialization."""
        with patch("core.config.settings") as mock_settings:
            mock_settings.openai_api_key = "test-key"

            await embedding_service.initialize()

            assert embedding_service.openai_client is not None
            assert embedding_service.sentence_transformer is not None

    async def test_initialize_without_openai_key(
        self, embedding_service, mock_sentence_transformer
    ):
        """Test initialization without OpenAI key."""
        with patch("core.config.settings") as mock_settings:
            mock_settings.openai_api_key = None

            await embedding_service.initialize()

            assert embedding_service.openai_client is None
            assert embedding_service.sentence_transformer is not None

    async def test_generate_openai_embedding(
        self, embedding_service, mock_openai_client
    ):
        """Test generating OpenAI embedding."""
        embedding_service.openai_client = mock_openai_client

        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1, 0.2, 0.3])]
        mock_openai_client.embeddings.create.return_value = mock_response

        result = await embedding_service.generate_embedding(
            "test text", EmbeddingModel.OPENAI_ADA_002
        )

        assert result == [0.1, 0.2, 0.3]
        mock_openai_client.embeddings.create.assert_called_once()

    async def test_generate_sentence_transformer_embedding(
        self, embedding_service, mock_sentence_transformer
    ):
        """Test generating sentence transformer embedding."""
        embedding_service.sentence_transformer = mock_sentence_transformer

        # Mock sentence transformer response
        mock_embedding = np.array([0.1, 0.2, 0.3])
        mock_sentence_transformer.encode.return_value = mock_embedding

        with patch("asyncio.get_event_loop") as mock_loop:
            mock_executor = AsyncMock()
            mock_executor.return_value = mock_embedding
            mock_loop.return_value.run_in_executor = mock_executor

            result = await embedding_service.generate_embedding(
                "test text", EmbeddingModel.SENTENCE_TRANSFORMERS
            )

            assert result == [0.1, 0.2, 0.3]

    async def test_generate_embedding_empty_text(self, embedding_service):
        """Test generating embedding with empty text fails."""
        with pytest.raises(ValueError, match="Text cannot be empty"):
            await embedding_service.generate_embedding(
                "", EmbeddingModel.OPENAI_ADA_002
            )

    async def test_generate_embeddings_batch(
        self, embedding_service, mock_openai_client
    ):
        """Test generating embeddings for multiple texts."""
        embedding_service.openai_client = mock_openai_client

        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.data = [
            MagicMock(embedding=[0.1, 0.2, 0.3]),
            MagicMock(embedding=[0.4, 0.5, 0.6]),
        ]
        mock_openai_client.embeddings.create.return_value = mock_response

        texts = ["text 1", "text 2"]
        results = await embedding_service.generate_embeddings(
            texts, EmbeddingModel.OPENAI_ADA_002
        )

        assert len(results) == 2
        assert results[0] == [0.1, 0.2, 0.3]
        assert results[1] == [0.4, 0.5, 0.6]

    async def test_embed_document(self, embedding_service, mock_openai_client):
        """Test embedding a document."""
        embedding_service.openai_client = mock_openai_client

        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1, 0.2, 0.3])]
        mock_openai_client.embeddings.create.return_value = mock_response

        doc = VectorDocument(
            id="test-doc",
            content="test content",
            metadata={"type": "test"},
        )

        result = await embedding_service.embed_document(
            doc, EmbeddingModel.OPENAI_ADA_002
        )

        assert result.embedding == [0.1, 0.2, 0.3]
        assert result.id == "test-doc"
        assert result.content == "test content"

    async def test_embed_documents_batch(self, embedding_service, mock_openai_client):
        """Test embedding multiple documents."""
        embedding_service.openai_client = mock_openai_client

        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.data = [
            MagicMock(embedding=[0.1, 0.2, 0.3]),
            MagicMock(embedding=[0.4, 0.5, 0.6]),
        ]
        mock_openai_client.embeddings.create.return_value = mock_response

        docs = [
            VectorDocument(id="doc1", content="content 1", metadata={}),
            VectorDocument(id="doc2", content="content 2", metadata={}),
        ]

        results = await embedding_service.embed_documents(
            docs, EmbeddingModel.OPENAI_ADA_002
        )

        assert len(results) == 2
        assert results[0].embedding == [0.1, 0.2, 0.3]
        assert results[1].embedding == [0.4, 0.5, 0.6]

    def test_get_model_dimension(self, embedding_service):
        """Test getting model dimensions."""
        assert (
            embedding_service.get_model_dimension(EmbeddingModel.OPENAI_ADA_002) == 1536
        )
        assert (
            embedding_service.get_model_dimension(EmbeddingModel.OPENAI_3_SMALL) == 1536
        )
        assert (
            embedding_service.get_model_dimension(EmbeddingModel.OPENAI_3_LARGE) == 3072
        )
        assert (
            embedding_service.get_model_dimension(EmbeddingModel.SENTENCE_TRANSFORMERS)
            == 384
        )

    async def test_calculate_similarity(self, embedding_service):
        """Test calculating similarity between embeddings."""
        # Identical vectors should have similarity 1.0
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        similarity = await embedding_service.calculate_similarity(vec1, vec2)
        assert abs(similarity - 1.0) < 0.001

        # Orthogonal vectors should have similarity 0.5 (normalized cosine)
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        similarity = await embedding_service.calculate_similarity(vec1, vec2)
        assert abs(similarity - 0.5) < 0.001

        # Opposite vectors should have similarity 0.0
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [-1.0, 0.0, 0.0]
        similarity = await embedding_service.calculate_similarity(vec1, vec2)
        assert abs(similarity - 0.0) < 0.001

    async def test_calculate_similarity_different_dimensions(self, embedding_service):
        """Test similarity calculation with different dimensions fails."""
        vec1 = [1.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]

        with pytest.raises(ValueError, match="Embeddings must have the same dimension"):
            await embedding_service.calculate_similarity(vec1, vec2)

    async def test_health_check(
        self, embedding_service, mock_openai_client, mock_sentence_transformer
    ):
        """Test health check."""
        embedding_service.openai_client = mock_openai_client
        embedding_service.sentence_transformer = mock_sentence_transformer

        # Mock successful embedding generation
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1, 0.2, 0.3])]
        mock_openai_client.embeddings.create.return_value = mock_response

        mock_embedding = np.array([0.1, 0.2, 0.3])
        mock_sentence_transformer.encode.return_value = mock_embedding

        with patch("asyncio.get_event_loop") as mock_loop:
            mock_executor = AsyncMock()
            mock_executor.return_value = mock_embedding
            mock_loop.return_value.run_in_executor = mock_executor

            status = await embedding_service.health_check()

            assert status["openai_available"] is True
            assert status["sentence_transformer_available"] is True
            assert status["openai_working"] is True
            assert status["sentence_transformer_working"] is True
            assert len(status["models_supported"]) > 0

    async def test_health_check_no_clients(self, embedding_service):
        """Test health check with no clients initialized."""
        status = await embedding_service.health_check()

        assert status["openai_available"] is False
        assert status["sentence_transformer_available"] is False
        assert status["openai_working"] is False
        assert status["sentence_transformer_working"] is False

    async def test_unsupported_model(self, embedding_service):
        """Test using unsupported model raises error."""

        # Create a mock unsupported model
        class UnsupportedModel:
            value = "unsupported-model"

        with pytest.raises(ValueError, match="Unsupported embedding model"):
            await embedding_service.generate_embedding("test", UnsupportedModel())

    async def test_openai_not_initialized(self, embedding_service):
        """Test OpenAI embedding without initialized client."""
        embedding_service.openai_client = None

        with pytest.raises(RuntimeError, match="OpenAI client not initialized"):
            await embedding_service.generate_embedding(
                "test", EmbeddingModel.OPENAI_ADA_002
            )

    async def test_sentence_transformer_not_initialized(self, embedding_service):
        """Test sentence transformer embedding without initialized model."""
        embedding_service.sentence_transformer = None

        with pytest.raises(RuntimeError, match="Sentence transformer not initialized"):
            await embedding_service.generate_embedding(
                "test", EmbeddingModel.SENTENCE_TRANSFORMERS
            )
