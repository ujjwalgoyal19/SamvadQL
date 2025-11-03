// @ts-nocheck

/**
 * Streaming Query Editor component that demonstrates progressive query rendering.
 * Shows real-time SQL generation with explanations and progress indicators.
 */

import React, { useState, useEffect } from 'react';
import { useStreaming } from '../hooks/useStreaming';
import { QueryResponse, ApiError } from '../types/api';

interface StreamingQueryEditorProps {
  userId: string;
  sessionId: string;
  onQueryComplete?: (response: QueryResponse) => void;
  onError?: (error: ApiError) => void;
  className?: string;
}

export const StreamingQueryEditor: React.FC<StreamingQueryEditorProps> = ({
  userId,
  sessionId,
  onQueryComplete,
  onError,
  className = ''
}) => {
  const [query, setQuery] = useState('');
  const [streamingLog, setStreamingLog] = useState<string[]>([]);

  const {
    isStreaming,
    currentSql,
    currentExplanation,
    progress,
    error,
    finalResponse,
    isConnected,
    connectionState,
    startQuery,
    stopStreaming,
    reset,
    connect,
    disconnect,
    estimateTimeRemaining
  } = useStreaming({
    userId,
    sessionId,
    onStreamStart: (requestId, query) => {
      setStreamingLog((prev) => [
        ...prev,
        `🚀 Started streaming query: "${query}" (ID: ${requestId})`
      ]);
    },
    onSqlUpdate: (sql, isComplete) => {
      if (isComplete) {
        setStreamingLog((prev) => [
          ...prev,
          `✅ SQL generation complete (${sql.length} characters)`
        ]);
      }
    },
    onExplanationUpdate: (explanation, isComplete) => {
      if (isComplete) {
        setStreamingLog((prev) => [
          ...prev,
          `📝 Explanation complete (${explanation.length} characters)`
        ]);
      }
    },
    onComplete: (response) => {
      setStreamingLog((prev) => [
        ...prev,
        `🎉 Query streaming completed successfully`
      ]);
      onQueryComplete?.(response);
    },
    onError: (error) => {
      setStreamingLog((prev) => [
        ...prev,
        `❌ Streaming error: ${error.message}`
      ]);
      onError?.(error);
    }
  });

  const handleSubmitQuery = async () => {
    if (!query.trim()) {
      alert('Please enter a query');
      return;
    }

    if (!isConnected) {
      alert('WebSocket not connected. Please connect first.');
      return;
    }

    try {
      await startQuery(query.trim());
    } catch (error) {
      console.error('Failed to start query:', error);
      alert(
        `Failed to start query: ${
          error instanceof Error ? error.message : 'Unknown error'
        }`
      );
    }
  };

  const handleReset = () => {
    reset();
    setStreamingLog([]);
    setQuery('');
  };

  const timeRemaining = estimateTimeRemaining();

  return (
    <div className={`streaming-query-editor ${className}`}>
      <div className="editor-header">
        <h2>Streaming Query Editor</h2>
        <div className="connection-status">
          <span
            className={`status-indicator ${
              isConnected ? 'connected' : 'disconnected'
            }`}
          >
            {isConnected ? '🟢' : '🔴'}
          </span>
          <span>WebSocket: {connectionState}</span>
          {!isConnected && (
            <button onClick={connect} className="connect-btn">
              Connect
            </button>
          )}
          {isConnected && (
            <button onClick={disconnect} className="disconnect-btn">
              Disconnect
            </button>
          )}
        </div>
      </div>

      {/* Query Input */}
      <div className="query-input-section">
        <label htmlFor="query-input">Natural Language Query:</label>
        <textarea
          id="query-input"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Enter your natural language query here..."
          rows={3}
          disabled={isStreaming}
          className="query-textarea"
        />
        <div className="input-actions">
          <button
            onClick={handleSubmitQuery}
            disabled={!isConnected || isStreaming || !query.trim()}
            className="submit-btn"
          >
            {isStreaming ? 'Streaming...' : 'Generate SQL'}
          </button>
          <button
            onClick={stopStreaming}
            disabled={!isStreaming}
            className="stop-btn"
          >
            Stop
          </button>
          <button onClick={handleReset} className="reset-btn">
            Reset
          </button>
        </div>
      </div>

      {/* Progress Indicator */}
      {isStreaming && (
        <div className="progress-section">
          <div className="progress-header">
            <span>Streaming Progress</span>
            <span>{Math.round(progress.percentComplete)}%</span>
          </div>
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${progress.percentComplete}%` }}
            />
          </div>
          <div className="progress-details">
            <span>
              Chunks: {progress.chunksReceived}
              {progress.totalExpected ? `/${progress.totalExpected}` : ''}
            </span>
            {timeRemaining && (
              <span>Est. remaining: {Math.round(timeRemaining / 1000)}s</span>
            )}
          </div>
        </div>
      )}

      {/* Streaming Results */}
      <div className="results-section">
        {/* SQL Output */}
        <div className="sql-output">
          <h3>Generated SQL {isStreaming && currentSql && '(Streaming...)'}</h3>
          <pre className="sql-content">
            {currentSql || finalResponse?.sql || 'No SQL generated yet...'}
          </pre>
        </div>

        {/* Explanation Output */}
        <div className="explanation-output">
          <h3>
            Explanation {isStreaming && currentExplanation && '(Streaming...)'}
          </h3>
          <div className="explanation-content">
            {currentExplanation ||
              finalResponse?.explanation ||
              'No explanation available yet...'}
          </div>
        </div>

        {/* Final Response Details */}
        {finalResponse && (
          <div className="response-details">
            <h3>Response Details</h3>
            <div className="details-grid">
              <div className="detail-item">
                <label>Confidence Score:</label>
                <span>
                  {(finalResponse.confidence_score * 100).toFixed(1)}%
                </span>
              </div>
              <div className="detail-item">
                <label>Selected Tables:</label>
                <span>{finalResponse.selected_tables.join(', ')}</span>
              </div>
              <div className="detail-item">
                <label>Validation Status:</label>
                <span className={`status-${finalResponse.validation_status}`}>
                  {finalResponse.validation_status}
                </span>
              </div>
              {finalResponse.execution_time_estimate && (
                <div className="detail-item">
                  <label>Est. Execution Time:</label>
                  <span>
                    {finalResponse.execution_time_estimate.toFixed(2)}s
                  </span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="error-section">
            <h3>Error</h3>
            <div className="error-content">
              <strong>{error.code}:</strong> {error.message}
              {error.details && (
                <pre>{JSON.stringify(error.details, null, 2)}</pre>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Streaming Log */}
      <div className="streaming-log">
        <h3>Streaming Log</h3>
        <div className="log-content">
          {streamingLog.length === 0 ? (
            <p>No streaming activity yet...</p>
          ) : (
            streamingLog.map((entry, index) => (
              <div key={index} className="log-entry">
                <span className="log-timestamp">
                  {new Date().toLocaleTimeString()}
                </span>
                <span className="log-message">{entry}</span>
              </div>
            ))
          )}
        </div>
      </div>

      <style jsx>{`
        .streaming-query-editor {
          max-width: 1200px;
          margin: 0 auto;
          padding: 20px;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
            sans-serif;
        }

        .editor-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
          padding-bottom: 10px;
          border-bottom: 1px solid #e0e0e0;
        }

        .connection-status {
          display: flex;
          align-items: center;
          gap: 10px;
        }

        .status-indicator {
          font-size: 12px;
        }

        .connect-btn,
        .disconnect-btn {
          padding: 4px 8px;
          font-size: 12px;
          border: 1px solid #ccc;
          border-radius: 4px;
          background: white;
          cursor: pointer;
        }

        .connect-btn:hover,
        .disconnect-btn:hover {
          background: #f5f5f5;
        }

        .query-input-section {
          margin-bottom: 20px;
        }

        .query-input-section label {
          display: block;
          margin-bottom: 5px;
          font-weight: 500;
        }

        .query-textarea {
          width: 100%;
          padding: 10px;
          border: 1px solid #ccc;
          border-radius: 4px;
          font-family: inherit;
          resize: vertical;
        }

        .input-actions {
          display: flex;
          gap: 10px;
          margin-top: 10px;
        }

        .submit-btn,
        .stop-btn,
        .reset-btn {
          padding: 8px 16px;
          border: 1px solid #ccc;
          border-radius: 4px;
          background: white;
          cursor: pointer;
        }

        .submit-btn {
          background: #007bff;
          color: white;
          border-color: #007bff;
        }

        .submit-btn:disabled {
          background: #ccc;
          border-color: #ccc;
          cursor: not-allowed;
        }

        .stop-btn {
          background: #dc3545;
          color: white;
          border-color: #dc3545;
        }

        .stop-btn:disabled {
          background: #ccc;
          border-color: #ccc;
          cursor: not-allowed;
        }

        .progress-section {
          margin-bottom: 20px;
          padding: 15px;
          background: #f8f9fa;
          border-radius: 4px;
        }

        .progress-header {
          display: flex;
          justify-content: space-between;
          margin-bottom: 10px;
          font-weight: 500;
        }

        .progress-bar {
          width: 100%;
          height: 8px;
          background: #e0e0e0;
          border-radius: 4px;
          overflow: hidden;
          margin-bottom: 10px;
        }

        .progress-fill {
          height: 100%;
          background: #007bff;
          transition: width 0.3s ease;
        }

        .progress-details {
          display: flex;
          justify-content: space-between;
          font-size: 12px;
          color: #666;
        }

        .results-section {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 20px;
          margin-bottom: 20px;
        }

        .sql-output,
        .explanation-output {
          border: 1px solid #e0e0e0;
          border-radius: 4px;
          overflow: hidden;
        }

        .sql-output h3,
        .explanation-output h3 {
          margin: 0;
          padding: 10px;
          background: #f8f9fa;
          border-bottom: 1px solid #e0e0e0;
          font-size: 14px;
        }

        .sql-content {
          padding: 15px;
          margin: 0;
          background: #f8f8f8;
          font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
          font-size: 12px;
          line-height: 1.4;
          overflow-x: auto;
          min-height: 100px;
        }

        .explanation-content {
          padding: 15px;
          min-height: 100px;
          line-height: 1.5;
        }

        .response-details {
          grid-column: 1 / -1;
          border: 1px solid #e0e0e0;
          border-radius: 4px;
          overflow: hidden;
        }

        .response-details h3 {
          margin: 0;
          padding: 10px;
          background: #f8f9fa;
          border-bottom: 1px solid #e0e0e0;
          font-size: 14px;
        }

        .details-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 15px;
          padding: 15px;
        }

        .detail-item {
          display: flex;
          flex-direction: column;
          gap: 5px;
        }

        .detail-item label {
          font-weight: 500;
          font-size: 12px;
          color: #666;
        }

        .status-valid {
          color: #28a745;
          font-weight: 500;
        }

        .status-invalid {
          color: #dc3545;
          font-weight: 500;
        }

        .status-warning {
          color: #ffc107;
          font-weight: 500;
        }

        .error-section {
          grid-column: 1 / -1;
          border: 1px solid #dc3545;
          border-radius: 4px;
          overflow: hidden;
        }

        .error-section h3 {
          margin: 0;
          padding: 10px;
          background: #f8d7da;
          border-bottom: 1px solid #dc3545;
          font-size: 14px;
          color: #721c24;
        }

        .error-content {
          padding: 15px;
          color: #721c24;
        }

        .error-content pre {
          background: #f8f8f8;
          padding: 10px;
          border-radius: 4px;
          overflow-x: auto;
          margin-top: 10px;
        }

        .streaming-log {
          border: 1px solid #e0e0e0;
          border-radius: 4px;
          overflow: hidden;
        }

        .streaming-log h3 {
          margin: 0;
          padding: 10px;
          background: #f8f9fa;
          border-bottom: 1px solid #e0e0e0;
          font-size: 14px;
        }

        .log-content {
          max-height: 200px;
          overflow-y: auto;
          padding: 10px;
        }

        .log-entry {
          display: flex;
          gap: 10px;
          margin-bottom: 5px;
          font-size: 12px;
        }

        .log-timestamp {
          color: #666;
          font-family: monospace;
          min-width: 80px;
        }

        .log-message {
          flex: 1;
        }

        @media (max-width: 768px) {
          .results-section {
            grid-template-columns: 1fr;
          }

          .details-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
};

export default StreamingQueryEditor;
