"""
WebSocket service for real-time communication and streaming response handling.
Manages WebSocket connections, message routing, and error handling.
"""

import json
import asyncio
from typing import Dict, Set, Optional, Any, Callable
from datetime import datetime
import uuid
import logging
from fastapi import WebSocket, WebSocketDisconnect
from dataclasses import dataclass

from .streaming_service import StreamingService, StreamChunk, streaming_service
from models.response import QueryResponse

logger = logging.getLogger(__name__)


@dataclass
class WebSocketConnection:
    """Represents an active WebSocket connection."""

    websocket: WebSocket
    user_id: str
    session_id: str
    connection_id: str
    connected_at: datetime
    last_activity: datetime
    subscribed_events: Set[str]


class WebSocketManager:
    """Manages WebSocket connections and message broadcasting."""

    def __init__(self):
        self.active_connections: Dict[str, WebSocketConnection] = {}
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> connection_ids
        self.session_connections: Dict[str, Set[str]] = (
            {}
        )  # session_id -> connection_ids
        self.streaming_service = streaming_service

    async def connect(self, websocket: WebSocket, user_id: str, session_id: str) -> str:
        """Accept and register a new WebSocket connection."""

        await websocket.accept()

        connection_id = str(uuid.uuid4())
        connection = WebSocketConnection(
            websocket=websocket,
            user_id=user_id,
            session_id=session_id,
            connection_id=connection_id,
            connected_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            subscribed_events=set(),
        )

        # Register connection
        self.active_connections[connection_id] = connection

        # Track by user
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(connection_id)

        # Track by session
        if session_id not in self.session_connections:
            self.session_connections[session_id] = set()
        self.session_connections[session_id].add(connection_id)

        logger.info(
            f"WebSocket connected: {connection_id} for user {user_id}, session {session_id}"
        )

        # Send connection confirmation
        await self.send_to_connection(
            connection_id,
            {
                "type": "connection",
                "data": {
                    "status": "connected",
                    "connection_id": connection_id,
                    "message": "WebSocket connection established",
                },
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        return connection_id

    async def disconnect(self, connection_id: str) -> None:
        """Disconnect and clean up a WebSocket connection."""

        if connection_id not in self.active_connections:
            return

        connection = self.active_connections[connection_id]

        # Remove from tracking
        del self.active_connections[connection_id]

        if connection.user_id in self.user_connections:
            self.user_connections[connection.user_id].discard(connection_id)
            if not self.user_connections[connection.user_id]:
                del self.user_connections[connection.user_id]

        if connection.session_id in self.session_connections:
            self.session_connections[connection.session_id].discard(connection_id)
            if not self.session_connections[connection.session_id]:
                del self.session_connections[connection.session_id]

        logger.info(f"WebSocket disconnected: {connection_id}")

    async def send_to_connection(
        self, connection_id: str, message: Dict[str, Any]
    ) -> bool:
        """Send message to a specific connection."""

        if connection_id not in self.active_connections:
            logger.warning(
                f"Attempted to send message to non-existent connection: {connection_id}"
            )
            return False

        connection = self.active_connections[connection_id]

        try:
            await connection.websocket.send_text(json.dumps(message))
            connection.last_activity = datetime.utcnow()
            return True
        except Exception as e:
            logger.error(f"Failed to send message to connection {connection_id}: {e}")
            await self.disconnect(connection_id)
            return False

    async def send_to_user(self, user_id: str, message: Dict[str, Any]) -> int:
        """Send message to all connections for a user."""

        if user_id not in self.user_connections:
            return 0

        connection_ids = list(self.user_connections[user_id])
        sent_count = 0

        for connection_id in connection_ids:
            if await self.send_to_connection(connection_id, message):
                sent_count += 1

        return sent_count

    async def send_to_session(self, session_id: str, message: Dict[str, Any]) -> int:
        """Send message to all connections for a session."""

        if session_id not in self.session_connections:
            return 0

        connection_ids = list(self.session_connections[session_id])
        sent_count = 0

        for connection_id in connection_ids:
            if await self.send_to_connection(connection_id, message):
                sent_count += 1

        return sent_count

    async def broadcast(self, message: Dict[str, Any]) -> int:
        """Broadcast message to all active connections."""

        connection_ids = list(self.active_connections.keys())
        sent_count = 0

        for connection_id in connection_ids:
            if await self.send_to_connection(connection_id, message):
                sent_count += 1

        return sent_count

    async def handle_message(self, connection_id: str, message: Dict[str, Any]) -> None:
        """Handle incoming WebSocket message."""

        if connection_id not in self.active_connections:
            return

        connection = self.active_connections[connection_id]
        connection.last_activity = datetime.utcnow()

        message_type = message.get("type")

        try:
            if message_type == "ping":
                await self._handle_ping(connection_id, message)
            elif message_type == "subscribe":
                await self._handle_subscribe(connection_id, message)
            elif message_type == "unsubscribe":
                await self._handle_unsubscribe(connection_id, message)
            elif message_type == "query_request":
                await self._handle_query_request(connection_id, message)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                await self.send_error(
                    connection_id, f"Unknown message type: {message_type}"
                )

        except Exception as e:
            logger.error(f"Error handling message from {connection_id}: {e}")
            await self.send_error(connection_id, f"Error processing message: {str(e)}")

    async def _handle_ping(self, connection_id: str, message: Dict[str, Any]) -> None:
        """Handle ping message with pong response."""

        pong_message = {
            "type": "pong",
            "data": {
                "timestamp": message.get("data", {}).get("timestamp"),
                "server_time": datetime.utcnow().isoformat(),
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

        await self.send_to_connection(connection_id, pong_message)

    async def _handle_subscribe(
        self, connection_id: str, message: Dict[str, Any]
    ) -> None:
        """Handle event subscription."""

        events = message.get("data", {}).get("events", [])
        connection = self.active_connections[connection_id]

        for event in events:
            connection.subscribed_events.add(event)

        await self.send_to_connection(
            connection_id,
            {
                "type": "subscription_confirmed",
                "data": {"events": list(connection.subscribed_events)},
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    async def _handle_unsubscribe(
        self, connection_id: str, message: Dict[str, Any]
    ) -> None:
        """Handle event unsubscription."""

        events = message.get("data", {}).get("events", [])
        connection = self.active_connections[connection_id]

        for event in events:
            connection.subscribed_events.discard(event)

        await self.send_to_connection(
            connection_id,
            {
                "type": "unsubscription_confirmed",
                "data": {"events": list(connection.subscribed_events)},
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    async def _handle_query_request(
        self, connection_id: str, message: Dict[str, Any]
    ) -> None:
        """Handle query request - this would integrate with query generation service."""

        # This is a placeholder - actual implementation would integrate with
        # the query generation service from task 5.2
        request_data = message.get("data", {})
        request_id = request_data.get("request_id", str(uuid.uuid4()))

        await self.send_to_connection(
            connection_id,
            {
                "type": "query_stream_start",
                "data": {
                    "request_id": request_id,
                    "message": "Query processing started",
                },
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": request_id,
            },
        )

    async def send_error(
        self,
        connection_id: str,
        error_message: str,
        error_code: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> None:
        """Send error message to connection."""

        error_msg = {
            "type": "error",
            "data": {
                "message": error_message,
                "code": error_code,
                "timestamp": datetime.utcnow().isoformat(),
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

        if request_id:
            error_msg["request_id"] = request_id

        await self.send_to_connection(connection_id, error_msg)

    async def stream_query_response(
        self,
        request_id: str,
        user_id: str,
        session_id: str,
        query: str,
        response_generator: Callable[[], Any],
    ) -> None:
        """Stream query response to relevant connections."""

        # Start streaming session
        await self.streaming_service.start_stream(
            request_id=request_id, user_id=user_id, session_id=session_id, query=query
        )

        # Send stream start notification
        start_message = {
            "type": "query_stream_start",
            "data": {"request_id": request_id, "query": query},
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id,
        }

        await self.send_to_session(session_id, start_message)

        try:
            # This would integrate with the actual query generation service
            # For now, we'll simulate streaming
            async for chunk in self._simulate_query_streaming(request_id):
                message = await self.streaming_service.format_websocket_message(chunk)
                await self.send_to_session(session_id, message)

        except Exception as e:
            error_chunk = await self.streaming_service.stream_error(
                request_id=request_id,
                error_message=str(e),
                error_code="STREAMING_ERROR",
            )
            error_message = await self.streaming_service.format_websocket_message(
                error_chunk, "query_stream_error"
            )
            await self.send_to_session(session_id, error_message)

        finally:
            await self.streaming_service.cleanup_stream(request_id)

    async def _simulate_query_streaming(self, request_id: str):
        """Simulate query streaming for testing purposes."""

        # This is a placeholder implementation
        # Real implementation would integrate with query generation service

        sample_sql = "SELECT u.id, u.name, u.email FROM users u WHERE u.created_at >= '2024-01-01'"
        sample_explanation = "This query retrieves user information for all users created since January 1st, 2024."

        async for chunk in self.streaming_service.stream_sql_generation(
            request_id=request_id,
            sql_content=sample_sql,
            explanation=sample_explanation,
        ):
            yield chunk

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get statistics about active connections."""

        return {
            "total_connections": len(self.active_connections),
            "unique_users": len(self.user_connections),
            "unique_sessions": len(self.session_connections),
            "connections_by_user": {
                user_id: len(connection_ids)
                for user_id, connection_ids in self.user_connections.items()
            },
        }


# Global WebSocket manager instance
websocket_manager = WebSocketManager()
