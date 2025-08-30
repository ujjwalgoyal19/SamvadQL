/**
 * Tests for streaming client functionality.
 * Tests progressive rendering, message processing, and error handling.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import {
  StreamingClient,
  createStreamingClient,
  formatStreamingProgress
} from '../streamingClient';
import {
  QueryStreamStartMessage,
  QueryStreamChunkMessage,
  QueryStreamCompleteMessage,
  QueryStreamErrorMessage
} from '../../types/websocket';
import { QueryResponse, ValidationStatus } from '../../types/api';

describe('StreamingClient', () => {
  let streamingClient: StreamingClient;
  let mockCallbacks: any;

  beforeEach(() => {
    mockCallbacks = {
      onStreamStart: vi.fn(),
      onChunk: vi.fn(),
      onSqlUpdate: vi.fn(),
      onExplanationUpdate: vi.fn(),
      onValidationUpdate: vi.fn(),
      onComplete: vi.fn(),
      onError: vi.fn(),
      onProgress: vi.fn()
    };

    streamingClient = new StreamingClient(mockCallbacks);
  });

  describe('Stream Initialization', () => {
    it('should initialize streaming session correctly', () => {
      const requestId = 'test-request-123';
      const query = 'SELECT * FROM users';

      streamingClient.startStream(requestId, query);

      const state = streamingClient.getState();
      expect(state).toBeDefined();
      expect(state!.requestId).toBe(requestId);
      expect(state!.isStreaming).toBe(true);
      expect(state!.chunks).toEqual([]);
      expect(state!.currentSql).toBe('');
      expect(state!.currentExplanation).toBe('');
      expect(state!.progress.chunksReceived).toBe(0);
      expect(state!.progress.percentComplete).toBe(0);

      expect(mockCallbacks.onStreamStart).toHaveBeenCalledWith(
        requestId,
        query
      );
    });

    it('should handle stream start message', () => {
      const message: QueryStreamStartMessage = {
        type: 'query_stream_start',
        data: {
          request_id: 'test-request-123',
          query: 'SELECT * FROM users'
        },
        timestamp: new Date().toISOString()
      };

      streamingClient.processMessage(message);

      expect(mockCallbacks.onStreamStart).toHaveBeenCalledWith(
        'test-request-123',
        'SELECT * FROM users'
      );
      expect(streamingClient.isStreaming()).toBe(true);
    });
  });

  describe('Chunk Processing', () => {
    beforeEach(() => {
      streamingClient.startStream('test-request-123', 'SELECT * FROM users');
    });

    it('should process SQL chunks correctly', () => {
      const chunkMessage: QueryStreamChunkMessage = {
        type: 'query_stream_chunk',
        data: {
          chunk: 'SELECT * FROM users',
          chunk_type: 'sql',
          is_partial: false,
          total_expected_chunks: 3
        },
        timestamp: new Date().toISOString(),
        request_id: 'test-request-123'
      };

      streamingClient.processMessage(chunkMessage);

      const state = streamingClient.getState();
      expect(state!.chunks).toHaveLength(1);
      expect(state!.currentSql).toBe('SELECT * FROM users');
      expect(state!.progress.chunksReceived).toBe(1);
      expect(state!.progress.totalExpected).toBe(3);
      expect(state!.progress.percentComplete).toBeCloseTo(33.33, 1);

      expect(mockCallbacks.onChunk).toHaveBeenCalled();
      expect(mockCallbacks.onSqlUpdate).toHaveBeenCalledWith(
        'SELECT * FROM users',
        true
      );
      expect(mockCallbacks.onProgress).toHaveBeenCalled();
    });

    it('should handle partial SQL chunks', () => {
      const chunk1: QueryStreamChunkMessage = {
        type: 'query_stream_chunk',
        data: {
          chunk: 'SELECT * FROM',
          chunk_type: 'sql',
          is_partial: true
        },
        timestamp: new Date().toISOString(),
        request_id: 'test-request-123'
      };

      const chunk2: QueryStreamChunkMessage = {
        type: 'query_stream_chunk',
        data: {
          chunk: ' users',
          chunk_type: 'sql',
          is_partial: false
        },
        timestamp: new Date().toISOString(),
        request_id: 'test-request-123'
      };

      streamingClient.processMessage(chunk1);
      streamingClient.processMessage(chunk2);

      expect(streamingClient.getCurrentSql()).toBe('SELECT * FROM users');
      expect(mockCallbacks.onSqlUpdate).toHaveBeenCalledWith(
        'SELECT * FROM',
        false
      );
      expect(mockCallbacks.onSqlUpdate).toHaveBeenCalledWith(
        'SELECT * FROM users',
        true
      );
    });

    it('should process explanation chunks correctly', () => {
      const chunkMessage: QueryStreamChunkMessage = {
        type: 'query_stream_chunk',
        data: {
          chunk: 'This query retrieves all users from the database.',
          chunk_type: 'explanation',
          is_partial: false
        },
        timestamp: new Date().toISOString(),
        request_id: 'test-request-123'
      };

      streamingClient.processMessage(chunkMessage);

      expect(streamingClient.getCurrentExplanation()).toBe(
        'This query retrieves all users from the database.'
      );
      expect(mockCallbacks.onExplanationUpdate).toHaveBeenCalledWith(
        'This query retrieves all users from the database.',
        true
      );
    });

    it('should process validation chunks correctly', () => {
      const validationData = {
        is_valid: true,
        errors: [],
        warnings: ['Query may be slow'],
        is_destructive: false,
        estimated_cost: 125.5
      };

      const chunkMessage: QueryStreamChunkMessage = {
        type: 'query_stream_chunk',
        data: {
          chunk: JSON.stringify(validationData),
          chunk_type: 'validation',
          is_partial: false
        },
        timestamp: new Date().toISOString(),
        request_id: 'test-request-123'
      };

      streamingClient.processMessage(chunkMessage);

      expect(mockCallbacks.onValidationUpdate).toHaveBeenCalledWith(
        validationData
      );
    });

    it('should handle invalid JSON in validation chunks', () => {
      const consoleSpy = vi
        .spyOn(console, 'error')
        .mockImplementation(() => {});

      const chunkMessage: QueryStreamChunkMessage = {
        type: 'query_stream_chunk',
        data: {
          chunk: 'invalid json',
          chunk_type: 'validation',
          is_partial: false
        },
        timestamp: new Date().toISOString(),
        request_id: 'test-request-123'
      };

      streamingClient.processMessage(chunkMessage);

      expect(consoleSpy).toHaveBeenCalledWith(
        'Failed to parse validation data:',
        expect.any(Error)
      );
      consoleSpy.mockRestore();
    });
  });

  describe('Stream Completion', () => {
    beforeEach(() => {
      streamingClient.startStream('test-request-123', 'SELECT * FROM users');
    });

    it('should handle stream completion correctly', () => {
      const finalResponse: QueryResponse = {
        sql: 'SELECT * FROM users WHERE active = true',
        explanation: 'Query to get active users',
        confidence_score: 0.95,
        selected_tables: ['users'],
        validation_status: ValidationStatus.VALID,
        optimization_suggestions: [],
        execution_time_estimate: 0.25,
        request_id: 'test-request-123',
        generated_at: new Date().toISOString()
      };

      const completeMessage: QueryStreamCompleteMessage = {
        type: 'query_stream_complete',
        data: {
          response: finalResponse,
          total_chunks: 5,
          duration_ms: 1500
        },
        timestamp: new Date().toISOString(),
        request_id: 'test-request-123'
      };

      streamingClient.processMessage(completeMessage);

      const state = streamingClient.getState();
      expect(state!.isStreaming).toBe(false);
      expect(state!.finalResponse).toEqual(finalResponse);
      expect(state!.progress.percentComplete).toBe(100);

      expect(mockCallbacks.onComplete).toHaveBeenCalledWith(
        finalResponse,
        state
      );
    });
  });

  describe('Error Handling', () => {
    beforeEach(() => {
      streamingClient.startStream('test-request-123', 'SELECT * FROM users');
    });

    it('should handle stream errors correctly', () => {
      const error = {
        code: 'SQL_SYNTAX_ERROR',
        message: 'Invalid SQL syntax'
      };

      const errorMessage: QueryStreamErrorMessage = {
        type: 'query_stream_error',
        data: {
          error,
          partial_response: { sql: 'SELECT * FROM' }
        },
        timestamp: new Date().toISOString(),
        request_id: 'test-request-123'
      };

      streamingClient.processMessage(errorMessage);

      const state = streamingClient.getState();
      expect(state!.isStreaming).toBe(false);
      expect(state!.error).toEqual(error);

      expect(mockCallbacks.onError).toHaveBeenCalledWith(error, state);
    });

    it('should handle error chunks correctly', () => {
      const errorData = {
        message: 'Database connection failed',
        code: 'DB_CONNECTION_ERROR',
        timestamp: new Date().toISOString()
      };

      const chunkMessage: QueryStreamChunkMessage = {
        type: 'query_stream_chunk',
        data: {
          chunk: JSON.stringify(errorData),
          chunk_type: 'error',
          is_partial: false
        },
        timestamp: new Date().toISOString(),
        request_id: 'test-request-123'
      };

      streamingClient.processMessage(chunkMessage);

      expect(mockCallbacks.onError).toHaveBeenCalledWith(
        errorData,
        expect.any(Object)
      );
    });

    it('should handle chunks without active stream', () => {
      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

      // Don't start stream
      streamingClient.reset();

      const chunkMessage: QueryStreamChunkMessage = {
        type: 'query_stream_chunk',
        data: {
          chunk: 'SELECT * FROM users',
          chunk_type: 'sql',
          is_partial: false
        },
        timestamp: new Date().toISOString(),
        request_id: 'test-request-123'
      };

      streamingClient.processMessage(chunkMessage);

      expect(consoleSpy).toHaveBeenCalledWith(
        'Received chunk without active stream'
      );
      consoleSpy.mockRestore();
    });
  });

  describe('Utility Methods', () => {
    it('should reset streaming state correctly', () => {
      streamingClient.startStream('test-request-123', 'SELECT * FROM users');

      // Add some state
      const chunkMessage: QueryStreamChunkMessage = {
        type: 'query_stream_chunk',
        data: {
          chunk: 'SELECT * FROM users',
          chunk_type: 'sql',
          is_partial: false
        },
        timestamp: new Date().toISOString(),
        request_id: 'test-request-123'
      };
      streamingClient.processMessage(chunkMessage);

      // Reset
      streamingClient.reset();

      expect(streamingClient.getState()).toBeNull();
      expect(streamingClient.isStreaming()).toBe(false);
      expect(streamingClient.getCurrentSql()).toBe('');
      expect(streamingClient.getCurrentExplanation()).toBe('');
    });

    it('should update callbacks correctly', () => {
      const newCallbacks = {
        onStreamStart: vi.fn(),
        onComplete: vi.fn()
      };

      streamingClient.updateCallbacks(newCallbacks);
      streamingClient.startStream('test-request-123', 'SELECT * FROM users');

      expect(newCallbacks.onStreamStart).toHaveBeenCalled();
      expect(mockCallbacks.onStreamStart).not.toHaveBeenCalled();
    });

    it('should reconstruct content from chunks correctly', () => {
      streamingClient.startStream('test-request-123', 'SELECT * FROM users');

      // Add SQL chunks
      const chunk1: QueryStreamChunkMessage = {
        type: 'query_stream_chunk',
        data: {
          chunk: 'SELECT * FROM',
          chunk_type: 'sql',
          is_partial: true
        },
        timestamp: new Date().toISOString(),
        request_id: 'test-request-123'
      };

      const chunk2: QueryStreamChunkMessage = {
        type: 'query_stream_chunk',
        data: {
          chunk: ' users',
          chunk_type: 'sql',
          is_partial: false
        },
        timestamp: new Date().toISOString(),
        request_id: 'test-request-123'
      };

      streamingClient.processMessage(chunk1);
      streamingClient.processMessage(chunk2);

      const reconstructedSql = streamingClient.reconstructContent('sql');
      expect(reconstructedSql).toBe('SELECT * FROM users');
    });

    it('should get progress correctly', () => {
      streamingClient.startStream('test-request-123', 'SELECT * FROM users');

      const progress = streamingClient.getProgress();
      expect(progress.chunksReceived).toBe(0);
      expect(progress.percentComplete).toBe(0);
      expect(progress.totalExpected).toBeUndefined();
    });
  });

  describe('Unknown Message Types', () => {
    it('should handle unknown message types gracefully', () => {
      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

      const unknownMessage = {
        type: 'unknown_message_type',
        data: { content: 'test' },
        timestamp: new Date().toISOString()
      };

      streamingClient.processMessage(unknownMessage as any);

      expect(consoleSpy).toHaveBeenCalledWith(
        'Unknown streaming message type:',
        'unknown_message_type'
      );
      consoleSpy.mockRestore();
    });
  });
});

describe('createStreamingClient', () => {
  it('should create streaming client with default error handling', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    const consoleLogSpy = vi.spyOn(console, 'log').mockImplementation(() => {});

    const client = createStreamingClient();

    // Test default error callback
    client.startStream('test-request', 'test query');
    const errorMessage: QueryStreamErrorMessage = {
      type: 'query_stream_error',
      data: {
        error: { code: 'TEST_ERROR', message: 'Test error' }
      },
      timestamp: new Date().toISOString(),
      request_id: 'test-request'
    };

    client.processMessage(errorMessage);

    expect(consoleSpy).toHaveBeenCalledWith('Streaming error:', {
      code: 'TEST_ERROR',
      message: 'Test error'
    });

    consoleSpy.mockRestore();
    consoleLogSpy.mockRestore();
  });

  it('should merge custom callbacks with defaults', () => {
    const customOnError = vi.fn();
    const client = createStreamingClient({ onError: customOnError });

    client.startStream('test-request', 'test query');
    const errorMessage: QueryStreamErrorMessage = {
      type: 'query_stream_error',
      data: {
        error: { code: 'TEST_ERROR', message: 'Test error' }
      },
      timestamp: new Date().toISOString(),
      request_id: 'test-request'
    };

    client.processMessage(errorMessage);

    expect(customOnError).toHaveBeenCalled();
  });
});

describe('formatStreamingProgress', () => {
  it('should format progress with total expected chunks', () => {
    const progress = {
      chunksReceived: 3,
      totalExpected: 10,
      percentComplete: 30
    };

    const formatted = formatStreamingProgress(progress);
    expect(formatted).toBe('3/10 chunks (30%)');
  });

  it('should format progress without total expected chunks', () => {
    const progress = {
      chunksReceived: 5,
      percentComplete: 0
    };

    const formatted = formatStreamingProgress(progress);
    expect(formatted).toBe('5 chunks received');
  });
});
