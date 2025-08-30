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
    baseURL: string = import.meta.env.VITE_API_URL || 'http://localhost:8000'
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
        data: undefined as any,
        success: false,
        errors: [error.response?.data?.message || 'Failed to submit query']
      };
    }
  }

  // Auth endpoints

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
        data: undefined as any,
        success: false,
        errors: [error.response?.data?.message || 'Failed to validate SQL']
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
        data: undefined as any,
        success: false,
        errors: [error.response?.data?.message || 'Failed to fetch tables']
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
        data: undefined as any,
        success: false,
        errors: [
          error.response?.data?.message || 'Failed to get table recommendations'
        ]
      };
    }
  }

  // Feedback endpoints
  async submitFeedback(
    feedback: Omit<UserFeedback, 'id' | 'createdAt'>
  ): Promise<ApiResponse<void>> {
    try {
      await this.client.post('/api/v1/feedback', feedback);
      return { data: undefined as any, success: true };
    } catch (error: any) {
      return {
        data: undefined as any,
        success: false,
        errors: [error.response?.data?.message || 'Failed to submit feedback']
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

  // Auth endpoints
  async login(username: string, password: string): Promise<ApiResponse<any>> {
    try {
      const response = await this.client.post('/api/v1/auth/login', {
        username,
        password
      });
      if (response.data?.access_token) {
        this.setAuthToken(response.data.access_token);
      }
      return { data: response.data, success: true };
    } catch (error: any) {
      return {
        data: undefined as any,
        success: false,
        errors: [error.response?.data?.detail || 'Login failed']
      };
    }
  }

  async signup(data: {
    username: string;
    email: string;
    password: string;
    full_name?: string;
  }): Promise<ApiResponse<any>> {
    try {
      const response = await this.client.post('/api/v1/auth/signup', data);
      if (response.data?.access_token) {
        this.setAuthToken(response.data.access_token);
      }
      return { data: response.data, success: true };
    } catch (error: any) {
      return {
        data: undefined as any,
        success: false,
        errors: [error.response?.data?.detail || 'Signup failed']
      };
    }
  }

  async forgotPassword(email: string): Promise<ApiResponse<any>> {
    try {
      const response = await this.client.post('/api/v1/auth/forgot-password', {
        email
      });
      return { data: response.data, success: true };
    } catch (error: any) {
      return {
        data: undefined as any,
        success: false,
        errors: [
          error.response?.data?.detail || 'Failed to initiate password reset'
        ]
      };
    }
  }

  async resetPassword(
    token: string,
    new_password: string
  ): Promise<ApiResponse<any>> {
    try {
      const response = await this.client.post('/api/v1/auth/reset-password', {
        token,
        new_password
      });
      return { data: response.data, success: true };
    } catch (error: any) {
      return {
        data: undefined as any,
        success: false,
        errors: [error.response?.data?.detail || 'Failed to reset password']
      };
    }
  }
}

export const apiService = new ApiService();
