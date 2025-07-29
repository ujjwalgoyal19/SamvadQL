"""Tests for data model validation logic."""

import pytest
from datetime import datetime
from uuid import uuid4
from pydantic import ValidationError

from models import (
    QueryRequest,
    QueryResponse,
    TableSchema,
    ColumnSchema,
    ValidationResult,
    ValidationStatus,
)


class TestColumnSchema:
    """Tests for ColumnSchema validation."""

    def test_valid_column_schema(self):
        """Test valid column schema creation."""
        column = ColumnSchema(
            name="user_id",
            data_type="integer",
            description="User identifier",
            sample_values=[1, 2, 3],
            is_nullable=False,
            is_primary_key=True,
            is_foreign_key=False,
        )

        assert column.name == "user_id"
        assert column.data_type == "integer"
        assert column.is_primary_key is True
        assert column.is_nullable is False

    def test_invalid_column_name(self):
        """Test invalid column name validation."""
        with pytest.raises(ValidationError) as exc_info:
            ColumnSchema(
                name="123invalid",
                data_type="integer",  # Cannot start with number
                description="Test column",
                is_nullable=True,
                is_primary_key=False,
                is_foreign_key=False,
            )

        assert "Column name must start with letter or underscore" in str(exc_info.value)

    def test_primary_key_cannot_be_nullable(self):
        """Test that primary key columns cannot be nullable."""
        with pytest.raises(ValidationError) as exc_info:
            ColumnSchema(
                name="id",
                data_type="integer",
                is_primary_key=True,
                is_nullable=True,
                description="Test column",
                is_foreign_key=False,
            )

        assert "Primary key columns cannot be nullable" in str(exc_info.value)

    def test_too_many_sample_values(self):
        """Test validation of too many sample values."""
        with pytest.raises(ValidationError) as exc_info:
            ColumnSchema(
                name="test_col",
                data_type="integer",
                sample_values=list(range(25)),  # More than 20
                description="Test column",
                is_nullable=True,
                is_primary_key=False,
                is_foreign_key=False,
            )

        assert "Too many sample values" in str(exc_info.value)

    def test_data_type_normalization(self):
        """Test data type normalization to lowercase."""
        column = ColumnSchema(
            name="test_col",
            data_type="VARCHAR(255)",
            description="Test column",
            is_nullable=True,
            is_primary_key=False,
            is_foreign_key=False,
        )

        assert column.data_type == "varchar(255)"


class TestTableSchema:
    """Tests for TableSchema validation."""

    def test_valid_table_schema(self):
        """Test valid table schema creation."""
        columns = [
            ColumnSchema(
                name="id",
                data_type="integer",
                is_primary_key=True,
                is_nullable=False,
                description="Primary key",
                is_foreign_key=False,
            ),
            ColumnSchema(
                name="name",
                data_type="varchar(255)",
                description="User name",
                is_nullable=True,
                is_primary_key=False,
                is_foreign_key=False,
            ),
        ]

        table = TableSchema(
            name="users",
            database_id=str(uuid4()),
            columns=columns,
            description="User table",
            tier="gold",
            tags=["user-data", "core"],
            row_count=1000,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        assert table.name == "users"
        assert len(table.columns) == 2
        assert table.tier == "gold"
        assert table.row_count == 1000

    def test_invalid_table_name(self):
        """Test invalid table name validation."""
        columns = [
            ColumnSchema(
                name="id",
                data_type="integer",
                description="Test column",
                is_nullable=False,
                is_primary_key=True,
                is_foreign_key=False,
            )
        ]

        with pytest.raises(ValidationError) as exc_info:
            TableSchema(
                name="123invalid",  # Cannot start with number
                database_id=str(uuid4()),
                columns=columns,
                description="Test table",
                tier="bronze",
                row_count=0,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

        assert "Table name must start with letter or underscore" in str(exc_info.value)

    def test_invalid_database_id(self):
        """Test invalid database ID validation."""
        columns = [
            ColumnSchema(
                name="id",
                data_type="integer",
                description="Test column",
                is_nullable=False,
                is_primary_key=True,
                is_foreign_key=False,
            )
        ]

        with pytest.raises(ValidationError) as exc_info:
            TableSchema(
                name="users",
                database_id="not-a-uuid",
                columns=columns,
                description="Test table",
                tier="bronze",
                row_count=0,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

        assert "Database ID must be a valid UUID" in str(exc_info.value)

    def test_empty_columns_list(self):
        """Test that tables must have at least one column."""
        with pytest.raises(ValidationError) as exc_info:
            TableSchema(
                name="users",
                database_id=str(uuid4()),
                columns=[],
                description="Test table",
                tier="bronze",
                row_count=0,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

        assert "List should have at least 1 item" in str(exc_info.value)

    def test_invalid_tier(self):
        """Test invalid tier validation."""
        columns = [
            ColumnSchema(
                name="id",
                data_type="integer",
                description="Test column",
                is_nullable=False,
                is_primary_key=True,
                is_foreign_key=False,
            )
        ]

        with pytest.raises(ValidationError) as exc_info:
            TableSchema(
                name="users",
                database_id=str(uuid4()),
                columns=columns,
                tier="invalid_tier",
                description="Test table",
                row_count=0,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

        assert "Invalid tier" in str(exc_info.value)

    def test_too_many_tags(self):
        """Test validation of too many tags."""
        columns = [
            ColumnSchema(
                name="id",
                data_type="integer",
                description="Test column",
                is_nullable=False,
                is_primary_key=True,
                is_foreign_key=False,
            )
        ]

        with pytest.raises(ValidationError) as exc_info:
            TableSchema(
                name="users",
                database_id=str(uuid4()),
                columns=columns,
                description="Test table",
                tier="bronze",
                tags=[f"tag{i}" for i in range(25)],  # More than 20
                row_count=0,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

        assert "Too many tags" in str(exc_info.value)

    def test_invalid_tag_format(self):
        """Test invalid tag format validation."""
        columns = [
            ColumnSchema(
                name="id",
                data_type="integer",
                description="Test column",
                is_nullable=False,
                is_primary_key=True,
                is_foreign_key=False,
            )
        ]

        with pytest.raises(ValidationError) as exc_info:
            TableSchema(
                name="users",
                database_id=str(uuid4()),
                columns=columns,
                description="Test table",
                tier="bronze",
                tags=["valid-tag", "invalid tag with spaces"],
                row_count=0,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

        assert "Tags can only contain alphanumeric characters" in str(exc_info.value)


class TestQueryRequest:
    """Tests for QueryRequest validation."""

    def test_valid_query_request(self):
        """Test valid query request creation."""
        request = QueryRequest(
            query="Show me all users from last month",
            user_id="user123",
            database_id=str(uuid4()),
            session_id=str(uuid4()),
            selected_tables=["users", "signups"],
            context={"timezone": "UTC"},
        )

        assert request.query == "Show me all users from last month"
        assert request.user_id == "user123"
        assert request.selected_tables is not None
        assert len(request.selected_tables) == 2

    def test_empty_query(self):
        """Test empty query validation."""
        with pytest.raises(ValidationError) as exc_info:
            QueryRequest(
                query="",
                user_id="user123",
                database_id=str(uuid4()),
                session_id=str(uuid4()),
                selected_tables=[],
                context={},
            )

        assert "String should have at least 1 character" in str(exc_info.value)

    def test_whitespace_only_query(self):
        """Test whitespace-only query validation."""
        with pytest.raises(ValidationError) as exc_info:
            QueryRequest(
                query="   \n\t   ",
                user_id="user123",
                database_id=str(uuid4()),
                session_id=str(uuid4()),
                selected_tables=[],
                context={},
            )

        assert "Query cannot be empty" in str(exc_info.value)

    def test_malicious_query_content(self):
        """Test detection of potentially malicious content."""
        with pytest.raises(ValidationError) as exc_info:
            QueryRequest(
                query="<script>alert('xss')</script>",
                user_id="user123",
                database_id=str(uuid4()),
                session_id=str(uuid4()),
                selected_tables=[],
                context={},
            )

        assert "potentially unsafe content" in str(exc_info.value)

    def test_invalid_user_id_format(self):
        """Test invalid user ID format validation."""
        with pytest.raises(ValidationError) as exc_info:
            QueryRequest(
                query="test query",
                user_id="user@domain.com",  # Contains invalid characters
                database_id=str(uuid4()),
                session_id=str(uuid4()),
                selected_tables=[],
                context={},
            )

        assert "User ID can only contain alphanumeric characters" in str(exc_info.value)

    def test_invalid_database_id_format(self):
        """Test invalid database ID format validation."""
        with pytest.raises(ValidationError) as exc_info:
            QueryRequest(
                query="test query",
                user_id="user123",
                database_id="not-a-uuid",
                session_id=str(uuid4()),
                selected_tables=[],
                context={},
            )

        assert "Database ID must be a valid UUID" in str(exc_info.value)

    def test_too_many_selected_tables(self):
        """Test validation of too many selected tables."""
        with pytest.raises(ValidationError) as exc_info:
            QueryRequest(
                query="test query",
                user_id="user123",
                database_id=str(uuid4()),
                session_id=str(uuid4()),
                selected_tables=[f"table{i}" for i in range(55)],  # More than 50
                context={},
            )

        assert "Too many selected tables" in str(exc_info.value)

    def test_invalid_table_name_format(self):
        """Test invalid table name format in selected tables."""
        with pytest.raises(ValidationError) as exc_info:
            QueryRequest(
                query="test query",
                user_id="user123",
                database_id=str(uuid4()),
                session_id=str(uuid4()),
                selected_tables=["valid_table", "123invalid"],  # Invalid table name
                context={},
            )

        assert "Invalid table name format" in str(exc_info.value)


class TestValidationResult:
    """Tests for ValidationResult validation."""

    def test_valid_validation_result(self):
        """Test valid validation result creation."""
        result = ValidationResult(
            is_valid=True,
            warnings=["Query may be slow"],
            estimated_cost=125.5,
            is_destructive=False,
            execution_plan="Sequential scan on users table",
        )

        assert result.is_valid is True
        assert len(result.warnings) == 1
        assert result.estimated_cost == 125.5

    def test_invalid_sql_must_have_errors(self):
        """Test that invalid SQL must have error messages."""
        with pytest.raises(ValidationError) as exc_info:
            ValidationResult(
                is_valid=False,
                errors=[],
                is_destructive=False,
                estimated_cost=0.0,
                execution_plan="",
            )  # Invalid SQL without errors

        assert "Invalid SQL must have at least one error message" in str(exc_info.value)

    def test_valid_sql_cannot_have_errors(self):
        """Test that valid SQL cannot have error messages."""
        with pytest.raises(ValidationError) as exc_info:
            ValidationResult(
                is_valid=True,
                errors=["Some error"],  # Valid SQL with errors
                is_destructive=False,
                estimated_cost=0.0,
                execution_plan="",
            )

        assert "Valid SQL cannot have error messages" in str(exc_info.value)

    def test_negative_estimated_cost(self):
        """Test validation of negative estimated cost."""
        with pytest.raises(ValidationError) as exc_info:
            ValidationResult(
                is_valid=True,
                estimated_cost=-10.0,
                is_destructive=False,
                execution_plan="",
            )

        assert "Input should be greater than or equal to 0" in str(exc_info.value)

    def test_empty_error_messages(self):
        """Test validation of empty error messages."""
        with pytest.raises(ValidationError) as exc_info:
            ValidationResult(
                is_valid=False,
                errors=["Valid error", ""],  # Empty error message
                is_destructive=False,
                estimated_cost=0.0,
                execution_plan="",
            )

        assert "Error and warning messages must be non-empty strings" in str(
            exc_info.value
        )


class TestQueryResponse:
    """Tests for QueryResponse validation."""

    def test_valid_query_response(self):
        """Test valid query response creation."""
        response = QueryResponse(
            sql="SELECT * FROM users",
            explanation="This query selects all users",
            confidence_score=0.95,
            selected_tables=["users"],
            validation_status=ValidationStatus.VALID,
            execution_time_estimate=0.25,
            request_id=str(uuid4()),
        )

        assert response.sql == "SELECT * FROM users"
        assert response.confidence_score == 0.95
        assert len(response.selected_tables) == 1

    def test_empty_sql(self):
        """Test empty SQL validation."""
        with pytest.raises(ValidationError) as exc_info:
            QueryResponse(
                sql="",
                explanation="Test explanation",
                confidence_score=0.95,
                selected_tables=["users"],
                validation_status=ValidationStatus.VALID,
                execution_time_estimate=0.25,
                request_id=str(uuid4()),
            )

        assert "String should have at least 1 character" in str(exc_info.value)

    def test_invalid_sql_start(self):
        """Test SQL must start with valid keyword."""
        with pytest.raises(ValidationError) as exc_info:
            QueryResponse(
                sql="INVALID QUERY",
                explanation="Test explanation",
                confidence_score=0.95,
                selected_tables=["users"],
                validation_status=ValidationStatus.VALID,
                execution_time_estimate=0.25,
                request_id=str(uuid4()),
            )

        assert "SQL must start with a valid SQL keyword" in str(exc_info.value)

    def test_confidence_score_out_of_range(self):
        """Test confidence score must be between 0 and 1."""
        with pytest.raises(ValidationError) as exc_info:
            QueryResponse(
                sql="SELECT * FROM users",
                explanation="Test explanation",
                confidence_score=1.5,  # Greater than 1
                selected_tables=["users"],
                validation_status=ValidationStatus.VALID,
                execution_time_estimate=0.25,
                request_id=str(uuid4()),
            )

        assert "Input should be less than or equal to 1" in str(exc_info.value)

    def test_empty_selected_tables(self):
        """Test that at least one table must be selected."""
        with pytest.raises(ValidationError) as exc_info:
            QueryResponse(
                sql="SELECT * FROM users",
                explanation="Test explanation",
                confidence_score=0.95,
                selected_tables=[],  # Empty list
                validation_status=ValidationStatus.VALID,
                execution_time_estimate=0.25,
                request_id=str(uuid4()),
            )

        assert "At least one table must be selected" in str(exc_info.value)

    def test_explanation_too_long(self):
        """Test explanation length validation."""
        with pytest.raises(ValidationError) as exc_info:
            QueryResponse(
                sql="SELECT * FROM users",
                explanation="x" * 5001,  # Too long
                confidence_score=0.95,
                selected_tables=["users"],
                validation_status=ValidationStatus.VALID,
                execution_time_estimate=0.25,
                request_id=str(uuid4()),
            )

        assert "Explanation is too long" in str(exc_info.value)

    def test_negative_execution_time(self):
        """Test negative execution time validation."""
        with pytest.raises(ValidationError) as exc_info:
            QueryResponse(
                sql="SELECT * FROM users",
                explanation="Test explanation",
                confidence_score=0.95,
                selected_tables=["users"],
                validation_status=ValidationStatus.VALID,
                execution_time_estimate=-1.0,
                request_id=str(uuid4()),
            )

        assert "Input should be greater than or equal to 0" in str(exc_info.value)

    def test_invalid_request_id_format(self):
        """Test invalid request ID format validation."""
        with pytest.raises(ValidationError) as exc_info:
            QueryResponse(
                sql="SELECT * FROM users",
                explanation="Test explanation",
                confidence_score=0.95,
                selected_tables=["users"],
                validation_status=ValidationStatus.VALID,
                execution_time_estimate=0.25,
                request_id="not-a-uuid",
            )

        assert "Request ID must be a valid UUID" in str(exc_info.value)
