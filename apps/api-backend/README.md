# SamvadQL Backend

FastAPI-based backend service for the SamvadQL Text-to-SQL conversational interface.

## Overview

The backend provides REST API endpoints and WebSocket connections for:

- Natural language to SQL query generation
- Database metadata management
- SQL validation and optimization
- Vector-based table recommendations
- User feedback collection and audit logging

## Architecture

- **Framework**: FastAPI with async/await support
- **Database**: PostgreSQL with asyncpg driver
- **Cache**: Redis for performance optimization
- **Vector DB**: Qdrant or OpenSearch for semantic search
- **Background Jobs**: Celery with Redis broker
- **LLM Integration**: LangChain with multiple providers (OpenAI, Anthropic, Azure, etc.)

### LangChain Integration

The backend uses LangChain for LLM operations, providing:

- **Multiple LLM Providers**: Support for OpenAI, Anthropic, Azure OpenAI, and other providers
- **Streaming Responses**: Real-time query generation with streaming callbacks
- **Chain Composition**: Modular chains for different SQL generation tasks
- **Memory Management**: Conversation history and context management
- **Prompt Templates**: Structured prompts for consistent SQL generation
- **Error Handling**: Robust error handling and fallback mechanisms

## Prerequisites

### Required Software

- Python 3.11 or higher
- PostgreSQL 15+ (or Docker)
- Redis 7+ (or Docker)
- Git

### Optional (for full functionality)

- Docker and Docker Compose
- Qdrant vector database
- OpenSearch (alternative to Qdrant)

## Quick Start with Docker

The easiest way to get started is using Docker Compose from the project root:

```bash
# From the project root directory
docker-compose up backend postgres redis qdrant
```

This will start:

- Backend API on http://localhost:8000
- PostgreSQL on localhost:5432
- Redis on localhost:6379
- Qdrant on localhost:6333

## Local Development Setup

### 1. Clone and Navigate

```bash
git clone <repository-url>
cd samvadql/backend
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

Create a `.env` file in the backend directory:

```bash
# Copy from example
cp ../.env.example .env
```

Edit `.env` with your configuration:

```env
# Database Configuration
DATABASE_URL=postgresql://samvadql:password@localhost:5432/samvadql

# Redis Configuration
REDIS_URL=redis://localhost:6379

# LLM Configuration (LangChain)
OPENAI_API_KEY=your-openai-api-key-here
ANTHROPIC_API_KEY=your-anthropic-api-key-here
LLM_PROVIDER=openai
LLM_MODEL=gpt-4
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=2000

# Vector Database Configuration
VECTOR_DB_PROVIDER=qdrant
QDRANT_URL=http://localhost:6333

# Security
SECRET_KEY=your-secret-key-here-change-in-production

# API Configuration
ALLOWED_ORIGINS=http://localhost:3000
```

### 5. Set Up Database

#### Option A: Using Docker

```bash
# Start PostgreSQL with Docker
docker run -d \
  --name samvadql-postgres \
  -e POSTGRES_DB=samvadql \
  -e POSTGRES_USER=samvadql \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 \
  postgres:15-alpine

# Initialize database schema
docker exec -i samvadql-postgres psql -U samvadql -d samvadql < ../scripts/init-db.sql
```

#### Option B: Local PostgreSQL Installation

```bash
# Create database and user
createdb samvadql
createuser samvadql -P  # Enter password when prompted

# Initialize schema
psql -U samvadql -d samvadql -f ../scripts/init-db.sql
```

### 6. Set Up Redis

#### Option A: Using Docker

```bash
docker run -d \
  --name samvadql-redis \
  -p 6379:6379 \
  redis:7-alpine
```

#### Option B: Local Redis Installation

```bash
# Install Redis (varies by OS)
# Ubuntu/Debian:
sudo apt-get install redis-server

# macOS with Homebrew:
brew install redis

# Start Redis
redis-server
```

### 7. Set Up Vector Database (Optional)

#### Qdrant (Recommended)

```bash
docker run -d \
  --name samvadql-qdrant \
  -p 6333:6333 \
  -p 6334:6334 \
  qdrant/qdrant:latest
```

#### OpenSearch (Alternative)

```bash
docker run -d \
  --name samvadql-opensearch \
  -p 9200:9200 \
  -p 9600:9600 \
  -e "discovery.type=single-node" \
  -e "DISABLE_SECURITY_PLUGIN=true" \
  opensearchproject/opensearch:2.11.0
```

### 8. Start the Backend Server

```bash
# Development mode with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or using Python directly
python main.py
```

The API will be available at:

- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Background Services

### Start Celery Worker

In a separate terminal:

```bash
# Activate virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Start Celery worker
celery -A worker worker --loglevel=info
```

### Start Celery Beat Scheduler

In another terminal:

```bash
# Activate virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Start Celery beat scheduler
celery -A worker beat --loglevel=info
```

## Configuration

### Environment Variables

| Variable             | Description                      | Default                  | Required |
| -------------------- | -------------------------------- | ------------------------ | -------- |
| `DATABASE_URL`       | PostgreSQL connection string     | -                        | Yes      |
| `REDIS_URL`          | Redis connection string          | `redis://localhost:6379` | Yes      |
| `OPENAI_API_KEY`     | OpenAI API key                   | -                        | Yes\*    |
| `ANTHROPIC_API_KEY`  | Anthropic API key                | -                        | Yes\*    |
| `LLM_PROVIDER`       | LLM provider (openai, anthropic) | `openai`                 | No       |
| `LLM_MODEL`          | LLM model name                   | `gpt-4`                  | No       |
| `LLM_TEMPERATURE`    | LLM temperature (0.0-1.0)        | `0.1`                    | No       |
| `LLM_MAX_TOKENS`     | Maximum tokens per response      | `2000`                   | No       |
| `VECTOR_DB_PROVIDER` | Vector DB (qdrant/opensearch)    | `qdrant`                 | No       |
| `QDRANT_URL`         | Qdrant connection URL            | `http://localhost:6333`  | No       |
| `OPENSEARCH_URL`     | OpenSearch connection URL        | `http://localhost:9200`  | No       |
| `SECRET_KEY`         | JWT signing secret               | -                        | Yes      |
| `ALLOWED_ORIGINS`    | CORS allowed origins             | `http://localhost:3000`  | No       |
| `DEBUG`              | Enable debug mode                | `False`                  | No       |

\*Note: At least one LLM provider API key is required (OPENAI_API_KEY or ANTHROPIC_API_KEY)

### Database Configuration

The application uses PostgreSQL as the primary database. The schema is automatically initialized using the script in `../scripts/init-db.sql`.

Key tables:

- `user_feedback` - User feedback on generated queries
- `audit_log` - System audit trail
- `query_execution_log` - Query execution history
- `database_connections` - Database connection configurations
- `table_metadata` - Cached table schema information

## API Endpoints

### Health Check

- `GET /health` - Service health status
- `GET /api/v1/status` - API status and version

### Query Generation (Planned)

- `POST /api/v1/query` - Submit natural language query
- `POST /api/v1/validate` - Validate SQL query
- `POST /api/v1/feedback` - Submit user feedback

### Metadata (Planned)

- `GET /api/v1/tables/{database_id}` - List database tables
- `POST /api/v1/tables/recommend` - Get table recommendations

## Development

### Project Structure

```
backend/
├── api/                    # API route handlers
├── core/                   # Core configuration and interfaces
│   ├── config.py          # Application configuration
│   └── interfaces.py      # Service interfaces
├── models/                 # Data models
│   └── base.py            # Core data classes
├── services/              # Business logic services
├── main.py                # FastAPI application entry point
├── worker.py              # Celery worker configuration
├── requirements.txt       # Python dependencies
└── Dockerfile            # Docker container definition
```

### Adding New Dependencies

```bash
# Add to requirements.txt
echo "new-package==1.0.0" >> requirements.txt

# Install
pip install -r requirements.txt
```

### Running Tests

```bash
# Install test dependencies (when available)
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

### Code Quality

```bash
# Format code
black .

# Sort imports
isort .

# Type checking
mypy .
```

## Troubleshooting

### Common Issues

1. **Database Connection Error**

   ```
   sqlalchemy.exc.OperationalError: could not connect to server
   ```

   - Ensure PostgreSQL is running
   - Check DATABASE_URL in .env
   - Verify database exists and user has permissions

2. **Redis Connection Error**

   ```
   redis.exceptions.ConnectionError: Error connecting to Redis
   ```

   - Ensure Redis is running
   - Check REDIS_URL in .env
   - Test connection: `redis-cli ping`

3. **Import Errors**

   ```
   ModuleNotFoundError: No module named 'backend'
   ```

   - Ensure virtual environment is activated
   - Run from the backend directory
   - Check PYTHONPATH if needed

4. **OpenAI API Errors**
   ```
   openai.error.AuthenticationError: Invalid API key
   ```
   - Verify OPENAI_API_KEY in .env
   - Check API key permissions and billing

### Logs and Debugging

- Application logs: Check console output when running with `--reload`
- Database logs: Check PostgreSQL logs
- Redis logs: Use `redis-cli monitor`
- Celery logs: Check worker terminal output

### Performance Monitoring

- Health endpoint: `GET /health`
- Database connections: Monitor PostgreSQL `pg_stat_activity`
- Redis memory: `redis-cli info memory`
- API metrics: Available at `/metrics` (when implemented)

## Production Deployment

### Environment Setup

1. Set production environment variables
2. Use a production WSGI server (Gunicorn)
3. Set up proper logging
4. Configure SSL/TLS
5. Set up monitoring and alerting

### Docker Production

```bash
# Build production image
docker build -t samvadql-backend .

# Run with production settings
docker run -d \
  --name samvadql-backend \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://... \
  -e REDIS_URL=redis://... \
  -e OPENAI_API_KEY=... \
  samvadql-backend
```

## Contributing

1. Follow the existing code structure
2. Add tests for new functionality
3. Update this README for new setup requirements
4. Follow Python PEP 8 style guidelines

## Support

For issues and questions:

1. Check the troubleshooting section above
2. Review the main project README
3. Check the API documentation at `/docs`
