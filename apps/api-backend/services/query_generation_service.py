"""
Query generation orchestration service for SamvadQL.

This service orchestrates the complete Text-to-SQL generation workflow,
combining RAG (Retrieval-Augmented Generation) with LLM services to generate
accurate SQL queries from natural language input.
"""

import asyncio
import logging
from typing import AsyncIterator, List, Optional, Dict, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field

from core.interfaces import (
    QueryGenerationServiceInterface,
    VectorSearchServiceInterface,
    LLMServiceInterface,
)
from services.llm_service import LLMService, LLMProvider
from services.vector_search_service import VectorSearchService
from services.metadata_service import MetadataExtractionService
from models import (
    QueryRequest,
    QueryResponse,
    TableSchema,
    TableRecommendation,
    DatabaseType,
    ValidationStatus,
    OptimizationSuggestion,
)

logger = logging.getLogger(__name__)


@dataclass
class QueryContext:
    """Context information for query generation."""

    user_id: str
    session_id: Optional[str] = None
    database_id: str = ""
    database_type: DatabaseType = DatabaseType.POSTGRESQL
    max_tables: int = 10
    confidence_threshold: float = 0.7
    context_window_limit: int = 8000  # Token limit for context
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GenerationStep:
    """Represents a step in the query generation process."""

    step_name: str
    status: str  # "pending", "in_progress", "completed", "failed"
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ContextWindowOptimizer:
    """Optimizes context window usage for large schemas."""

    def __init__(self, max_tokens: int = 8000):
        self.max_tokens = max_tokens
        self.avg_tokens_per_char = 0.25  # Rough estimate

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text."""
        return int(len(text) * self.avg_tokens_per_char)

    def optimize_table_schemas(
        self, tables: List[TableSchema], query: str, system_prompt: str
    ) -> List[TableSchema]:
        """Optimize table schemas to fit within context window."""
        # Calculate base token usage
        base_tokens = (
            self.estimate_tokens(system_prompt)
            + self.estimate_tokens(query)
            + 500  # Buffer for response
        )

        available_tokens = self.max_tokens - base_tokens

        if available_tokens <= 0:
            logger.warning("Context window too small for base prompt")
            return tables[:1]  # Return at least one table

        # Sort tables by relevance (assuming they're already ranked)
        optimized_tables = []
        current_tokens = 0

        for table in tables:
            table_text = self._format_table_for_estimation(table)
            table_tokens = self.estimate_tokens(table_text)

            if current_tokens + table_tokens <= available_tokens:
                optimized_tables.append(table)
                current_tokens += table_tokens
            else:
                # Try to include a simplified version
                simplified_table = self._simplify_table_schema(table)
                simplified_tokens = self.estimate_tokens(
                    self._format_table_for_estimation(simplified_table)
                )

                if current_tokens + simplified_tokens <= available_tokens:
                    optimized_tables.append(simplified_table)
                    current_tokens += simplified_tokens
                else:
                    break

        logger.info(f"Optimized {len(tables)} tables to {len(optimized_tables)} tables")
        return optimized_tables

    def _format_table_for_estimation(self, table: TableSchema) -> str:
        """Format table schema for token estimation."""
        text = f"Table: {table.name}\n"
        if table.description:
            text += f"Description: {table.description}\n"

        text += "Columns:\n"
        for column in table.columns:
            text += f"  - {column.name} ({column.data_type})"
            if column.description:
                text += f" - {column.description}"
            text += "\n"

        return text

    def _simplify_table_schema(self, table: TableSchema) -> TableSchema:
        """Create a simplified version of table schema."""
        # Keep only essential columns (first 10) and remove descriptions
        simplified_columns = []
        for i, column in enumerate(table.columns[:10]):
            simplified_column = column.model_copy()
            if i > 5:  # Remove descriptions for less important columns
                simplified_column.description = None
            simplified_columns.append(simplified_column)

        simplified_table = table.model_copy()
        simplified_table.columns = simplified_columns
        if len(table.description or "") > 100:
            simplified_table.description = (table.description or "")[:100] + "..."

        return simplified_table


class QueryGenerationService(QueryGenerationServiceInterface):
    """Main query generation orchestration service."""

    def __init__(
        self,
        llm_service: Optional[LLMService] = None,
        vector_search_service: Optional[VectorSearchService] = None,
        metadata_service: Optional[MetadataExtractionService] = None,
    ):
        self.llm_service = llm_service or LLMService()
        self.vector_search_service = vector_search_service or VectorSearchService()
        self.metadata_service = metadata_service or MetadataExtractionService()
        self.context_optimizer = ContextWindowOptimizer()

        # Track generation steps for debugging and monitoring
        self.generation_steps: Dict[str, List[GenerationStep]] = {}

    async def generate_sql(self, request: QueryRequest) -> AsyncIterator[QueryResponse]:
        """
        Generate SQL from natural language query request.

        This is the main orchestration method that combines:
        1. Table discovery via vector search
        2. Context optimization
        3. LLM-based SQL generation
        4. Iterative refinement if needed
        """
        request_id = request.session_id or f"req_{datetime.now().timestamp()}"

        try:
            # Initialize generation steps tracking
            self.generation_steps[request_id] = []

            # Create query context
            context = QueryContext(
                user_id=request.user_id,
                session_id=request.session_id,
                database_id=request.database_id,
                database_type=(
                    DatabaseType(request.database_type)
                    if hasattr(request, "database_type")
                    else DatabaseType.POSTGRESQL
                ),
                metadata=request.context or {},
            )

            # Step 1: Table Discovery
            yield await self._emit_progress_response(
                "Discovering relevant tables...", request_id
            )

            relevant_tables = await self._discover_relevant_tables(
                request.query, context, request_id
            )

            if not relevant_tables:
                yield QueryResponse(
                    sql="SELECT 1 as no_tables_found",
                    explanation="Could not find relevant tables for your query. Please check your question or specify table names.",
                    confidence_score=0.0,
                    selected_tables=["no_tables_found"],
                    validation_status=ValidationStatus.INVALID,
                    optimization_suggestions=[],
                    execution_time_estimate=0,
                )
                return

            # Step 2: Context Optimization
            yield await self._emit_progress_response(
                "Optimizing context for LLM...", request_id
            )

            optimized_tables = await self._optimize_context(
                relevant_tables, request.query, context, request_id
            )

            # Step 3: SQL Generation
            yield await self._emit_progress_response(
                "Generating SQL query...", request_id
            )

            async for response in self._generate_sql_with_llm(
                request.query, optimized_tables, context, request_id
            ):
                # Add selected tables to response
                response.selected_tables = [table.name for table in optimized_tables]
                yield response

        except Exception as e:
            logger.error(f"Query generation failed for request {request_id}: {e}")
            yield QueryResponse(
                sql="SELECT 1 as error_placeholder",
                explanation=f"An error occurred during query generation: {str(e)}",
                confidence_score=0.0,
                selected_tables=["error_placeholder"],
                validation_status=ValidationStatus.INVALID,
                optimization_suggestions=[],
                execution_time_estimate=0,
            )
        finally:
            # Clean up generation steps
            if request_id in self.generation_steps:
                del self.generation_steps[request_id]

    async def refine_query(
        self,
        original_sql: str,
        refinement_request: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[QueryResponse]:
        """Refine existing SQL query based on user feedback."""
        try:
            # Use LLM service directly for refinement
            async for response in self.llm_service.refine_query_stream(
                original_sql=original_sql,
                refinement_request=refinement_request,
                context=context,
            ):
                yield response

        except Exception as e:
            logger.error(f"Query refinement failed: {e}")
            yield QueryResponse(
                sql=(
                    original_sql
                    if original_sql.upper()
                    .strip()
                    .startswith(
                        (
                            "SELECT",
                            "WITH",
                            "INSERT",
                            "UPDATE",
                            "DELETE",
                            "CREATE",
                            "ALTER",
                            "DROP",
                        )
                    )
                    else "SELECT 1 as refinement_error"
                ),
                explanation=f"Error refining query: {str(e)}",
                confidence_score=0.0,
                selected_tables=["refinement_error"],
                validation_status=ValidationStatus.INVALID,
                optimization_suggestions=[],
                execution_time_estimate=0,
            )

    async def _discover_relevant_tables(
        self, query: str, context: QueryContext, request_id: str
    ) -> List[TableSchema]:
        """Discover relevant tables using vector search and metadata service."""
        step = GenerationStep(
            step_name="table_discovery", status="in_progress", start_time=datetime.now()
        )
        self.generation_steps[request_id].append(step)

        try:
            # If specific tables are mentioned in context, use those
            if context.metadata.get("selected_tables"):
                table_names = context.metadata["selected_tables"]
                tables = []
                for table_name in table_names:
                    # Note: This would need database_type and connection_config in real implementation
                    # For now, we'll skip this functionality
                    table = None
                    if table:
                        tables.append(table)

                step.status = "completed"
                step.end_time = datetime.now()
                step.result = f"Found {len(tables)} specified tables"
                return tables

            # Use vector search to find relevant tables
            recommendations = await self.vector_search_service.search_tables(
                query=query, database_id=context.database_id, limit=context.max_tables
            )

            # Convert recommendations to table schemas
            tables = []
            for rec in recommendations:
                if rec.relevance_score >= context.confidence_threshold:
                    # Note: This would need database_type and connection_config in real implementation
                    # For now, we'll skip this functionality
                    table = None
                    if table:
                        tables.append(table)

            # If no tables found via vector search, get all tables as fallback
            if not tables:
                logger.warning(f"No tables found via vector search for query: {query}")
                # Note: This would need database_type and connection_config in real implementation
                # For now, we'll return empty list
                all_tables = []
                tables = all_tables[: context.max_tables]

            step.status = "completed"
            step.end_time = datetime.now()
            step.result = f"Found {len(tables)} relevant tables"

            return tables

        except Exception as e:
            step.status = "failed"
            step.end_time = datetime.now()
            step.error = str(e)
            logger.error(f"Table discovery failed: {e}")
            return []

    async def _optimize_context(
        self,
        tables: List[TableSchema],
        query: str,
        context: QueryContext,
        request_id: str,
    ) -> List[TableSchema]:
        """Optimize context window usage."""
        step = GenerationStep(
            step_name="context_optimization",
            status="in_progress",
            start_time=datetime.now(),
        )
        self.generation_steps[request_id].append(step)

        try:
            # Create a sample system prompt to estimate token usage
            sample_prompt = f"""You are an expert SQL query generator.
Available Tables: {len(tables)} tables
Database Type: {context.database_type.value}
Context: {context.metadata}"""

            optimized_tables = self.context_optimizer.optimize_table_schemas(
                tables, query, sample_prompt
            )

            step.status = "completed"
            step.end_time = datetime.now()
            step.result = (
                f"Optimized from {len(tables)} to {len(optimized_tables)} tables"
            )

            return optimized_tables

        except Exception as e:
            step.status = "failed"
            step.end_time = datetime.now()
            step.error = str(e)
            logger.error(f"Context optimization failed: {e}")
            return tables  # Return original tables on error

    async def _generate_sql_with_llm(
        self,
        query: str,
        tables: List[TableSchema],
        context: QueryContext,
        request_id: str,
    ) -> AsyncIterator[QueryResponse]:
        """Generate SQL using LLM service."""
        step = GenerationStep(
            step_name="sql_generation", status="in_progress", start_time=datetime.now()
        )
        self.generation_steps[request_id].append(step)

        try:
            # Prepare context for LLM
            llm_context = {
                "database_type": context.database_type.value,
                "user_id": context.user_id,
                "session_id": context.session_id,
                "request_id": request_id,
                **context.metadata,
            }

            # Generate SQL using LLM service
            async for response in self.llm_service.generate_sql_stream(
                query=query,
                tables=tables,
                database_type=context.database_type,
                context=llm_context,
            ):
                # Enhance response with generation metadata
                if hasattr(response, "metadata"):
                    response.metadata = response.metadata or {}
                    response.metadata.update(
                        {
                            "generation_steps": len(
                                self.generation_steps.get(request_id, [])
                            ),
                            "tables_considered": len(tables),
                            "context_optimized": True,
                        }
                    )

                yield response

            step.status = "completed"
            step.end_time = datetime.now()
            step.result = "SQL generated successfully"

        except Exception as e:
            step.status = "failed"
            step.end_time = datetime.now()
            step.error = str(e)
            logger.error(f"SQL generation failed: {e}")

            yield QueryResponse(
                sql="SELECT 1 as generation_error",
                explanation=f"LLM generation failed: {str(e)}",
                confidence_score=0.0,
                selected_tables=(
                    [table.name for table in tables] if tables else ["generation_error"]
                ),
                validation_status=ValidationStatus.INVALID,
                optimization_suggestions=[],
                execution_time_estimate=0,
            )

    async def _emit_progress_response(
        self, message: str, request_id: str
    ) -> QueryResponse:
        """Emit a progress response for streaming updates."""
        return QueryResponse(
            sql="SELECT 1 as generating",
            explanation=message,
            confidence_score=0.0,
            selected_tables=["generating"],
            validation_status=ValidationStatus.INVALID,
            optimization_suggestions=[],
            execution_time_estimate=0,
        )

    async def get_generation_steps(self, request_id: str) -> List[GenerationStep]:
        """Get generation steps for debugging and monitoring."""
        return self.generation_steps.get(request_id, [])

    async def health_check(self) -> Dict[str, Any]:
        """Check health of all dependent services."""
        health_status = {
            "query_generation_service": "healthy",
            "llm_service": {},
            "vector_search_service": "unknown",
            "metadata_service": "unknown",
        }

        try:
            # Check LLM service health
            llm_health = await self.llm_service.health_check()
            health_status["llm_service"] = llm_health

            # Check if any LLM provider is healthy
            if not any(llm_health.values()):
                health_status["query_generation_service"] = "degraded"

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            health_status["query_generation_service"] = "unhealthy"
            health_status["error"] = str(e)

        return health_status


class QueryRefinementEngine:
    """Engine for iterative query refinement based on feedback."""

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self.refinement_history: Dict[str, List[Dict[str, Any]]] = {}

    async def refine_with_feedback(
        self,
        session_id: str,
        original_sql: str,
        feedback: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[QueryResponse]:
        """Refine SQL query based on user feedback with history tracking."""

        # Track refinement history
        if session_id not in self.refinement_history:
            self.refinement_history[session_id] = []

        refinement_entry = {
            "timestamp": datetime.now(),
            "original_sql": original_sql,
            "feedback": feedback,
            "context": context,
        }

        try:
            # Include refinement history in context
            enhanced_context = context or {}
            enhanced_context["refinement_history"] = self.refinement_history[
                session_id
            ][
                -3:
            ]  # Last 3 refinements

            async for response in self.llm_service.refine_query_stream(
                original_sql=original_sql,
                refinement_request=feedback,
                context=enhanced_context,
            ):
                # Track successful refinement
                if response.validation_status == ValidationStatus.VALID:
                    refinement_entry["refined_sql"] = response.sql
                    refinement_entry["success"] = True

                yield response

            self.refinement_history[session_id].append(refinement_entry)

            # Limit history size
            if len(self.refinement_history[session_id]) > 10:
                self.refinement_history[session_id] = self.refinement_history[
                    session_id
                ][-10:]

        except Exception as e:
            refinement_entry["error"] = str(e)
            refinement_entry["success"] = False
            self.refinement_history[session_id].append(refinement_entry)

            yield QueryResponse(
                sql=(
                    original_sql
                    if original_sql.upper()
                    .strip()
                    .startswith(
                        (
                            "SELECT",
                            "WITH",
                            "INSERT",
                            "UPDATE",
                            "DELETE",
                            "CREATE",
                            "ALTER",
                            "DROP",
                        )
                    )
                    else "SELECT 1 as refinement_error"
                ),
                explanation=f"Refinement failed: {str(e)}",
                confidence_score=0.0,
                selected_tables=["refinement_error"],
                validation_status=ValidationStatus.INVALID,
                optimization_suggestions=[],
                execution_time_estimate=0,
            )

    def get_refinement_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get refinement history for a session."""
        return self.refinement_history.get(session_id, [])

    def clear_history(self, session_id: str) -> None:
        """Clear refinement history for a session."""
        if session_id in self.refinement_history:
            del self.refinement_history[session_id]
