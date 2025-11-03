/**
 * Simplified tests for useStreaming hook focusing on public API and behavior.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useStreaming } from '../useStreaming';

// Mock the useWebSocket hook with a simple implementation
const mockSend = vi.fn();
const mockConnect = vi.fn();
const mockDisconnect = vi.fn();

vi.mock('../useWebSocket', () => ({
  useWebSocket: vi.fn(() => ({
    state: { status: 'connected' },
    send: mockSend,
    connect: mockConnect,
    disconnect: mockDisconnect,
    isConnected: true
  }))
}));

describe('useStreaming - Basic Functionality', () => {
  const defaultOptions = {
    userId: 'test-user-123',
    sessionId: 'test-session-456'
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockSend.mockResolvedValue(undefined);
    mockConnect.mockResolvedValue(undefined);
    mockDisconnect.mockImplementation(() => {});
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
  });

  describe('Query Operations', () => {
    it('should provide startQuery function', () => {
      const { result } = renderHook(() => useStreaming(defaultOptions));

      expect(typeof result.current.startQuery).toBe('function');
    });

    it('should provide stopStreaming function', () => {
      const { result } = renderHook(() => useStreaming(defaultOptions));

      expect(typeof result.current.stopStreaming).toBe('function');
    });

    it('should provide reset function', () => {
      const { result } = renderHook(() => useStreaming(defaultOptions));

      expect(typeof result.current.reset).toBe('function');
    });

    it('should attempt to send WebSocket message when starting query', async () => {
      const { result } = renderHook(() => useStreaming(defaultOptions));

      await act(async () => {
        await result.current.startQuery('SELECT * FROM users');
      });

      expect(mockSend).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'query_request',
          data: expect.objectContaining({
            query: 'SELECT * FROM users',
            user_id: 'test-user-123',
            session_id: 'test-session-456'
          })
        })
      );
    });
  });

  describe('Connection Management', () => {
    it('should provide connect function', () => {
      const { result } = renderHook(() => useStreaming(defaultOptions));

      expect(typeof result.current.connect).toBe('function');
    });

    it('should provide disconnect function', () => {
      const { result } = renderHook(() => useStreaming(defaultOptions));

      expect(typeof result.current.disconnect).toBe('function');
    });

    it('should call WebSocket connect when connect is called', () => {
      const { result } = renderHook(() => useStreaming(defaultOptions));

      act(() => {
        result.current.connect();
      });

      expect(mockConnect).toHaveBeenCalled();
    });

    it('should call WebSocket disconnect when disconnect is called', () => {
      const { result } = renderHook(() => useStreaming(defaultOptions));

      act(() => {
        result.current.disconnect();
      });

      expect(mockDisconnect).toHaveBeenCalled();
    });
  });

  describe('Utility Functions', () => {
    it('should provide getStreamingState function', () => {
      const { result } = renderHook(() => useStreaming(defaultOptions));

      expect(typeof result.current.getStreamingState).toBe('function');
    });

    it('should provide estimateTimeRemaining function', () => {
      const { result } = renderHook(() => useStreaming(defaultOptions));

      expect(typeof result.current.estimateTimeRemaining).toBe('function');
    });

    it('should return null for time estimation initially', () => {
      const { result } = renderHook(() => useStreaming(defaultOptions));

      expect(result.current.estimateTimeRemaining()).toBeNull();
    });
  });

  describe('Callbacks', () => {
    it('should accept callback options', () => {
      const onStreamStart = vi.fn();
      const onComplete = vi.fn();
      const onError = vi.fn();

      const { result } = renderHook(() =>
        useStreaming({
          ...defaultOptions,
          onStreamStart,
          onComplete,
          onError
        })
      );

      // Should not throw and should initialize properly
      expect(result.current.isStreaming).toBe(false);
    });
  });

  describe('Error Handling', () => {
    it('should handle send errors gracefully', async () => {
      mockSend.mockRejectedValue(new Error('Send failed'));

      const { result } = renderHook(() => useStreaming(defaultOptions));

      await expect(async () => {
        await act(async () => {
          await result.current.startQuery('SELECT * FROM users');
        });
      }).rejects.toThrow('Send failed');
    });
  });

  describe('State Management', () => {
    it('should reset state when reset is called', () => {
      const { result } = renderHook(() => useStreaming(defaultOptions));

      act(() => {
        result.current.reset();
      });

      expect(result.current.isStreaming).toBe(false);
      expect(result.current.currentSql).toBe('');
      expect(result.current.currentExplanation).toBe('');
      expect(result.current.error).toBeNull();
      expect(result.current.finalResponse).toBeNull();
    });

    it('should stop streaming when stopStreaming is called', () => {
      const { result } = renderHook(() => useStreaming(defaultOptions));

      act(() => {
        result.current.stopStreaming();
      });

      expect(result.current.isStreaming).toBe(false);
    });
  });
});
