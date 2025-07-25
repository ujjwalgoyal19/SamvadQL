/**
 * WebSocket message type definitions for real-time communication
 */

import { QueryResponse, ApiError } from './api';

// Base WebSocket message interface
export interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
  request_id?: string;
  session_id?: string;
}

// Connection status messages
export interface ConnectionMessage extends WebSocketMessage {
  type: 'connection';
  data: {
    status: 'connected' | 'disconnected' | 'reconnecting' | 'error';
    message?: string;
  };
}

// Query streaming messages
export interface QueryStreamStartMessage extends WebSocketMessage {
  type: 'query_stream_start';
  data: {
    request_id: string;
    query: string;
  };
}

export interface QueryStreamChunkMessage extends WebSocketMessage {
  type: 'query_stream_chunk';
  data: {
    chunk: string;
    chunk_type: 'sql' | 'explanation' | 'metadata';
    is_partial: boolean;
  };
}

export interface QueryStreamCompleteMessage extends WebSocketMessage {
  type: 'query_stream_complete';
  data: {
    response: QueryResponse;
    total_chunks: number;
    duration_ms: number;
  };
}

export interface QueryStreamErrorMessage extends WebSocketMessage {
  type: 'query_stream_error';
  data: {
    error: ApiError;
    partial_response?: Partial<QueryResponse>;
  };
}

// Table selection and validation messages
export interface TableSuggestionMessage extends WebSocketMessage {
  type: 'table_suggestion';
  data: {
    suggested_tables: string[];
    confidence_scores: Record<string, number>;
    reasoning: string;
  };
}

export interface ValidationUpdateMessage extends WebSocketMessage {
  type: 'validation_update';
  data: {
    is_valid: boolean;
    errors: string[];
    warnings: string[];
    suggestions: string[];
  };
}

// System status messages
export interface SystemStatusMessage extends WebSocketMessage {
  type: 'system_status';
  data: {
    status: 'healthy' | 'degraded' | 'down';
    services: Record<string, 'up' | 'down' | 'degraded'>;
    message?: string;
  };
}

export interface RateLimitMessage extends WebSocketMessage {
  type: 'rate_limit';
  data: {
    limit_type: 'query' | 'connection' | 'bandwidth';
    current_usage: number;
    limit: number;
    reset_time: string;
  };
}

// User session messages
export interface SessionUpdateMessage extends WebSocketMessage {
  type: 'session_update';
  data: {
    session_id: string;
    expires_at: string;
    preferences: Record<string, any>;
  };
}

export interface UserActivityMessage extends WebSocketMessage {
  type: 'user_activity';
  data: {
    activity_type: 'query' | 'feedback' | 'navigation';
    details: Record<string, any>;
  };
}

// Heartbeat and keepalive
export interface HeartbeatMessage extends WebSocketMessage {
  type: 'heartbeat';
  data: {
    server_time: string;
    client_should_respond: boolean;
  };
}

export interface PingMessage extends WebSocketMessage {
  type: 'ping';
  data: {
    timestamp: string;
  };
}

export interface PongMessage extends WebSocketMessage {
  type: 'pong';
  data: {
    timestamp: string;
    latency_ms?: number;
  };
}

// Union type for all possible WebSocket messages
export type WebSocketMessageType =
  | ConnectionMessage
  | QueryStreamStartMessage
  | QueryStreamChunkMessage
  | QueryStreamCompleteMessage
  | QueryStreamErrorMessage
  | TableSuggestionMessage
  | ValidationUpdateMessage
  | SystemStatusMessage
  | RateLimitMessage
  | SessionUpdateMessage
  | UserActivityMessage
  | HeartbeatMessage
  | PingMessage
  | PongMessage;

// WebSocket connection configuration
export interface WebSocketConfig {
  url: string;
  protocols?: string[];
  reconnect: boolean;
  reconnectInterval: number;
  maxReconnectAttempts: number;
  heartbeatInterval: number;
  timeout: number;
}

// WebSocket connection state
export interface WebSocketState {
  status: 'connecting' | 'connected' | 'disconnected' | 'error';
  lastConnected?: Date;
  lastDisconnected?: Date;
  reconnectAttempts: number;
  latency?: number;
  error?: string;
}

// Event handlers for WebSocket messages
export interface WebSocketEventHandlers {
  onConnection?: (message: ConnectionMessage) => void;
  onQueryStreamStart?: (message: QueryStreamStartMessage) => void;
  onQueryStreamChunk?: (message: QueryStreamChunkMessage) => void;
  onQueryStreamComplete?: (message: QueryStreamCompleteMessage) => void;
  onQueryStreamError?: (message: QueryStreamErrorMessage) => void;
  onTableSuggestion?: (message: TableSuggestionMessage) => void;
  onValidationUpdate?: (message: ValidationUpdateMessage) => void;
  onSystemStatus?: (message: SystemStatusMessage) => void;
  onRateLimit?: (message: RateLimitMessage) => void;
  onSessionUpdate?: (message: SessionUpdateMessage) => void;
  onUserActivity?: (message: UserActivityMessage) => void;
  onHeartbeat?: (message: HeartbeatMessage) => void;
  onPing?: (message: PingMessage) => void;
  onPong?: (message: PongMessage) => void;
  onError?: (error: Error) => void;
  onClose?: (event: CloseEvent) => void;
}

// Message queue for handling offline scenarios
export interface QueuedMessage {
  message: WebSocketMessage;
  timestamp: Date;
  retryCount: number;
  priority: 'high' | 'medium' | 'low';
}

// WebSocket client interface
export interface WebSocketClient {
  connect(): Promise<void>;
  disconnect(): void;
  send(message: WebSocketMessage): Promise<void>;
  subscribe(
    eventType: string,
    handler: (message: WebSocketMessage) => void
  ): void;
  unsubscribe(
    eventType: string,
    handler?: (message: WebSocketMessage) => void
  ): void;
  getState(): WebSocketState;
  isConnected(): boolean;
}
