# SamvadQL Backend Documentation

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Project Structure](#project-structure)
4. [Core Components](#core-components)
5. [API Endpoints](#api-endpoints)
6. [Services](#services)
7. [Data Models](#data-models)
8. [Database Integration](#database-integration)
9. [Authentication & Security](#authentication--security)
10. [Configuration](#configuration)
11. [Development Guide](#development-guide)
12. [Testing](#testing)
13. [Deployment](#deployment)
14. [Troubleshooting](#troubleshooting)

## Overview

SamvadQL backend is a FastAPI-based microservice that provides Text-to-SQL conversion capabilities through natural language processing. The system leverages Large Language Models (LLMs) and vector search to generate accurate SQL queries from natural language input.

### Key Features

- **Multi-LLM Support**: OpenAI, Anthropic, and local models via Ollama
- **Real-time Streaming**: Progressive query generation with live explanations
- **Vector Search**: Intelligent table discovery using semantic similarity
- **Multi-Database Support**: PostgreSQL, MySQL, Snowflake, BigQuery
- **SQL Validation**: Comprehensive syntax and safety validation
- **Metadata Caching**: Redis-based caching for performance optimization
- **Audit Logging**: Complete request/response tracking
- **Authentication**: JWT-based user authentication with role-based access

### Technology Stack

- **Framework**: FastAPI 0.104.1 with Python 3.11+
- **Database**: PostgreSQL 15+ (primary), with multi-database support
- **ORM**: SQLAlchemy 2.0+ with async support
- **Caching**: Redis 7+ for performance optimization
- **LLM Integration**: LangChain with multiple provider support
- **Vector Database**: Qdrant or OpenSearch for semantic search
- **Background Jobs**: Celery with Redis broker
- **Validation**: Pydantic 2.5+ for data models and API validation

## Architecture

### High-Level Architecture

```mermaid
graph TB
    Client[Frontend Client] --> API[FastAPI Application]
    API --> Auth[Authentication Service]
    API --> Query[Query Generation Service]
    API --> Meta[Metadata Service]
    API --> Vector[Vector Search Service]

    Query --> LLM[LLM Service]
    LLM --> OpenAI[OpenAI]
    LLM --> Anthropic[Anthropic]
    LLM --> Ollama[Ollama/Local Models]

    Meta --> Cache[Redis Cache]
    Meta --> DB[Database Connectors]
    DB --> PG[PostgreSQL]
    DB --> MySQL[MySQL]
    DB --> SF[Snowflake]
    DB --> BQ[BigQuery]

    Vector --> Qdrant[Qdrant Vector DB]
    Vector --> OpenSearch[OpenSearch]

    Query --> Celery[Background Jobs]
    Celery --> Redis[Redis Broker]
```

### Request Flow

1. **Authentication**: JWT token validation
2. **Query Processing**: Natural language query analysis
3. **Table Discovery**: Vector search for relevant tables
4. **Context Optimization**: Schema optimization for LLM context window
5. **SQL Generation**: LLM-based query generation with streaming
6. **Validation**: SQL syntax and safety validation
7. **Response**: Structured response with explanations and metadata

## Project Structure

```
apps/api-backend/
├── api/                    # API route handlers
│   ├── v1.py              # Main API endpoints
│   └── auth.py            # Authentication endpoints
├── core/                   # Core configuration and interfaces
│   ├── config.py          # Application configuration
│   ├── interfaces.py      # Service interfaces
│   └── db/                # Database connection management
├── models/                 # Pydantic data models
│   ├── base.py            # Base models and enums
│   ├── request.py         # Request models
│   ├── response.py        # Response models
│   ├── auth.py            # Authentication models
│   └── ...
├── services/               # Business logic layer
│   ├── query_generation_service.py  # Main orchestration
│   ├── llm_service.py               # LLM abstraction
│   ├── metadata_service.py         # Database metadata
│   ├── vector_search_service.py    # Vector search
│   └── ...
├── repositories/           # Data access layer
│   ├── base.py            # Base repository
│   ├── metadata.py        # Metadata repository
│   ├── user_feedback.py   # Feedback repository
│   └── ...
├── migrations/             # Database migrations
├── tests/                  # Test files
├── examples/               # Usage examples
├── main.py                # Application entry point
└── requirements.txt       # Dependencies
```

## Core Components

### 1. FastAPI Application (`main.py`)

The main application entry point configures FastAPI with:

- **CORS Middleware**: Cross-origin request handling
- **GZip Middleware**: Response compression
- **Lifespan Events**: Startup/shutdown hooks
- **Health Endpoints**: Liveness and readiness probes

```python
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    debug=settings.debug,
    lifespan=lifespan,
)
```

### 2. Configuration Management (`core/config.py`)

Centralized configuration using Pydantic Settings:

```python
class Settings(BaseSettings):
    # API Configuration
    api_title: str = "SamvadQL API"
    debug: bool = False

    # Database Configuration
    database_url: Optional[str] = None
    redis_url: str = "redis://localhost:6379"

    # LLM Configuration
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    llm_provider: str = "openai"

    # Vector Database Configuration
    vector_db_provider: str = "qdrant"
    qdrant_url: str = "http://localhost:6333"
```

### 3. Service Interfaces (`core/interfaces.py`)

Abstract interfaces defining contracts for all services:

- `LLMServiceInterface`: LLM provider abstraction
- `VectorSearchServiceInterface`: Vector search operations
- `MetadataServiceInterface`: Database metadata operations
- `DatabaseConnectorInterface`: Database connection abstraction
- `QueryGenerationServiceInterface`: Main orchestration interface

## API Endpoints

### Authentication Endpoints (`/api/v1/auth`)

| Method | Endpoint           | Description             |
| ------ | ------------------ | ----------------------- |
| POST   | `/signup`          | Create new user account |
| POST   | `/login`           | Authenticate user       |
| POST   | `/forgot-password` | Initiate password reset |
| POST   | `/reset-password`  | Complete password reset |

### Query Endpoints (`/api/v1`)

| Method | Endpoint                | Description                               |
| ------ | ----------------------- | ----------------------------------------- |
| POST   | `/query`                | Submit natural language query (streaming) |
| GET    | `/tables/{database_id}` | Get available tables with pagination      |
| POST   | `/validate`             | Validate SQL query                        |
| POST   | `/feedback`             | Submit user feedback                      |
| GET    | `/feedback/stats`       | Get feedback statistics                   |
| GET    | `/health`               | API health check                          |

### Query Submission Example

```python
# Request
{
    "query": "Show me all users who signed up last month",
    "user_id": "user123",
    "database_id": "550e8400-e29b-41d4-a716-446655440000",
    "selected_tables": ["users", "signups"],
    "context": {"timezone": "UTC"}
}

# Streaming Response
{
    "sql": "SELECT * FROM users WHERE created_at >= '2024-01-01'",
    "explanation": "This query retrieves all users created on or after January 1st, 2024",
    "confidence_score": 0.95,
    "selected_tables": ["users"],
    "validation_status": "valid",
    "optimization_suggestions": [],
    "execution_time_estimate": 0.25
}
```

## Services

### 1. Query Generation Service

**Purpose**: Orchestrates the complete Text-to-SQL workflow

**Key Features**:

- Table discovery via vector search
- Context window optimization
- LLM-based SQL generation
- Streaming response support
- Error handling and fallbacks

**Main Methods**:

```python
async def generate_sql(request: QueryRequest) -> AsyncIterator[QueryResponse]
async def refine_query(original_sql: str, refinement_request: str) -> AsyncIterator[QueryResponse]
```

### 2. LLM Service

**Purpose**: Abstracts multiple LLM providers with unified interface

**Supported Providers**:

- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- Ollama (Llama, DeepSeek, local models)

**Key Features**:

- Provider abstraction
- Streaming support
- Prompt template management
- Response parsing and validation
- Health monitoring

**Template System**:

```python
templates = {
    "sql_generation": PromptTemplate(...),
    "query_refinement": PromptTemplate(...),
    "sql_correction": PromptTemplate(...)
}
```

### 3. Metadata Service

**Purpose**: Extracts and caches database schema information

**Key Features**:

- Multi-database support
- Redis caching with TTL
- Sample data collection
- Schema versioning
- Incremental refresh

**Caching Strategy**:

- Table list: 1 hour TTL
- Table metadata: 2 hours TTL
- Sample data: 4 hours TTL

### 4. Vector Search Service

**Purpose**: Semantic search for relevant tables and queries

**Key Features**:

- Table embedding and indexing
- Semantic similarity search
- Query-table relevance scoring
- Historical query indexing

### 5. Authentication Service

**Purpose**: User authentication and authorization

**Key Features**:

- JWT token generation/validation
- Password hashing (bcrypt)
- Role-based access control
- Password reset functionality

## Data Models

### Core Models

#### QueryRequest

```python
class QueryRequest(BaseModel):
    query: str                              # Natural language query
    user_id: str                           # User identifier
    database_id: str                       # Database UUID
    selected_tables: Optional[List[str]]   # Pre-selected tables
    context: Optional[Dict[str, Any]]      # Additional context
    session_id: Optional[str]              # Session identifier
```

#### QueryResponse

```python
class QueryResponse(BaseModel):
    sql: str                               # Generated SQL
    explanation: str                       # Human-readable explanation
    confidence_score: float                # Confidence (0-1)
    selected_tables: List[str]             # Tables used
    validation_status: ValidationStatus    # Validation result
    optimization_suggestions: List[OptimizationSuggestion]
    execution_time_estimate: Optional[float]
```

#### TableSchema

```python
class TableSchema(BaseModel):
    name: str                              # Table name
    database_id: str                       # Database UUID
    columns: List[ColumnSchema]            # Column definitions
    description: Optional[str]             # Table description
    tier: Optional[str]                    # Data tier (gold/silver/bronze)
    tags: List[str]                        # Categorization tags
    row_count: Optional[int]               # Approximate row count
```

### Validation and Enums

```python
class DatabaseType(Enum):
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SNOWFLAKE = "snowflake"
    BIGQUERY = "bigquery"

class ValidationStatus(Enum):
    VALID = "valid"
    INVALID = "invalid"
    WARNING = "warning"
    UNSAFE = "unsafe"
```

## Database Integration

### Connector Architecture

The system uses a factory pattern for database connectors:

```python
class DatabaseConnectorFactory:
    @staticmethod
    def create_connector(db_type: DatabaseType, config: Dict) -> BaseDatabaseConnector:
        if db_type == DatabaseType.POSTGRESQL:
            return PostgreSQLConnector(config)
        elif db_type == DatabaseType.MYSQL:
            return MySQLConnector(config)
        # ... other connectors
```

### Supported Databases

| Database   | Driver                     | Features                       |
| ---------- | -------------------------- | ------------------------------ |
| PostgreSQL | asyncpg                    | Full support, primary database |
| MySQL      | aiomysql                   | Full support                   |
| Snowflake  | snowflake-connector-python | Query execution, metadata      |
| BigQuery   | google-cloud-bigquery      | Query execution, metadata      |

### Connection Management

- **Async Connections**: All database operations are asynchronous
- **Connection Pooling**: Managed by SQLAlchemy
- **Health Checks**: Regular connectivity validation
- **Timeout Handling**: Configurable query timeouts

## Authentication & Security

### JWT Authentication

```python
# Token Structure
{
    "sub": "user_id",
    "exp": 1234567890,
    "iat": 1234567890,
    "permissions": ["query:read", "query:write"],
    "roles": ["viewer", "analyst"]
}
```

### Security Features

- **Password Hashing**: bcrypt with salt
- **SQL Injection Prevention**: Parameterized queries
- **Input Validation**: Pydantic model validation
- **Rate Limiting**: Configurable request limits
- **CORS Configuration**: Controlled cross-origin access

### Role-Based Access Control

| Role    | Permissions                     |
| ------- | ------------------------------- |
| Viewer  | Read-only query access          |
| Analyst | Query creation and modification |
| Admin   | Full system access              |

## Configuration

### Environment Variables

```bash
# API Configuration
API_TITLE="SamvadQL API"
DEBUG=false

# Database
DATABASE_URL="postgresql://user:pass@localhost:5432/samvadql"
REDIS_URL="redis://localhost:6379"

# LLM Configuration
OPENAI_API_KEY="sk-..."
ANTHROPIC_API_KEY="sk-ant-..."
LLM_PROVIDER="openai"
LLM_MODEL="gpt-4"
LLM_TEMPERATURE=0.1

# Vector Database
VECTOR_DB_PROVIDER="qdrant"
QDRANT_URL="http://localhost:6333"

# Security
SECRET_KEY="your-secret-key"
ALLOWED_ORIGINS="http://localhost:3000"
```

### Configuration Validation

All configuration is validated using Pydantic:

```python
@field_validator("allowed_origins", mode="before")
@classmethod
def parse_allowed_origins(cls, v):
    if isinstance(v, str):
        return [origin.strip() for origin in v.split(",")]
    return v
```

## Development Guide

### Setup

1. **Install Dependencies**:

```bash
cd apps/api-backend
pip install -r requirements.txt
```

2. **Environment Configuration**:

```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Database Setup**:

```bash
# Run migrations
python migrations/cli.py up
```

4. **Start Development Server**:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Development Commands

```bash
# Run tests
python -m pytest tests/ -v

# Run specific test
python -m pytest tests/test_llm_service.py -v

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html

# Format code
black .
isort .

# Type checking
mypy .

# Linting
flake8 .
```

### Adding New LLM Providers

1. **Create Client Class**:

```python
class NewProviderClient(BaseLLMClient):
    def _initialize_client(self) -> None:
        # Initialize provider-specific client
        pass

    async def generate_stream(self, messages: List[BaseMessage]) -> AsyncIterator[StreamingResponse]:
        # Implement streaming generation
        pass
```

2. **Register in LLMService**:

```python
def _initialize_clients(self) -> None:
    # Add new provider initialization
    if settings.new_provider_api_key:
        config = LLMConfig(provider=LLMProvider.NEW_PROVIDER, ...)
        self.clients[LLMProvider.NEW_PROVIDER] = NewProviderClient(config)
```

### Adding New Database Connectors

1. **Implement Connector**:

```python
class NewDatabaseConnector(BaseDatabaseConnector):
    async def connect(self) -> None:
        # Implement connection logic
        pass

    async def execute_query(self, sql: str) -> List[Dict[str, Any]]:
        # Implement query execution
        pass
```

2. **Register in Factory**:

```python
@staticmethod
def create_connector(db_type: DatabaseType, config: Dict) -> BaseDatabaseConnector:
    if db_type == DatabaseType.NEW_DATABASE:
        return NewDatabaseConnector(config)
```

## Testing

### Test Structure

```
tests/
├── test_api_v1_integration.py      # API integration tests
├── test_llm_service.py             # LLM service tests
├── test_metadata_service.py        # Metadata service tests
├── test_query_generation_service.py # Query generation tests
├── test_vector_search_service.py   # Vector search tests
├── test_models.py                  # Model validation tests
└── test_repositories.py           # Repository tests
```

### Test Categories

1. **Unit Tests**: Individual component testing
2. **Integration Tests**: Service interaction testing
3. **API Tests**: Endpoint testing with test client
4. **Database Tests**: Repository and connector testing

### Running Tests

```bash
# All tests
python -m pytest

# Specific test file
python -m pytest tests/test_llm_service.py

# With coverage
python -m pytest --cov=. --cov-report=html

# Integration tests only
python -m pytest tests/test_*_integration.py
```

### Test Configuration

```python
# conftest.py
@pytest.fixture
async def test_client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
def mock_llm_service():
    with patch('services.llm_service.LLMService') as mock:
        yield mock
```

## Deployment

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose

```yaml
version: '3.8'
services:
  api:
    build: ./apps/api-backend
    ports:
      - '8000:8000'
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/samvadql
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: samvadql
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password

  redis:
    image: redis:7-alpine
```

### Production Considerations

1. **Environment Variables**: Use secrets management
2. **Database Connections**: Configure connection pooling
3. **Logging**: Structured logging with correlation IDs
4. **Monitoring**: Health checks and metrics
5. **Security**: HTTPS, rate limiting, input validation

### Health Checks

```python
# Kubernetes health check
@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "samvadql-backend"}

@app.get("/ready")
async def readiness_check():
    # Check dependencies
    components = await check_dependencies()
    return {"ready": all(components.values()), "components": components}
```

## Troubleshooting

### Common Issues

#### 1. LLM Service Errors

**Symptoms**:

- "No client configured for provider" errors
- Streaming responses fail

**Solutions**:

- Verify API keys in environment variables
- Check provider availability
- Review LLM service logs

```bash
# Check LLM service health
curl http://localhost:8000/api/v1/health
```

#### 2. Database Connection Issues

**Symptoms**:

- Connection timeout errors
- Metadata extraction failures

**Solutions**:

- Verify database connectivity
- Check connection string format
- Review database logs

```python
# Test database connection
async def test_connection():
    connector = await get_connector(database_id, database_type, config)
    health = await connector.health_check()
    print(f"Database health: {health}")
```

#### 3. Vector Search Issues

**Symptoms**:

- No relevant tables found
- Poor table recommendations

**Solutions**:

- Verify vector database connectivity
- Check table indexing status
- Review embedding quality

#### 4. Cache Issues

**Symptoms**:

- Slow metadata retrieval
- Stale data returned

**Solutions**:

- Check Redis connectivity
- Clear cache manually
- Review TTL settings

```bash
# Clear Redis cache
redis-cli FLUSHDB
```

### Debugging Tools

#### 1. Logging Configuration

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Service-specific loggers
logger = logging.getLogger(__name__)
```

#### 2. Request Tracing

```python
# Add correlation ID to requests
@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    correlation_id = str(uuid4())
    request.state.correlation_id = correlation_id
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response
```

#### 3. Performance Monitoring

```python
import time
from functools import wraps

def monitor_performance(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        duration = time.time() - start_time
        logger.info(f"{func.__name__} took {duration:.2f}s")
        return result
    return wrapper
```

### Performance Optimization

#### 1. Database Query Optimization

- Use connection pooling
- Implement query result caching
- Optimize metadata queries
- Use database-specific optimizations

#### 2. LLM Response Optimization

- Implement response caching
- Use streaming for better UX
- Optimize prompt templates
- Implement fallback strategies

#### 3. Memory Management

- Monitor memory usage
- Implement connection cleanup
- Use async context managers
- Clear unused caches

### Monitoring and Alerting

#### Key Metrics

- Request latency (p50, p95, p99)
- Error rates by endpoint
- LLM provider response times
- Database connection pool usage
- Cache hit rates

#### Health Checks

- API endpoint availability
- Database connectivity
- LLM provider availability
- Vector database status
- Redis connectivity

---

This documentation provides a comprehensive guide to understanding, developing, and maintaining the SamvadQL backend. For specific implementation details, refer to the source code and inline documentation.
