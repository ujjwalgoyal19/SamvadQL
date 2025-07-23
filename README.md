# SamvadQL - Text-to-SQL Conversational Interface

SamvadQL is an open-source Text-to-SQL conversational interface that enables users to translate natural language queries into precise and executable SQL commands. The system provides an intuitive, AI-driven experience for data access and interaction.

## Features

- **Natural Language Processing**: Convert natural language questions into SQL queries using advanced LLMs
- **Real-time Streaming**: Get progressive query generation with live explanations
- **Intelligent Schema Selection**: Automatic table and column recommendation using vector search
- **Multi-Database Support**: Works with PostgreSQL, MySQL, Snowflake, and BigQuery
- **SQL Validation**: Comprehensive syntax validation and safety checks
- **Query Optimization**: Performance suggestions and optimization recommendations
- **Interactive Refinement**: Edit and refine generated queries conversationally
- **Audit & Compliance**: Complete audit logging and governance features

## Architecture

The system follows a microservices architecture with:

- **Frontend**: React/Next.js with TypeScript and Material-UI
- **Backend**: FastAPI with Python, async/await support
- **Vector Database**: Qdrant or OpenSearch for semantic search
- **Cache Layer**: Redis for performance optimization
- **Database Support**: Multiple database connectors
- **Background Jobs**: Celery for async processing

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)

### Development Setup

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd samvadql
   ```

2. **Set up environment variables**

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start the development environment**

   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - Frontend: [http://localhost:3000](http://localhost:3000)
   - Backend API: [http://localhost:8000](http://localhost:8000)
   - API Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)

### Local Development

#### Backend Development

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

#### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

## Project Structure

```bash
samvadql/
├── backend/                 # FastAPI backend
│   ├── api/                # API endpoints
│   ├── core/               # Core configuration and interfaces
│   ├── models/             # Data models
│   ├── services/           # Business logic services
│   ├── main.py            # Application entry point
│   └── requirements.txt   # Python dependencies
├── frontend/               # React/Next.js frontend
│   ├── src/
│   │   ├── app/           # Next.js app directory
│   │   ├── components/    # React components
│   │   ├── services/      # API and WebSocket services
│   │   ├── types/         # TypeScript type definitions
│   │   └── theme/         # Material-UI theme
│   ├── package.json       # Node.js dependencies
│   └── tsconfig.json      # TypeScript configuration
├── shared/                 # Shared utilities and types
├── scripts/               # Database initialization scripts
├── docker-compose.yml     # Development environment
└── .env.example          # Environment configuration template
```

## Configuration

### Environment Variables

Key configuration options:

- `DATABASE_URL`: Primary database connection string
- `REDIS_URL`: Redis cache connection
- `OPENAI_API_KEY`: OpenAI API key for LLM services
- `QDRANT_URL`: Vector database connection
- `SECRET_KEY`: JWT signing secret

### Database Setup

The system automatically initializes the database schema on startup. See `scripts/init-db.sql` for the complete schema.

## Development Status

This project is currently in active development. The current implementation includes:

✅ **Completed (Task 1)**:

- Project structure and core interfaces
- TypeScript and Python data models
- Docker Compose development environment
- Basic FastAPI application setup
- React/Next.js frontend foundation

🚧 **In Progress**:

- Core data models and validation (Task 2)
- Database connectivity and metadata service (Task 3)
- Vector search and RAG infrastructure (Task 4)

📋 **Planned**:

- Query generation and LLM integration
- Validation and safety services
- Caching and performance optimization
- Frontend components and real-time streaming
- Background services and job scheduling

## Contributing

This project follows a spec-driven development approach. See `.kiro/specs/samvadql-text-to-sql/` for detailed requirements, design, and implementation tasks.

## License

[License information to be added]

## Support

[Support information to be added]
