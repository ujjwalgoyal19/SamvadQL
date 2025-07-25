"""Tests for repository implementations."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from models.base import UserFeedback, AuditLogEntry
from repositories.user_feedback import UserFeedbackRepository
from repositories.audit_log import AuditLogRepository
from repositories.query_execution import QueryExecutionRepository, QueryExecutionLog


@pytest.mark.asyncio
class TestUserFeedbackRepository:
    """Tests for UserFeedbackRepository."""

    @pytest.fixture
    def repository(self):
        """Create repository instance with mocked database manager."""
        repo = UserFeedbackRepository()
        repo._db_manager = AsyncMock()
        return repo

    @pytest.fixture
    def sample_feedback(self):
        """Sample user feedback data."""
        return UserFeedback(
            id=str(uuid4()),
            user_id="test_user",
            query_id=str(uuid4()),
            original_query="Show me all users",
            generated_sql="SELECT * FROM users",
            feedback_type="accept",
            rating=5,
            comments="Great query!",
            created_at=datetime.utcnow(),
        )

    def test_table_name(self, repository):
        """Test table name is correct."""
        assert repository.get_table_name() == "user_feedback"

    def test_to_dict(self, repository, sample_feedback):
        """Test converting feedback to dictionary."""
        result = repository.to_dict(sample_feedback)

        assert result["id"] == sample_feedback.id
        assert result["user_id"] == sample_feedback.user_id
        assert result["query_id"] == sample_feedback.query_id
        assert result["original_query"] == sample_feedback.original_query
        assert result["generated_sql"] == sample_feedback.generated_sql
        assert result["feedback_type"] == sample_feedback.feedback_type
        assert result["rating"] == sample_feedback.rating
        assert result["comments"] == sample_feedback.comments
        assert result["created_at"] == sample_feedback.created_at

    def test_from_dict(self, repository):
        """Test converting dictionary to feedback."""
        data = {
            "id": str(uuid4()),
            "user_id": "test_user",
            "query_id": str(uuid4()),
            "original_query": "Show me all users",
            "generated_sql": "SELECT * FROM users",
            "feedback_type": "accept",
            "rating": 5,
            "comments": "Great query!",
            "created_at": datetime.utcnow(),
        }

        result = repository.from_dict(data)

        assert isinstance(result, UserFeedback)
        assert result.id == data["id"]
        assert result.user_id == data["user_id"]
        assert result.query_id == data["query_id"]
        assert result.original_query == data["original_query"]
        assert result.generated_sql == data["generated_sql"]
        assert result.feedback_type == data["feedback_type"]
        assert result.rating == data["rating"]
        assert result.comments == data["comments"]
        assert result.created_at == data["created_at"]

    async def test_get_by_user_id(self, repository):
        """Test getting feedback by user ID."""
        mock_connection = AsyncMock()
        mock_row = {
            "id": str(uuid4()),
            "user_id": "test_user",
            "query_id": str(uuid4()),
            "original_query": "test query",
            "generated_sql": "SELECT 1",
            "feedback_type": "accept",
            "rating": None,
            "comments": None,
            "created_at": datetime.utcnow(),
        }

        repository._db_manager.get_connection.return_value.__aenter__.return_value = (
            mock_connection
        )
        mock_connection.fetch.return_value = [mock_row]

        result = await repository.get_by_user_id("test_user", limit=10)

        assert len(result) == 1
        assert isinstance(result[0], UserFeedback)
        assert result[0].user_id == "test_user"

    async def test_get_feedback_stats(self, repository):
        """Test getting feedback statistics."""
        mock_connection = AsyncMock()
        mock_rows = [
            {"feedback_type": "accept", "count": 10, "avg_rating": 4.5},
            {"feedback_type": "reject", "count": 3, "avg_rating": 2.0},
        ]

        repository._db_manager.get_connection.return_value.__aenter__.return_value = (
            mock_connection
        )
        mock_connection.fetch.return_value = mock_rows

        result = await repository.get_feedback_stats()

        assert "accept" in result
        assert result["accept"]["count"] == 10
        assert result["accept"]["avg_rating"] == 4.5
        assert "reject" in result
        assert result["reject"]["count"] == 3
        assert result["reject"]["avg_rating"] == 2.0


@pytest.mark.asyncio
class TestAuditLogRepository:
    """Tests for AuditLogRepository."""

    @pytest.fixture
    def repository(self):
        """Create repository instance with mocked database manager."""
        repo = AuditLogRepository()
        repo._db_manager = AsyncMock()
        return repo

    @pytest.fixture
    def sample_audit_entry(self):
        """Sample audit log entry."""
        return AuditLogEntry(
            id=str(uuid4()),
            user_id="test_user",
            action="query_generated",
            resource_type="query",
            resource_id=str(uuid4()),
            details={"query": "SELECT * FROM users"},
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            created_at=datetime.utcnow(),
        )

    def test_table_name(self, repository):
        """Test table name is correct."""
        assert repository.get_table_name() == "audit_log"

    def test_to_dict(self, repository, sample_audit_entry):
        """Test converting audit entry to dictionary."""
        result = repository.to_dict(sample_audit_entry)

        assert result["id"] == sample_audit_entry.id
        assert result["user_id"] == sample_audit_entry.user_id
        assert result["action"] == sample_audit_entry.action
        assert result["resource_type"] == sample_audit_entry.resource_type
        assert result["resource_id"] == sample_audit_entry.resource_id
        assert result["details"] == sample_audit_entry.details
        assert result["ip_address"] == sample_audit_entry.ip_address
        assert result["user_agent"] == sample_audit_entry.user_agent
        assert result["created_at"] == sample_audit_entry.created_at

    def test_from_dict(self, repository):
        """Test converting dictionary to audit entry."""
        data = {
            "id": str(uuid4()),
            "user_id": "test_user",
            "action": "query_generated",
            "resource_type": "query",
            "resource_id": str(uuid4()),
            "details": {"query": "SELECT * FROM users"},
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0",
            "created_at": datetime.utcnow(),
        }

        result = repository.from_dict(data)

        assert isinstance(result, AuditLogEntry)
        assert result.id == data["id"]
        assert result.user_id == data["user_id"]
        assert result.action == data["action"]
        assert result.resource_type == data["resource_type"]
        assert result.resource_id == data["resource_id"]
        assert result.details == data["details"]
        assert result.ip_address == data["ip_address"]
        assert result.user_agent == data["user_agent"]
        assert result.created_at == data["created_at"]

    async def test_log_action(self, repository):
        """Test logging an action."""
        mock_connection = AsyncMock()
        mock_row = {
            "id": str(uuid4()),
            "user_id": "test_user",
            "action": "query_generated",
            "resource_type": "query",
            "resource_id": None,
            "details": {"test": "data"},
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0",
            "created_at": datetime.utcnow(),
        }

        repository._db_manager.get_connection.return_value.__aenter__.return_value = (
            mock_connection
        )
        mock_connection.fetchrow.return_value = mock_row

        result = await repository.log_action(
            user_id="test_user",
            action="query_generated",
            resource_type="query",
            details={"test": "data"},
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
        )

        assert isinstance(result, AuditLogEntry)
        assert result.user_id == "test_user"
        assert result.action == "query_generated"
        assert result.resource_type == "query"

    async def test_get_activity_summary(self, repository):
        """Test getting activity summary."""
        mock_connection = AsyncMock()
        mock_rows = [
            {
                "action": "query_generated",
                "resource_type": "query",
                "count": 100,
                "unique_users": 25,
            },
            {
                "action": "feedback_submitted",
                "resource_type": "feedback",
                "count": 50,
                "unique_users": 20,
            },
        ]

        repository._db_manager.get_connection.return_value.__aenter__.return_value = (
            mock_connection
        )
        mock_connection.fetch.return_value = mock_rows

        result = await repository.get_activity_summary()

        assert len(result) == 2
        assert result[0]["action"] == "query_generated"
        assert result[0]["count"] == 100
        assert result[0]["unique_users"] == 25
        assert result[1]["action"] == "feedback_submitted"
        assert result[1]["count"] == 50
        assert result[1]["unique_users"] == 20


@pytest.mark.asyncio
class TestQueryExecutionRepository:
    """Tests for QueryExecutionRepository."""

    @pytest.fixture
    def repository(self):
        """Create repository instance with mocked database manager."""
        repo = QueryExecutionRepository()
        repo._db_manager = AsyncMock()
        return repo

    @pytest.fixture
    def sample_query_log(self):
        """Sample query execution log."""
        return QueryExecutionLog(
            id=str(uuid4()),
            query_id=str(uuid4()),
            user_id="test_user",
            original_query="Show me all users",
            generated_sql="SELECT * FROM users",
            schema_versions={"users": "v1.0"},
            execution_timestamp=datetime.utcnow(),
            execution_result="success",
            error_message=None,
            performance_metrics={"execution_time_ms": 150},
        )

    def test_table_name(self, repository):
        """Test table name is correct."""
        assert repository.get_table_name() == "query_execution_log"

    def test_to_dict(self, repository, sample_query_log):
        """Test converting query log to dictionary."""
        result = repository.to_dict(sample_query_log)

        assert result["id"] == sample_query_log.id
        assert result["query_id"] == sample_query_log.query_id
        assert result["user_id"] == sample_query_log.user_id
        assert result["original_query"] == sample_query_log.original_query
        assert result["generated_sql"] == sample_query_log.generated_sql
        assert result["schema_versions"] == sample_query_log.schema_versions
        assert result["execution_timestamp"] == sample_query_log.execution_timestamp
        assert result["execution_result"] == sample_query_log.execution_result
        assert result["error_message"] == sample_query_log.error_message
        assert result["performance_metrics"] == sample_query_log.performance_metrics

    def test_from_dict(self, repository):
        """Test converting dictionary to query log."""
        data = {
            "id": str(uuid4()),
            "query_id": str(uuid4()),
            "user_id": "test_user",
            "original_query": "Show me all users",
            "generated_sql": "SELECT * FROM users",
            "schema_versions": {"users": "v1.0"},
            "execution_timestamp": datetime.utcnow(),
            "execution_result": "success",
            "error_message": None,
            "performance_metrics": {"execution_time_ms": 150},
        }

        result = repository.from_dict(data)

        assert isinstance(result, QueryExecutionLog)
        assert result.id == data["id"]
        assert result.query_id == data["query_id"]
        assert result.user_id == data["user_id"]
        assert result.original_query == data["original_query"]
        assert result.generated_sql == data["generated_sql"]
        assert result.schema_versions == data["schema_versions"]
        assert result.execution_timestamp == data["execution_timestamp"]
        assert result.execution_result == data["execution_result"]
        assert result.error_message == data["error_message"]
        assert result.performance_metrics == data["performance_metrics"]

    async def test_log_query_execution(self, repository):
        """Test logging query execution."""
        mock_connection = AsyncMock()
        mock_row = {
            "id": str(uuid4()),
            "query_id": str(uuid4()),
            "user_id": "test_user",
            "original_query": "Show me all users",
            "generated_sql": "SELECT * FROM users",
            "schema_versions": {"users": "v1.0"},
            "execution_timestamp": datetime.utcnow(),
            "execution_result": "success",
            "error_message": None,
            "performance_metrics": {"execution_time_ms": 150},
        }

        repository._db_manager.get_connection.return_value.__aenter__.return_value = (
            mock_connection
        )
        mock_connection.fetchrow.return_value = mock_row

        result = await repository.log_query_execution(
            query_id=str(uuid4()),
            user_id="test_user",
            original_query="Show me all users",
            generated_sql="SELECT * FROM users",
            schema_versions={"users": "v1.0"},
            execution_result="success",
            performance_metrics={"execution_time_ms": 150},
        )

        assert isinstance(result, QueryExecutionLog)
        assert result.user_id == "test_user"
        assert result.original_query == "Show me all users"
        assert result.generated_sql == "SELECT * FROM users"

    async def test_get_performance_stats(self, repository):
        """Test getting performance statistics."""
        mock_connection = AsyncMock()
        mock_row = {
            "total_queries": 1000,
            "successful_queries": 950,
            "failed_queries": 50,
            "avg_execution_time_ms": 250.5,
            "unique_users": 100,
        }

        repository._db_manager.get_connection.return_value.__aenter__.return_value = (
            mock_connection
        )
        mock_connection.fetchrow.return_value = mock_row

        result = await repository.get_performance_stats()

        assert result["total_queries"] == 1000
        assert result["successful_queries"] == 950
        assert result["failed_queries"] == 50
        assert result["success_rate"] == 95.0  # 950/1000 * 100
        assert result["avg_execution_time_ms"] == 250.5
        assert result["unique_users"] == 100
