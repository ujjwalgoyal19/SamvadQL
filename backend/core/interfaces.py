"""Core interfaces for SamvadQL services."""

from abc import ABC, abstractmethod
from typing import AsyncIterator, List, Optional, Dict, Any
from langchain.schema import BaseMessage
from langchain.callbacks.base import BaseCallbackHandler
from models.base import (
    QueryRequest,
    QueryResponse,
    TableSchema,
    ValidationResult,
    TableRecommendation,
    DatabaseType,
    OptimizationSuggestion,
)


class LLMServiceInterface(ABC):
    """Interface for Large Language Model services using LangChain."""

    @abstractmethod
    async def generate_sql(
        self,
        query: str,
        tables: List[TableSchema],
        context: Optional[Dict[str, Any]] = None,
        callbacks: Optional[List[BaseCallbackHandler]] = None,
    ) -> AsyncIterator[QueryResponse]:
        """Generate SQL from natural language query using LangChain."""
        pass

    @abstractmethod
    async def refine_query(
        self,
        original_sql: str,
        refinement_request: str,
        context: Optional[Dict[str, Any]] = None,
        callbacks: Optional[List[BaseCallbackHandler]] = None,
    ) -> AsyncIterator[QueryResponse]:
        """Refine existing SQL query based on user feedback."""
        pass

    @abstractmethod
    async def correct_sql(
        self,
        invalid_sql: str,
        error_message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Attempt to correct invalid SQL using LangChain."""
        pass

    @abstractmethod
    async def create_chain(self, chain_type: str, **kwargs) -> Any:
        """Create a LangChain chain for specific use cases."""
        pass

    @abstractmethod
    async def invoke_with_history(
        self,
        messages: List[BaseMessage],
        callbacks: Optional[List[BaseCallbackHandler]] = None,
    ) -> BaseMessage:
        """Invoke LLM with conversation history."""
        pass


class VectorSearchServiceInterface(ABC):
    """Interface for vector search services."""

    @abstractmethod
    async def search_tables(
        self, query: str, database_id: str, limit: int = 10
    ) -> List[TableRecommendation]:
        """Search for relevant tables using semantic similarity."""
        pass

    @abstractmethod
    async def rerank_tables(
        self, query: str, candidates: List[TableSchema]
    ) -> List[TableSchema]:
        """Re-rank table candidates using LLM evaluation."""
        pass

    @abstractmethod
    async def index_table(self, table: TableSchema, summary: str) -> None:
        """Index a table with its summary for search."""
        pass

    @abstractmethod
    async def index_query(self, query: str, sql: str, tables: List[str]) -> None:
        """Index a query-SQL pair for future reference."""
        pass


class ValidationServiceInterface(ABC):
    """Interface for SQL validation services."""

    @abstractmethod
    async def validate_sql(
        self, sql: str, database_type: DatabaseType, database_id: str
    ) -> ValidationResult:
        """Validate SQL syntax and safety."""
        pass

    @abstractmethod
    async def suggest_optimizations(
        self, sql: str, database_type: DatabaseType, database_id: str
    ) -> List[OptimizationSuggestion]:
        """Suggest query optimizations."""
        pass

    @abstractmethod
    async def check_safety(self, sql: str) -> bool:
        """Check if SQL contains destructive operations."""
        pass


class MetadataServiceInterface(ABC):
    """Interface for database metadata services."""

    @abstractmethod
    async def get_table_schema(
        self, database_id: str, table_name: str
    ) -> Optional[TableSchema]:
        """Get schema for a specific table."""
        pass

    @abstractmethod
    async def list_tables(
        self, database_id: str, filter_pattern: Optional[str] = None
    ) -> List[TableSchema]:
        """List all tables in a database."""
        pass

    @abstractmethod
    async def refresh_metadata(self, database_id: str) -> None:
        """Refresh metadata cache for a database."""
        pass

    @abstractmethod
    async def get_sample_data(
        self, database_id: str, table_name: str, column_name: str, limit: int = 10
    ) -> List[Any]:
        """Get sample data for a column."""
        pass


class DatabaseConnectorInterface(ABC):
    """Interface for database connectors."""

    @abstractmethod
    async def connect(self) -> None:
        """Establish database connection."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close database connection."""
        pass

    @abstractmethod
    async def execute_query(
        self, sql: str, params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute SQL query and return results."""
        pass

    @abstractmethod
    async def explain_query(self, sql: str) -> str:
        """Get query execution plan."""
        pass

    @abstractmethod
    async def get_table_metadata(self, table_name: str) -> TableSchema:
        """Get metadata for a specific table."""
        pass

    @abstractmethod
    async def list_tables(self) -> List[str]:
        """List all table names."""
        pass


class CacheServiceInterface(ABC):
    """Interface for caching services."""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with optional TTL."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete key from cache."""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        pass


class QueryGenerationServiceInterface(ABC):
    """Interface for query generation orchestration."""

    @abstractmethod
    async def generate_sql(self, request: QueryRequest) -> AsyncIterator[QueryResponse]:
        """Generate SQL from natural language query request."""
        pass

    @abstractmethod
    async def refine_query(
        self,
        original_sql: str,
        refinement_request: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[QueryResponse]:
        """Refine existing SQL query."""
        pass
