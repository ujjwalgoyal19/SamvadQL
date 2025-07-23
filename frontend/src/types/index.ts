/**
 * TypeScript interfaces for SamvadQL frontend
 */

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

export enum FeedbackType {
  ACCEPT = 'accept',
  REJECT = 'reject',
  MODIFY = 'modify'
}

export interface ColumnSchema {
  name: string;
  dataType: string;
  description?: string;
  sampleValues: any[];
  isNullable: boolean;
  isPrimaryKey: boolean;
  isForeignKey: boolean;
}

export interface TableSchema {
  name: string;
  databaseId: string;
  columns: ColumnSchema[];
  description?: string;
  sampleQueries: string[];
  tier?: string;
  tags: string[];
  rowCount?: number;
  createdAt?: string;
  updatedAt?: string;
}

export interface QueryRequest {
  query: string;
  userId: string;
  databaseId: string;
  selectedTables?: string[];
  context?: Record<string, any>;
  sessionId?: string;
  requestId: string;
}

export interface ValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
  isDestructive: boolean;
  estimatedCost?: number;
  executionPlan?: string;
}

export interface OptimizationSuggestion {
  type: string;
  description: string;
  impact: 'high' | 'medium' | 'low';
  suggestedSql?: string;
}

export interface QueryResponse {
  sql: string;
  explanation: string;
  confidenceScore: number;
  selectedTables: string[];
  validationStatus: ValidationStatus;
  optimizationSuggestions: OptimizationSuggestion[];
  executionTimeEstimate?: number;
  requestId?: string;
  generatedAt: string;
}

export interface TableRecommendation {
  tableSchema: TableSchema;
  relevanceScore: number;
  matchReason: string;
  summary?: string;
}

export interface QueryContext {
  userId: string;
  sessionId: string;
  databaseType: DatabaseType;
  previousQueries: string[];
  userPreferences: Record<string, any>;
}

export interface UserFeedback {
  id: string;
  userId: string;
  queryId: string;
  originalQuery: string;
  generatedSql: string;
  feedbackType: FeedbackType;
  comments?: string;
  rating?: number;
  createdAt: string;
}

export interface StreamingMessage {
  type: 'query_progress' | 'query_complete' | 'error' | 'table_suggestions';
  data: any;
  requestId: string;
  timestamp: string;
}

export interface ApiError {
  message: string;
  code: string;
  details?: Record<string, any>;
}

export interface ApiResponse<T> {
  data?: T;
  error?: ApiError;
  success: boolean;
}

// WebSocket message types
export interface WebSocketMessage {
  type: string;
  payload: any;
  requestId?: string;
}

// UI State interfaces
export interface QueryState {
  isLoading: boolean;
  currentQuery: string;
  currentResponse?: QueryResponse;
  streamingContent: string;
  error?: string;
  selectedTables: string[];
  tableRecommendations: TableRecommendation[];
}

export interface DatabaseState {
  connectedDatabases: DatabaseConnection[];
  currentDatabase?: string;
  availableTables: TableSchema[];
  isLoadingTables: boolean;
}

export interface DatabaseConnection {
  id: string;
  name: string;
  type: DatabaseType;
  isConnected: boolean;
  lastConnected?: string;
}

export interface UserSession {
  userId: string;
  sessionId: string;
  isAuthenticated: boolean;
  preferences: UserPreferences;
}

export interface UserPreferences {
  theme: 'light' | 'dark';
  defaultDatabase?: string;
  queryHistory: QueryHistoryItem[];
  favoriteQueries: string[];
}

export interface QueryHistoryItem {
  id: string;
  query: string;
  sql: string;
  timestamp: string;
  databaseId: string;
  success: boolean;
}
