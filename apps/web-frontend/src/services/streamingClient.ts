/**
 * Streaming client for progressive query rendering and real-time response handling.
 * Handles JSON streaming consumption and WebSocket message processing.
 */

import {
  WebSocketMessage,
  QueryStreamChunkMessage,
  QueryStreamCompleteMessage,
  QueryStreamErrorMessage,
  QueryStreamStartMessage
} from '../types/websocket';
import { QueryResponse, ApiError } from '../types/api';

export interface StreamingChunk {
  chunkId: string;
  chunkType:
    | 'sql'
    | 'explanation'
    | 'metadata'
    | 'validation'
    | 'error'
    | 'complete';
  content: string;
  isPartial: boolean;
  sequenceNumber: number;
  totalExpectedChunks?: number;
  requestId: string;
  timestamp: string;
}

export interface StreamingState {
  requestId: string;
  isStreaming: boolean;
  chunks: StreamingChunk[];
  currentSql: string;
  currentExplanation: string;
  error?: ApiError;
  finalResponse?: QueryResponse;
  progress: {
    chunksReceived: number;
    totalExpected?: number;
    percentComplete: number;
  };
}

export interface StreamingCallbacks {
  onStreamStart?: (requestId: string, query: string) => void;
  onChunk?: (chunk: StreamingChunk, state: StreamingState) => void;
  onSqlUpdate?: (sql: string, isComplete: boolean) => void;
  onExplanationUpdate?: (explanation: string, isComplete: boolean) => void;
  onValidationUpdate?: (validation: any) => void;
  onComplete?: (response: QueryResponse, state: StreamingState) => void;
  onError?: (error: ApiError, partialState?: StreamingState) => void;
  onProgress?: (progress: {
    chunksReceived: number;
    totalExpected?: number;
    percentComplete: number;
  }) => void;
}

export class StreamingClient {
  private state: StreamingState | null = null;
  private callbacks: StreamingCallbacks = {};
  private chunkBuffer: Map<string, StreamingChunk[]> = new Map();

  constructor(callbacks: StreamingCallbacks = {}) {
    this.callbacks = callbacks;
  }

  /**
   * Initialize streaming session
   */
  startStream(requestId: string, query: string): void {
    this.state = {
      requestId,
      isStreaming: true,
      chunks: [],
      currentSql: '',
      currentExplanation: '',
      progress: {
        chunksReceived: 0,
        percentComplete: 0
      }
    };

    this.chunkBuffer.set(requestId, []);
    this.callbacks.onStreamStart?.(requestId, query);
  }

  /**
   * Process incoming WebSocket message
   */
  processMessage(message: WebSocketMessage): void {
    switch (message.type) {
      case 'query_stream_start':
        this.handleStreamStart(message as QueryStreamStartMessage);
        break;
      case 'query_stream_chunk':
        this.handleStreamChunk(message as QueryStreamChunkMessage);
        break;
      case 'query_stream_complete':
        this.handleStreamComplete(message as QueryStreamCompleteMessage);
        break;
      case 'query_stream_error':
        this.handleStreamError(message as QueryStreamErrorMessage);
        break;
      default:
        console.warn('Unknown streaming message type:', message.type);
    }
  }

  /**
   * Handle stream start message
   */
  private handleStreamStart(message: QueryStreamStartMessage): void {
    const { request_id, query } = message.data;
    this.startStream(request_id, query);
  }

  /**
   * Handle streaming chunk message
   */
  private handleStreamChunk(message: QueryStreamChunkMessage): void {
    if (!this.state) {
      console.warn('Received chunk without active stream');
      return;
    }

    const chunkData = message.data;
    const chunk: StreamingChunk = {
      chunkId: message.timestamp, // Use timestamp as chunk ID if not provided
      chunkType: chunkData.chunk_type as StreamingChunk['chunkType'],
      content: chunkData.chunk,
      isPartial: chunkData.is_partial,
      sequenceNumber: this.state.chunks.length + 1,
      totalExpectedChunks: chunkData.total_expected_chunks,
      requestId: message.request_id || this.state.requestId,
      timestamp: message.timestamp
    };

    // Add chunk to state
    this.state.chunks.push(chunk);
    this.state.progress.chunksReceived = this.state.chunks.length;

    if (chunk.totalExpectedChunks) {
      this.state.progress.totalExpected = chunk.totalExpectedChunks;
      this.state.progress.percentComplete =
        (this.state.progress.chunksReceived / chunk.totalExpectedChunks) * 100;
    }

    // Update content based on chunk type
    this.updateContentFromChunk(chunk);

    // Trigger callbacks
    this.callbacks.onChunk?.(chunk, this.state);
    this.callbacks.onProgress?.(this.state.progress);
  }

  /**
   * Handle stream completion message
   */
  private handleStreamComplete(message: QueryStreamCompleteMessage): void {
    if (!this.state) {
      console.warn('Received completion without active stream');
      return;
    }

    const { response, total_chunks, duration_ms } = message.data;

    this.state.isStreaming = false;
    this.state.finalResponse = response;
    this.state.progress.percentComplete = 100;

    this.callbacks.onComplete?.(response, this.state);
  }

  /**
   * Handle stream error message
   */
  private handleStreamError(message: QueryStreamErrorMessage): void {
    if (!this.state) {
      console.warn('Received error without active stream');
      return;
    }

    const { error, partial_response } = message.data;

    this.state.isStreaming = false;
    this.state.error = error;

    this.callbacks.onError?.(error, this.state);
  }

  /**
   * Update content from streaming chunk
   */
  private updateContentFromChunk(chunk: StreamingChunk): void {
    if (!this.state) return;

    switch (chunk.chunkType) {
      case 'sql':
        if (chunk.isPartial) {
          this.state.currentSql += chunk.content;
        } else {
          this.state.currentSql += chunk.content;
        }
        this.callbacks.onSqlUpdate?.(this.state.currentSql, !chunk.isPartial);
        break;

      case 'explanation':
        if (chunk.isPartial) {
          this.state.currentExplanation += chunk.content;
        } else {
          this.state.currentExplanation += chunk.content;
        }
        this.callbacks.onExplanationUpdate?.(
          this.state.currentExplanation,
          !chunk.isPartial
        );
        break;

      case 'validation':
        try {
          const validationData = JSON.parse(chunk.content);
          this.callbacks.onValidationUpdate?.(validationData);
        } catch (e) {
          console.error('Failed to parse validation data:', e);
        }
        break;

      case 'error':
        try {
          const errorData = JSON.parse(chunk.content);
          this.callbacks.onError?.(errorData, this.state);
        } catch (e) {
          console.error('Failed to parse error data:', e);
        }
        break;
    }
  }

  /**
   * Get current streaming state
   */
  getState(): StreamingState | null {
    return this.state;
  }

  /**
   * Check if currently streaming
   */
  isStreaming(): boolean {
    return this.state?.isStreaming || false;
  }

  /**
   * Get current SQL content
   */
  getCurrentSql(): string {
    return this.state?.currentSql || '';
  }

  /**
   * Get current explanation content
   */
  getCurrentExplanation(): string {
    return this.state?.currentExplanation || '';
  }

  /**
   * Get streaming progress
   */
  getProgress(): {
    chunksReceived: number;
    totalExpected?: number;
    percentComplete: number;
  } {
    return this.state?.progress || { chunksReceived: 0, percentComplete: 0 };
  }

  /**
   * Reset streaming state
   */
  reset(): void {
    if (this.state) {
      this.chunkBuffer.delete(this.state.requestId);
    }
    this.state = null;
  }

  /**
   * Update callbacks
   */
  updateCallbacks(callbacks: Partial<StreamingCallbacks>): void {
    this.callbacks = { ...this.callbacks, ...callbacks };
  }

  /**
   * Get all chunks for debugging
   */
  getChunks(): StreamingChunk[] {
    return this.state?.chunks || [];
  }

  /**
   * Reconstruct content from chunks (useful for debugging)
   */
  reconstructContent(chunkType: StreamingChunk['chunkType']): string {
    if (!this.state) return '';

    return this.state.chunks
      .filter((chunk) => chunk.chunkType === chunkType)
      .sort((a, b) => a.sequenceNumber - b.sequenceNumber)
      .map((chunk) => chunk.content)
      .join('');
  }
}

/**
 * Create a streaming client with default error handling
 */
export function createStreamingClient(
  callbacks: StreamingCallbacks = {}
): StreamingClient {
  const defaultCallbacks: StreamingCallbacks = {
    onError: (error, state) => {
      console.error('Streaming error:', error);
    },
    onProgress: (progress) => {
      console.log('Streaming progress:', progress);
    },
    ...callbacks
  };

  return new StreamingClient(defaultCallbacks);
}

/**
 * Utility function to format streaming progress as percentage
 */
export function formatStreamingProgress(progress: {
  chunksReceived: number;
  totalExpected?: number;
  percentComplete: number;
}): string {
  if (progress.totalExpected) {
    return `${progress.chunksReceived}/${
      progress.totalExpected
    } chunks (${Math.round(progress.percentComplete)}%)`;
  }
  return `${progress.chunksReceived} chunks received`;
}

/**
 * Utility function to estimate completion time based on current progress
 */
export function estimateCompletionTime(
  startTime: Date,
  progress: {
    chunksReceived: number;
    totalExpected?: number;
    percentComplete: number;
  }
): number | null {
  if (!progress.totalExpected || progress.chunksReceived === 0) {
    return null;
  }

  const elapsedMs = Date.now() - startTime.getTime();
  const avgTimePerChunk = elapsedMs / progress.chunksReceived;
  const remainingChunks = progress.totalExpected - progress.chunksReceived;

  return remainingChunks * avgTimePerChunk;
}
