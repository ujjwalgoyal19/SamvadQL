/**
 * React hook for managing streaming query responses and progressive rendering.
 * Integrates with WebSocket connection and streaming client.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import {
  StreamingClient,
  StreamingState,
  StreamingCallbacks,
  createStreamingClient
} from '../services/streamingClient';
import { useWebSocket } from './useWebSocket';
import { QueryResponse, ApiError } from '../types/api';
import { WebSocketMessage } from '../types/websocket';

export interface UseStreamingOptions {
  websocketUrl?: string;
  userId: string;
  sessionId: string;
  onStreamStart?: (requestId: string, query: string) => void;
  onSqlUpdate?: (sql: string, isComplete: boolean) => void;
  onExplanationUpdate?: (explanation: string, isComplete: boolean) => void;
  onComplete?: (response: QueryResponse) => void;
  onError?: (error: ApiError) => void;
  autoConnect?: boolean;
}

export interface UseStreamingReturn {
  // Streaming state
  isStreaming: boolean;
  currentSql: string;
  currentExplanation: string;
  progress: {
    chunksReceived: number;
    totalExpected?: number;
    percentComplete: number;
  };
  error: ApiError | null;
  finalResponse: QueryResponse | null;

  // WebSocket state
  isConnected: boolean;
  connectionState: string;

  // Actions
  startQuery: (query: string, requestId?: string) => Promise<void>;
  stopStreaming: () => void;
  reset: () => void;
  connect: () => Promise<void>;
  disconnect: () => void;

  // Utilities
  getStreamingState: () => StreamingState | null;
  estimateTimeRemaining: () => number | null;
}

export function useStreaming(options: UseStreamingOptions): UseStreamingReturn {
  const {
    websocketUrl = `ws://localhost:8000/ws`,
    userId,
    sessionId,
    onStreamStart,
    onSqlUpdate,
    onExplanationUpdate,
    onComplete,
    onError,
    autoConnect = true
  } = options;

  // State
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentSql, setCurrentSql] = useState('');
  const [currentExplanation, setCurrentExplanation] = useState('');
  const [progress, setProgress] = useState({
    chunksReceived: 0,
    percentComplete: 0
  });
  const [error, setError] = useState<ApiError | null>(null);
  const [finalResponse, setFinalResponse] = useState<QueryResponse | null>(
    null
  );

  // Refs
  const streamingClientRef = useRef<StreamingClient | null>(null);
  const streamStartTimeRef = useRef<Date | null>(null);

  // WebSocket connection
  const websocketUrlWithParams = `${websocketUrl}?user_id=${userId}&session_id=${sessionId}`;

  const {
    state: wsState,
    send: sendWebSocketMessage,
    connect: connectWebSocket,
    disconnect: disconnectWebSocket,
    isConnected
  } = useWebSocket(websocketUrlWithParams, {
    onMessage: handleWebSocketMessage,
    onError: (error) => {
      console.error('WebSocket error:', error);
      setError({
        code: 'WEBSOCKET_ERROR',
        message: error.message
      });
    },
    onOpen: () => {
      console.log('WebSocket connected for streaming');
    },
    onClose: () => {
      console.log('WebSocket disconnected');
      if (isStreaming) {
        setError({
          code: 'CONNECTION_LOST',
          message: 'WebSocket connection lost during streaming'
        });
        setIsStreaming(false);
      }
    }
  });

  // Initialize streaming client
  useEffect(() => {
    const callbacks: StreamingCallbacks = {
      onStreamStart: (requestId, query) => {
        setIsStreaming(true);
        setError(null);
        setFinalResponse(null);
        setCurrentSql('');
        setCurrentExplanation('');
        setProgress({ chunksReceived: 0, percentComplete: 0 });
        streamStartTimeRef.current = new Date();
        onStreamStart?.(requestId, query);
      },

      onSqlUpdate: (sql, isComplete) => {
        setCurrentSql(sql);
        onSqlUpdate?.(sql, isComplete);
      },

      onExplanationUpdate: (explanation, isComplete) => {
        setCurrentExplanation(explanation);
        onExplanationUpdate?.(explanation, isComplete);
      },

      onProgress: (progressData) => {
        setProgress(progressData);
      },

      onComplete: (response) => {
        setIsStreaming(false);
        setFinalResponse(response);
        setProgress((prev) => ({ ...prev, percentComplete: 100 }));
        onComplete?.(response);
      },

      onError: (errorData) => {
        setIsStreaming(false);
        setError(errorData);
        onError?.(errorData);
      }
    };

    streamingClientRef.current = createStreamingClient(callbacks);

    return () => {
      streamingClientRef.current?.reset();
    };
  }, [onStreamStart, onSqlUpdate, onExplanationUpdate, onComplete, onError]);

  // Auto-connect on mount
  useEffect(() => {
    if (autoConnect && !isConnected) {
      connectWebSocket();
    }
  }, [autoConnect, isConnected, connectWebSocket]);

  // Handle WebSocket messages
  function handleWebSocketMessage(message: WebSocketMessage): void {
    if (streamingClientRef.current) {
      streamingClientRef.current.processMessage(message);
    }
  }

  // Start query streaming
  const startQuery = useCallback(
    async (query: string, requestId?: string): Promise<void> => {
      if (!isConnected) {
        throw new Error('WebSocket not connected');
      }

      if (isStreaming) {
        throw new Error('Already streaming a query');
      }

      const queryRequestId =
        requestId ||
        `query_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

      try {
        await sendWebSocketMessage({
          type: 'query_request',
          data: {
            request_id: queryRequestId,
            query,
            user_id: userId,
            session_id: sessionId
          },
          timestamp: new Date().toISOString(),
          request_id: queryRequestId,
          session_id: sessionId
        });
      } catch (error) {
        setError({
          code: 'SEND_ERROR',
          message: `Failed to send query: ${
            error instanceof Error ? error.message : 'Unknown error'
          }`
        });
        throw error;
      }
    },
    [isConnected, isStreaming, sendWebSocketMessage, userId, sessionId]
  );

  // Stop streaming
  const stopStreaming = useCallback(() => {
    if (streamingClientRef.current) {
      streamingClientRef.current.reset();
    }
    setIsStreaming(false);
    streamStartTimeRef.current = null;
  }, []);

  // Reset all state
  const reset = useCallback(() => {
    stopStreaming();
    setCurrentSql('');
    setCurrentExplanation('');
    setProgress({ chunksReceived: 0, percentComplete: 0 });
    setError(null);
    setFinalResponse(null);
  }, [stopStreaming]);

  // Get streaming state
  const getStreamingState = useCallback((): StreamingState | null => {
    return streamingClientRef.current?.getState() || null;
  }, []);

  // Estimate time remaining
  const estimateTimeRemaining = useCallback((): number | null => {
    if (
      !streamStartTimeRef.current ||
      !progress.totalExpected ||
      progress.chunksReceived === 0
    ) {
      return null;
    }

    const elapsedMs = Date.now() - streamStartTimeRef.current.getTime();
    const avgTimePerChunk = elapsedMs / progress.chunksReceived;
    const remainingChunks = progress.totalExpected - progress.chunksReceived;

    return remainingChunks * avgTimePerChunk;
  }, [progress]);

  return {
    // Streaming state
    isStreaming,
    currentSql,
    currentExplanation,
    progress,
    error,
    finalResponse,

    // WebSocket state
    isConnected,
    connectionState: wsState.status,

    // Actions
    startQuery,
    stopStreaming,
    reset,
    connect: connectWebSocket,
    disconnect: disconnectWebSocket,

    // Utilities
    getStreamingState,
    estimateTimeRemaining
  };
}

/**
 * Hook for streaming with automatic retry logic
 */
export function useStreamingWithRetry(
  options: UseStreamingOptions & {
    maxRetries?: number;
    retryDelay?: number;
  }
): UseStreamingReturn & {
  retryCount: number;
  isRetrying: boolean;
} {
  const { maxRetries = 3, retryDelay = 1000, ...streamingOptions } = options;

  const [retryCount, setRetryCount] = useState(0);
  const [isRetrying, setIsRetrying] = useState(false);

  const retryTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const streaming = useStreaming({
    ...streamingOptions,
    onError: (error) => {
      options.onError?.(error);

      // Attempt retry for connection errors
      if (
        (error.code === 'WEBSOCKET_ERROR' ||
          error.code === 'CONNECTION_LOST') &&
        retryCount < maxRetries
      ) {
        setIsRetrying(true);
        setRetryCount((prev) => prev + 1);

        retryTimeoutRef.current = setTimeout(() => {
          streaming.connect();
          setIsRetrying(false);
        }, retryDelay * Math.pow(2, retryCount)); // Exponential backoff
      }
    }
  });

  // Reset retry count on successful connection
  useEffect(() => {
    if (streaming.isConnected && retryCount > 0) {
      setRetryCount(0);
    }
  }, [streaming.isConnected, retryCount]);

  // Cleanup retry timeout
  useEffect(() => {
    return () => {
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
      }
    };
  }, []);

  return {
    ...streaming,
    retryCount,
    isRetrying
  };
}
