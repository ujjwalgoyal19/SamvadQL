"""
Tests for streaming service functionality.
Tests JSON streaming utilities, progressive rendering, and error handling.
"""

import pytest
import asyncio
import json
from datetime import datetime
from unittest.mock import Mock, AsyncMock

from services.streaming_service import StreamingService, StreamChunk, StreamingContext
from models.response import QueryResponse, ValidationResult
from models.enums import ValidationStatus


class TestStreamingService:
    """Test cases for StreamingService."""

    @pytest.fixture
    def streaming_service(self):
        """Create a StreamingService instance for testing."""
        return StreamingService()

    @pytest.fixture
    def sample_context_data(self):
        """Sample data for streaming context."""
        return {
            "request_id": "test-request-123",
            "user_id": "user-456",
            "session_id": "session-789",
            "query": "SELECT * FROM users WHERE active = true",
        }

    @pytest.mark.asyncio
    async def test_start_stream(self, streaming_service, sample_context_data):
        """Test starting a streaming session."""
        context = await streaming_service.start_stream(**sample_context_data)

        assert isinstance(context, StreamingContext)
        assert context.request_id == sample_context_data["request_id"]
        assert context.user_id == sample_context_data["user_id"]
        assert context.session_id == sample_context_data["session_id"]
        assert context.query == sample_context_data["query"]
        assert context.chunks_sent == 0
        assert not context.is_complete
        assert context.error is None
        assert isinstance(context.start_time, datetime)

        # Verify context is stored
        assert sample_context_data["request_id"] in streaming_service.active_streams

    @pytest.mark.asyncio
    async def test_create_chunk(self, streaming_service, sample_context_data):
        """Test creating streaming chunks."""
        # Start stream first
        await streaming_service.start_stream(**sample_context_data)

        # Create chunk
        chunk = await streaming_service.create_chunk(
            request_id=sample_context_data["request_id"],
            chunk_type="sql",
            content="SELECT * FROM users",
            is_partial=True,
            total_expected_chunks=5,
        )

        assert isinstance(chunk, StreamChunk)
        assert chunk.chunk_type == "sql"
        assert chunk.content == "SELECT * FROM users"
        assert chunk.is_partial is True
        assert chunk.sequence_number == 1
        assert chunk.total_expected_chunks == 5
        assert chunk.request_id == sample_context_data["request_id"]
        assert isinstance(chunk.timestamp, datetime)

        # Verify context updated
        context = streaming_service.active_streams[sample_context_data["request_id"]]
        assert context.chunks_sent == 1

    @pytest.mark.asyncio
    async def test_create_chunk_invalid_request(self, streaming_service):
        """Test creating chunk with invalid request ID."""
        with pytest.raises(ValueError, match="No active stream found"):
            await streaming_service.create_chunk(
                request_id="invalid-request",
                chunk_type="sql",
                content="SELECT * FROM users",
            )

    @pytest.mark.asyncio
    async def test_stream_sql_generation(self, streaming_service, sample_context_data):
        """Test streaming SQL generation with progressive rendering."""
        # Start stream
        await streaming_service.start_stream(**sample_context_data)

        sql_content = "SELECT u.id, u.name, u.email FROM users u WHERE u.active = true ORDER BY u.created_at DESC"
        explanation = "This query retrieves active users with their basic information, ordered by creation date."

        chunks = []
        async for chunk in streaming_service.stream_sql_generation(
            request_id=sample_context_data["request_id"],
            sql_content=sql_content,
            explanation=explanation,
        ):
            chunks.append(chunk)

        # Verify chunks were generated
        assert len(chunks) > 0

        # Verify SQL chunks
        sql_chunks = [c for c in chunks if c.chunk_type == "sql"]
        assert len(sql_chunks) > 0

        # Reconstruct SQL from chunks
        reconstructed_sql = "".join(c.content for c in sql_chunks)
        assert reconstructed_sql == sql_content

        # Verify explanation chunks
        explanation_chunks = [c for c in chunks if c.chunk_type == "explanation"]
        assert len(explanation_chunks) > 0

        # Reconstruct explanation from chunks
        reconstructed_explanation = "".join(c.content for c in explanation_chunks)
        assert reconstructed_explanation == explanation

        # Verify chunk properties
        for i, chunk in enumerate(chunks):
            assert chunk.request_id == sample_context_data["request_id"]
            assert chunk.sequence_number == i + 1
            assert isinstance(chunk.timestamp, datetime)

    @pytest.mark.asyncio
    async def test_stream_validation_result(
        self, streaming_service, sample_context_data
    ):
        """Test streaming validation results."""
        # Start stream
        await streaming_service.start_stream(**sample_context_data)

        validation_result = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=["Query may be slow"],
            is_destructive=False,
            estimated_cost=125.5,
        )

        chunk = await streaming_service.stream_validation_result(
            request_id=sample_context_data["request_id"],
            validation_result=validation_result,
        )

        assert chunk.chunk_type == "validation"
        assert not chunk.is_partial

        # Parse validation data
        validation_data = json.loads(chunk.content)
        assert validation_data["is_valid"] is True
        assert validation_data["errors"] == []
        assert validation_data["warnings"] == ["Query may be slow"]
        assert validation_data["is_destructive"] is False
        assert validation_data["estimated_cost"] == 125.5

    @pytest.mark.asyncio
    async def test_stream_error(self, streaming_service, sample_context_data):
        """Test streaming error information."""
        # Start stream
        await streaming_service.start_stream(**sample_context_data)

        error_message = "SQL syntax error"
        error_code = "SYNTAX_ERROR"
        partial_response = {"sql": "SELECT * FROM"}

        chunk = await streaming_service.stream_error(
            request_id=sample_context_data["request_id"],
            error_message=error_message,
            error_code=error_code,
            partial_response=partial_response,
        )

        assert chunk.chunk_type == "error"
        assert not chunk.is_partial

        # Parse error data
        error_data = json.loads(chunk.content)
        assert error_data["message"] == error_message
        assert error_data["code"] == error_code
        assert error_data["partial_response"] == partial_response
        assert "timestamp" in error_data

        # Verify context updated with error
        context = streaming_service.active_streams[sample_context_data["request_id"]]
        assert context.error == error_message

    @pytest.mark.asyncio
    async def test_complete_stream(self, streaming_service, sample_context_data):
        """Test completing streaming session."""
        # Start stream and send some chunks
        await streaming_service.start_stream(**sample_context_data)
        await streaming_service.create_chunk(
            request_id=sample_context_data["request_id"],
            chunk_type="sql",
            content="SELECT * FROM users",
        )

        # Create final response
        import uuid

        final_response = QueryResponse(
            sql="SELECT * FROM users WHERE active = true",
            explanation="Query to get active users",
            confidence_score=0.95,
            selected_tables=["users"],
            validation_status=ValidationStatus.VALID,
            optimization_suggestions=[],
            execution_time_estimate=0.25,
            request_id=str(uuid.uuid4()),
        )

        chunk = await streaming_service.complete_stream(
            request_id=sample_context_data["request_id"], final_response=final_response
        )

        assert chunk.chunk_type == "complete"
        assert not chunk.is_partial

        # Parse completion data
        completion_data = json.loads(chunk.content)
        assert "response" in completion_data
        assert "total_chunks" in completion_data
        assert "duration_ms" in completion_data

        response_data = completion_data["response"]
        assert response_data["sql"] == final_response.sql
        assert response_data["explanation"] == final_response.explanation
        assert response_data["confidence_score"] == final_response.confidence_score

        # Verify context marked as complete
        context = streaming_service.active_streams[sample_context_data["request_id"]]
        assert context.is_complete

    @pytest.mark.asyncio
    async def test_cleanup_stream(self, streaming_service, sample_context_data):
        """Test cleaning up streaming session."""
        # Start stream
        await streaming_service.start_stream(**sample_context_data)
        assert sample_context_data["request_id"] in streaming_service.active_streams

        # Cleanup
        await streaming_service.cleanup_stream(sample_context_data["request_id"])
        assert sample_context_data["request_id"] not in streaming_service.active_streams

    def test_get_stream_status(self, streaming_service, sample_context_data):
        """Test getting stream status."""
        # No active stream
        status = streaming_service.get_stream_status(sample_context_data["request_id"])
        assert status is None

        # With active stream
        asyncio.run(streaming_service.start_stream(**sample_context_data))
        status = streaming_service.get_stream_status(sample_context_data["request_id"])
        assert status is not None
        assert status.request_id == sample_context_data["request_id"]

    def test_get_active_streams(self, streaming_service, sample_context_data):
        """Test getting list of active streams."""
        # No active streams
        active = streaming_service.get_active_streams()
        assert active == []

        # With active stream
        asyncio.run(streaming_service.start_stream(**sample_context_data))
        active = streaming_service.get_active_streams()
        assert len(active) == 1
        assert active[0] == sample_context_data["request_id"]

    def test_split_content(self, streaming_service):
        """Test content splitting for streaming."""
        # Empty content
        chunks = streaming_service._split_content("", 10)
        assert chunks == [""]

        # Content smaller than chunk size
        content = "SELECT * FROM users"
        chunks = streaming_service._split_content(content, 50)
        assert chunks == [content]

        # Content larger than chunk size
        content = (
            "SELECT id, name, email FROM users WHERE active = true ORDER BY created_at"
        )
        chunks = streaming_service._split_content(content, 20)
        assert len(chunks) > 1
        assert "".join(chunks) == content

        # Verify chunk sizes
        for chunk in chunks[:-1]:  # All but last chunk
            assert len(chunk) == 20
        assert len(chunks[-1]) <= 20  # Last chunk can be smaller

    @pytest.mark.asyncio
    async def test_format_websocket_message(
        self, streaming_service, sample_context_data
    ):
        """Test formatting streaming chunk as WebSocket message."""
        # Start stream and create chunk
        await streaming_service.start_stream(**sample_context_data)
        chunk = await streaming_service.create_chunk(
            request_id=sample_context_data["request_id"],
            chunk_type="sql",
            content="SELECT * FROM users",
            is_partial=True,
            total_expected_chunks=5,
        )

        # Format as WebSocket message
        message = await streaming_service.format_websocket_message(chunk)

        assert message["type"] == "query_stream_chunk"
        assert "data" in message
        assert "timestamp" in message
        assert message["request_id"] == sample_context_data["request_id"]

        data = message["data"]
        assert data["chunk_type"] == "sql"
        assert data["content"] == "SELECT * FROM users"
        assert data["is_partial"] is True
        assert data["sequence_number"] == 1
        assert data["total_expected_chunks"] == 5
        assert data["request_id"] == sample_context_data["request_id"]

    @pytest.mark.asyncio
    async def test_concurrent_streams(self, streaming_service):
        """Test handling multiple concurrent streams."""
        # Start multiple streams
        contexts = []
        for i in range(3):
            context_data = {
                "request_id": f"request-{i}",
                "user_id": f"user-{i}",
                "session_id": f"session-{i}",
                "query": f"SELECT * FROM table_{i}",
            }
            context = await streaming_service.start_stream(**context_data)
            contexts.append(context)

        # Verify all streams are active
        active_streams = streaming_service.get_active_streams()
        assert len(active_streams) == 3

        # Create chunks for each stream
        for i, context in enumerate(contexts):
            chunk = await streaming_service.create_chunk(
                request_id=context.request_id,
                chunk_type="sql",
                content=f"SELECT * FROM table_{i}",
            )
            assert chunk.request_id == context.request_id

        # Verify each context has correct chunk count
        for context in contexts:
            stored_context = streaming_service.active_streams[context.request_id]
            assert stored_context.chunks_sent == 1

    @pytest.mark.asyncio
    async def test_streaming_with_delays(self, streaming_service, sample_context_data):
        """Test streaming with realistic delays."""
        # Start stream
        await streaming_service.start_stream(**sample_context_data)

        # Override chunk buffer size for testing
        original_buffer_size = streaming_service.chunk_buffer_size
        streaming_service.chunk_buffer_size = 10  # Small chunks for testing

        try:
            sql_content = "SELECT id, name FROM users WHERE active = true"
            explanation = "Get active user data"

            start_time = datetime.utcnow()
            chunks = []

            async for chunk in streaming_service.stream_sql_generation(
                request_id=sample_context_data["request_id"],
                sql_content=sql_content,
                explanation=explanation,
            ):
                chunks.append(chunk)

            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            # Verify streaming took some time (due to delays)
            assert duration > 0.1  # Should take at least 100ms with delays
            assert len(chunks) > 2  # Should have multiple chunks due to small buffer

        finally:
            # Restore original buffer size
            streaming_service.chunk_buffer_size = original_buffer_size


@pytest.mark.asyncio
async def test_streaming_service_error_scenarios():
    """Test error scenarios in streaming service."""
    service = StreamingService()

    # Test operations without active stream
    with pytest.raises(ValueError):
        await service.create_chunk("invalid-id", "sql", "content")

    with pytest.raises(ValueError):
        async for chunk in service.stream_sql_generation(
            "invalid-id", "sql", "explanation"
        ):
            pass

    with pytest.raises(ValueError):
        await service.complete_stream("invalid-id", Mock())


@pytest.mark.asyncio
async def test_streaming_service_integration():
    """Integration test for complete streaming workflow."""
    service = StreamingService()

    # Sample data
    request_id = "integration-test-123"
    user_id = "user-456"
    session_id = "session-789"
    query = "Get all active users with their email addresses"

    # Start stream
    context = await service.start_stream(request_id, user_id, session_id, query)
    assert context.request_id == request_id

    # Stream SQL generation
    sql_content = "SELECT id, name, email FROM users WHERE active = true"
    explanation = (
        "This query retrieves all active users with their ID, name, and email address."
    )

    chunks = []
    async for chunk in service.stream_sql_generation(
        request_id, sql_content, explanation
    ):
        chunks.append(chunk)

        # Format as WebSocket message
        message = await service.format_websocket_message(chunk)
        assert message["type"] == "query_stream_chunk"
        assert message["request_id"] == request_id

    # Stream validation
    validation_result = ValidationResult(
        is_valid=True, errors=[], warnings=[], is_destructive=False, estimated_cost=50.0
    )

    validation_chunk = await service.stream_validation_result(
        request_id, validation_result
    )
    chunks.append(validation_chunk)

    # Complete stream
    import uuid

    final_response = QueryResponse(
        sql=sql_content,
        explanation=explanation,
        confidence_score=0.95,
        selected_tables=["users"],
        validation_status=ValidationStatus.VALID,
        optimization_suggestions=[],
        execution_time_estimate=0.15,
        request_id=str(uuid.uuid4()),
    )

    completion_chunk = await service.complete_stream(request_id, final_response)
    chunks.append(completion_chunk)

    # Verify complete workflow
    assert len(chunks) > 3  # SQL chunks + explanation chunks + validation + completion

    # Verify chunk types
    chunk_types = [c.chunk_type for c in chunks]
    assert "sql" in chunk_types
    assert "explanation" in chunk_types
    assert "validation" in chunk_types
    assert "complete" in chunk_types

    # Verify sequence numbers
    for i, chunk in enumerate(chunks):
        assert chunk.sequence_number == i + 1

    # Cleanup
    await service.cleanup_stream(request_id)
    assert request_id not in service.active_streams
