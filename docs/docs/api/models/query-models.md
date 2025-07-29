# Query Models

## QueryRequest

Request model for SQL generation.

```python
class QueryRequest(BaseModel):
    question: str = Field(..., description="Natural language question")
    database_id: str = Field(..., description="Database identifier")
    context: Optional[QueryContext] = None
    options: Optional[QueryOptions] = None
```

## QueryResponse

Response model for generated SQL.

```python
class QueryResponse(BaseModel):
    sql: str = Field(..., description="Generated SQL query")
    explanation: str = Field(..., description="Query explanation")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score")
    tables_used: List[str] = Field(default_factory=list)
    estimated_rows: Optional[int] = None
```

## ExecutionResult

Model for query execution results.

```python
class ExecutionResult(BaseModel):
    results: List[Dict[str, Any]] = Field(default_factory=list)
    row_count: int = Field(..., description="Number of rows returned")
    execution_time: float = Field(..., description="Execution time in seconds")
    columns: List[str] = Field(default_factory=list)
    query_plan: Optional[str] = None
```
