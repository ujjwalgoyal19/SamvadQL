#!/usr/bin/env node

const fs = require('fs-extra');
const path = require('path');
const glob = require('glob');

/**
 * Generate component documentation from React frontend files
 */
class ComponentDocGenerator {
  constructor() {
    // Check if running in Docker with mounted volumes
    this.frontendPath = fs.existsSync('/source/frontend/src')
      ? '/source/frontend/src'
      : path.join(__dirname, '../../frontend/src');
    this.docsPath = path.join(__dirname, '../docs/components');
  }

  async generateDocs() {
    console.log('🚀 Generating component documentation...');

    await fs.ensureDir(this.docsPath);
    await this.generateOverview();
    await this.generateUIComponentDocs();
    await this.generateHookDocs();
    await this.generateServiceDocs();

    console.log('✅ Component documentation generated successfully!');
  }

  async generateOverview() {
    const content = `# Components Overview

SamvadQL frontend is built with React 18+ and TypeScript, using modern patterns and best practices.

## Architecture

The frontend follows a component-based architecture with clear separation of concerns:

- **UI Components**: Reusable interface elements built with shadcn/ui
- **Hooks**: Custom React hooks for state management and side effects
- **Services**: API clients and external service integrations
- **Types**: TypeScript definitions for type safety

## Design System

We use [shadcn/ui](https://ui.shadcn.com/) as our component library, built on top of:
- **Radix UI**: Accessible, unstyled components
- **Tailwind CSS**: Utility-first CSS framework
- **Lucide React**: Beautiful, customizable icons

## Component Structure

\`\`\`
src/
├── components/
│   ├── ui/              # shadcn/ui components
│   ├── query/           # Query-related components
│   ├── schema/          # Schema browser components
│   └── chat/            # Chat interface components
├── hooks/               # Custom React hooks
├── services/            # API and WebSocket clients
├── types/               # TypeScript definitions
└── lib/                 # Utility functions
\`\`\`

## Styling Conventions

- Use Tailwind CSS classes for styling
- Follow shadcn/ui patterns for component variants
- Use CSS variables for theme customization
- Responsive design with mobile-first approach

## State Management

- **Local State**: React useState and useReducer
- **Server State**: Custom hooks with React Query patterns
- **Global State**: Redux Toolkit for complex state
- **Form State**: React Hook Form with Zod validation

## Next Steps

- [UI Components](./ui/query-editor.md) - Interactive interface components
- [Hooks](./hooks/use-query.md) - Custom React hooks
- [Services](./services/api-client.md) - API and WebSocket clients
`;

    await fs.writeFile(path.join(this.docsPath, 'overview.md'), content);
  }

  async generateUIComponentDocs() {
    const uiPath = path.join(this.docsPath, 'ui');
    await fs.ensureDir(uiPath);

    // Query Editor component
    const queryEditorContent = `# QueryEditor Component

The QueryEditor is the main interface for users to input natural language questions and view generated SQL.

## Usage

\`\`\`tsx
import { QueryEditor } from '@/components/query/QueryEditor';

function App() {
  return (
    <QueryEditor
      onSubmit={handleQuerySubmit}
      onSqlChange={handleSqlChange}
      isLoading={isGenerating}
      initialValue=""
    />
  );
}
\`\`\`

## Props

| Prop | Type | Description |
|------|------|-------------|
| \`onSubmit\` | \`(question: string) => void\` | Called when user submits a question |
| \`onSqlChange\` | \`(sql: string) => void\` | Called when generated SQL changes |
| \`isLoading\` | \`boolean\` | Shows loading state during generation |
| \`initialValue\` | \`string\` | Initial question text |
| \`placeholder\` | \`string\` | Placeholder text for input |
| \`disabled\` | \`boolean\` | Disables the editor |

## Features

- **Syntax Highlighting**: SQL syntax highlighting in the output
- **Auto-resize**: Text area automatically resizes with content
- **Keyboard Shortcuts**: Ctrl+Enter to submit, Escape to clear
- **Streaming Support**: Real-time display of generated SQL
- **Error Handling**: Displays validation errors and suggestions

## Example

\`\`\`tsx
function QueryPage() {
  const [question, setQuestion] = useState('');
  const [sql, setSql] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (question: string) => {
    setIsLoading(true);
    try {
      const result = await generateSQL(question);
      setSql(result.sql);
    } catch (error) {
      console.error('Failed to generate SQL:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <QueryEditor
        onSubmit={handleSubmit}
        onSqlChange={setSql}
        isLoading={isLoading}
        placeholder="Ask a question about your data..."
      />
      {sql && (
        <div className="bg-gray-50 p-4 rounded-lg">
          <pre className="text-sm">{sql}</pre>
        </div>
      )}
    </div>
  );
}
\`\`\`

## Styling

The component uses Tailwind CSS classes and can be customized:

\`\`\`css
.query-editor {
  @apply border rounded-lg p-4 focus-within:ring-2 focus-within:ring-blue-500;
}

.query-editor textarea {
  @apply w-full resize-none border-none outline-none;
}

.query-editor .sql-output {
  @apply bg-gray-50 border-t p-4 font-mono text-sm;
}
\`\`\`
`;

    await fs.writeFile(path.join(uiPath, 'query-editor.md'), queryEditorContent);

    // Result Viewer component
    const resultViewerContent = `# ResultViewer Component

The ResultViewer displays query execution results in a tabular format with pagination and export options.

## Usage

\`\`\`tsx
import { ResultViewer } from '@/components/query/ResultViewer';

function QueryResults() {
  return (
    <ResultViewer
      data={queryResults}
      columns={columnDefinitions}
      isLoading={isExecuting}
      onExport={handleExport}
    />
  );
}
\`\`\`

## Props

| Prop | Type | Description |
|------|------|-------------|
| \`data\` | \`Array<Record<string, any>>\` | Query result data |
| \`columns\` | \`ColumnDefinition[]\` | Column definitions |
| \`isLoading\` | \`boolean\` | Shows loading state |
| \`onExport\` | \`(format: string) => void\` | Export handler |
| \`pageSize\` | \`number\` | Rows per page (default: 50) |
| \`maxHeight\` | \`string\` | Maximum table height |

## Features

- **Virtual Scrolling**: Efficient rendering of large datasets
- **Column Sorting**: Click column headers to sort
- **Pagination**: Navigate through large result sets
- **Export Options**: CSV, JSON, Excel export
- **Column Resizing**: Drag column borders to resize
- **Cell Formatting**: Automatic formatting based on data type

## Column Definition

\`\`\`tsx
interface ColumnDefinition {
  key: string;
  title: string;
  type: 'string' | 'number' | 'date' | 'boolean';
  width?: number;
  sortable?: boolean;
  formatter?: (value: any) => string;
}
\`\`\`

## Example

\`\`\`tsx
function QueryResultsPage() {
  const columns: ColumnDefinition[] = [
    { key: 'id', title: 'ID', type: 'number', width: 80 },
    { key: 'name', title: 'Name', type: 'string', width: 200 },
    { key: 'email', title: 'Email', type: 'string', width: 250 },
    {
      key: 'created_at',
      title: 'Created',
      type: 'date',
      width: 150,
      formatter: (value) => new Date(value).toLocaleDateString()
    }
  ];

  const handleExport = (format: string) => {
    switch (format) {
      case 'csv':
        exportToCSV(data);
        break;
      case 'json':
        exportToJSON(data);
        break;
      case 'excel':
        exportToExcel(data);
        break;
    }
  };

  return (
    <ResultViewer
      data={queryResults}
      columns={columns}
      isLoading={isExecuting}
      onExport={handleExport}
      pageSize={100}
      maxHeight="600px"
    />
  );
}
\`\`\`
`;

    await fs.writeFile(path.join(uiPath, 'result-viewer.md'), resultViewerContent);
  }

  async generateHookDocs() {
    const hooksPath = path.join(this.docsPath, 'hooks');
    await fs.ensureDir(hooksPath);

    const useQueryContent = `# useQuery Hook

Custom hook for managing SQL query generation and execution.

## Usage

\`\`\`tsx
import { useQuery } from '@/hooks/useQuery';

function QueryComponent() {
  const {
    question,
    setQuestion,
    sql,
    results,
    isGenerating,
    isExecuting,
    error,
    generateSQL,
    executeSQL,
    reset
  } = useQuery();

  return (
    <div>
      <input
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="Ask a question..."
      />
      <button onClick={generateSQL} disabled={isGenerating}>
        Generate SQL
      </button>
      {sql && (
        <button onClick={executeSQL} disabled={isExecuting}>
          Execute Query
        </button>
      )}
    </div>
  );
}
\`\`\`

## Return Value

| Property | Type | Description |
|----------|------|-------------|
| \`question\` | \`string\` | Current natural language question |
| \`setQuestion\` | \`(q: string) => void\` | Update the question |
| \`sql\` | \`string\` | Generated SQL query |
| \`results\` | \`QueryResult\` | Execution results |
| \`isGenerating\` | \`boolean\` | SQL generation in progress |
| \`isExecuting\` | \`boolean\` | Query execution in progress |
| \`error\` | \`Error \\| null\` | Current error state |
| \`generateSQL\` | \`() => Promise<void>\` | Generate SQL from question |
| \`executeSQL\` | \`() => Promise<void>\` | Execute the generated SQL |
| \`reset\` | \`() => void\` | Reset all state |

## Options

\`\`\`tsx
const query = useQuery({
  databaseId: 'my-database',
  autoExecute: false,
  streaming: true,
  onSuccess: (results) => console.log('Query succeeded:', results),
  onError: (error) => console.error('Query failed:', error)
});
\`\`\`

## Streaming Support

When \`streaming: true\` is enabled, the hook provides real-time updates:

\`\`\`tsx
const { sql, isGenerating, streamingChunk } = useQuery({
  streaming: true
});

// SQL is updated in real-time as it's generated
useEffect(() => {
  if (streamingChunk) {
    console.log('New chunk:', streamingChunk.content);
  }
}, [streamingChunk]);
\`\`\`

## Error Handling

The hook provides comprehensive error handling:

\`\`\`tsx
const { error, generateSQL } = useQuery();

useEffect(() => {
  if (error) {
    if (error.type === 'VALIDATION_ERROR') {
      // Handle validation errors
      showValidationError(error.message);
    } else if (error.type === 'NETWORK_ERROR') {
      // Handle network errors
      showNetworkError();
    }
  }
}, [error]);
\`\`\`
`;

    await fs.writeFile(path.join(hooksPath, 'use-query.md'), useQueryContent);
  }

  async generateServiceDocs() {
    const servicesPath = path.join(this.docsPath, 'services');
    await fs.ensureDir(servicesPath);

    const apiClientContent = `# API Client Service

The API client handles all HTTP requests to the SamvadQL backend.

## Usage

\`\`\`tsx
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
\`\`\`

## Methods

### Authentication

\`\`\`tsx
// Login
const auth = await apiClient.login({
  username: 'user@example.com',
  password: 'password'
});

// Refresh token
const newAuth = await apiClient.refreshToken();

// Logout
await apiClient.logout();
\`\`\`

### Query Operations

\`\`\`tsx
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
\`\`\`

### Schema Operations

\`\`\`tsx
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
\`\`\`

## Configuration

\`\`\`tsx
import { createAPIClient } from '@/services/apiClient';

const apiClient = createAPIClient({
  baseURL: 'http://localhost:8000/api/v1',
  timeout: 30000,
  retries: 3,
  onError: (error) => {
    console.error('API Error:', error);
  }
});
\`\`\`

## Error Handling

The API client provides structured error handling:

\`\`\`tsx
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
\`\`\`

## Request/Response Types

\`\`\`tsx
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
\`\`\`
`;

    await fs.writeFile(path.join(servicesPath, 'api-client.md'), apiClientContent);
  }
}

// Run the generator
if (require.main === module) {
  const generator = new ComponentDocGenerator();
  generator.generateDocs().catch(console.error);
}

module.exports = ComponentDocGenerator;