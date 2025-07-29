/**
 * Custom React hook for WebSocket connection management
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import {
  WebSocketClient,
  WebSocketConfig,
  WebSocketState,
  WebSocketMessage,
  WebSocketEventHandlers,
  QueuedMessage
} from '../types/websocket';

interface UseWebSocketOptions extends Partial<WebSocketConfig> {
  onMessage?: (message: WebSocketMessage) => void;
  onError?: (error: Error) => void;
  onOpen?: () => void;
  onClose?: () => void;
}

interface UseWebSocketReturn {
  state: WebSocketState;
  send: (message: WebSocketMessage) => Promise<void>;
  connect: () => Promise<void>;
  disconnect: () => void;
  isConnected: boolean;
}

const DEFAULT_CONFIG: WebSocketConfig = {
  url: '',
  reconnect: true,
  reconnectInterval: 5000,
  maxReconnectAttempts: 5,
  heartbeatInterval: 30000,
  timeout: 10000
};

export function useWebSocket(
  url: string,
  options: UseWebSocketOptions = {}
): UseWebSocketReturn {
  const { onMessage, onError, onOpen, onClose, ...configOptions } = options;

  const config: WebSocketConfig = {
    ...DEFAULT_CONFIG,
    url,
    ...configOptions
  };

  const [state, setState] = useState<WebSocketState>({
    status: 'disconnected',
    reconnectAttempts: 0
  });

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const messageQueueRef = useRef<QueuedMessage[]>([]);

  const updateState = useCallback((updates: Partial<WebSocketState>) => {
    setState((prev) => ({ ...prev, ...updates }));
  }, []);

  const clearTimeouts = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }
  }, []);

  const startHeartbeat = useCallback(() => {
    if (config.heartbeatInterval > 0) {
      heartbeatIntervalRef.current = setInterval(() => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          const heartbeatMessage: WebSocketMessage = {
            type: 'ping',
            data: { timestamp: new Date().toISOString() },
            timestamp: new Date().toISOString()
          };
          wsRef.current.send(JSON.stringify(heartbeatMessage));
        }
      }, config.heartbeatInterval);
    }
  }, [config.heartbeatInterval]);

  const processMessageQueue = useCallback(() => {
    if (
      wsRef.current?.readyState === WebSocket.OPEN &&
      messageQueueRef.current.length > 0
    ) {
      const messages = [...messageQueueRef.current];
      messageQueueRef.current = [];

      messages.forEach((queuedMessage) => {
        try {
          wsRef.current?.send(JSON.stringify(queuedMessage.message));
        } catch (error) {
          console.error('Failed to send queued message:', error);
          // Re-queue message if it failed
          messageQueueRef.current.push(queuedMessage);
        }
      });
    }
  }, []);

  const handleMessage = useCallback(
    (event: MessageEvent) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);

        // Handle pong messages for latency calculation
        if (message.type === 'pong') {
          const sentTime = new Date(message.data.timestamp).getTime();
          const latency = Date.now() - sentTime;
          updateState({ latency });
        }

        onMessage?.(message);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
        onError?.(error as Error);
      }
    },
    [onMessage, onError, updateState]
  );

  const handleOpen = useCallback(() => {
    updateState({
      status: 'connected',
      lastConnected: new Date(),
      reconnectAttempts: 0,
      error: undefined
    });

    startHeartbeat();
    processMessageQueue();
    onOpen?.();
  }, [updateState, startHeartbeat, processMessageQueue, onOpen]);

  const handleClose = useCallback(
    (event: CloseEvent) => {
      clearTimeouts();

      updateState({
        status: 'disconnected',
        lastDisconnected: new Date()
      });

      // Attempt reconnection if enabled and not a manual close
      if (
        config.reconnect &&
        !event.wasClean &&
        state.reconnectAttempts < config.maxReconnectAttempts
      ) {
        updateState({
          status: 'disconnected',
          reconnectAttempts: state.reconnectAttempts + 1
        });

        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, config.reconnectInterval);
      }

      onClose?.();
    },
    [clearTimeouts, updateState, config, state.reconnectAttempts, onClose]
  );

  const handleError = useCallback(
    (event: Event) => {
      const error = new Error('WebSocket connection error');
      updateState({
        status: 'error',
        error: error.message
      });
      onError?.(error);
    },
    [updateState, onError]
  );

  const connect = useCallback(async (): Promise<void> => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    updateState({ status: 'connecting' });

    try {
      wsRef.current = new WebSocket(config.url, config.protocols);

      wsRef.current.onopen = handleOpen;
      wsRef.current.onmessage = handleMessage;
      wsRef.current.onclose = handleClose;
      wsRef.current.onerror = handleError;

      // Set connection timeout
      const timeoutId = setTimeout(() => {
        if (wsRef.current?.readyState === WebSocket.CONNECTING) {
          wsRef.current.close();
          const error = new Error('WebSocket connection timeout');
          updateState({
            status: 'error',
            error: error.message
          });
          onError?.(error);
        }
      }, config.timeout);

      // Clear timeout when connection is established
      wsRef.current.onopen = (event) => {
        clearTimeout(timeoutId);
        handleOpen();
      };
    } catch (error) {
      updateState({
        status: 'error',
        error: (error as Error).message
      });
      onError?.(error as Error);
    }
  }, [
    config,
    updateState,
    handleOpen,
    handleMessage,
    handleClose,
    handleError,
    onError
  ]);

  const disconnect = useCallback(() => {
    clearTimeouts();

    if (wsRef.current) {
      wsRef.current.close(1000, 'Manual disconnect');
      wsRef.current = null;
    }

    updateState({
      status: 'disconnected',
      reconnectAttempts: 0
    });
  }, [clearTimeouts, updateState]);

  const send = useCallback(
    async (message: WebSocketMessage): Promise<void> => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        try {
          wsRef.current.send(JSON.stringify(message));
        } catch (error) {
          throw new Error(
            `Failed to send message: ${(error as Error).message}`
          );
        }
      } else {
        // Queue message for later sending
        const queuedMessage: QueuedMessage = {
          message,
          timestamp: new Date(),
          retryCount: 0,
          priority: 'medium'
        };
        messageQueueRef.current.push(queuedMessage);

        // Try to reconnect if not connected
        if (state.status === 'disconnected') {
          await connect();
        }
      }
    },
    [state.status, connect]
  );

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      clearTimeouts();
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [clearTimeouts]);

  return {
    state,
    send,
    connect,
    disconnect,
    isConnected: state.status === 'connected'
  };
}
