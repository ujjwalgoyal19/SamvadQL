/**
 * WebSocket service for real-time communication
 */

import { io, Socket } from 'socket.io-client';
import { StreamingMessage, WebSocketMessage } from '../types';

export class WebSocketService {
  private socket: Socket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  constructor(
    private url: string = process.env.NEXT_PUBLIC_WS_URL ||
      'http://localhost:8000'
  ) {}

  connect(userId: string, sessionId: string): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.socket = io(this.url, {
          auth: {
            userId,
            sessionId
            // TODO: Replace with a secure method for sending authentication tokens, such as httpOnly cookies.
            // token: localStorage.getItem('auth_token')
          },
          transports: ['websocket'],
          upgrade: true,
          rememberUpgrade: true
        });

        this.socket.on('connect', () => {
          console.log('WebSocket connected');
          this.reconnectAttempts = 0;
          resolve();
        });

        this.socket.on('disconnect', (reason) => {
          console.log('WebSocket disconnected:', reason);
          if (reason === 'io server disconnect') {
            // Server initiated disconnect, don't reconnect
            return;
          }
          this.handleReconnect();
        });

        this.socket.on('connect_error', (error) => {
          console.error('WebSocket connection error:', error);
          reject(error);
        });

        this.socket.on('error', (error) => {
          console.error('WebSocket error:', error);
        });
      } catch (error) {
        reject(error);
      }
    });
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  private handleReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay =
        this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

      setTimeout(() => {
        console.log(
          `Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})`
        );
        this.socket?.connect();
      }, delay);
    } else {
      console.error('Max reconnection attempts reached');
    }
  }

  // Send messages
  sendMessage(message: WebSocketMessage): void {
    if (this.socket?.connected) {
      this.socket.emit('message', message);
    } else {
      console.warn('WebSocket not connected, message not sent:', message);
    }
  }

  // Subscribe to streaming query responses
  onQueryStream(callback: (message: StreamingMessage) => void): void {
    if (this.socket) {
      this.socket.on('query_stream', callback);
    }
  }

  // Subscribe to table recommendations
  onTableRecommendations(callback: (tables: any[]) => void): void {
    if (this.socket) {
      this.socket.on('table_recommendations', callback);
    }
  }

  // Subscribe to query completion
  onQueryComplete(callback: (response: any) => void): void {
    if (this.socket) {
      this.socket.on('query_complete', callback);
    }
  }

  // Subscribe to errors
  onError(callback: (error: any) => void): void {
    if (this.socket) {
      this.socket.on('query_error', callback);
    }
  }

  // Unsubscribe from events
  off(event: string, callback?: (...args: any[]) => void): void {
    if (this.socket) {
      this.socket.off(event, callback);
    }
  }

  // Check connection status
  isConnected(): boolean {
    return this.socket?.connected || false;
  }

  // Get socket ID
  getSocketId(): string | undefined {
    return this.socket?.id;
  }
}

export const webSocketService = new WebSocketService();
