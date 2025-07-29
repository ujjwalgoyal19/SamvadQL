# QueryEditor Component

The QueryEditor is the main interface for users to input natural language questions and view generated SQL.

## Usage

```tsx
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
```

## Props

| Prop | Type | Description |
|------|------|-------------|
| `onSubmit` | `(question: string) => void` | Called when user submits a question |
| `onSqlChange` | `(sql: string) => void` | Called when generated SQL changes |
| `isLoading` | `boolean` | Shows loading state during generation |
| `initialValue` | `string` | Initial question text |
| `placeholder` | `string` | Placeholder text for input |
| `disabled` | `boolean` | Disables the editor |

## Features

- **Syntax Highlighting**: SQL syntax highlighting in the output
- **Auto-resize**: Text area automatically resizes with content
- **Keyboard Shortcuts**: Ctrl+Enter to submit, Escape to clear
- **Streaming Support**: Real-time display of generated SQL
- **Error Handling**: Displays validation errors and suggestions

## Example

```tsx
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
```

## Styling

The component uses Tailwind CSS classes and can be customized:

```css
.query-editor {
  @apply border rounded-lg p-4 focus-within:ring-2 focus-within:ring-blue-500;
}

.query-editor textarea {
  @apply w-full resize-none border-none outline-none;
}

.query-editor .sql-output {
  @apply bg-gray-50 border-t p-4 font-mono text-sm;
}
```
