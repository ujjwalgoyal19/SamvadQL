#!/usr/bin/env python3
"""
Comprehensive test runner for SamvadQL backend components.
This script demonstrates how to test all the implemented functionality.
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
from uuid import uuid4

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))
os.chdir(backend_dir)

from models.base import (
    QueryRequest,
    QueryResponse,
    TableSchema,
    ColumnSchema,
    ValidationResult,
    ValidationStatus,
    UserFeedback,
    AuditLogEntry,
)
from core.db.config import DatabaseConfig, parse_database_url
from core.db.pool import DatabaseConnectionManager
from repositories.user_feedback import UserFeedbackRepository
from repositories.audit_log import AuditLogRepository
from repositories.query_execution import QueryExecutionRepository, QueryExecutionLog
from migrations.migration_manager import MigrationManager, Migration


class TestRunner:
    """Comprehensive test runner for all components."""

    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0

    def log_test(self, test_name: str, passed: bool, message: str = ""):
        """Log test result."""
        status = "PASS" if passed else "FAIL"
        self.results.append(f"[{status}] {test_name}: {message}")

        if passed:
            self.passed += 1
        else:
            self.failed += 1

        print(f"[{status}] {test_name}: {message}")

    def test_data_models(self):
        """Test Pydantic data models and validation."""
        print("\n=== Testing Data Models ===")

        # Test QueryRequest validation
        try:
            # Valid request
            request = QueryRequest(
                query="Show me all users from last month",
                user_id="test_user",
                database_id=str(uuid4()),
                selected_tables=["users", "signups"],
            )
            self.log_test(
                "QueryRequest - Valid",
                True,
                f"Created request with ID {request.request_id}",
            )
        except Exception as e:
            self.log_test("QueryRequest - Valid", False, str(e))

        # Test invalid query
        try:
            QueryRequest(
                query="",  # Empty query should fail
                user_id="test_user",
                database_id=str(uuid4()),
            )
            self.log_test(
                "QueryRequest - Empty Query", False, "Should have failed validation"
            )
        except Exception as e:
            self.log_test(
                "QueryRequest - Empty Query", True, "Correctly rejected empty query"
            )

        # Test malicious content detection
        try:
            QueryRequest(
                query="<script>alert('xss')</script>",
                user_id="test_user",
                database_id=str(uuid4()),
            )
            self.log_test(
                "QueryRequest - XSS Detection", False, "Should have detected XSS"
            )
        except Exception as e:
            self.log_test(
                "QueryRequest - XSS Detection",
                True,
                "Correctly detected unsafe content",
            )

        # Test TableSchema validation
        try:
            columns = [
                ColumnSchema(
                    name="id",
                    data_type="integer",
                    is_primary_key=True,
                    is_nullable=False,
                ),
                ColumnSchema(
                    name="name", data_type="varchar(255)", description="User name"
                ),
            ]

            table = TableSchema(
                name="users",
                database_id=str(uuid4()),
                columns=columns,
                description="User accounts table",
                tier="gold",
                tags=["user-data", "core"],
            )
            self.log_test(
                "TableSchema - Valid", True, f"Created table schema for {table.name}"
            )
        except Exception as e:
            self.log_test("TableSchema - Valid", False, str(e))

        # Test ValidationResult consistency
        try:
            # Valid SQL with errors should fail
            ValidationResult(is_valid=True, errors=["Some error"])
            self.log_test(
                "ValidationResult - Consistency",
                False,
                "Should have failed consistency check",
            )
        except Exception as e:
            self.log_test(
                "ValidationResult - Consistency", True, "Correctly enforced consistency"
            )

        # Test QueryResponse validation
        try:
            response = QueryResponse(
                sql="SELECT * FROM users WHERE created_at >= '2024-01-01'",
                explanation="This query retrieves all users created after January 1st, 2024",
                confidence_score=0.95,
                selected_tables=["users"],
                validation_status=ValidationStatus.VALID,
            )
            self.log_test(
                "QueryResponse - Valid",
                True,
                f"Created response with confidence {response.confidence_score}",
            )
        except Exception as e:
            self.log_test("QueryResponse - Valid", False, str(e))

    def test_database_utilities(self):
        """Test database connection utilities."""
        print("\n=== Testing Database Utilities ===")

        # Test URL parsing
        try:
            config = parse_database_url("postgresql://user:pass@localhost:5432/testdb")
            self.log_test(
                "Database URL Parsing",
                True,
                f"Parsed: {config.host}:{config.port}/{config.database}",
            )
        except Exception as e:
            self.log_test("Database URL Parsing", False, str(e))

        # Test config creation
        try:
            config = DatabaseConfig(
                host="localhost",
                port=5432,
                database="test_db",
                username="test_user",
                password="test_pass",
            )
            self.log_test(
                "Database Config", True, f"Created config for {config.database}"
            )
        except Exception as e:
            self.log_test("Database Config", False, str(e))

        # Test connection manager creation (without actual connection)
        try:
            config = DatabaseConfig(
                host="localhost",
                port=5432,
                database="test_db",
                username="test_user",
                password="test_pass",
            )
            manager = DatabaseConnectionManager(config)
            self.log_test("Connection Manager", True, "Created connection manager")
        except Exception as e:
            self.log_test("Connection Manager", False, str(e))

    def test_repositories(self):
        """Test repository implementations."""
        print("\n=== Testing Repositories ===")

        # Test UserFeedbackRepository
        try:
            repo = UserFeedbackRepository()

            # Test data conversion
            feedback = UserFeedback(
                id=str(uuid4()),
                user_id="test_user",
                query_id=str(uuid4()),
                original_query="Show me all users",
                generated_sql="SELECT * FROM users",
                feedback_type="accept",
                rating=5,
                comments="Great query!",
            )

            # Test to_dict conversion
            data = repo.to_dict(feedback)
            self.log_test(
                "UserFeedback - to_dict",
                True,
                f"Converted feedback to dict with {len(data)} fields",
            )

            # Test from_dict conversion
            restored = repo.from_dict(data)
            self.log_test(
                "UserFeedback - from_dict",
                True,
                f"Restored feedback with ID {restored.id}",
            )

        except Exception as e:
            self.log_test("UserFeedback Repository", False, str(e))

        # Test AuditLogRepository
        try:
            repo = AuditLogRepository()

            audit_entry = AuditLogEntry(
                id=str(uuid4()),
                user_id="test_user",
                action="query_generated",
                resource_type="query",
                resource_id=str(uuid4()),
                details={"query": "SELECT * FROM users"},
                ip_address="192.168.1.1",
            )

            # Test data conversion
            data = repo.to_dict(audit_entry)
            restored = repo.from_dict(data)

            self.log_test(
                "AuditLog Repository",
                True,
                f"Processed audit entry for action: {restored.action}",
            )

        except Exception as e:
            self.log_test("AuditLog Repository", False, str(e))

        # Test QueryExecutionRepository
        try:
            repo = QueryExecutionRepository()

            query_log = QueryExecutionLog(
                id=str(uuid4()),
                query_id=str(uuid4()),
                user_id="test_user",
                original_query="Show me all users",
                generated_sql="SELECT * FROM users",
                schema_versions={"users": "v1.0"},
                execution_result="success",
                performance_metrics={"execution_time_ms": 150},
            )

            # Test data conversion
            data = repo.to_dict(query_log)
            restored = repo.from_dict(data)

            self.log_test(
                "QueryExecution Repository",
                True,
                f"Processed query log with result: {restored.execution_result}",
            )

        except Exception as e:
            self.log_test("QueryExecution Repository", False, str(e))

    def test_migrations(self):
        """Test migration system."""
        print("\n=== Testing Migration System ===")

        # Test Migration creation
        try:
            migration = Migration(
                version="20240101_120000",
                name="Test Migration",
                up_sql="CREATE TABLE test (id INTEGER);",
                down_sql="DROP TABLE test;",
            )
            self.log_test("Migration Creation", True, f"Created migration: {migration}")
        except Exception as e:
            self.log_test("Migration Creation", False, str(e))

        # Test MigrationManager
        try:
            manager = MigrationManager()

            # Test migration file creation
            import tempfile

            with tempfile.TemporaryDirectory() as temp_dir:
                manager.migrations_dir = Path(temp_dir)

                file_path = manager.create_migration_file(
                    name="Test Migration",
                    up_sql="CREATE TABLE test (id INTEGER);",
                    down_sql="DROP TABLE test;",
                )

                self.log_test(
                    "Migration File Creation", True, f"Created file: {file_path.name}"
                )

                # Test file parsing
                parsed = manager._parse_migration_file(file_path)
                if parsed and parsed.name == "Test Migration":
                    self.log_test(
                        "Migration File Parsing",
                        True,
                        f"Parsed migration: {parsed.name}",
                    )
                else:
                    self.log_test(
                        "Migration File Parsing",
                        False,
                        "Failed to parse migration file",
                    )

        except Exception as e:
            self.log_test("Migration Manager", False, str(e))

    async def test_async_operations(self):
        """Test async operations (simplified)."""
        print("\n=== Testing Async Operations (Simplified) ===")

        # Test async repository data conversion (without database)
        try:
            repo = UserFeedbackRepository()

            # Test data conversion methods (these don't require database)
            feedback = UserFeedback(
                id=str(uuid4()),
                user_id="test_user",
                query_id=str(uuid4()),
                original_query="test query",
                generated_sql="SELECT 1",
                feedback_type="accept",
                rating=5,
                comments="Great!",
                created_at=datetime.utcnow(),
            )

            # Test to_dict and from_dict conversion
            data = repo.to_dict(feedback)
            restored = repo.from_dict(data)

            if (
                restored.user_id == feedback.user_id
                and restored.rating == feedback.rating
            ):
                self.log_test(
                    "Async Repository Data Conversion",
                    True,
                    f"Successfully converted feedback data for user {restored.user_id}",
                )
            else:
                self.log_test(
                    "Async Repository Data Conversion", False, "Data conversion failed"
                )

            # Test table name method
            table_name = repo.get_table_name()
            if table_name == "user_feedback":
                self.log_test(
                    "Repository Table Name",
                    True,
                    f"Correct table name: {table_name}",
                )
            else:
                self.log_test(
                    "Repository Table Name", False, f"Wrong table name: {table_name}"
                )

        except Exception as e:
            self.log_test("Async Repository Operations", False, str(e))

    def test_frontend_types(self):
        """Test frontend TypeScript type compatibility."""
        print("\n=== Testing Frontend Type Compatibility ===")

        try:
            # Test that our Python models can be serialized to JSON
            # (which would be consumed by TypeScript frontend)
            import json

            # Create a QueryRequest
            request = QueryRequest(
                query="Show me all users",
                user_id="test_user",
                database_id=str(uuid4()),
                selected_tables=["users"],
            )

            # Serialize to JSON (as would be sent to frontend)
            json_data = request.model_dump_json()
            parsed_data = json.loads(json_data)

            # Check that all expected fields are present
            expected_fields = [
                "query",
                "user_id",
                "database_id",
                "selected_tables",
                "request_id",
            ]
            missing_fields = [
                field for field in expected_fields if field not in parsed_data
            ]

            if not missing_fields:
                self.log_test(
                    "Frontend JSON Serialization",
                    True,
                    f"All {len(expected_fields)} fields present",
                )
            else:
                self.log_test(
                    "Frontend JSON Serialization",
                    False,
                    f"Missing fields: {missing_fields}",
                )

            # Test QueryResponse serialization
            response = QueryResponse(
                sql="SELECT * FROM users",
                explanation="This query selects all users",
                confidence_score=0.95,
                selected_tables=["users"],
                validation_status=ValidationStatus.VALID,
            )

            response_json = response.model_dump_json()
            response_data = json.loads(response_json)

            if "sql" in response_data and "confidence_score" in response_data:
                self.log_test(
                    "Response JSON Serialization",
                    True,
                    "QueryResponse serialized correctly",
                )
            else:
                self.log_test(
                    "Response JSON Serialization", False, "Missing required fields"
                )

        except Exception as e:
            self.log_test("Frontend Type Compatibility", False, str(e))

    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)

        for result in self.results:
            print(result)

        print(f"\nTotal Tests: {self.passed + self.failed}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Success Rate: {(self.passed / (self.passed + self.failed) * 100):.1f}%")

        if self.failed == 0:
            print("\n🎉 All tests passed!")
        else:
            print(f"\n⚠️  {self.failed} test(s) failed")

    async def run_all_tests(self):
        """Run all tests."""
        print("Starting comprehensive test suite for SamvadQL backend...")
        print(
            "This tests all implemented components without requiring a database connection."
        )

        self.test_data_models()
        self.test_database_utilities()
        self.test_repositories()
        self.test_migrations()
        await self.test_async_operations()
        self.test_frontend_types()

        self.print_summary()

        return self.failed == 0


async def main():
    """Main test runner."""
    runner = TestRunner()
    success = await runner.run_all_tests()

    if success:
        print("\n✅ All components are working correctly!")
        print("\nNext steps to test with a real database:")
        print("1. Set up a PostgreSQL database")
        print("2. Set DATABASE_URL environment variable")
        print("3. Run: python -m pytest tests/ -v")
        print("4. Run migrations: python migrations/cli.py up")
        print("5. Test the FastAPI endpoints: uvicorn main:app --reload")
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
