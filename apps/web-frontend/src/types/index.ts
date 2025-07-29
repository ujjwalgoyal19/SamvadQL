/**
 * Main types export file for the frontend application
 */

// Re-export all API types
export * from './api';

// Re-export WebSocket types
export * from './websocket';

// Additional frontend-specific types
export interface AppConfig {
  apiBaseUrl: string;
  wsBaseUrl: string;
  environment: 'development' | 'production' | 'test';
  version: string;
  features: {
    realTimeStreaming: boolean;
    offlineMode: boolean;
    analytics: boolean;
    feedback: boolean;
  };
}

export interface User {
  id: string;
  username: string;
  email?: string;
  preferences: UserPreferences;
  permissions: string[];
  created_at: string;
  last_active: string;
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'auto';
  language: string;
  timezone: string;
  defaultDatabase?: string;
  queryHistory: boolean;
  notifications: {
    email: boolean;
    push: boolean;
    inApp: boolean;
  };
  ui: {
    showLineNumbers: boolean;
    autoComplete: boolean;
    syntaxHighlighting: boolean;
    wordWrap: boolean;
  };
}

export interface Session {
  id: string;
  user_id: string;
  created_at: string;
  expires_at: string;
  last_active: string;
  ip_address?: string;
  user_agent?: string;
}

// UI State types
export interface QueryEditorState {
  query: string;
  selectedTables: string[];
  isLoading: boolean;
  isStreaming: boolean;
  currentResponse?: QueryResponse;
  history: QueryHistoryItem[];
  suggestions: string[];
}

export interface QueryHistoryItem {
  id: string;
  query: string;
  sql: string;
  timestamp: string;
  success: boolean;
  execution_time?: number;
}

export interface TableExplorerState {
  selectedDatabase?: string;
  tables: TableSchema[];
  filteredTables: TableSchema[];
  searchQuery: string;
  selectedTier?: string;
  selectedTags: string[];
  isLoading: boolean;
  error?: string;
}

export interface NotificationState {
  notifications: Notification[];
  unreadCount: number;
}

export interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  actions?: NotificationAction[];
}

export interface NotificationAction {
  label: string;
  action: () => void;
  style?: 'primary' | 'secondary' | 'danger';
}

// Form types
export interface QueryForm {
  query: string;
  database_id: string;
  selected_tables: string[];
  context?: Record<string, any>;
}

export interface FeedbackForm {
  feedback_type: 'accept' | 'reject' | 'modify';
  rating?: number;
  comments?: string;
}

export interface TableFilterForm {
  search: string;
  tier?: string;
  tags: string[];
  database_id?: string;
}

// Component prop types
export interface QueryEditorProps {
  initialQuery?: string;
  onQuerySubmit: (query: QueryForm) => void;
  onQueryChange?: (query: string) => void;
  isLoading?: boolean;
  disabled?: boolean;
}

export interface TableSelectorProps {
  tables: TableSchema[];
  selectedTables: string[];
  onSelectionChange: (tables: string[]) => void;
  maxSelections?: number;
  disabled?: boolean;
}

export interface ResultsViewerProps {
  response?: QueryResponse;
  isStreaming?: boolean;
  onFeedback?: (feedback: FeedbackForm) => void;
  onRefine?: (refinement: string) => void;
}

// Error types
export interface AppError {
  code: string;
  message: string;
  details?: any;
  timestamp: string;
  context?: {
    component?: string;
    action?: string;
    userId?: string;
  };
}

// Loading states
export type LoadingState = 'idle' | 'loading' | 'success' | 'error';

export interface AsyncState<T> {
  data?: T;
  loading: LoadingState;
  error?: AppError;
  lastUpdated?: string;
}

// Route types
export interface RouteParams {
  [key: string]: string | undefined;
}

export interface NavigationItem {
  id: string;
  label: string;
  path: string;
  icon?: string;
  badge?: string | number;
  children?: NavigationItem[];
  permissions?: string[];
}

// Theme types
export interface Theme {
  name: string;
  colors: {
    primary: string;
    secondary: string;
    success: string;
    warning: string;
    error: string;
    info: string;
    background: string;
    surface: string;
    text: {
      primary: string;
      secondary: string;
      disabled: string;
    };
  };
  typography: {
    fontFamily: string;
    fontSize: {
      xs: string;
      sm: string;
      md: string;
      lg: string;
      xl: string;
    };
  };
  spacing: {
    xs: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
  };
}

// Analytics types
export interface AnalyticsEvent {
  name: string;
  properties?: Record<string, any>;
  timestamp: string;
  user_id?: string;
  session_id?: string;
}

export interface PerformanceMetrics {
  queryExecutionTime: number;
  renderTime: number;
  networkLatency: number;
  memoryUsage?: number;
}

// Utility types
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;

export type RequiredFields<T, K extends keyof T> = T & Required<Pick<T, K>>;
