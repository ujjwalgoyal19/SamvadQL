# ResultViewer Component

The ResultViewer displays query execution results in a tabular format with pagination and export options.

## Usage

```tsx
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
```

## Props

| Prop | Type | Description |
|------|------|-------------|
| `data` | `Array<Record<string, any>>` | Query result data |
| `columns` | `ColumnDefinition[]` | Column definitions |
| `isLoading` | `boolean` | Shows loading state |
| `onExport` | `(format: string) => void` | Export handler |
| `pageSize` | `number` | Rows per page (default: 50) |
| `maxHeight` | `string` | Maximum table height |

## Features

- **Virtual Scrolling**: Efficient rendering of large datasets
- **Column Sorting**: Click column headers to sort
- **Pagination**: Navigate through large result sets
- **Export Options**: CSV, JSON, Excel export
- **Column Resizing**: Drag column borders to resize
- **Cell Formatting**: Automatic formatting based on data type

## Column Definition

```tsx
interface ColumnDefinition {
  key: string;
  title: string;
  type: 'string' | 'number' | 'date' | 'boolean';
  width?: number;
  sortable?: boolean;
  formatter?: (value: any) => string;
}
```

## Example

```tsx
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
```
