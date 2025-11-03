"""
Integration tests for API v1 endpoints.
"""

import asyncio
import json
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient
from httpx import AsyncClient

from main import app
from models import (
    QueryRequest,
    QueryResponse,
    TableSchema,
    ColumnSchema,
    UserFeedback,
    ValidationResult,
    ValidationStatus,
    DatabaseType,
)


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def async_client():
    """Async test client fixture."""
    return AsyncClient(app=app, base_url="http://test")


@pytest.fixture
def sample_query_request():
    """Sample query request fixture."""
    return {
        "query": "Show me all users who signed up last month",
        "user_id": "test_user_123",
        "database_id": str(uuid4()),
        "selected_tables": ["users"],
        "context": {"timezone": "UTC"},
        "session_id": "test_session_123",
    }


@pytest.fixture
def sample_table_schema():
    """Sample table schema fixture."""
    return TableSchema(
        name="users",
        database_id=str(uuid4()),
        columns=[
            ColumnSchema(
                name="id",
                data_type="integer",
                description="Primary key",
                is_primary_key=True,
                is_nullable=False,
            ),
            ColumnSchema(
                name="email",
                data_type="varchar",
                description="User email",
                is_nullable=False,
            ),
        ],
        description="User accounts table",
        tier="gold",
        tags=["users", "core"],
    )


class TestQueryEndpoint:
    """Test cases for the /api/v1/query endpoint."""

    @patch("api.v1.query_service")
    def test_submit_query_success(
        self, mock_query_service, client, sample_query_request
    ):
        """Test successful query submission."""
        # Mock the query service response
        mock_response = QueryResponse(
            sql="SELECT * FROM users WHERE created_at >= '2024-01-01'",
            explanation="This query retrieves all users created after January 1st, 2024",
            confidence_score=0.95,
            selected_tables=["users"],
            validation_status=ValidationStatus.VALID,
        )

        async def mock_generate():
            yield mock_response

        mock_query_service.generate_sql.return_value = mock_generate()

        # Make request
        response = client.post("/api/v1/query", json=sample_query_request)

        # Verify response
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"

        # Verify service was called
        mock_query_service.generate_sql.assert_called_once()

    def test_submit_query_empty_query(self, client):
        """Test query submission with empty query."""
        request_data = {
            "query": "",
            "user_id": "test_user",
            "database_id": str(uuid4()),
        }

        response = client.post("/api/v1/query", json=request_data)
        assert response.status_code == 422  # Pydantic validation error
        assert "String should have at least 1 character" in str(response.json())

    def test_submit_query_invalid_request(self, client):
        """Test query submission with invalid request data."""
        request_data = {
            "query": "test query",
            # Missing required fields
        }

        response = client.post("/api/v1/query", json=request_data)
        assert response.status_code == 422  # Validation error


class TestTablesEndpoint:
    """Test cases for the /api/v1/tables/{database_id} endpoint."""

    @patch("api.v1.metadata_service")
    def test_get_tables_success(
        self, mock_metadata_service, client, sample_table_schema
    ):
        """Test successful table retrieval."""
        database_id = str(uuid4())

        # Mock metadata service responses
        async def mock_list_tables():
            return ["users", "orders"]

        async def mock_get_metadata():
            return sample_table_schema

        mock_metadata_service.list_tables.return_value = mock_list_tables()
        mock_metadata_service.get_table_metadata.return_value = mock_get_metadata()

        # Make request
        response = client.get(f"/api/v1/tables/{database_id}")

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["database_id"] == database_id
        assert "tables" in data
        assert data["total_count"] >= 0
        assert data["page"] == 1
        assert data["page_size"] == 50

    def test_get_tables_with_pagination(self, client):
        """Test table retrieval with pagination parameters."""
        database_id = str(uuid4())

        response = client.get(
            f"/api/v1/tables/{database_id}", params={"page": 2, "page_size": 10}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["page_size"] == 10

    def test_get_tables_with_search_filter(self, client):
        """Test table retrieval with search filter."""
        database_id = str(uuid4())

        response = client.get(
            f"/api/v1/tables/{database_id}", params={"search": "user"}
        )

        assert response.status_code == 200

    def test_get_tables_with_tier_filter(self, client):
        """Test table retrieval with tier filter."""
        database_id = str(uuid4())

        response = client.get(f"/api/v1/tables/{database_id}", params={"tier": "gold"})

        assert response.status_code == 200

    def test_get_tables_with_tags_filter(self, client):
        """Test table retrieval with tags filter."""
        database_id = str(uuid4())

        response = client.get(
            f"/api/v1/tables/{database_id}", params={"tags": "users,core"}
        )

        assert response.status_code == 200


class TestValidateEndpoint:
    """Test cases for the /api/v1/validate endpoint."""

    def test_validate_sql_success(self, client):
        """Test successful SQL validation."""
        request_data = {
            "sql": "SELECT * FROM users WHERE id = 1",
            "database_id": str(uuid4()),
            "database_type": "postgresql",
        }

        response = client.post("/api/v1/validate", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert "is_valid" in data
        assert "errors" in data
        assert "warnings" in data
        assert "is_destructive" in data

    def test_validate_sql_empty_query(self, client):
        """Test SQL validation with empty query."""
        request_data = {
            "sql": "",
            "database_id": str(uuid4()),
        }

        response = client.post("/api/v1/validate", json=request_data)

        assert response.status_code == 422  # Pydantic validation error
        assert "String should have at least 1 character" in str(response.json())

    def test_validate_sql_destructive_operation(self, client):
        """Test SQL validation with destructive operation."""
        request_data = {
            "sql": "DELETE FROM users WHERE id = 1",
            "database_id": str(uuid4()),
        }

        response = client.post("/api/v1/validate", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["is_destructive"] is True

    def test_validate_sql_invalid_syntax(self, client):
        """Test SQL validation with invalid syntax."""
        request_data = {
            "sql": "INVALID SQL QUERY (",
            "database_id": str(uuid4()),
        }

        response = client.post("/api/v1/validate", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is False
        assert len(data["errors"]) > 0


class TestFeedbackEndpoint:
    """Test cases for the /api/v1/feedback endpoint."""

    @patch("api.v1.feedback_repository")
    def test_submit_feedback_success(self, mock_feedback_repo, client):
        """Test successful feedback submission."""
        request_data = {
            "user_id": "test_user_123",
            "query_id": str(uuid4()),
            "original_query": "Show me all users",
            "generated_sql": "SELECT * FROM users",
            "feedback_type": "accept",
            "comments": "Great query!",
            "rating": 5,
        }

        # Mock repository
        async def mock_create():
            return None

        mock_feedback_repo.create.return_value = mock_create()

        response = client.post("/api/v1/feedback", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "feedback_id" in data

    def test_submit_feedback_invalid_type(self, client):
        """Test feedback submission with invalid feedback type."""
        request_data = {
            "user_id": "test_user_123",
            "query_id": str(uuid4()),
            "original_query": "Show me all users",
            "generated_sql": "SELECT * FROM users",
            "feedback_type": "invalid_type",
        }

        response = client.post("/api/v1/feedback", json=request_data)
        assert response.status_code == 422  # Validation error

    def test_submit_feedback_invalid_rating(self, client):
        """Test feedback submission with invalid rating."""
        request_data = {
            "user_id": "test_user_123",
            "query_id": str(uuid4()),
            "original_query": "Show me all users",
            "generated_sql": "SELECT * FROM users",
            "feedback_type": "accept",
            "rating": 10,  # Invalid rating (should be 1-5)
        }

        response = client.post("/api/v1/feedback", json=request_data)
        assert response.status_code == 422  # Validation error

    @patch("api.v1.feedback_repository")
    def test_get_feedback_stats(self, mock_feedback_repo, client):
        """Test feedback statistics retrieval."""
        # Mock repository response
        mock_stats = {
            "accept": {"count": 100, "avg_rating": 4.5},
            "reject": {"count": 20, "avg_rating": 2.0},
        }

        async def mock_get_stats():
            return mock_stats

        mock_feedback_repo.get_feedback_stats.return_value = mock_get_stats()

        response = client.get("/api/v1/feedback/stats?days=30")

        assert response.status_code == 200
        data = response.json()
        assert data["period_days"] == 30
        assert "stats" in data


class TestHealthEndpoint:
    """Test cases for the /api/v1/health endpoint."""

    @patch("api.v1.query_service")
    def test_health_check_success(self, mock_query_service, client):
        """Test successful health check."""

        # Mock service health
        async def mock_health_check():
            return {"status": "healthy"}

        mock_query_service.health_check.return_value = mock_health_check()

        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "services" in data


class TestStreamingResponse:
    """Test cases for streaming responses."""

    @pytest.mark.asyncio
    @patch("api.v1.query_service")
    async def test_streaming_query_response(
        self, mock_query_service, async_client, sample_query_request
    ):
        """Test streaming query response."""
        # Mock streaming response
        mock_responses = [
            QueryResponse(
                sql="SELECT 1 as generating",
                explanation="Generating query...",
                confidence_score=0.0,
                selected_tables=["generating"],
                validation_status=ValidationStatus.INVALID,
            ),
            QueryResponse(
                sql="SELECT * FROM users",
                explanation="Final query",
                confidence_score=0.95,
                selected_tables=["users"],
                validation_status=ValidationStatus.VALID,
            ),
        ]

        async def mock_generate():
            for response in mock_responses:
                yield response

        mock_query_service.generate_sql.return_value = mock_generate()

        # Make streaming request
        async with async_client as client:
            async with client.stream(
                "POST", "/api/v1/query", json=sample_query_request
            ) as response:
                assert response.status_code == 200
                assert response.headers["content-type"] == "text/plain; charset=utf-8"

                # Read streaming content
                content_chunks = []
                async for chunk in response.aiter_text():
                    if chunk.strip():
                        content_chunks.append(chunk)

                assert len(content_chunks) > 0


class TestErrorHandling:
    """Test cases for error handling."""

    @patch("api.v1.query_service")
    def test_query_service_error(
        self, mock_query_service, client, sample_query_request
    ):
        """Test handling of query service errors."""
        # Mock service error
        mock_query_service.generate_sql.side_effect = Exception("Service unavailable")

        response = client.post("/api/v1/query", json=sample_query_request)

        assert response.status_code == 500
        assert "Internal server error" in response.json()["detail"]

    @patch("api.v1.metadata_service")
    def test_metadata_service_error(self, mock_metadata_service, client):
        """Test handling of metadata service errors."""
        database_id = str(uuid4())

        # Mock service error
        mock_metadata_service.list_tables.side_effect = Exception(
            "Database connection failed"
        )

        response = client.get(f"/api/v1/tables/{database_id}")

        # Should return empty response instead of error
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 0
        assert len(data["tables"]) == 0

    @patch("api.v1.feedback_repository")
    def test_feedback_repository_error(self, mock_feedback_repo, client):
        """Test handling of feedback repository errors."""
        request_data = {
            "user_id": "test_user_123",
            "query_id": str(uuid4()),
            "original_query": "Show me all users",
            "generated_sql": "SELECT * FROM users",
            "feedback_type": "accept",
        }

        # Mock repository error
        mock_feedback_repo.create.side_effect = Exception("Database error")

        # Should still return success since it's handled in background
        response = client.post("/api/v1/feedback", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


if __name__ == "__main__":
    pytest.main([__file__])
