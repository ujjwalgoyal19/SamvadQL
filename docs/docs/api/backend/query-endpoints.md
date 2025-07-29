# Query API Endpoints

## POST /query/generate

Generate SQL from natural language.

### Request Body

```json
{
  "question": "Show me all users who signed up last month",
  "database_id": "string",
  "context": {
    "tables": ["users", "signups"],
    "previous_queries": []
  }
}
```

### Response

```json
{
  "success": true,
  "data": {
    "sql": "SELECT * FROM users WHERE created_at >= '2024-01-01'",
    "explanation": "This query retrieves all users...",
    "confidence": 0.95,
    "tables_used": ["users"]
  }
}
```

## POST /query/execute

Execute generated SQL query.

### Request Body

```json
{
  "sql": "SELECT * FROM users LIMIT 10",
  "database_id": "string",
  "dry_run": false
}
```

### Response

```json
{
  "success": true,
  "data": {
    "results": [
      {"id": 1, "name": "John Doe", "email": "john@example.com"}
    ],
    "row_count": 1,
    "execution_time": 0.045,
    "columns": ["id", "name", "email"]
  }
}
```

## GET /query/history

Get query history for user.

### Query Parameters

- `limit`: Number of queries to return (default: 50)
- `offset`: Pagination offset (default: 0)

### Response

```json
{
  "success": true,
  "data": {
    "queries": [
      {
        "id": "uuid",
        "question": "Show me all users",
        "sql": "SELECT * FROM users",
        "created_at": "2024-01-01T00:00:00Z"
      }
    ],
    "total": 100
  }
}
```
