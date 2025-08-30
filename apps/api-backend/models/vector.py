"""Vector database models for SamvadQL."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class VectorProvider(Enum):
    """Supported vector database providers."""

    QDRANT = "qdrant"
    OPENSEARCH = "opensearch"
    WEAVIATE = "weaviate"


class EmbeddingModel(Enum):
    """Supported embedding models."""

    OPENAI_ADA_002 = "text-embedding-ada-002"
    OPENAI_3_SMALL = "text-embedding-3-small"
    OPENAI_3_LARGE = "text-embedding-3-large"
    SENTENCE_TRANSFORMERS = "sentence-transformers/all-MiniLM-L6-v2"


class VectorDocument(BaseModel):
    """Base vector document model."""

    id: str = Field(..., description="Unique document identifier")
    content: str = Field(..., description="Text content to be embedded")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Document metadata"
    )
    embedding: Optional[List[float]] = Field(None, description="Vector embedding")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )

    @field_validator("content")
    @classmethod
    def validate_content(cls, v):
        """Validate content is not empty."""
        if not v or v.isspace():
            raise ValueError("Content cannot be empty")
        return v.strip()


class TableSummaryDocument(VectorDocument):
    """Vector document for table summaries."""

    table_name: str = Field(..., description="Table name")
    database_id: str = Field(..., description="Database identifier")
    schema_summary: str = Field(..., description="Schema summary")
    sample_data_summary: Optional[str] = Field(None, description="Sample data summary")
    usage_patterns: List[str] = Field(
        default_factory=list, description="Common usage patterns"
    )
    tier: Optional[str] = Field(None, description="Table tier")

    def __init__(self, **data):
        # Auto-generate content from table information
        if "content" not in data:
            content_parts = [
                f"Table: {data.get('table_name', '')}",
                f"Schema: {data.get('schema_summary', '')}",
            ]
            if data.get("sample_data_summary"):
                content_parts.append(f"Sample data: {data['sample_data_summary']}")
            if data.get("usage_patterns"):
                content_parts.append(
                    f"Usage patterns: {', '.join(data['usage_patterns'])}"
                )

            data["content"] = " | ".join(content_parts)

        super().__init__(**data)


class QuerySummaryDocument(VectorDocument):
    """Vector document for query summaries."""

    original_query: str = Field(..., description="Original natural language query")
    generated_sql: str = Field(..., description="Generated SQL")
    tables_used: List[str] = Field(..., description="Tables used in the query")
    query_type: str = Field(..., description="Type of query (SELECT, INSERT, etc.)")
    success: bool = Field(True, description="Whether the query was successful")

    def __init__(self, **data):
        # Auto-generate content from query information
        if "content" not in data:
            content_parts = [
                f"Query: {data.get('original_query', '')}",
                f"SQL: {data.get('generated_sql', '')}",
                f"Tables: {', '.join(data.get('tables_used', []))}",
                f"Type: {data.get('query_type', '')}",
            ]

            data["content"] = " | ".join(content_parts)

        super().__init__(**data)


class VectorSearchResult(BaseModel):
    """Vector search result."""

    document: VectorDocument = Field(..., description="Retrieved document")
    score: float = Field(..., ge=0.0, le=1.0, description="Similarity score")
    distance: Optional[float] = Field(None, description="Vector distance")

    @field_validator("score")
    @classmethod
    def validate_score(cls, v):
        """Validate score is between 0 and 1."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Score must be between 0.0 and 1.0")
        return v


class VectorIndexConfig(BaseModel):
    """Vector index configuration."""

    name: str = Field(..., description="Index name")
    dimension: int = Field(..., gt=0, description="Vector dimension")
    metric: str = Field(default="cosine", description="Distance metric")
    provider: VectorProvider = Field(..., description="Vector database provider")
    embedding_model: EmbeddingModel = Field(..., description="Embedding model")

    @field_validator("metric")
    @classmethod
    def validate_metric(cls, v):
        """Validate distance metric."""
        valid_metrics = ["cosine", "euclidean", "dot_product", "manhattan"]
        if v not in valid_metrics:
            raise ValueError(f"Metric must be one of: {', '.join(valid_metrics)}")
        return v


class VectorHealthStatus(BaseModel):
    """Vector database health status."""

    is_healthy: bool = Field(..., description="Overall health status")
    provider: VectorProvider = Field(..., description="Vector database provider")
    connection_status: str = Field(..., description="Connection status")
    index_count: int = Field(default=0, ge=0, description="Number of indices")
    document_count: int = Field(default=0, ge=0, description="Total document count")
    last_check: datetime = Field(
        default_factory=datetime.utcnow, description="Last health check"
    )
    error_message: Optional[str] = Field(None, description="Error message if unhealthy")
