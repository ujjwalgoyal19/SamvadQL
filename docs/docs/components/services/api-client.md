# API Client Service

The API client handles all HTTP requests to the SamvadQL backend.

## Usage

```tsx
import { apiClient } from '@/services/apiClient';

// Generate SQL
const result = await apiClient.generateSQL({
  question: 'Show me all users',
  databaseId: 'my-db'
});

// Execute query
const execution = await apiClient.executeQuery({
  sql: result.sql,
  databaseId: 'my-db'
});
```

## Methods

### Authentication

```tsx
// Login
const auth = await apiClient.login({
  username: 'user@example.com',
  password: 'password'
});

// Refresh token
const newAuth = await apiClient.refreshToken();

// Logout
await apiClient.logout();
```

### Query Operations

```tsx
// Generate SQL from natural language
const generation = await apiClient.generateSQL({
  question: string,
  databaseId: string,
  context?: QueryContext
});

// Execute SQL query
const execution = await apiClient.executeQuery({
  sql: string,
  databaseId: string,
  dryRun?: boolean
});

// Get query history
const history = await apiClient.getQueryHistory({
  limit?: number,
  offset?: number
});
```

### Schema Operations

```tsx
// Get database schema
const schema = await apiClient.getSchema(databaseId);

// Search tables and columns
const searchResults = await apiClient.searchSchema({
  query: string,
  databaseId: string
});

// Get table details
const tableInfo = await apiClient.getTableInfo({
  databaseId: string,
  tableName: string
});
```

## Configuration

```tsx
import { createAPIClient } from '@/services/apiClient';

const apiClient = createAPIClient({
  baseURL: 'http://localhost:8000/api/v1',
  timeout: 30000,
  retries: 3,
  onError: (error) => {
    console.error('API Error:', error);
  }
});
```

## Error Handling

The API client provides structured error handling:

```tsx
try {
  const result = await apiClient.generateSQL(request);
} catch (error) {
  if (error.status === 401) {
    // Handle authentication error
    redirectToLogin();
  } else if (error.status === 429) {
    // Handle rate limiting
    showRateLimitError();
  } else {
    // Handle other errors
    showGenericError(error.message);
  }
}
```

## Request/Response Types

```tsx
interface GenerateSQLRequest {
  question: string;
  databaseId: string;
  context?: {
    tables?: string[];
    previousQueries?: string[];
  };
}

interface GenerateSQLResponse {
  sql: string;
  explanation: string;
  confidence: number;
  tablesUsed: string[];
  estimatedRows?: number;
}

interface ExecuteQueryRequest {
  sql: string;
  databaseId: string;
  dryRun?: boolean;
  limit?: number;
}

interface ExecuteQueryResponse {
  results: Array<Record<string, any>>;
  rowCount: number;
  executionTime: number;
  columns: string[];
  queryPlan?: string;
}
```
