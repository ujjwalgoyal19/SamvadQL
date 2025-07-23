/**
 * API service for SamvadQL frontend
 */

import axios, { AxiosInstance, AxiosResponse } from 'axios';
import {
  QueryRequest,
  QueryResponse,
  TableSchema,
  ValidationResult,
  UserFeedback,
  ApiResponse,
  TableRecommendation
} from '../types';

class ApiService {
  private client: AxiosInstance;
  private authToken?: string;

  /**
   * Set the authentication token securely in memory.
   * @param token The JWT or authentication token.
   */
  setAuthToken(token: string) {
    this.authToken = token;
  }

  /**
   * Clear the authentication token from memory.
   */
  clearAuthToken() {
    this.authToken = undefined;
  }

  constructor(
    baseURL: string = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  ) {
    this.client = axios.create({
      baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json'
      }
    });

    // Request interceptor for auth
    // NOTE: Avoid using localStorage for tokens due to XSS vulnerability.
    // Instead, expect the token to be set via a setter method or use HttpOnly cookies for authentication.
    this.client.interceptors.request.use((config) => {
      // If using cookies, the browser will send them automatically.
      // If you must use a token, inject it securely via a setter method (see below).
      if (this.authToken) {
        config.headers.Authorization = `Bearer ${this.authToken}`;
      }
      return config;
    });

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('API Error:', error);
        return Promise.reject(error);
      }
    );
  }

  // Query endpoints
  async submitQuery(
    request: QueryRequest
  ): Promise<ApiResponse<QueryResponse>> {
    try {
      const response: AxiosResponse<QueryResponse> = await this.client.post(
        '/api/v1/query',
        request
      );
      return { data: response.data, success: true };
    } catch (error: any) {
      return {
        error: {
          message: error.response?.data?.message || 'Failed to submit query',
          code: error.response?.status?.toString() || 'UNKNOWN_ERROR',
          details: error.response?.data
        },
        success: false
      };
    }
  }

  async validateSql(
    sql: string,
    databaseId: string
  ): Promise<ApiResponse<ValidationResult>> {
    try {
      const response: AxiosResponse<ValidationResult> = await this.client.post(
        '/api/v1/validate',
        { sql, databaseId }
      );
      return { data: response.data, success: true };
    } catch (error: any) {
      return {
        error: {
          message: error.response?.data?.message || 'Failed to validate SQL',
          code: error.response?.status?.toString() || 'UNKNOWN_ERROR'
        },
        success: false
      };
    }
  }

  // Table endpoints
  async getTables(
    databaseId: string,
    filter?: string
  ): Promise<ApiResponse<TableSchema[]>> {
    try {
      const params = filter ? { filter } : {};
      const response: AxiosResponse<TableSchema[]> = await this.client.get(
        `/api/v1/tables/${databaseId}`,
        { params }
      );
      return { data: response.data, success: true };
    } catch (error: any) {
      return {
        error: {
          message: error.response?.data?.message || 'Failed to fetch tables',
          code: error.response?.status?.toString() || 'UNKNOWN_ERROR'
        },
        success: false
      };
    }
  }

  async getTableRecommendations(
    query: string,
    databaseId: string
  ): Promise<ApiResponse<TableRecommendation[]>> {
    try {
      const response: AxiosResponse<TableRecommendation[]> =
        await this.client.post('/api/v1/tables/recommend', {
          query,
          databaseId
        });
      return { data: response.data, success: true };
    } catch (error: any) {
      return {
        error: {
          message:
            error.response?.data?.message ||
            'Failed to get table recommendations',
          code: error.response?.status?.toString() || 'UNKNOWN_ERROR'
        },
        success: false
      };
    }
  }

  // Feedback endpoints
  async submitFeedback(
    feedback: Omit<UserFeedback, 'id' | 'createdAt'>
  ): Promise<ApiResponse<void>> {
    try {
      await this.client.post('/api/v1/feedback', feedback);
      return { success: true };
    } catch (error: any) {
      return {
        error: {
          message: error.response?.data?.message || 'Failed to submit feedback',
          code: error.response?.status?.toString() || 'UNKNOWN_ERROR'
        },
        success: false
      };
    }
  }

  // Health check
  async healthCheck(): Promise<boolean> {
    try {
      await this.client.get('/health');
      return true;
    } catch {
      return false;
    }
  }
}

export const apiService = new ApiService();
