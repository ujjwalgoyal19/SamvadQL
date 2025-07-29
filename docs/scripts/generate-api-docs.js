#!/usr/bin/env node

const fs = require('fs-extra');
const path = require('path');
const glob = require('glob');

/**
 * Generate API documentation from Python backend files
 */
class APIDocGenerator {
  constructor() {
    // Check if running in Docker with mounted volumes
    this.backendPath = fs.existsSync('/source/backend')
      ? '/source/backend'
      : path.join(__dirname, '../../backend');
    this.docsPath = path.join(__dirname, '../docs/api');
    this.outputPath = path.join(this.docsPath);
  }

  async generateDocs() {
    console.log('🚀 Generating API documentation...');

    await fs.ensureDir(this.outputPath);
    await this.generateOverview();
    await this.generateBackendDocs();
    await this.generateModelDocs();
    await this.generateServiceDocs();

    console.log('✅ API documentation generated successfully!');
  }

  async generateOverview() {
    const content = `---
title: "API Introduction"
description: "SamvadQL REST API and WebSocket interface for text-to-SQL conversion"
---

## Base URL

\`\`\`
http://localhost:8000/api/v1
\`\`\`

## Authentication

All API endpoints require authentication using JWT tokens. Include the token in the Authorization header:

\`\`\`bash
Authorization: Bearer <your-jwt-token>
\`\`\`

## Response Format

All API responses follow a consistent format:

\`\`\`json
{
  "success": true,
  "data": {},
  "message": "Success message",
  "timestamp": "2024-01-01T00:00:00Z"
}
\`\`\`

## Error Handling

<Tabs>
  <Tab title="Error Response">
    \`\`\`json
    {
      "success": false,
      "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid input parameters",
        "details": {}
      },
      "timestamp": "2024-01-01T00:00:00Z"
    }
    \`\`\`
  </Tab>
  <Tab title="Common Error Codes">
    | Code | Description |
    |------|-------------|
    | \`VALIDATION_ERROR\` | Invalid input parameters |
    | \`AUTHENTICATION_ERROR\` | Invalid or missing token |
    | \`RATE_LIMIT_ERROR\` | Too many requests |
    | \`DATABASE_ERROR\` | Database connection issue |
    | \`LLM_ERROR\` | Language model service error |
  </Tab>
</Tabs>

## Rate Limiting

<Info>
API endpoints are rate-limited to prevent abuse:
- **Authenticated users**: 100 requests per minute
- **Unauthenticated requests**: 10 requests per minute
</Info>

## WebSocket Connection

Real-time features use WebSocket connections:

\`\`\`javascript
const socket = io('ws://localhost:8000/ws');

socket.on('connect', () => {
  console.log('Connected to SamvadQL');
});

socket.on('sql_generation', (data) => {
  console.log('SQL chunk received:', data);
});
\`\`\`

## Next Steps

<CardGroup cols={2}>
  <Card title="Authentication" icon="key" href="/api-reference/authentication">
    Learn how to authenticate with the API
  </Card>
  <Card title="Query Endpoints" icon="search" href="/api-reference/query/generate">
    Generate and execute SQL queries
  </Card>
</CardGroup>
`;

    await fs.writeFile(path.join(this.outputPath, 'introduction.mdx'), content);
  }

  async generateBackendDocs() {
    const backendDocsPath = path.join(this.outputPath, 'backend');
    await fs.ensureDir(backendDocsPath);

    // Generate authentication docs
    const authContent = `---
title: "Authentication"
api: "POST /auth/login"
description: "Authenticate users and manage JWT tokens"
---

## Login

<api method="POST" url="/auth/login">
  Authenticate user and receive JWT token.
</api>

### Request Body

<ParamField body="username" type="string" required>
  User's email address or username
</ParamField>

<ParamField body="password" type="string" required>
  User's password
</ParamField>

### Response

<ResponseField name="success" type="boolean">
  Indicates if the request was successful
</ResponseField>

<ResponseField name="data" type="object">
  <Expandable title="data">
    <ResponseField name="access_token" type="string">
      JWT access token for API authentication
    </ResponseField>
    <ResponseField name="token_type" type="string">
      Token type (always "bearer")
    </ResponseField>
    <ResponseField name="expires_in" type="number">
      Token expiration time in seconds
    </ResponseField>
  </Expandable>
</ResponseField>

<RequestExample>
\`\`\`bash cURL
curl -X POST "http://localhost:8000/api/v1/auth/login" \\
  -H "Content-Type: application/json" \\
  -d '{
    "username": "user@example.com",
    "password": "your-password"
  }'
\`\`\`

\`\`\`javascript JavaScript
const response = await fetch('/api/v1/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    username: 'user@example.com',
    password: 'your-password'
  })
});
\`\`\`
</RequestExample>

<ResponseExample>
\`\`\`json Success Response
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 3600
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
\`\`\`
</ResponseExample>

---

## Refresh Token

<api method="POST" url="/auth/refresh">
  Refresh JWT token using existing token.
</api>

### Headers

<ParamField header="Authorization" type="string" required>
  Bearer token for authentication
</ParamField>

<RequestExample>
\`\`\`bash cURL
curl -X POST "http://localhost:8000/api/v1/auth/refresh" \\
  -H "Authorization: Bearer your-jwt-token"
\`\`\`
</RequestExample>

<ResponseExample>
\`\`\`json Success Response
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 3600
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
\`\`\`
</ResponseExample>
`;

    await fs.writeFile(
      path.join(this.outputPath, 'authentication.mdx'),
      authContent
    );

    // Generate query endpoints docs
    const queryContent = `# Query API Endpoints

## POST /query/generate

Generate SQL from natural language.

### Request Body

\`\`\`json
{
  "question": "Show me all users who signed up last month",
  "database_id": "string",
  "context": {
    "tables": ["users", "signups"],
    "previous_queries": []
  }
}
\`\`\`

### Response

\`\`\`json
{
  "success": true,
  "data": {
    "sql": "SELECT * FROM users WHERE created_at >= '2024-01-01'",
    "explanation": "This query retrieves all users...",
    "confidence": 0.95,
    "tables_used": ["users"]
  }
}
\`\`\`

## POST /query/execute

Execute generated SQL query.

### Request Body

\`\`\`json
{
  "sql": "SELECT * FROM users LIMIT 10",
  "database_id": "string",
  "dry_run": false
}
\`\`\`

### Response

\`\`\`json
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
\`\`\`

## GET /query/history

Get query history for user.

### Query Parameters

- \`limit\`: Number of queries to return (default: 50)
- \`offset\`: Pagination offset (default: 0)

### Response

\`\`\`json
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
\`\`\`
`;

    await fs.writeFile(
      path.join(backendDocsPath, 'query-endpoints.md'),
      queryContent
    );
  }

  async generateModelDocs() {
    const modelsPath = path.join(this.outputPath, 'models');
    await fs.ensureDir(modelsPath);

    const queryModelsContent = `# Query Models

## QueryRequest

Request model for SQL generation.

\`\`\`python
class QueryRequest(BaseModel):
    question: str = Field(..., description="Natural language question")
    database_id: str = Field(..., description="Database identifier")
    context: Optional[QueryContext] = None
    options: Optional[QueryOptions] = None
\`\`\`

## QueryResponse

Response model for generated SQL.

\`\`\`python
class QueryResponse(BaseModel):
    sql: str = Field(..., description="Generated SQL query")
    explanation: str = Field(..., description="Query explanation")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score")
    tables_used: List[str] = Field(default_factory=list)
    estimated_rows: Optional[int] = None
\`\`\`

## ExecutionResult

Model for query execution results.

\`\`\`python
class ExecutionResult(BaseModel):
    results: List[Dict[str, Any]] = Field(default_factory=list)
    row_count: int = Field(..., description="Number of rows returned")
    execution_time: float = Field(..., description="Execution time in seconds")
    columns: List[str] = Field(default_factory=list)
    query_plan: Optional[str] = None
\`\`\`
`;

    await fs.writeFile(
      path.join(modelsPath, 'query-models.md'),
      queryModelsContent
    );
  }

  async generateServiceDocs() {
    const servicesPath = path.join(this.outputPath, 'services');
    await fs.ensureDir(servicesPath);

    const llmServiceContent = `# LLM Service

The LLM Service handles natural language to SQL conversion using various language models.

## Configuration

\`\`\`python
class LLMConfig:
    provider: str = "openai"  # openai, anthropic, local
    model: str = "gpt-4"
    temperature: float = 0.1
    max_tokens: int = 2000
\`\`\`

## Methods

### generate_sql()

Generate SQL from natural language question.

\`\`\`python
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
\`\`\`

### explain_query()

Provide explanation for generated SQL.

\`\`\`python
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
\`\`\`

## Streaming Support

The LLM service supports streaming responses for real-time query generation:

\`\`\`python
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
\`\`\`
`;

    await fs.writeFile(
      path.join(servicesPath, 'llm-service.md'),
      llmServiceContent
    );
  }
}

// Run the generator
if (require.main === module) {
  const generator = new APIDocGenerator();
  generator.generateDocs().catch(console.error);
}

module.exports = APIDocGenerator;
