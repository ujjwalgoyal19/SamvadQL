/**
 * API service for SamvadQL frontend
 */

import axios, { AxiosInstance, AxiosResponse } from 'axios';
import {
  QueryRequest,
  QueryResponse,
  TableListResponse,
  ValidationResult,
  UserFeedback,
  ApiResponse,
  TableRecommendation,
  BulkGrantRequest,
  BulkRevokeRequest,
  BulkPermissionResponse,
  HierarchyRequest,
  HierarchyResponse,
  PermissionHierarchy
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
      },
      withCredentials: true // Enable sending cookies for cross-origin requests
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

  async validateSql(
    sql: string,
    databaseId: string
  ): Promise<ApiResponse<ValidationResult>> {
    try {
      const response: AxiosResponse<ValidationResult> = await this.client.post(
        '/api/v1/validate',
        { sql, database_id: databaseId }
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
    options?: {
      page?: number;
      pageSize?: number;
      search?: string;
      tier?: string;
      tags?: string;
    }
  ): Promise<ApiResponse<TableListResponse>> {
    try {
      const params: Record<string, any> = {};
      if (options?.page) params.page = options.page;
      if (options?.pageSize) params.page_size = options.pageSize;
      if (options?.search) params.search = options.search;
      if (options?.tier) params.tier = options.tier;
      if (options?.tags) params.tags = options.tags;

      const response: AxiosResponse<TableListResponse> = await this.client.get(
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
    newPassword: string
  ): Promise<ApiResponse<any>> {
    try {
      const response = await this.client.post('/api/v1/auth/reset-password', {
        token,
        new_password: newPassword
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

  // Permission Management endpoints

  async grantUserPermission(
    userId: string,
    resourceType: string,
    resourceId: string,
    permission: string
  ): Promise<ApiResponse<any>> {
    try {
      const response = await this.client.post(
        `/api/v1/permissions/users/${userId}/grant`,
        { resource_type: resourceType, resource_id: resourceId, permission }
      );
      return { data: response.data, success: true };
    } catch (error: any) {
      return {
        data: undefined as any,
        success: false,
        errors: [error.response?.data?.detail || 'Failed to grant permission']
      };
    }
  }

  async revokeUserPermission(
    userId: string,
    resourceType: string,
    resourceId: string,
    permission: string
  ): Promise<ApiResponse<any>> {
    try {
      const response = await this.client.delete(
        `/api/v1/permissions/users/${userId}/revoke`,
        {
          data: {
            resource_type: resourceType,
            resource_id: resourceId,
            permission
          }
        }
      );
      return { data: response.data, success: true };
    } catch (error: any) {
      return {
        data: undefined as any,
        success: false,
        errors: [error.response?.data?.detail || 'Failed to revoke permission']
      };
    }
  }

  async getUserPermissions(userId: string): Promise<ApiResponse<any>> {
    try {
      const response = await this.client.get(
        `/api/v1/permissions/users/${userId}`
      );
      return { data: response.data, success: true };
    } catch (error: any) {
      return {
        data: undefined as any,
        success: false,
        errors: [error.response?.data?.detail || 'Failed to get permissions']
      };
    }
  }

  async checkUserPermission(
    userId: string,
    resourceType: string,
    resourceId: string,
    permission: string
  ): Promise<ApiResponse<any>> {
    try {
      const response = await this.client.post(
        `/api/v1/permissions/users/${userId}/check`,
        { resource_type: resourceType, resource_id: resourceId, permission }
      );
      return { data: response.data, success: true };
    } catch (error: any) {
      return {
        data: undefined as any,
        success: false,
        errors: [error.response?.data?.detail || 'Failed to check permission']
      };
    }
  }

  async grantRolePermission(
    roleId: string,
    resourceType: string,
    resourceId: string,
    permission: string
  ): Promise<ApiResponse<any>> {
    try {
      const response = await this.client.post(
        `/api/v1/permissions/roles/${roleId}/grant`,
        { resource_type: resourceType, resource_id: resourceId, permission }
      );
      return { data: response.data, success: true };
    } catch (error: any) {
      return {
        data: undefined as any,
        success: false,
        errors: [
          error.response?.data?.detail || 'Failed to grant role permission'
        ]
      };
    }
  }

  async revokeRolePermission(
    roleId: string,
    resourceType: string,
    resourceId: string,
    permission: string
  ): Promise<ApiResponse<any>> {
    try {
      const response = await this.client.delete(
        `/api/v1/permissions/roles/${roleId}/revoke`,
        {
          data: {
            resource_type: resourceType,
            resource_id: resourceId,
            permission
          }
        }
      );
      return { data: response.data, success: true };
    } catch (error: any) {
      return {
        data: undefined as any,
        success: false,
        errors: [
          error.response?.data?.detail || 'Failed to revoke role permission'
        ]
      };
    }
  }

  async getResourcePermissions(
    resourceType: string,
    resourceId: string
  ): Promise<ApiResponse<any>> {
    try {
      const response = await this.client.get(
        `/api/v1/permissions/resources/${resourceType}/${resourceId}`
      );
      return { data: response.data, success: true };
    } catch (error: any) {
      return {
        data: undefined as any,
        success: false,
        errors: [
          error.response?.data?.detail || 'Failed to get resource permissions'
        ]
      };
    }
  }

  // Bulk Permission Operations

  async bulkGrantPermissions(
    userId: string,
    permissions: BulkGrantRequest
  ): Promise<ApiResponse<BulkPermissionResponse>> {
    try {
      const response: AxiosResponse<BulkPermissionResponse> =
        await this.client.post(
          `/api/v1/permissions/bulk-grant?user_id=${userId}`,
          permissions
        );
      return { data: response.data, success: true };
    } catch (error: any) {
      const status = error.response?.status;
      if (status === 403) {
        return {
          data: undefined as any,
          success: false,
          errors: ["Forbidden: You don't have permission to grant permissions"]
        };
      }
      return {
        data: undefined as any,
        success: false,
        errors: [
          error.response?.data?.detail || 'Failed to bulk grant permissions'
        ]
      };
    }
  }

  async bulkRevokePermissions(
    userId: string,
    permissions: BulkRevokeRequest
  ): Promise<ApiResponse<BulkPermissionResponse>> {
    try {
      const response: AxiosResponse<BulkPermissionResponse> =
        await this.client.post(
          `/api/v1/permissions/bulk-revoke?user_id=${userId}`,
          permissions
        );
      return { data: response.data, success: true };
    } catch (error: any) {
      const status = error.response?.status;
      if (status === 403) {
        return {
          data: undefined as any,
          success: false,
          errors: ["Forbidden: You don't have permission to revoke permissions"]
        };
      }
      return {
        data: undefined as any,
        success: false,
        errors: [
          error.response?.data?.detail || 'Failed to bulk revoke permissions'
        ]
      };
    }
  }

  // Permission Hierarchy Operations

  async createPermissionHierarchy(
    hierarchy: HierarchyRequest
  ): Promise<ApiResponse<HierarchyResponse>> {
    try {
      const response: AxiosResponse<HierarchyResponse> = await this.client.post(
        `/api/v1/permissions/hierarchy`,
        hierarchy
      );
      return { data: response.data, success: true };
    } catch (error: any) {
      const status = error.response?.status;
      if (status === 403) {
        return {
          data: undefined as any,
          success: false,
          errors: ["Forbidden: You don't have permission to create hierarchies"]
        };
      }
      if (status === 400) {
        return {
          data: undefined as any,
          success: false,
          errors: [
            error.response?.data?.detail ||
              'Bad request: Invalid hierarchy configuration'
          ]
        };
      }
      return {
        data: undefined as any,
        success: false,
        errors: [
          error.response?.data?.detail ||
            'Failed to create permission hierarchy'
        ]
      };
    }
  }

  async getPermissionHierarchy(
    resourceType: string,
    resourceId: string
  ): Promise<ApiResponse<PermissionHierarchy>> {
    try {
      const response: AxiosResponse<PermissionHierarchy> =
        await this.client.get(
          `/api/v1/permissions/hierarchy/${resourceType}/${resourceId}`
        );
      return { data: response.data, success: true };
    } catch (error: any) {
      const status = error.response?.status;
      if (status === 403) {
        return {
          data: undefined as any,
          success: false,
          errors: ["Forbidden: You don't have permission to view hierarchies"]
        };
      }
      if (status === 404) {
        return {
          data: undefined as any,
          success: false,
          errors: ['Not found: No hierarchy found for this resource']
        };
      }
      return {
        data: undefined as any,
        success: false,
        errors: [
          error.response?.data?.detail || 'Failed to get permission hierarchy'
        ]
      };
    }
  }
}

export const apiService = new ApiService();
