/**
 * TypeScript interfaces for API requests and responses
 */

// Enums
export enum DatabaseType {
  POSTGRESQL = 'postgresql',
  MYSQL = 'mysql',
  SNOWFLAKE = 'snowflake',
  BIGQUERY = 'bigquery'
}

export enum ValidationStatus {
  VALID = 'valid',
  INVALID = 'invalid',
  WARNING = 'warning',
  UNSAFE = 'unsafe'
}

// Core data interfaces
export interface ColumnSchema {
  name: string;
  data_type: string;
  description?: string;
  sample_values: any[];
  is_nullable: boolean;
  is_primary_key: boolean;
  is_foreign_key: boolean;
}

export interface TableSchema {
  name: string;
  database_id: string;
  columns: ColumnSchema[];
  description?: string;
  sample_queries: string[];
  tier?: string;
  tags: string[];
  row_count?: number;
  created_at?: string;
  updated_at?: string;
}

export interface QueryRequest {
  query: string;
  user_id: string;
  database_id: string;
  selected_tables?: string[];
  context?: Record<string, any>;
  session_id?: string;
  request_id: string;
}

export interface ValidationResult {
  is_valid: boolean;
  errors: string[];
  warnings: string[];
  is_destructive: boolean;
  estimated_cost?: number;
  execution_plan?: string;
}

export interface OptimizationSuggestion {
  type: string;
  description: string;
  impact: 'high' | 'medium' | 'low';
  suggested_sql?: string;
}

export interface QueryResponse {
  sql: string;
  explanation: string;
  confidence_score: number;
  selected_tables: string[];
  validation_status: ValidationStatus;
  optimization_suggestions: OptimizationSuggestion[];
  execution_time_estimate?: number;
  request_id?: string;
  generated_at: string;
}

export interface TableRecommendation {
  table_schema: TableSchema;
  relevance_score: number;
  match_reason: string;
  summary?: string;
}

export interface QueryContext {
  user_id: string;
  session_id: string;
  database_type: DatabaseType;
  previous_queries: string[];
  user_preferences: Record<string, any>;
}

export interface UserFeedback {
  id: string;
  user_id: string;
  query_id: string;
  original_query: string;
  generated_sql: string;
  feedback_type: 'accept' | 'reject' | 'modify';
  comments?: string;
  rating?: number;
  created_at: string;
}

export interface AuditLogEntry {
  id: string;
  user_id: string;
  action: string;
  resource_type: string;
  resource_id?: string;
  details: Record<string, any>;
  ip_address?: string;
  user_agent?: string;
  created_at: string;
}

// API Response wrappers
export interface ApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
  errors?: string[];
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  per_page: number;
  has_next: boolean;
  has_prev: boolean;
}

// API Endpoints
export interface HealthResponse {
  status: 'healthy' | 'unhealthy';
  service: string;
  timestamp: string;
}

export interface StatusResponse {
  status: 'running' | 'stopped';
  version: string;
  environment: 'development' | 'production';
}

export interface TablesResponse {
  tables: TableSchema[];
  total: number;
}

export interface ValidateRequest {
  sql: string;
  database_id: string;
}

export interface FeedbackRequest {
  query_id: string;
  feedback_type: 'accept' | 'reject' | 'modify';
  comments?: string;
  rating?: number;
}

// Error types
export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, any>;
}

export interface ValidationError {
  field: string;
  message: string;
  code: string;
}

// Utility types for form handling
export type QueryFormData = Omit<QueryRequest, 'request_id' | 'user_id'>;
export type FeedbackFormData = Omit<FeedbackRequest, 'query_id'>;
export type TableFilters = {
  search?: string;
  tier?: string;
  tags?: string[];
  database_id?: string;
};

// WebSocket message types (will be used in websocket.ts)
export interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
  request_id?: string;
}

export interface QueryStreamMessage extends WebSocketMessage {
  type: 'query_stream';
  data: {
    chunk: string;
    is_complete: boolean;
    response?: QueryResponse;
  };
}

export interface ErrorMessage extends WebSocketMessage {
  type: 'error';
  data: {
    error: ApiError;
  };
}

export interface StatusMessage extends WebSocketMessage {
  type: 'status';
  data: {
    status: string;
    message: string;
  };
}
