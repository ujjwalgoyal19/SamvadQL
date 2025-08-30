"""Table and query summarization service for SamvadQL."""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
import structlog

from core.config import settings

# Import LangChain service with fallback
try:
    from services.langchain_service import LangChainLLMService as LangChainService
except ImportError:
    LangChainService = None
from models import (
    TableSchema,
    ColumnSchema,
    QueryRequest,
    QueryResponse,
    TableSummaryDocument,
    QuerySummaryDocument,
)

logger = structlog.get_logger(__name__)


class SummarizationService:
    """Service for generating table and query summaries using LLM."""

    def __init__(self):
        self.llm_service: Optional[LangChainService] = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the summarization service."""
        try:
            if LangChainService:
                self.llm_service = LangChainService()
                # Note: LangChain service might not have async initialize
                if hasattr(self.llm_service, "initialize"):
                    await self.llm_service.initialize()
                logger.info("Summarization service initialized with LLM")
            else:
                logger.warning(
                    "LangChain service not available, using fallback summaries"
                )

            self._initialized = True
            logger.info("Summarization service initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize summarization service", error=str(e))
            # Initialize without LLM service for basic functionality
            self._initialized = True
            logger.info("Summarization service initialized in fallback mode")

    async def summarize_table(
        self,
        table: TableSchema,
        sample_queries: Optional[List[str]] = None,
        sample_data: Optional[Dict[str, List[Any]]] = None,
    ) -> str:
        """Generate a comprehensive summary of a table using LLM."""
        if not self._initialized:
            raise RuntimeError("Summarization service not initialized")

        try:
            # Build context for the table
            context = self._build_table_context(table, sample_queries, sample_data)

            # Create prompt for table summarization
            prompt = self._create_table_summary_prompt(context)

            # Generate summary using LLM
            summary = await self._generate_summary_with_llm(prompt)

            logger.info(
                "Generated table summary",
                table_name=table.name,
                database_id=table.database_id,
                summary_length=len(summary),
            )

            return summary

        except Exception as e:
            logger.error(
                "Failed to summarize table",
                table_name=table.name,
                error=str(e),
            )
            raise

    async def summarize_query(
        self,
        original_query: str,
        generated_sql: str,
        tables_used: List[str],
        execution_success: bool = True,
        execution_time: Optional[float] = None,
    ) -> str:
        """Generate a summary of a query execution for future reference."""
        if not self._initialized:
            raise RuntimeError("Summarization service not initialized")

        try:
            # Build context for the query
            context = {
                "original_query": original_query,
                "generated_sql": generated_sql,
                "tables_used": tables_used,
                "execution_success": execution_success,
                "execution_time": execution_time,
            }

            # Create prompt for query summarization
            prompt = self._create_query_summary_prompt(context)

            # Generate summary using LLM
            summary = await self._generate_summary_with_llm(prompt)

            logger.info(
                "Generated query summary",
                query_length=len(original_query),
                tables_count=len(tables_used),
                summary_length=len(summary),
            )

            return summary

        except Exception as e:
            logger.error(
                "Failed to summarize query",
                query=original_query[:100],
                error=str(e),
            )
            raise

    async def batch_summarize_tables(
        self,
        tables: List[TableSchema],
        batch_size: int = 5,
    ) -> Dict[str, str]:
        """Summarize multiple tables in batches."""
        if not self._initialized:
            raise RuntimeError("Summarization service not initialized")

        summaries = {}

        # Process tables in batches to avoid overwhelming the LLM
        for i in range(0, len(tables), batch_size):
            batch = tables[i : i + batch_size]

            # Process batch concurrently
            batch_tasks = [self.summarize_table(table) for table in batch]

            try:
                batch_summaries = await asyncio.gather(
                    *batch_tasks, return_exceptions=True
                )

                for table, summary in zip(batch, batch_summaries):
                    if isinstance(summary, Exception):
                        logger.error(
                            "Failed to summarize table in batch",
                            table_name=table.name,
                            error=str(summary),
                        )
                        summaries[f"{table.database_id}:{table.name}"] = (
                            f"Error: {str(summary)}"
                        )
                    else:
                        summaries[f"{table.database_id}:{table.name}"] = summary

                # Add delay between batches to respect rate limits
                if i + batch_size < len(tables):
                    await asyncio.sleep(1.0)

            except Exception as e:
                logger.error("Batch summarization failed", batch_start=i, error=str(e))
                # Continue with next batch
                continue

        logger.info(
            "Completed batch table summarization",
            total_tables=len(tables),
            successful_summaries=len(
                [s for s in summaries.values() if not s.startswith("Error:")]
            ),
        )

        return summaries

    async def create_table_summary_document(
        self,
        table: TableSchema,
        summary: Optional[str] = None,
        sample_queries: Optional[List[str]] = None,
        sample_data: Optional[Dict[str, List[Any]]] = None,
    ) -> TableSummaryDocument:
        """Create a complete table summary document for vector indexing."""
        if not summary:
            summary = await self.summarize_table(table, sample_queries, sample_data)

        # Extract usage patterns from sample queries
        usage_patterns = []
        if sample_queries:
            usage_patterns = await self._extract_usage_patterns(sample_queries)

        # Create sample data summary
        sample_data_summary = None
        if sample_data:
            sample_data_summary = self._create_sample_data_summary(sample_data)

        document = TableSummaryDocument(
            id=f"{table.database_id}:{table.name}",
            table_name=table.name,
            database_id=table.database_id,
            schema_summary=summary,
            sample_data_summary=sample_data_summary,
            usage_patterns=usage_patterns,
            tier=table.tier,
            metadata={
                "table_name": table.name,
                "database_id": table.database_id,
                "description": table.description,
                "tier": table.tier,
                "tags": table.tags,
                "column_count": len(table.columns),
                "row_count": table.row_count,
                "created_at": datetime.utcnow().isoformat(),
            },
        )

        return document

    async def create_query_summary_document(
        self,
        original_query: str,
        generated_sql: str,
        tables_used: List[str],
        execution_success: bool = True,
        execution_time: Optional[float] = None,
        summary: Optional[str] = None,
    ) -> QuerySummaryDocument:
        """Create a complete query summary document for vector indexing."""
        if not summary:
            summary = await self.summarize_query(
                original_query,
                generated_sql,
                tables_used,
                execution_success,
                execution_time,
            )

        # Extract query type
        query_type = self._extract_query_type(generated_sql)

        document = QuerySummaryDocument(
            id=f"query_{datetime.utcnow().timestamp()}",
            original_query=original_query,
            generated_sql=generated_sql,
            tables_used=tables_used,
            query_type=query_type,
            success=execution_success,
            metadata={
                "tables_used": tables_used,
                "query_length": len(original_query),
                "sql_length": len(generated_sql),
                "table_count": len(tables_used),
                "execution_time": execution_time,
                "execution_success": execution_success,
                "created_at": datetime.utcnow().isoformat(),
            },
        )

        return document

    def _build_table_context(
        self,
        table: TableSchema,
        sample_queries: Optional[List[str]] = None,
        sample_data: Optional[Dict[str, List[Any]]] = None,
    ) -> Dict[str, Any]:
        """Build comprehensive context for table summarization."""
        context = {
            "table_name": table.name,
            "description": table.description or "No description available",
            "tier": table.tier or "unknown",
            "tags": table.tags or [],
            "row_count": table.row_count,
            "columns": [],
        }

        # Add column information
        for col in table.columns:
            col_info = {
                "name": col.name,
                "type": col.data_type,
                "description": col.description or "No description",
                "nullable": col.is_nullable,
                "primary_key": getattr(col, "is_primary_key", False),
                "sample_values": getattr(col, "sample_values", [])[
                    :5
                ],  # Limit to 5 samples
            }
            context["columns"].append(col_info)

        # Add sample queries if available
        if sample_queries:
            context["sample_queries"] = sample_queries[:10]  # Limit to 10 queries

        # Add sample data if available
        if sample_data:
            context["sample_data"] = {
                col: values[:3]
                for col, values in sample_data.items()  # Limit to 3 samples per column
            }

        return context

    def _create_table_summary_prompt(self, context: Dict[str, Any]) -> str:
        """Create a prompt for table summarization."""
        prompt = f"""
Analyze the following database table and provide a comprehensive summary that would help users understand when and how to use this table.

Table Name: {context['table_name']}
Description: {context['description']}
Tier: {context['tier']}
Tags: {', '.join(context['tags']) if context['tags'] else 'None'}
Row Count: {context['row_count'] or 'Unknown'}

Columns:
"""

        for col in context["columns"]:
            prompt += f"- {col['name']} ({col['type']}): {col['description']}"
            if col["primary_key"]:
                prompt += " [PRIMARY KEY]"
            if not col["nullable"]:
                prompt += " [NOT NULL]"
            if col["sample_values"]:
                prompt += (
                    f" (Sample values: {', '.join(map(str, col['sample_values']))})"
                )
            prompt += "\n"

        if context.get("sample_queries"):
            prompt += f"\nSample Queries:\n"
            for i, query in enumerate(context["sample_queries"], 1):
                prompt += f"{i}. {query}\n"

        if context.get("sample_data"):
            prompt += f"\nSample Data:\n"
            for col, values in context["sample_data"].items():
                prompt += f"- {col}: {', '.join(map(str, values))}\n"

        prompt += """
Please provide a concise but comprehensive summary (2-3 sentences) that includes:
1. What this table contains and its primary purpose
2. Key relationships or important columns
3. Common use cases or query patterns
4. Any notable characteristics or constraints

Focus on information that would help someone decide if this table is relevant for their query.
"""

        return prompt

    def _create_query_summary_prompt(self, context: Dict[str, Any]) -> str:
        """Create a prompt for query summarization."""
        prompt = f"""
Analyze the following query execution and provide a summary for future reference.

Original Query: {context['original_query']}
Generated SQL: {context['generated_sql']}
Tables Used: {', '.join(context['tables_used'])}
Execution Success: {context['execution_success']}
"""

        if context.get("execution_time"):
            prompt += f"Execution Time: {context['execution_time']:.3f} seconds\n"

        prompt += """
Please provide a concise summary (1-2 sentences) that includes:
1. What the user was trying to accomplish
2. The approach taken (joins, aggregations, filters, etc.)
3. Which tables were involved and why
4. Any notable patterns or techniques used

This summary will help identify similar queries in the future.
"""

        return prompt

    async def _generate_summary_with_llm(self, prompt: str) -> str:
        """Generate summary using the LLM service."""
        if not self.llm_service:
            return self._generate_fallback_summary(prompt)

        try:
            # Use the LLM service to generate summary
            # This is a simplified approach - in practice you might want to use
            # specific chains or more sophisticated prompting
            if hasattr(self.llm_service, "generate_text"):
                response = await self.llm_service.generate_text(
                    prompt=prompt,
                    max_tokens=200,
                    temperature=0.3,
                )
                return response.strip()
            else:
                # Fallback if method doesn't exist
                return self._generate_fallback_summary(prompt)

        except Exception as e:
            logger.error("Failed to generate summary with LLM", error=str(e))
            # Fallback to basic summary
            return self._generate_fallback_summary(prompt)

    def _generate_fallback_summary(self, prompt: str) -> str:
        """Generate a basic summary without LLM."""
        # Extract key information from the prompt for basic summary
        if "Table Name:" in prompt:
            # Table summary fallback
            lines = prompt.split("\n")
            table_name = ""
            description = ""
            column_count = 0

            for line in lines:
                if line.startswith("Table Name:"):
                    table_name = line.split(":", 1)[1].strip()
                elif line.startswith("Description:"):
                    description = line.split(":", 1)[1].strip()
                elif line.startswith("- ") and "(" in line and ")" in line:
                    column_count += 1

            if description and description != "No description available":
                return f"Table {table_name} contains {description.lower()}. It has {column_count} columns and serves as a data source for queries."
            else:
                return f"Table {table_name} has {column_count} columns and is available for querying."

        elif "Original Query:" in prompt:
            # Query summary fallback
            lines = prompt.split("\n")
            for line in lines:
                if line.startswith("Original Query:"):
                    query = line.split(":", 1)[1].strip()
                    return f"Query to {query.lower()[:50]}... executed successfully."

        return "Summary generated using basic analysis - detailed information available in metadata."

    async def _extract_usage_patterns(self, sample_queries: List[str]) -> List[str]:
        """Extract common usage patterns from sample queries."""
        if not sample_queries:
            return []

        patterns = []

        # Simple pattern detection based on SQL keywords
        for query in sample_queries:
            query_upper = query.upper()

            if "JOIN" in query_upper:
                patterns.append("table joins")
            if "GROUP BY" in query_upper:
                patterns.append("aggregation")
            if "ORDER BY" in query_upper:
                patterns.append("sorting")
            if "WHERE" in query_upper:
                patterns.append("filtering")
            if "COUNT" in query_upper or "SUM" in query_upper or "AVG" in query_upper:
                patterns.append("analytics")

        # Remove duplicates and limit
        return list(set(patterns))[:5]

    def _create_sample_data_summary(self, sample_data: Dict[str, List[Any]]) -> str:
        """Create a summary of sample data."""
        if not sample_data:
            return ""

        summaries = []
        for col, values in sample_data.items():
            if values:
                # Get unique values and their types
                unique_values = list(set(str(v) for v in values if v is not None))[:3]
                if unique_values:
                    summaries.append(f"{col}: {', '.join(unique_values)}")

        return "; ".join(summaries)

    def _extract_query_type(self, sql: str) -> str:
        """Extract the type of SQL query."""
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

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on summarization service."""
        status = {
            "initialized": self._initialized,
            "llm_service_available": self.llm_service is not None,
        }

        if self.llm_service:
            try:
                llm_status = await self.llm_service.health_check()
                status["llm_service_status"] = llm_status
            except Exception as e:
                status["llm_service_error"] = str(e)

        return status
