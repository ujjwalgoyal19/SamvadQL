# useQuery Hook

Custom hook for managing SQL query generation and execution.

## Usage

```tsx
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
```

## Return Value

| Property | Type | Description |
|----------|------|-------------|
| `question` | `string` | Current natural language question |
| `setQuestion` | `(q: string) => void` | Update the question |
| `sql` | `string` | Generated SQL query |
| `results` | `QueryResult` | Execution results |
| `isGenerating` | `boolean` | SQL generation in progress |
| `isExecuting` | `boolean` | Query execution in progress |
| `error` | `Error \| null` | Current error state |
| `generateSQL` | `() => Promise<void>` | Generate SQL from question |
| `executeSQL` | `() => Promise<void>` | Execute the generated SQL |
| `reset` | `() => void` | Reset all state |

## Options

```tsx
const query = useQuery({
  databaseId: 'my-database',
  autoExecute: false,
  streaming: true,
  onSuccess: (results) => console.log('Query succeeded:', results),
  onError: (error) => console.error('Query failed:', error)
});
```

## Streaming Support

When `streaming: true` is enabled, the hook provides real-time updates:

```tsx
const { sql, isGenerating, streamingChunk } = useQuery({
  streaming: true
});

// SQL is updated in real-time as it's generated
useEffect(() => {
  if (streamingChunk) {
    console.log('New chunk:', streamingChunk.content);
  }
}, [streamingChunk]);
```

## Error Handling

The hook provides comprehensive error handling:

```tsx
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
```
