"""
Streaming service for progressive query rendering and real-time response handling.
Implements JSON streaming utilities for WebSocket communication.
"""

import json
import asyncio
from typing import AsyncIterator, Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime
import uuid
import logging

from models.response import QueryResponse, ValidationResult
from models.enums import ValidationStatus

logger = logging.getLogger(__name__)


@dataclass
class StreamChunk:
    """Represents a single chunk of streaming data."""

    chunk_id: str
    chunk_type: str  # 'sql', 'explanation', 'metadata', 'validation', 'error'
    content: str
    is_partial: bool
    timestamp: datetime
    request_id: str
    sequence_number: int
    total_expected_chunks: Optional[int] = None


@dataclass
class StreamingContext:
    """Context for managing streaming session."""

    request_id: str
    user_id: str
    session_id: str
    query: str
    start_time: datetime
    chunks_sent: int = 0
    is_complete: bool = False
    error: Optional[str] = None


class StreamingService:
    """Service for handling progressive query rendering via JSON streaming."""

    def __init__(self):
        self.active_streams: Dict[str, StreamingContext] = {}
        self.chunk_buffer_size = 1024  # Maximum chunk size in characters

    async def start_stream(
        self, request_id: str, user_id: str, session_id: str, query: str
    ) -> StreamingContext:
        """Initialize a new streaming session."""

        context = StreamingContext(
            request_id=request_id,
            user_id=user_id,
            session_id=session_id,
            query=query,
            start_time=datetime.utcnow(),
        )

        self.active_streams[request_id] = context

        logger.info(f"Started streaming session {request_id} for user {user_id}")

        return context

    async def create_chunk(
        self,
        request_id: str,
        chunk_type: str,
        content: str,
        is_partial: bool = False,
        total_expected_chunks: Optional[int] = None,
    ) -> StreamChunk:
        """Create a streaming chunk with proper formatting."""

        if request_id not in self.active_streams:
            raise ValueError(f"No active stream found for request {request_id}")

        context = self.active_streams[request_id]
        context.chunks_sent += 1

        chunk = StreamChunk(
            chunk_id=str(uuid.uuid4()),
            chunk_type=chunk_type,
            content=content,
            is_partial=is_partial,
            timestamp=datetime.utcnow(),
            request_id=request_id,
            sequence_number=context.chunks_sent,
            total_expected_chunks=total_expected_chunks,
        )

        return chunk

    async def stream_sql_generation(
        self, request_id: str, sql_content: str, explanation: str
    ) -> AsyncIterator[StreamChunk]:
        """Stream SQL generation with progressive rendering."""

        if request_id not in self.active_streams:
            raise ValueError(f"No active stream found for request {request_id}")

        # Stream SQL content in chunks
        sql_chunks = self._split_content(sql_content, self.chunk_buffer_size)
        explanation_chunks = self._split_content(explanation, self.chunk_buffer_size)

        total_chunks = (
            len(sql_chunks) + len(explanation_chunks) + 1
        )  # +1 for completion

        # Stream SQL chunks
        for i, chunk_content in enumerate(sql_chunks):
            is_partial = i < len(sql_chunks) - 1
            chunk = await self.create_chunk(
                request_id=request_id,
                chunk_type="sql",
                content=chunk_content,
                is_partial=is_partial,
                total_expected_chunks=total_chunks,
            )
            yield chunk

            # Add small delay for realistic streaming effect
            await asyncio.sleep(0.05)

        # Stream explanation chunks
        for i, chunk_content in enumerate(explanation_chunks):
            is_partial = i < len(explanation_chunks) - 1
            chunk = await self.create_chunk(
                request_id=request_id,
                chunk_type="explanation",
                content=chunk_content,
                is_partial=is_partial,
                total_expected_chunks=total_chunks,
            )
            yield chunk

            await asyncio.sleep(0.05)

    async def stream_validation_result(
        self, request_id: str, validation_result: ValidationResult
    ) -> StreamChunk:
        """Stream validation results."""

        validation_data = {
            "is_valid": validation_result.is_valid,
            "errors": validation_result.errors,
            "warnings": validation_result.warnings,
            "is_destructive": validation_result.is_destructive,
            "estimated_cost": validation_result.estimated_cost,
        }

        chunk = await self.create_chunk(
            request_id=request_id,
            chunk_type="validation",
            content=json.dumps(validation_data),
            is_partial=False,
        )

        return chunk

    async def stream_error(
        self,
        request_id: str,
        error_message: str,
        error_code: Optional[str] = None,
        partial_response: Optional[Dict[str, Any]] = None,
    ) -> StreamChunk:
        """Stream error information."""

        if request_id in self.active_streams:
            self.active_streams[request_id].error = error_message

        error_data = {
            "message": error_message,
            "code": error_code,
            "partial_response": partial_response,
            "timestamp": datetime.utcnow().isoformat(),
        }

        chunk = await self.create_chunk(
            request_id=request_id,
            chunk_type="error",
            content=json.dumps(error_data),
            is_partial=False,
        )

        logger.error(f"Streaming error for request {request_id}: {error_message}")

        return chunk

    async def complete_stream(
        self, request_id: str, final_response: QueryResponse
    ) -> StreamChunk:
        """Complete the streaming session with final response."""

        if request_id not in self.active_streams:
            raise ValueError(f"No active stream found for request {request_id}")

        context = self.active_streams[request_id]
        context.is_complete = True

        # Create completion chunk with full response
        completion_data = {
            "response": {
                "sql": final_response.sql,
                "explanation": final_response.explanation,
                "confidence_score": final_response.confidence_score,
                "selected_tables": final_response.selected_tables,
                "validation_status": final_response.validation_status.value,
                "optimization_suggestions": [
                    asdict(suggestion)
                    for suggestion in final_response.optimization_suggestions
                ],
                "execution_time_estimate": final_response.execution_time_estimate,
                "request_id": final_response.request_id,
                "generated_at": final_response.generated_at.isoformat(),
            },
            "total_chunks": context.chunks_sent + 1,
            "duration_ms": int(
                (datetime.utcnow() - context.start_time).total_seconds() * 1000
            ),
        }

        chunk = await self.create_chunk(
            request_id=request_id,
            chunk_type="complete",
            content=json.dumps(completion_data),
            is_partial=False,
        )

        logger.info(
            f"Completed streaming session {request_id} with {context.chunks_sent + 1} chunks"
        )

        return chunk

    async def cleanup_stream(self, request_id: str) -> None:
        """Clean up streaming session resources."""

        if request_id in self.active_streams:
            context = self.active_streams[request_id]
            logger.info(
                f"Cleaning up stream {request_id} after {context.chunks_sent} chunks"
            )
            del self.active_streams[request_id]

    def get_stream_status(self, request_id: str) -> Optional[StreamingContext]:
        """Get current status of a streaming session."""
        return self.active_streams.get(request_id)

    def get_active_streams(self) -> List[str]:
        """Get list of active stream request IDs."""
        return list(self.active_streams.keys())

    def _split_content(self, content: str, chunk_size: int) -> List[str]:
        """Split content into chunks for streaming."""

        if not content:
            return [""]

        chunks = []
        for i in range(0, len(content), chunk_size):
            chunk = content[i : i + chunk_size]
            chunks.append(chunk)

        return chunks

    async def format_websocket_message(
        self, chunk: StreamChunk, message_type: str = "query_stream_chunk"
    ) -> Dict[str, Any]:
        """Format streaming chunk as WebSocket message."""

        return {
            "type": message_type,
            "data": {
                "chunk_id": chunk.chunk_id,
                "chunk_type": chunk.chunk_type,
                "content": chunk.content,
                "is_partial": chunk.is_partial,
                "sequence_number": chunk.sequence_number,
                "total_expected_chunks": chunk.total_expected_chunks,
                "request_id": chunk.request_id,
            },
            "timestamp": chunk.timestamp.isoformat(),
            "request_id": chunk.request_id,
        }


# Global streaming service instance
streaming_service = StreamingService()
