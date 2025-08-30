"""
Tests for WebSocket service functionality.
Tests WebSocket connection management, message routing, and error handling.
"""

import pytest
import asyncio
import json
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from services.websocket_service import WebSocketManager, WebSocketConnection
from fastapi import WebSocket


class MockWebSocket:
    """Mock WebSocket for testing."""

    def __init__(self):
        self.messages_sent = []
        self.is_closed = False
        self.accept_called = False

    async def accept(self):
        self.accept_called = True

    async def send_text(self, data: str):
        if self.is_closed:
            raise Exception("WebSocket is closed")
        self.messages_sent.append(data)

    def close(self):
        self.is_closed = True


class TestWebSocketManager:
    """Test cases for WebSocketManager."""

    @pytest.fixture
    def ws_manager(self):
        """Create a WebSocketManager instance for testing."""
        return WebSocketManager()

    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket for testing."""
        return MockWebSocket()

    @pytest.mark.asyncio
    async def test_connect_websocket(self, ws_manager, mock_websocket):
        """Test WebSocket connection establishment."""
        user_id = "user-123"
        session_id = "session-456"

        connection_id = await ws_manager.connect(mock_websocket, user_id, session_id)

        # Verify connection was accepted
        assert mock_websocket.accept_called

        # Verify connection is tracked
        assert connection_id in ws_manager.active_connections
        assert user_id in ws_manager.user_connections
        assert session_id in ws_manager.session_connections

        # Verify connection details
        connection = ws_manager.active_connections[connection_id]
        assert connection.user_id == user_id
        assert connection.session_id == session_id
        assert connection.websocket == mock_websocket
        assert isinstance(connection.connected_at, datetime)

        # Verify confirmation message was sent
        assert len(mock_websocket.messages_sent) == 1
        message = json.loads(mock_websocket.messages_sent[0])
        assert message["type"] == "connection"
        assert message["data"]["status"] == "connected"

    @pytest.mark.asyncio
    async def test_disconnect_websocket(self, ws_manager, mock_websocket):
        """Test WebSocket disconnection."""
        user_id = "user-123"
        session_id = "session-456"

        # Connect first
        connection_id = await ws_manager.connect(mock_websocket, user_id, session_id)

        # Verify connection exists
        assert connection_id in ws_manager.active_connections

        # Disconnect
        await ws_manager.disconnect(connection_id)

        # Verify connection removed
        assert connection_id not in ws_manager.active_connections
        assert user_id not in ws_manager.user_connections
        assert session_id not in ws_manager.session_connections

    @pytest.mark.asyncio
    async def test_send_to_connection(self, ws_manager, mock_websocket):
        """Test sending message to specific connection."""
        user_id = "user-123"
        session_id = "session-456"

        # Connect
        connection_id = await ws_manager.connect(mock_websocket, user_id, session_id)

        # Clear initial messages
        mock_websocket.messages_sent.clear()

        # Send message
        test_message = {
            "type": "test",
            "data": {"content": "Hello World"},
            "timestamp": datetime.utcnow().isoformat(),
        }

        result = await ws_manager.send_to_connection(connection_id, test_message)

        # Verify message sent successfully
        assert result is True
        assert len(mock_websocket.messages_sent) == 1

        sent_message = json.loads(mock_websocket.messages_sent[0])
        assert sent_message == test_message

    @pytest.mark.asyncio
    async def test_send_to_nonexistent_connection(self, ws_manager):
        """Test sending message to non-existent connection."""
        result = await ws_manager.send_to_connection("invalid-id", {"type": "test"})
        assert result is False

    @pytest.mark.asyncio
    async def test_send_to_user(self, ws_manager):
        """Test sending message to all connections for a user."""
        user_id = "user-123"

        # Create multiple connections for same user
        mock_ws1 = MockWebSocket()
        mock_ws2 = MockWebSocket()

        conn1_id = await ws_manager.connect(mock_ws1, user_id, "session-1")
        conn2_id = await ws_manager.connect(mock_ws2, user_id, "session-2")

        # Clear initial messages
        mock_ws1.messages_sent.clear()
        mock_ws2.messages_sent.clear()

        # Send message to user
        test_message = {"type": "broadcast", "data": "Hello User"}
        sent_count = await ws_manager.send_to_user(user_id, test_message)

        # Verify message sent to both connections
        assert sent_count == 2
        assert len(mock_ws1.messages_sent) == 1
        assert len(mock_ws2.messages_sent) == 1

    @pytest.mark.asyncio
    async def test_send_to_session(self, ws_manager):
        """Test sending message to all connections for a session."""
        session_id = "session-123"

        # Create multiple connections for same session
        mock_ws1 = MockWebSocket()
        mock_ws2 = MockWebSocket()

        conn1_id = await ws_manager.connect(mock_ws1, "user-1", session_id)
        conn2_id = await ws_manager.connect(mock_ws2, "user-2", session_id)

        # Clear initial messages
        mock_ws1.messages_sent.clear()
        mock_ws2.messages_sent.clear()

        # Send message to session
        test_message = {"type": "session_broadcast", "data": "Hello Session"}
        sent_count = await ws_manager.send_to_session(session_id, test_message)

        # Verify message sent to both connections
        assert sent_count == 2
        assert len(mock_ws1.messages_sent) == 1
        assert len(mock_ws2.messages_sent) == 1

    @pytest.mark.asyncio
    async def test_broadcast_message(self, ws_manager):
        """Test broadcasting message to all connections."""
        # Create multiple connections
        connections = []
        mock_websockets = []

        for i in range(3):
            mock_ws = MockWebSocket()
            conn_id = await ws_manager.connect(mock_ws, f"user-{i}", f"session-{i}")
            connections.append(conn_id)
            mock_websockets.append(mock_ws)
            mock_ws.messages_sent.clear()  # Clear initial messages

        # Broadcast message
        test_message = {"type": "global_broadcast", "data": "Hello Everyone"}
        sent_count = await ws_manager.broadcast(test_message)

        # Verify message sent to all connections
        assert sent_count == 3
        for mock_ws in mock_websockets:
            assert len(mock_ws.messages_sent) == 1

    @pytest.mark.asyncio
    async def test_handle_ping_message(self, ws_manager, mock_websocket):
        """Test handling ping message."""
        user_id = "user-123"
        session_id = "session-456"

        # Connect
        connection_id = await ws_manager.connect(mock_websocket, user_id, session_id)
        mock_websocket.messages_sent.clear()

        # Send ping message
        ping_message = {
            "type": "ping",
            "data": {"timestamp": "2024-01-01T12:00:00Z"},
            "timestamp": datetime.utcnow().isoformat(),
        }

        await ws_manager.handle_message(connection_id, ping_message)

        # Verify pong response
        assert len(mock_websocket.messages_sent) == 1
        pong_response = json.loads(mock_websocket.messages_sent[0])
        assert pong_response["type"] == "pong"
        assert pong_response["data"]["timestamp"] == "2024-01-01T12:00:00Z"
        assert "server_time" in pong_response["data"]

    @pytest.mark.asyncio
    async def test_handle_subscribe_message(self, ws_manager, mock_websocket):
        """Test handling subscription message."""
        user_id = "user-123"
        session_id = "session-456"

        # Connect
        connection_id = await ws_manager.connect(mock_websocket, user_id, session_id)
        mock_websocket.messages_sent.clear()

        # Send subscription message
        subscribe_message = {
            "type": "subscribe",
            "data": {"events": ["query_stream", "table_recommendations"]},
            "timestamp": datetime.utcnow().isoformat(),
        }

        await ws_manager.handle_message(connection_id, subscribe_message)

        # Verify subscription confirmation
        assert len(mock_websocket.messages_sent) == 1
        confirmation = json.loads(mock_websocket.messages_sent[0])
        assert confirmation["type"] == "subscription_confirmed"
        assert set(confirmation["data"]["events"]) == {
            "query_stream",
            "table_recommendations",
        }

        # Verify connection has subscribed events
        connection = ws_manager.active_connections[connection_id]
        assert "query_stream" in connection.subscribed_events
        assert "table_recommendations" in connection.subscribed_events

    @pytest.mark.asyncio
    async def test_handle_query_request_message(self, ws_manager, mock_websocket):
        """Test handling query request message."""
        user_id = "user-123"
        session_id = "session-456"

        # Connect
        connection_id = await ws_manager.connect(mock_websocket, user_id, session_id)
        mock_websocket.messages_sent.clear()

        # Send query request message
        query_message = {
            "type": "query_request",
            "data": {
                "request_id": "test-query-123",
                "query": "SELECT * FROM users WHERE active = true",
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

        await ws_manager.handle_message(connection_id, query_message)

        # Verify query stream start response
        assert len(mock_websocket.messages_sent) == 1
        response = json.loads(mock_websocket.messages_sent[0])
        assert response["type"] == "query_stream_start"
        assert response["data"]["request_id"] == "test-query-123"

    @pytest.mark.asyncio
    async def test_send_error(self, ws_manager, mock_websocket):
        """Test sending error message."""
        user_id = "user-123"
        session_id = "session-456"

        # Connect
        connection_id = await ws_manager.connect(mock_websocket, user_id, session_id)
        mock_websocket.messages_sent.clear()

        # Send error
        await ws_manager.send_error(
            connection_id, "Test error message", "TEST_ERROR", "request-123"
        )

        # Verify error message
        assert len(mock_websocket.messages_sent) == 1
        error_message = json.loads(mock_websocket.messages_sent[0])
        assert error_message["type"] == "error"
        assert error_message["data"]["message"] == "Test error message"
        assert error_message["data"]["code"] == "TEST_ERROR"
        assert error_message["request_id"] == "request-123"

    @pytest.mark.asyncio
    async def test_connection_cleanup_on_send_failure(self, ws_manager):
        """Test connection cleanup when sending fails."""
        mock_websocket = MockWebSocket()
        user_id = "user-123"
        session_id = "session-456"

        # Connect
        connection_id = await ws_manager.connect(mock_websocket, user_id, session_id)

        # Simulate WebSocket failure
        mock_websocket.is_closed = True

        # Try to send message
        result = await ws_manager.send_to_connection(connection_id, {"type": "test"})

        # Verify send failed and connection was cleaned up
        assert result is False
        assert connection_id not in ws_manager.active_connections

    def test_get_connection_stats(self, ws_manager):
        """Test getting connection statistics."""
        # Initially no connections
        stats = ws_manager.get_connection_stats()
        assert stats["total_connections"] == 0
        assert stats["unique_users"] == 0
        assert stats["unique_sessions"] == 0

        # Add connections
        asyncio.run(self._add_test_connections(ws_manager))

        # Check updated stats
        stats = ws_manager.get_connection_stats()
        assert stats["total_connections"] == 3
        assert stats["unique_users"] == 2  # user-1 has 2 connections, user-2 has 1
        assert stats["unique_sessions"] == 3
        assert stats["connections_by_user"]["user-1"] == 2
        assert stats["connections_by_user"]["user-2"] == 1

    async def _add_test_connections(self, ws_manager):
        """Helper to add test connections."""
        # User 1 with 2 connections
        await ws_manager.connect(MockWebSocket(), "user-1", "session-1")
        await ws_manager.connect(MockWebSocket(), "user-1", "session-2")

        # User 2 with 1 connection
        await ws_manager.connect(MockWebSocket(), "user-2", "session-3")

    @pytest.mark.asyncio
    async def test_multiple_users_same_session(self, ws_manager):
        """Test multiple users in same session."""
        session_id = "shared-session"

        # Connect multiple users to same session
        mock_ws1 = MockWebSocket()
        mock_ws2 = MockWebSocket()

        conn1_id = await ws_manager.connect(mock_ws1, "user-1", session_id)
        conn2_id = await ws_manager.connect(mock_ws2, "user-2", session_id)

        # Verify both connections tracked under session
        assert len(ws_manager.session_connections[session_id]) == 2
        assert conn1_id in ws_manager.session_connections[session_id]
        assert conn2_id in ws_manager.session_connections[session_id]

        # Send message to session
        mock_ws1.messages_sent.clear()
        mock_ws2.messages_sent.clear()

        test_message = {"type": "session_message", "data": "Hello Session"}
        sent_count = await ws_manager.send_to_session(session_id, test_message)

        # Verify both users received message
        assert sent_count == 2
        assert len(mock_ws1.messages_sent) == 1
        assert len(mock_ws2.messages_sent) == 1

    @pytest.mark.asyncio
    async def test_invalid_message_handling(self, ws_manager, mock_websocket):
        """Test handling of invalid messages."""
        user_id = "user-123"
        session_id = "session-456"

        # Connect
        connection_id = await ws_manager.connect(mock_websocket, user_id, session_id)
        mock_websocket.messages_sent.clear()

        # Send message with unknown type
        invalid_message = {
            "type": "unknown_type",
            "data": {"content": "test"},
            "timestamp": datetime.utcnow().isoformat(),
        }

        await ws_manager.handle_message(connection_id, invalid_message)

        # Should receive error message
        assert len(mock_websocket.messages_sent) == 1
        error_response = json.loads(mock_websocket.messages_sent[0])
        assert error_response["type"] == "error"
        assert "Unknown message type" in error_response["data"]["message"]


@pytest.mark.asyncio
async def test_websocket_manager_integration():
    """Integration test for WebSocket manager workflow."""
    ws_manager = WebSocketManager()

    # Create mock WebSockets
    user1_ws = MockWebSocket()
    user2_ws = MockWebSocket()

    # Connect users
    user1_conn = await ws_manager.connect(user1_ws, "user-1", "session-1")
    user2_conn = await ws_manager.connect(user2_ws, "user-2", "session-2")

    # Clear initial connection messages
    user1_ws.messages_sent.clear()
    user2_ws.messages_sent.clear()

    # User 1 subscribes to events
    subscribe_msg = {
        "type": "subscribe",
        "data": {"events": ["query_stream"]},
        "timestamp": datetime.utcnow().isoformat(),
    }
    await ws_manager.handle_message(user1_conn, subscribe_msg)

    # User 1 sends query request
    query_msg = {
        "type": "query_request",
        "data": {"request_id": "integration-test-123", "query": "SELECT * FROM users"},
        "timestamp": datetime.utcnow().isoformat(),
    }
    await ws_manager.handle_message(user1_conn, query_msg)

    # Verify responses
    assert len(user1_ws.messages_sent) >= 2  # Subscription confirmation + query start
    assert len(user2_ws.messages_sent) == 0  # User 2 shouldn't receive anything

    # Send broadcast message
    broadcast_msg = {
        "type": "system_announcement",
        "data": "System maintenance in 5 minutes",
    }
    sent_count = await ws_manager.broadcast(broadcast_msg)

    # Verify broadcast reached both users
    assert sent_count == 2

    # Disconnect users
    await ws_manager.disconnect(user1_conn)
    await ws_manager.disconnect(user2_conn)

    # Verify cleanup
    assert len(ws_manager.active_connections) == 0
    assert len(ws_manager.user_connections) == 0
    assert len(ws_manager.session_connections) == 0
