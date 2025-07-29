# LLM Service

The LLM Service handles natural language to SQL conversion using various language models.

## Configuration

```python
class LLMConfig:
    provider: str = "openai"  # openai, anthropic, local
    model: str = "gpt-4"
    temperature: float = 0.1
    max_tokens: int = 2000
```

## Methods

### generate_sql()

Generate SQL from natural language question.

```python
async def generate_sql(
    question: str,
    schema_context: SchemaContext,
    options: Optional[GenerationOptions] = None
) -> SQLGeneration:
    """
    Generate SQL query from natural language.

    Args:
        question: Natural language question
        schema_context: Database schema information
        options: Generation options and constraints

    Returns:
        SQLGeneration object with query and metadata
    """
```

### explain_query()

Provide explanation for generated SQL.

```python
async def explain_query(
    sql: str,
    context: Optional[str] = None
) -> QueryExplanation:
    """
    Generate human-readable explanation of SQL query.

    Args:
        sql: SQL query to explain
        context: Additional context for explanation

    Returns:
        QueryExplanation with detailed breakdown
    """
```

## Streaming Support

The LLM service supports streaming responses for real-time query generation:

```python
async def generate_sql_stream(
    question: str,
    schema_context: SchemaContext
) -> AsyncGenerator[SQLGenerationChunk, None]:
    """Stream SQL generation in real-time."""
    async for chunk in self.llm_client.stream_completion(...):
        yield SQLGenerationChunk(
            content=chunk.content,
            is_complete=chunk.is_complete,
            metadata=chunk.metadata
        )
```
