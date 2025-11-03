"""Embedding generation service for SamvadQL."""

import asyncio
from typing import List, Optional, Dict, Any
import numpy as np
from core.config import settings
from models import EmbeddingModel, VectorDocument
import structlog

# Optional imports with fallbacks
try:
    import openai

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None

try:
    from sentence_transformers import SentenceTransformer

    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None

logger = structlog.get_logger(__name__)


class EmbeddingService:
    """Service for generating text embeddings."""

    def __init__(self):
        self.openai_client = None
        self.sentence_transformer = None
        self._model_dimensions = {
            EmbeddingModel.OPENAI_ADA_002: 1536,
            EmbeddingModel.OPENAI_3_SMALL: 1536,
            EmbeddingModel.OPENAI_3_LARGE: 3072,
            EmbeddingModel.SENTENCE_TRANSFORMERS: 384,
        }

    async def initialize(self) -> None:
        """Initialize embedding models."""
        try:
            # Initialize OpenAI client if API key is available and openai is installed
            if OPENAI_AVAILABLE and settings.openai_api_key:
                self.openai_client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
                logger.info("OpenAI embedding client initialized")
            elif not OPENAI_AVAILABLE:
                logger.warning("OpenAI package not available")

            # Initialize sentence transformer model in a thread pool if available
            if SENTENCE_TRANSFORMERS_AVAILABLE:
                await asyncio.get_event_loop().run_in_executor(
                    None, self._init_sentence_transformer
                )
                logger.info("Sentence transformer model initialized")
            else:
                logger.warning("Sentence transformers package not available")

        except Exception as e:
            logger.error("Failed to initialize embedding service", error=str(e))
            raise

    def _init_sentence_transformer(self) -> None:
        """Initialize sentence transformer model (runs in thread pool)."""
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            self.sentence_transformer = SentenceTransformer(
                "sentence-transformers/all-MiniLM-L6-v2"
            )

    async def generate_embedding(
        self, text: str, model: EmbeddingModel = EmbeddingModel.OPENAI_ADA_002
    ) -> List[float]:
        """Generate embedding for a single text."""
        if not text or text.isspace():
            raise ValueError("Text cannot be empty")

        try:
            if model in [
                EmbeddingModel.OPENAI_ADA_002,
                EmbeddingModel.OPENAI_3_SMALL,
                EmbeddingModel.OPENAI_3_LARGE,
            ]:
                return await self._generate_openai_embedding(text, model)
            elif model == EmbeddingModel.SENTENCE_TRANSFORMERS:
                return await self._generate_sentence_transformer_embedding(text)
            else:
                raise ValueError(f"Unsupported embedding model: {model}")

        except Exception as e:
            logger.error(
                "Failed to generate embedding",
                text_length=len(text),
                model=model.value,
                error=str(e),
            )
            raise

    async def generate_embeddings(
        self,
        texts: List[str],
        model: EmbeddingModel = EmbeddingModel.OPENAI_ADA_002,
        batch_size: int = 100,
    ) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        if not texts:
            return []

        # Validate all texts
        for i, text in enumerate(texts):
            if not text or text.isspace():
                raise ValueError(f"Text at index {i} cannot be empty")

        try:
            # Process in batches to avoid rate limits
            embeddings = []
            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]

                if model in [
                    EmbeddingModel.OPENAI_ADA_002,
                    EmbeddingModel.OPENAI_3_SMALL,
                    EmbeddingModel.OPENAI_3_LARGE,
                ]:
                    batch_embeddings = await self._generate_openai_embeddings_batch(
                        batch, model
                    )
                elif model == EmbeddingModel.SENTENCE_TRANSFORMERS:
                    batch_embeddings = (
                        await self._generate_sentence_transformer_embeddings_batch(
                            batch
                        )
                    )
                else:
                    raise ValueError(f"Unsupported embedding model: {model}")

                embeddings.extend(batch_embeddings)

                # Add small delay between batches to respect rate limits
                if i + batch_size < len(texts):
                    await asyncio.sleep(0.1)

            return embeddings

        except Exception as e:
            logger.error(
                "Failed to generate batch embeddings",
                text_count=len(texts),
                model=model.value,
                error=str(e),
            )
            raise

    async def embed_document(
        self,
        document: VectorDocument,
        model: EmbeddingModel = EmbeddingModel.OPENAI_ADA_002,
    ) -> VectorDocument:
        """Generate embedding for a document and return updated document."""
        embedding = await self.generate_embedding(document.content, model)
        document.embedding = embedding
        return document

    async def embed_documents(
        self,
        documents: List[VectorDocument],
        model: EmbeddingModel = EmbeddingModel.OPENAI_ADA_002,
    ) -> List[VectorDocument]:
        """Generate embeddings for multiple documents."""
        texts = [doc.content for doc in documents]
        embeddings = await self.generate_embeddings(texts, model)

        for doc, embedding in zip(documents, embeddings):
            doc.embedding = embedding

        return documents

    def get_model_dimension(self, model: EmbeddingModel) -> int:
        """Get the dimension of embeddings for a specific model."""
        return self._model_dimensions.get(model, 1536)

    async def _generate_openai_embedding(
        self, text: str, model: EmbeddingModel
    ) -> List[float]:
        """Generate OpenAI embedding for a single text."""
        if not self.openai_client:
            raise RuntimeError("OpenAI client not initialized")

        response = await self.openai_client.embeddings.create(
            model=model.value, input=text, encoding_format="float"
        )

        return response.data[0].embedding

    async def _generate_openai_embeddings_batch(
        self, texts: List[str], model: EmbeddingModel
    ) -> List[List[float]]:
        """Generate OpenAI embeddings for multiple texts."""
        if not self.openai_client:
            raise RuntimeError("OpenAI client not initialized")

        response = await self.openai_client.embeddings.create(
            model=model.value, input=texts, encoding_format="float"
        )

        return [data.embedding for data in response.data]

    async def _generate_sentence_transformer_embedding(self, text: str) -> List[float]:
        """Generate sentence transformer embedding for a single text."""
        if not self.sentence_transformer:
            raise RuntimeError("Sentence transformer not initialized")

        # Run in thread pool to avoid blocking
        embedding = await asyncio.get_event_loop().run_in_executor(
            None, self.sentence_transformer.encode, text
        )

        return embedding.tolist()

    async def _generate_sentence_transformer_embeddings_batch(
        self, texts: List[str]
    ) -> List[List[float]]:
        """Generate sentence transformer embeddings for multiple texts."""
        if not self.sentence_transformer:
            raise RuntimeError("Sentence transformer not initialized")

        # Run in thread pool to avoid blocking
        embeddings = await asyncio.get_event_loop().run_in_executor(
            None, self.sentence_transformer.encode, texts
        )

        return embeddings.tolist()

    async def calculate_similarity(
        self, embedding1: List[float], embedding2: List[float]
    ) -> float:
        """Calculate cosine similarity between two embeddings."""
        if len(embedding1) != len(embedding2):
            raise ValueError("Embeddings must have the same dimension")

        # Convert to numpy arrays for efficient computation
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        # Calculate cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = dot_product / (norm1 * norm2)

        # Ensure result is between 0 and 1
        return max(0.0, min(1.0, (similarity + 1) / 2))

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on embedding service."""
        status = {
            "openai_available": self.openai_client is not None,
            "sentence_transformer_available": self.sentence_transformer is not None,
            "models_supported": [model.value for model in EmbeddingModel],
        }

        # Test embedding generation if possible
        try:
            if self.sentence_transformer:
                test_embedding = await self.generate_embedding(
                    "test", EmbeddingModel.SENTENCE_TRANSFORMERS
                )
                status["sentence_transformer_working"] = len(test_embedding) > 0
            else:
                status["sentence_transformer_working"] = False

            if self.openai_client:
                # Only test if we have an API key
                test_embedding = await self.generate_embedding(
                    "test", EmbeddingModel.OPENAI_ADA_002
                )
                status["openai_working"] = len(test_embedding) > 0
            else:
                status["openai_working"] = False

        except Exception as e:
            logger.warning("Embedding health check failed", error=str(e))
            status["health_check_error"] = str(e)

        return status
