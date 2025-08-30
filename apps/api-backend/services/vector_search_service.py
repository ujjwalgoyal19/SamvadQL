"""Vector search service for SamvadQL."""

from typing import List, Optional, Dict, Any
import asyncio
from datetime import datetime
import structlog

from core.config import settings
from core.vector import VectorDatabaseFactory
from core.vector.base import VectorDatabaseInterface
from core.interfaces import VectorSearchServiceInterface
from services.embedding_service import EmbeddingService
from models import (
    TableSchema,
    TableRecommendation,
    VectorIndexConfig,
    VectorProvider,
    EmbeddingModel,
    TableSummaryDocument,
    QuerySummaryDocument,
    VectorSearchResult,
    VectorHealthStatus,
)

logger = structlog.get_logger(__name__)


class VectorSearchService(VectorSearchServiceInterface):
    """Service for vector-based semantic search."""

    def __init__(self):
        self.vector_db: Optional[VectorDatabaseInterface] = None
        self.embedding_service: Optional[EmbeddingService] = None
        self._initialized = False

        # Index names
        self.table_index = "table_summaries"
        self.query_index = "query_summaries"

        # Configuration
        self.embedding_model = EmbeddingModel.OPENAI_ADA_002
        self.vector_dimension = 1536  # Default for OpenAI ada-002

    async def initialize(self) -> None:
        """Initialize vector search service."""
        try:
            # Create vector database instance
            self.vector_db = VectorDatabaseFactory.create_vector_database()
            await self.vector_db.connect()

            # Initialize embedding service
            self.embedding_service = EmbeddingService()
            await self.embedding_service.initialize()

            # Update vector dimension based on embedding model
            self.vector_dimension = self.embedding_service.get_model_dimension(
                self.embedding_model
            )

            # Ensure indices exist
            await self._ensure_indices_exist()

            self._initialized = True
            logger.info("Vector search service initialized successfully")

        except Exception as e:
            logger.error("Failed to initialize vector search service", error=str(e))
            raise

    async def shutdown(self) -> None:
        """Shutdown vector search service."""
        if self.vector_db:
            await self.vector_db.disconnect()
        self._initialized = False
        logger.info("Vector search service shutdown")

    async def search_tables(
        self, query: str, database_id: str, limit: int = 10
    ) -> List[TableRecommendation]:
        """Search for relevant tables using semantic similarity."""
        if not self._initialized:
            raise RuntimeError("Vector search service not initialized")

        try:
            # Generate embedding for the query
            query_embedding = await self.embedding_service.generate_embedding(
                query, self.embedding_model
            )

            # Search in table summaries index
            filters = {"database_id": database_id} if database_id else None
            search_results = await self.vector_db.search(
                index_name=self.table_index,
                query_vector=query_embedding,
                limit=limit,
                filters=filters,
                min_score=0.3,  # Minimum relevance threshold
            )

            # Convert to table recommendations
            recommendations = []
            for result in search_results:
                # Extract table information from document metadata
                metadata = result.document.metadata

                # Create a basic table schema from metadata
                # In a real implementation, you'd fetch the full schema
                table_schema = TableSchema(
                    name=metadata.get("table_name", "unknown"),
                    database_id=metadata.get("database_id", database_id),
                    columns=[],  # Would be populated from metadata service
                    description=metadata.get("description"),
                    tier=metadata.get("tier"),
                    tags=metadata.get("tags", []),
                )

                recommendation = TableRecommendation(
                    table_schema=table_schema,
                    relevance_score=result.score,
                    match_reason=f"Semantic similarity: {result.score:.3f}",
                    summary=result.document.content,
                )
                recommendations.append(recommendation)

            logger.info(
                "Performed table search",
                query_length=len(query),
                database_id=database_id,
                results_count=len(recommendations),
            )

            return recommendations

        except Exception as e:
            logger.error("Failed to search tables", query=query, error=str(e))
            return []

    async def rerank_tables(
        self, query: str, candidates: List[TableSchema]
    ) -> List[TableSchema]:
        """Re-rank table candidates using LLM evaluation."""
        if not candidates:
            return []

        try:
            # For now, implement a simple embedding-based re-ranking
            # In a full implementation, this would use LLM for more sophisticated ranking

            query_embedding = await self.embedding_service.generate_embedding(
                query, self.embedding_model
            )

            # Calculate similarity scores for each candidate
            scored_candidates = []
            for table in candidates:
                # Create a summary text for the table
                table_text = f"Table: {table.name}"
                if table.description:
                    table_text += f" Description: {table.description}"
                if table.columns:
                    column_names = [
                        col.name for col in table.columns[:10]
                    ]  # Limit columns
                    table_text += f" Columns: {', '.join(column_names)}"

                # Generate embedding for table
                table_embedding = await self.embedding_service.generate_embedding(
                    table_text, self.embedding_model
                )

                # Calculate similarity
                similarity = await self.embedding_service.calculate_similarity(
                    query_embedding, table_embedding
                )

                scored_candidates.append((table, similarity))

            # Sort by similarity score (descending)
            scored_candidates.sort(key=lambda x: x[1], reverse=True)

            # Return re-ranked tables
            reranked_tables = [table for table, _ in scored_candidates]

            logger.info(
                "Re-ranked tables",
                query_length=len(query),
                candidates_count=len(candidates),
            )

            return reranked_tables

        except Exception as e:
            logger.error("Failed to re-rank tables", query=query, error=str(e))
            return candidates  # Return original order on error

    async def index_table(self, table: TableSchema, summary: str) -> None:
        """Index a table with its summary for search."""
        if not self._initialized:
            raise RuntimeError("Vector search service not initialized")

        try:
            # Create table summary document
            document = TableSummaryDocument(
                id=f"{table.database_id}:{table.name}",
                table_name=table.name,
                database_id=table.database_id,
                schema_summary=summary,
                tier=table.tier,
                metadata={
                    "table_name": table.name,
                    "database_id": table.database_id,
                    "description": table.description,
                    "tier": table.tier,
                    "tags": table.tags,
                    "column_count": len(table.columns),
                    "row_count": table.row_count,
                },
            )

            # Generate embedding
            document = await self.embedding_service.embed_document(
                document, self.embedding_model
            )

            # Index the document
            success = await self.vector_db.upsert_document(self.table_index, document)

            if success:
                logger.info(
                    "Indexed table summary",
                    table_name=table.name,
                    database_id=table.database_id,
                )
            else:
                logger.error(
                    "Failed to index table summary",
                    table_name=table.name,
                    database_id=table.database_id,
                )

        except Exception as e:
            logger.error(
                "Failed to index table",
                table_name=table.name,
                error=str(e),
            )

    async def index_query(self, query: str, sql: str, tables: List[str]) -> None:
        """Index a query-SQL pair for future reference."""
        if not self._initialized:
            raise RuntimeError("Vector search service not initialized")

        try:
            # Create query summary document
            document = QuerySummaryDocument(
                id=f"query_{datetime.utcnow().timestamp()}",
                original_query=query,
                generated_sql=sql,
                tables_used=tables,
                query_type=self._extract_query_type(sql),
                metadata={
                    "tables_used": tables,
                    "query_length": len(query),
                    "sql_length": len(sql),
                    "table_count": len(tables),
                },
            )

            # Generate embedding
            document = await self.embedding_service.embed_document(
                document, self.embedding_model
            )

            # Index the document
            success = await self.vector_db.upsert_document(self.query_index, document)

            if success:
                logger.debug(
                    "Indexed query",
                    query_length=len(query),
                    tables_count=len(tables),
                )
            else:
                logger.error("Failed to index query")

        except Exception as e:
            logger.error("Failed to index query", query=query, error=str(e))

    async def search_similar_queries(
        self, query: str, limit: int = 5
    ) -> List[VectorSearchResult]:
        """Search for similar historical queries."""
        if not self._initialized:
            raise RuntimeError("Vector search service not initialized")

        try:
            # Generate embedding for the query
            query_embedding = await self.embedding_service.generate_embedding(
                query, self.embedding_model
            )

            # Search in query summaries index
            search_results = await self.vector_db.search(
                index_name=self.query_index,
                query_vector=query_embedding,
                limit=limit,
                min_score=0.4,  # Higher threshold for query similarity
            )

            logger.debug(
                "Searched similar queries",
                query_length=len(query),
                results_count=len(search_results),
            )

            return search_results

        except Exception as e:
            logger.error("Failed to search similar queries", query=query, error=str(e))
            return []

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on vector search service."""
        status = {
            "initialized": self._initialized,
            "embedding_service": None,
            "vector_database": None,
        }

        try:
            # Check embedding service
            if self.embedding_service:
                status["embedding_service"] = (
                    await self.embedding_service.health_check()
                )

            # Check vector database
            if self.vector_db:
                vector_health = await self.vector_db.health_check()
                status["vector_database"] = {
                    "is_healthy": vector_health.is_healthy,
                    "provider": vector_health.provider.value,
                    "connection_status": vector_health.connection_status,
                    "index_count": vector_health.index_count,
                    "document_count": vector_health.document_count,
                    "error_message": vector_health.error_message,
                }

            # Check indices
            if self._initialized:
                status["indices"] = {
                    "table_index_exists": await self.vector_db.index_exists(
                        self.table_index
                    ),
                    "query_index_exists": await self.vector_db.index_exists(
                        self.query_index
                    ),
                    "table_document_count": await self.vector_db.count_documents(
                        self.table_index
                    ),
                    "query_document_count": await self.vector_db.count_documents(
                        self.query_index
                    ),
                }

        except Exception as e:
            logger.error("Vector search health check failed", error=str(e))
            status["health_check_error"] = str(e)

        return status

    async def _ensure_indices_exist(self) -> None:
        """Ensure required indices exist in the vector database."""
        # Table summaries index
        if not await self.vector_db.index_exists(self.table_index):
            config = VectorIndexConfig(
                name=self.table_index,
                dimension=self.vector_dimension,
                metric="cosine",
                provider=VectorProvider(settings.vector_db_provider),
                embedding_model=self.embedding_model,
            )
            await self.vector_db.create_index(config)
            logger.info("Created table summaries index")

        # Query summaries index
        if not await self.vector_db.index_exists(self.query_index):
            config = VectorIndexConfig(
                name=self.query_index,
                dimension=self.vector_dimension,
                metric="cosine",
                provider=VectorProvider(settings.vector_db_provider),
                embedding_model=self.embedding_model,
            )
            await self.vector_db.create_index(config)
            logger.info("Created query summaries index")

    def _extract_query_type(self, sql: str) -> str:
        """Extract the type of SQL query (SELECT, INSERT, etc.)."""
        sql_upper = sql.upper().strip()

        if sql_upper.startswith("SELECT") or sql_upper.startswith("WITH"):
            return "SELECT"
        elif sql_upper.startswith("INSERT"):
            return "INSERT"
        elif sql_upper.startswith("UPDATE"):
            return "UPDATE"
        elif sql_upper.startswith("DELETE"):
            return "DELETE"
        elif sql_upper.startswith("CREATE"):
            return "CREATE"
        elif sql_upper.startswith("ALTER"):
            return "ALTER"
        elif sql_upper.startswith("DROP"):
            return "DROP"
        else:
            return "UNKNOWN"
