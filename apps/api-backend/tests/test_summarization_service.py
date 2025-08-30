"""Tests for summarization service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from services.summarization_service import SummarizationService
from models import (
    TableSchema,
    ColumnSchema,
    TableSummaryDocument,
    QuerySummaryDocument,
)


class TestSummarizationService:
    """Test summarization service."""

    @pytest.fixture
    def summarization_service(self):
        """Create summarization service instance."""
        return SummarizationService()

    @pytest.fixture
    def sample_table_schema(self):
        """Create sample table schema."""
        return TableSchema(
            name="users",
            database_id="db-123",
            columns=[
                ColumnSchema(
                    name="id",
                    data_type="integer",
                    description="User ID",
                    is_primary_key=True,
                    is_nullable=False,
                ),
                ColumnSchema(
                    name="email",
                    data_type="varchar",
                    description="User email address",
                    is_nullable=False,
                ),
                ColumnSchema(
                    name="created_at",
                    data_type="timestamp",
                    description="Account creation date",
                    is_nullable=False,
                ),
            ],
            description="User accounts and profile information",
            tier="gold",
            tags=["users", "core", "authentication"],
            row_count=150000,
        )

    async def test_initialize_without_llm(self, summarization_service):
        """Test service initialization without LLM service."""
        with patch("services.summarization_service.LangChainService", None):
            await summarization_service.initialize()

            assert summarization_service._initialized is True
            assert summarization_service.llm_service is None

    async def test_initialize_with_llm(self, summarization_service):
        """Test service initialization with LLM service."""
        mock_llm_service = AsyncMock()

        with patch("services.summarization_service.LangChainService") as mock_llm_class:
            mock_llm_class.return_value = mock_llm_service

            await summarization_service.initialize()

            assert summarization_service._initialized is True
            assert summarization_service.llm_service == mock_llm_service

    async def test_summarize_table_fallback(
        self, summarization_service, sample_table_schema
    ):
        """Test table summarization with fallback (no LLM)."""
        await summarization_service.initialize()

        summary = await summarization_service.summarize_table(sample_table_schema)

        assert isinstance(summary, str)
        assert len(summary) > 0
        assert "users" in summary.lower()
        assert "3 columns" in summary

    async def test_summarize_table_with_sample_data(
        self, summarization_service, sample_table_schema
    ):
        """Test table summarization with sample data."""
        await summarization_service.initialize()

        sample_queries = [
            "SELECT * FROM users WHERE created_at > '2024-01-01'",
            "SELECT COUNT(*) FROM users GROUP BY DATE(created_at)",
        ]

        sample_data = {
            "id": [1, 2, 3],
            "email": ["user1@example.com", "user2@example.com", "user3@example.com"],
        }

        summary = await summarization_service.summarize_table(
            sample_table_schema, sample_queries, sample_data
        )

        assert isinstance(summary, str)
        assert len(summary) > 0

    async def test_summarize_query_fallback(self, summarization_service):
        """Test query summarization with fallback."""
        await summarization_service.initialize()

        summary = await summarization_service.summarize_query(
            original_query="Find all users created this year",
            generated_sql="SELECT * FROM users WHERE created_at >= '2024-01-01'",
            tables_used=["users"],
            execution_success=True,
            execution_time=0.25,
        )

        assert isinstance(summary, str)
        assert len(summary) > 0
        assert "find all users created this year" in summary.lower()

    async def test_batch_summarize_tables(
        self, summarization_service, sample_table_schema
    ):
        """Test batch table summarization."""
        await summarization_service.initialize()

        # Create multiple tables
        tables = [sample_table_schema]
        for i in range(2, 4):
            table = TableSchema(
                name=f"table_{i}",
                database_id="db-123",
                columns=[
                    ColumnSchema(
                        name="id",
                        data_type="integer",
                        description="Primary key",
                        is_primary_key=True,
                        is_nullable=False,
                    )
                ],
                description=f"Test table {i}",
            )
            tables.append(table)

        summaries = await summarization_service.batch_summarize_tables(
            tables, batch_size=2
        )

        assert len(summaries) == 3
        assert "db-123:users" in summaries
        assert "db-123:table_2" in summaries
        assert "db-123:table_3" in summaries

        for summary in summaries.values():
            assert isinstance(summary, str)
            assert len(summary) > 0

    async def test_create_table_summary_document(
        self, summarization_service, sample_table_schema
    ):
        """Test creating table summary document."""
        await summarization_service.initialize()

        document = await summarization_service.create_table_summary_document(
            sample_table_schema
        )

        assert isinstance(document, TableSummaryDocument)
        assert document.table_name == "users"
        assert document.database_id == "db-123"
        assert document.tier == "gold"
        assert len(document.content) > 0
        assert document.metadata["table_name"] == "users"
        assert document.metadata["column_count"] == 3

    async def test_create_query_summary_document(self, summarization_service):
        """Test creating query summary document."""
        await summarization_service.initialize()

        document = await summarization_service.create_query_summary_document(
            original_query="Find active users",
            generated_sql="SELECT * FROM users WHERE status = 'active'",
            tables_used=["users"],
            execution_success=True,
            execution_time=0.15,
        )

        assert isinstance(document, QuerySummaryDocument)
        assert document.original_query == "Find active users"
        assert document.generated_sql == "SELECT * FROM users WHERE status = 'active'"
        assert document.tables_used == ["users"]
        assert document.query_type == "SELECT"
        assert document.success is True
        assert len(document.content) > 0

    def test_build_table_context(self, summarization_service, sample_table_schema):
        """Test building table context."""
        sample_queries = ["SELECT * FROM users"]
        sample_data = {"id": [1, 2], "email": ["test@example.com"]}

        context = summarization_service._build_table_context(
            sample_table_schema, sample_queries, sample_data
        )

        assert context["table_name"] == "users"
        assert context["description"] == "User accounts and profile information"
        assert context["tier"] == "gold"
        assert len(context["columns"]) == 3
        assert context["sample_queries"] == sample_queries
        assert "id" in context["sample_data"]

    def test_create_table_summary_prompt(
        self, summarization_service, sample_table_schema
    ):
        """Test creating table summary prompt."""
        context = summarization_service._build_table_context(sample_table_schema)
        prompt = summarization_service._create_table_summary_prompt(context)

        assert isinstance(prompt, str)
        assert "Table Name: users" in prompt
        assert "User accounts and profile information" in prompt
        assert "Tier: gold" in prompt
        assert "id (integer)" in prompt
        assert "email (varchar)" in prompt

    def test_create_query_summary_prompt(self, summarization_service):
        """Test creating query summary prompt."""
        context = {
            "original_query": "Find all users",
            "generated_sql": "SELECT * FROM users",
            "tables_used": ["users"],
            "execution_success": True,
            "execution_time": 0.1,
        }

        prompt = summarization_service._create_query_summary_prompt(context)

        assert isinstance(prompt, str)
        assert "Original Query: Find all users" in prompt
        assert "Generated SQL: SELECT * FROM users" in prompt
        assert "Tables Used: users" in prompt
        assert "Execution Success: True" in prompt
        assert "Execution Time: 0.100 seconds" in prompt

    def test_generate_fallback_summary_table(self, summarization_service):
        """Test fallback summary generation for tables."""
        prompt = """
Table Name: test_table
Description: A test table for testing
Tier: silver
Tags: test, sample
Row Count: 1000

Columns:
- id (integer): Primary key [PRIMARY KEY] [NOT NULL]
- name (varchar): User name
- email (varchar): Email address
"""

        summary = summarization_service._generate_fallback_summary(prompt)

        assert isinstance(summary, str)
        assert "test_table" in summary
        assert "3 columns" in summary

    def test_generate_fallback_summary_query(self, summarization_service):
        """Test fallback summary generation for queries."""
        prompt = """
Original Query: Find all active users
Generated SQL: SELECT * FROM users WHERE status = 'active'
Tables Used: users
Execution Success: True
"""

        summary = summarization_service._generate_fallback_summary(prompt)

        assert isinstance(summary, str)
        assert "find all active users" in summary.lower()

    async def test_extract_usage_patterns(self, summarization_service):
        """Test extracting usage patterns from queries."""
        sample_queries = [
            "SELECT u.name, p.title FROM users u JOIN posts p ON u.id = p.user_id",
            "SELECT COUNT(*) FROM users GROUP BY created_date",
            "SELECT * FROM users WHERE status = 'active' ORDER BY created_at",
            "SELECT AVG(age) FROM users",
        ]

        patterns = await summarization_service._extract_usage_patterns(sample_queries)

        assert isinstance(patterns, list)
        assert "table joins" in patterns
        assert "aggregation" in patterns
        assert "sorting" in patterns
        assert "filtering" in patterns
        assert "analytics" in patterns

    def test_create_sample_data_summary(self, summarization_service):
        """Test creating sample data summary."""
        sample_data = {
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
            "status": ["active", "inactive", "active"],
        }

        summary = summarization_service._create_sample_data_summary(sample_data)

        assert isinstance(summary, str)
        assert "id: 1, 2, 3" in summary
        assert "name: Alice, Bob, Charlie" in summary
        assert "status: active, inactive" in summary

    def test_extract_query_type(self, summarization_service):
        """Test extracting query type from SQL."""
        test_cases = [
            ("SELECT * FROM users", "SELECT"),
            ("INSERT INTO users VALUES (1, 'test')", "INSERT"),
            ("UPDATE users SET name = 'test'", "UPDATE"),
            ("DELETE FROM users WHERE id = 1", "DELETE"),
            ("CREATE TABLE test (id INT)", "CREATE"),
            ("ALTER TABLE users ADD COLUMN age INT", "ALTER"),
            ("DROP TABLE test", "DROP"),
            ("WITH cte AS (SELECT * FROM users) SELECT * FROM cte", "SELECT"),
            ("INVALID SQL STATEMENT", "UNKNOWN"),
        ]

        for sql, expected_type in test_cases:
            result = summarization_service._extract_query_type(sql)
            assert result == expected_type

    async def test_health_check(self, summarization_service):
        """Test health check."""
        await summarization_service.initialize()

        status = await summarization_service.health_check()

        assert isinstance(status, dict)
        assert "initialized" in status
        assert "llm_service_available" in status
        assert status["initialized"] is True

    async def test_error_handling_not_initialized(
        self, summarization_service, sample_table_schema
    ):
        """Test error handling when service not initialized."""
        with pytest.raises(RuntimeError, match="Summarization service not initialized"):
            await summarization_service.summarize_table(sample_table_schema)

    async def test_error_handling_in_batch_processing(
        self, summarization_service, sample_table_schema
    ):
        """Test error handling in batch processing."""
        await summarization_service.initialize()

        # Create a table that will cause an error
        bad_table = TableSchema(
            name="",  # Invalid name
            database_id="db-123",
            columns=[],
        )

        tables = [sample_table_schema, bad_table]
        summaries = await summarization_service.batch_summarize_tables(
            tables, batch_size=1
        )

        # Should have results for both tables, with error for the bad one
        assert len(summaries) == 2
        assert "db-123:users" in summaries
        assert "db-123:" in summaries  # Bad table with empty name
