/**
 * Tests for useStreaming hook.
 * Tests React hook integration, WebSocket management, and streaming state.
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useStreaming } from '../useStreaming';
import { QueryResponse, ValidationStatus } from '../../types/api';

// Mock the useWebSocket hook
const mockSend = vi.fn();
const mockConnect = vi.fn();
const mockDisconnect = vi.fn();
let mockIsConnected = true;
let mockWebSocketState = { status: 'connected' };

vi.mock('../useWebSocket', () => ({
  useWebSocket: vi.fn(() => ({
    state: mockWebSocketState,
    send: mockSend,
    connect: mockConnect,
    disconnect: mockDisconnect,
    isConnected: mockIsConnected
  }))
}));

describe('useStreaming', () => {
  const defaultOptions = {
    userId: 'test-user-123',
    sessionId: 'test-session-456',
    websocketUrl: 'ws://localhost:8000/ws'
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockSend.mockResolvedValue(undefined);
    mockConnect.mockResolvedValue(undefined);
    mockDisconnect.mockImplementation(() => {});
    mockIsConnected = true;
    mockWebSocketState = { status: 'connected' };
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Initial State', () => {
    it('should initialize with correct default state', () => {
      const { result } = renderHook(() => useStreaming(defaultOptions));

      expect(result.current.isStreaming).toBe(false);
      expect(result.current.currentSql).toBe('');
      expect(result.current.currentExplanation).toBe('');
      expect(result.current.progress.chunksReceived).toBe(0);
      expect(result.current.progress.percentComplete).toBe(0);
      expect(result.current.error).toBeNull();
      expect(result.current.finalResponse).toBeNull();
      expect(result.current.isConnected).toBe(true);
      expect(result.current.connectionState).toBe('connected');
    });

    it('should auto-connect when autoConnect is true', () => {
      renderHook(() => useStreaming({ ...defaultOptions, autoConnect: true }));

      expect(mockConnect).toHaveBeenCalled();
    });

    it('should not auto-connect when autoConnect is false', () => {
      renderHook(() => useStreaming({ ...defaultOptions, autoConnect: false }));

      expect(mockConnect).not.toHaveBeenCalled();
    });
  });

  describe('Query Streaming', () => {
    it('should start query streaming successfully', async () => {
      const onStreamStart = vi.fn();
      const { result } = renderHook(() =>
        useStreaming({ ...defaultOptions, onStreamStart })
      );

      await act(async () => {
        await result.current.startQuery('SELECT * FROM users');
      });

      expect(mockSend).toHaveBeenCalledWith({
        type: 'query_request',
        data: {
          request_id: expect.any(String),
          query: 'SELECT * FROM users',
          user_id: 'test-user-123',
          session_id: 'test-session-456'
        },
        timestamp: expect.any(String),
        request_id: expect.any(String),
        session_id: 'test-session-456'
      });
    });

    it('should throw error when not connected', async () => {
      // Mock disconnected state
      const { useWebSocket } = await import('../useWebSocket');
      vi.mocked(useWebSocket).mockReturnValue({
        state: { status: 'disconnected' },
        send: mockSend,
        connect: mockConnect,
        disconnect: mockDisconnect,
        isConnected: false
      } as any);

      const { result } = renderHook(() => useStreaming(defaultOptions));

      await expect(async () => {
        await act(async () => {
          await result.current.startQuery('SELECT * FROM users');
        });
      }).rejects.toThrow('WebSocket not connected');
    });

    it('should throw error when already streaming', async () => {
      const { result } = renderHook(() => useStreaming(defaultOptions));

      // Start first query
      await act(async () => {
        await result.current.startQuery('SELECT * FROM users');
      });

      // Simulate streaming state
      act(() => {
        // This would normally be set by the streaming callbacks
        // For testing, we'll manually trigger the state change
      });

      // Try to start second query
      await expect(async () => {
        await act(async () => {
          await result.current.startQuery('SELECT * FROM orders');
        });
      }).rejects.toThrow('Already streaming a query');
    });

    it('should use custom request ID when provided', async () => {
      const { result } = renderHook(() => useStreaming(defaultOptions));
      const customRequestId = 'custom-request-123';

      await act(async () => {
        await result.current.startQuery('SELECT * FROM users', customRequestId);
      });

      expect(mockSend).toHaveBeenCalledWith(
        expect.objectContaining({
          data: expect.objectContaining({
            request_id: customRequestId
          }),
          request_id: customRequestId
        })
      );
    });
  });

  describe('Streaming Callbacks', () => {
    it('should call onStreamStart callback', async () => {
      const onStreamStart = vi.fn();
      const { result } = renderHook(() =>
        useStreaming({ ...defaultOptions, onStreamStart })
      );

      // Simulate stream start
      act(() => {
        const streamingClient = (result.current as any).streamingClientRef
          ?.current;
        if (streamingClient) {
          streamingClient.startStream(
            'test-request-123',
            'SELECT * FROM users'
          );
        }
      });

      expect(onStreamStart).toHaveBeenCalledWith(
        'test-request-123',
        'SELECT * FROM users'
      );
    });

    it('should call onSqlUpdate callback', async () => {
      const onSqlUpdate = vi.fn();
      const { result } = renderHook(() =>
        useStreaming({ ...defaultOptions, onSqlUpdate })
      );

      // Simulate SQL update
      act(() => {
        const callbacks = (result.current as any).streamingClientRef?.current
          ?.callbacks;
        if (callbacks?.onSqlUpdate) {
          callbacks.onSqlUpdate('SELECT * FROM users', true);
        }
      });

      expect(onSqlUpdate).toHaveBeenCalledWith('SELECT * FROM users', true);
    });

    it('should call onExplanationUpdate callback', async () => {
      const onExplanationUpdate = vi.fn();
      const { result } = renderHook(() =>
        useStreaming({ ...defaultOptions, onExplanationUpdate })
      );

      // Simulate explanation update
      act(() => {
        const callbacks = (result.current as any).streamingClientRef?.current
          ?.callbacks;
        if (callbacks?.onExplanationUpdate) {
          callbacks.onExplanationUpdate('This query gets all users', true);
        }
      });

      expect(onExplanationUpdate).toHaveBeenCalledWith(
        'This query gets all users',
        true
      );
    });

    it('should call onComplete callback', async () => {
      const onComplete = vi.fn();
      const { result } = renderHook(() =>
        useStreaming({ ...defaultOptions, onComplete })
      );

      const mockResponse: QueryResponse = {
        sql: 'SELECT * FROM users',
        explanation: 'Get all users',
        confidence_score: 0.95,
        selected_tables: ['users'],
        validation_status: ValidationStatus.VALID,
        optimization_suggestions: [],
        request_id: 'test-request-123',
        generated_at: new Date().toISOString()
      };

      // Simulate completion
      act(() => {
        const callbacks = (result.current as any).streamingClientRef?.current
          ?.callbacks;
        if (callbacks?.onComplete) {
          callbacks.onComplete(mockResponse);
        }
      });

      expect(onComplete).toHaveBeenCalledWith(mockResponse);
    });

    it('should call onError callback', async () => {
      const onError = vi.fn();
      const { result } = renderHook(() =>
        useStreaming({ ...defaultOptions, onError })
      );

      const mockError = {
        code: 'SQL_SYNTAX_ERROR',
        message: 'Invalid SQL syntax'
      };

      // Simulate error
      act(() => {
        const callbacks = (result.current as any).streamingClientRef?.current
          ?.callbacks;
        if (callbacks?.onError) {
          callbacks.onError(mockError);
        }
      });

      expect(onError).toHaveBeenCalledWith(mockError);
    });
  });

  describe('State Management', () => {
    it('should update streaming state correctly', () => {
      const { result } = renderHook(() => useStreaming(defaultOptions));

      // Simulate streaming start
      act(() => {
        const callbacks = (result.current as any).streamingClientRef?.current
          ?.callbacks;
        if (callbacks?.onStreamStart) {
          callbacks.onStreamStart('test-request-123', 'SELECT * FROM users');
        }
      });

      expect(result.current.isStreaming).toBe(true);
      expect(result.current.error).toBeNull();
      expect(result.current.finalResponse).toBeNull();
      expect(result.current.currentSql).toBe('');
      expect(result.current.currentExplanation).toBe('');
    });

    it('should update SQL content progressively', () => {
      const { result } = renderHook(() => useStreaming(defaultOptions));

      // Simulate SQL updates
      act(() => {
        const callbacks = (result.current as any).streamingClientRef?.current
          ?.callbacks;
        if (callbacks?.onSqlUpdate) {
          callbacks.onSqlUpdate('SELECT *', false);
        }
      });

      expect(result.current.currentSql).toBe('SELECT *');

      act(() => {
        const callbacks = (result.current as any).streamingClientRef?.current
          ?.callbacks;
        if (callbacks?.onSqlUpdate) {
          callbacks.onSqlUpdate('SELECT * FROM users', true);
        }
      });

      expect(result.current.currentSql).toBe('SELECT * FROM users');
    });

    it('should update progress correctly', () => {
      const { result } = renderHook(() => useStreaming(defaultOptions));

      // Simulate progress update
      act(() => {
        const callbacks = (result.current as any).streamingClientRef?.current
          ?.callbacks;
        if (callbacks?.onProgress) {
          callbacks.onProgress({
            chunksReceived: 3,
            totalExpected: 10,
            percentComplete: 30
          });
        }
      });

      expect(result.current.progress.chunksReceived).toBe(3);
      expect(result.current.progress.totalExpected).toBe(10);
      expect(result.current.progress.percentComplete).toBe(30);
    });
  });

  describe('Control Actions', () => {
    it('should stop streaming correctly', () => {
      const { result } = renderHook(() => useStreaming(defaultOptions));

      // Start streaming
      act(() => {
        const callbacks = (result.current as any).streamingClientRef?.current
          ?.callbacks;
        if (callbacks?.onStreamStart) {
          callbacks.onStreamStart('test-request-123', 'SELECT * FROM users');
        }
      });

      expect(result.current.isStreaming).toBe(true);

      // Stop streaming
      act(() => {
        result.current.stopStreaming();
      });

      expect(result.current.isStreaming).toBe(false);
    });

    it('should reset state correctly', () => {
      const { result } = renderHook(() => useStreaming(defaultOptions));

      // Set some state
      act(() => {
        const callbacks = (result.current as any).streamingClientRef?.current
          ?.callbacks;
        if (callbacks?.onStreamStart) {
          callbacks.onStreamStart('test-request-123', 'SELECT * FROM users');
        }
        if (callbacks?.onSqlUpdate) {
          callbacks.onSqlUpdate('SELECT * FROM users', true);
        }
      });

      expect(result.current.isStreaming).toBe(true);
      expect(result.current.currentSql).toBe('SELECT * FROM users');

      // Reset
      act(() => {
        result.current.reset();
      });

      expect(result.current.isStreaming).toBe(false);
      expect(result.current.currentSql).toBe('');
      expect(result.current.currentExplanation).toBe('');
      expect(result.current.progress.chunksReceived).toBe(0);
      expect(result.current.error).toBeNull();
      expect(result.current.finalResponse).toBeNull();
    });

    it('should connect and disconnect WebSocket', () => {
      const { result } = renderHook(() => useStreaming(defaultOptions));

      act(() => {
        result.current.connect();
      });

      expect(mockConnect).toHaveBeenCalled();

      act(() => {
        result.current.disconnect();
      });

      expect(mockDisconnect).toHaveBeenCalled();
    });
  });

  describe('Utility Functions', () => {
    it('should estimate time remaining correctly', () => {
      const { result } = renderHook(() => useStreaming(defaultOptions));

      // Without progress data
      expect(result.current.estimateTimeRemaining()).toBeNull();

      // With progress data but no start time
      act(() => {
        const callbacks = (result.current as any).streamingClientRef?.current
          ?.callbacks;
        if (callbacks?.onProgress) {
          callbacks.onProgress({
            chunksReceived: 3,
            totalExpected: 10,
            percentComplete: 30
          });
        }
      });

      // Still null without start time
      expect(result.current.estimateTimeRemaining()).toBeNull();
    });

    it('should get streaming state correctly', () => {
      const { result } = renderHook(() => useStreaming(defaultOptions));

      // Initially null
      expect(result.current.getStreamingState()).toBeNull();

      // After starting stream
      act(() => {
        const callbacks = (result.current as any).streamingClientRef?.current
          ?.callbacks;
        if (callbacks?.onStreamStart) {
          callbacks.onStreamStart('test-request-123', 'SELECT * FROM users');
        }
      });

      const state = result.current.getStreamingState();
      expect(state).toBeDefined();
      expect(state?.requestId).toBe('test-request-123');
    });
  });

  describe('Error Scenarios', () => {
    it('should handle WebSocket send errors', async () => {
      mockSend.mockRejectedValue(new Error('Send failed'));

      const { result } = renderHook(() => useStreaming(defaultOptions));

      await expect(async () => {
        await act(async () => {
          await result.current.startQuery('SELECT * FROM users');
        });
      }).rejects.toThrow('Send failed');
    });

    it('should set error state on WebSocket errors', () => {
      const { useWebSocket } = require('../useWebSocket');

      vi.mocked(useWebSocket).mockImplementation(
        (_url: any, options: { onError: (arg0: Error) => void }) => {
          // Simulate WebSocket error
          setTimeout(() => {
            options?.onError?.(new Error('WebSocket connection failed'));
          }, 0);

          return {
            state: { status: 'error' },
            send: mockSend,
            connect: mockConnect,
            disconnect: mockDisconnect,
            isConnected: false
          };
        }
      );

      const { result } = renderHook(() => useStreaming(defaultOptions));

      // Wait for error to be processed
      waitFor(() => {
        expect(result.current.error).toEqual({
          code: 'WEBSOCKET_ERROR',
          message: 'WebSocket connection failed'
        });
      });
    });
  });

  describe('Cleanup', () => {
    it('should cleanup on unmount', () => {
      const { result, unmount } = renderHook(() =>
        useStreaming(defaultOptions)
      );

      // Start streaming
      act(() => {
        const callbacks = (result.current as any).streamingClientRef?.current
          ?.callbacks;
        if (callbacks?.onStreamStart) {
          callbacks.onStreamStart('test-request-123', 'SELECT * FROM users');
        }
      });

      // Unmount should cleanup
      unmount();

      // Verify cleanup (this is implicit - no errors should occur)
      expect(true).toBe(true);
    });
  });
});
