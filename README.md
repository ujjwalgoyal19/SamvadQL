# SamvadQL - Text-to-SQL Conversational Interface

SamvadQL is an open-source Text-to-SQL conversational interface that enables users to translate natural language queries into precise and executable SQL commands. The system provides an intuitive, AI-driven experience for data access and interaction.

## Features

- **Natural Language Processing**: Convert natural language questions into SQL queries using advanced LLMs
- **Real-time Streaming**: Get progressive query generation with live explanations
- **Intelligent Schema Selection**: Automatic table and column recommendation using Pinecone vector search
- **Multi-Database Support**: Works with PostgreSQL and MySQL
- **SQL Validation**: Comprehensive syntax validation and safety checks
- **Query Optimization**: Performance suggestions and optimization recommendations
- **Interactive Refinement**: Edit and refine generated queries conversationally
- **Audit & Compliance**: Complete audit logging and governance features
- **Authentication & Authorization**: JWT-based authentication with role-based access control

## Architecture

The system is structured as a **Turborepo monorepo** with the following components:

- **Frontend**: React with TypeScript, Vite, and Tailwind CSS (`apps/web-frontend`)
  - Orchestrated by Turborepo with pnpm workspaces
  - Runs locally: `pnpm dev` (starts on port 3001)

- **Backend**: FastAPI with Python async/await support (`apps/api-backend`)
  - Runs locally: `poetry run uvicorn main:app --reload` (starts on port 8000)
  - Poetry for dependency management
  
- **Infrastructure (Docker only for persistence)**:
  - PostgreSQL 15-alpine: Primary relational database
  - Redis 7-alpine: Cache layer for performance optimization
  - Pinecone: Cloud-based vector database for semantic search (no Docker needed)
  
- **Supported Databases**: PostgreSQL, MySQL connectors available
- **Vector Search**: Pinecone for intelligent schema selection and semantic matching

## Quick Start

### Prerequisites

- Docker and Docker Compose (for PostgreSQL and Redis infrastructure)
- Node.js 20+ and pnpm 10.13.1+ (for frontend)
- Python 3.11+ and Poetry (for backend)
- Pinecone API key (create free account at [pinecone.io](https://pinecone.io))

### Local Development Setup

**1. Clone and install dependencies:**

```bash
git clone https://github.com/ujjwalgoyal19/SamvadQL.git
cd SamvadQL

# Install monorepo dependencies (pnpm workspaces)
pnpm install

# Backend setup with Poetry
cd apps/api-backend
poetry install
cd ../..
```

**2. Configure environment:**

```bash
# Copy environment template to root
cp .env.example .env

# Edit .env with your credentials:
# - PINECONE_API_KEY: Your Pinecone API key
# - OPENAI_API_KEY: Your OpenAI API key for LLM services
# - DATABASE_URL: Postgres connection (set by docker-compose)
# - REDIS_URL: Redis connection (set by docker-compose)
```

**3. Start infrastructure services (PostgreSQL & Redis only):**

```bash
docker-compose up -d
```

This starts:

- PostgreSQL 15 on `localhost:5432`
- Redis 7 on `localhost:6379`

**4. Run both frontend and backend together:**

```bash
# From root directory - runs both apps via Turborepo
pnpm dev
```

This will start:

- Frontend at <http://localhost:3001> (Vite dev server)
- Backend at <http://localhost:8000> (FastAPI + Uvicorn)

**Or run individually in separate terminals:**

```bash
# Terminal 1 - Frontend
cd apps/web-frontend
pnpm dev

# Terminal 2 - Backend  
cd apps/api-backend
poetry run uvicorn main:app --reload
```

**Access Points**:

- Frontend: <http://localhost:3001>
- Backend API: <http://localhost:8000>
- API Documentation: <http://localhost:8000/docs> (Swagger UI)

**Stop infrastructure when done:**

```bash
docker-compose down
```

📖 **For troubleshooting and advanced workflows, read `docs/DEV_WORKFLOW.md`**

## Project Structure

```
SamvadQL/
├── apps/
│   ├── web-frontend/                # React + TypeScript frontend (Vite)
│   │   ├── src/
│   │   │   ├── components/         # React components
│   │   │   ├── pages/              # Page components
│   │   │   ├── services/           # API and WebSocket services
│   │   │   ├── types/              # TypeScript type definitions
│   │   │   └── store/              # Redux/Zustand state management
│   │   ├── package.json            # Frontend dependencies
│   │   ├── vite.config.ts          # Vite configuration
│   │   ├── tsconfig.json           # TypeScript configuration
│   │   └── tailwind.config.js      # Tailwind CSS configuration
│   │
│   └── api-backend/                # FastAPI backend
│       ├── main.py                 # Application entry point
│       ├── api/
│       │   ├── v1.py              # API v1 endpoints
│       │   ├── auth.py            # Authentication endpoints
│       │   ├── dependencies.py    # FastAPI dependencies
│       │   └── permissions.py     # Permission checks
│       ├── services/              # Business logic services
│       ├── repositories/          # Database access layer
│       ├── models/                # Data models and schemas
│       ├── core/
│       │   ├── config.py         # Configuration (Pydantic settings)
│       │   ├── interfaces.py     # Core interfaces
│       │   ├── db/               # Database connections
│       │   ├── logging/          # Logging configuration
│       │   └── vector/           # Vector database clients
│       ├── migrations/           # SQL migration scripts
│       ├── pyproject.toml        # Poetry dependencies
│       └── poetry.lock           # Locked dependency versions
│
├── shared/                        # Shared Python utilities and types
│   ├── types.py                  # Shared type definitions
│   └── utils.py                  # Shared utility functions
│
├── docs/                         # Documentation (Mintlify)
│   ├── docs/
│   │   ├── getting-started/     # Getting started guides
│   │   ├── api/                 # API documentation
│   │   ├── architecture/        # Architecture guides
│   │   └── development/         # Development guides
│   ├── mint.json                # Mintlify configuration
│   ├── package.json             # Doc dependencies
│   └── scripts/                 # Doc generation scripts
│
├── scripts/                      # Utility scripts
│   ├── dev-setup.sh            # Development setup script
│   ├── init-db.sql             # Database initialization
│   └── migrations/             # Migration management
│
├── docker-compose.yml          # Infrastructure services
├── docker-compose.override.yml.example
├── package.json                # Root package.json
├── pnpm-workspace.yaml         # pnpm workspace configuration
├── turbo.json                  # Turborepo configuration
├── .env.example                # Environment template
└── README.md                   # This file
```

## Configuration

### Environment Variables

SamvadQL uses environment variables for configuration. Two templates are provided:

#### Development Environment

Create a `.env` file in the repository root for local development:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/samvadql
REDIS_URL=redis://localhost:6379/0

# Vector Search (Pinecone)
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENVIRONMENT=your_pinecone_environment
PINECONE_INDEX_NAME=samvadql-vectors

# LLM Services
OPENAI_API_KEY=your_openai_api_key
LLM_PROVIDER=openai
LLM_MODEL=gpt-4
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=2000

# Security
SECRET_KEY=your-secret-key-for-jwt
ALGORITHM=HS256

# Backend
BACKEND_CORS_ORIGINS=["http://localhost:3001"]
DEBUG=true
DEV_MODE=true
```

#### Production Environment

For production deployments, use `.env.production.example` as a template:

```bash
cp .env.production.example .env.production
# Edit .env.production with your production credentials
```

**Important:** Never commit `.env.production` to version control. Instead:

1. **Use your deployment platform's secrets management:**
   - **GitHub Actions:** GitHub Secrets
   - **AWS:** AWS Secrets Manager or Parameter Store
   - **Azure:** Azure Key Vault
   - **Docker Compose:** Pass secrets via environment overrides or use `docker-compose.prod.yml`

2. **Production configuration includes:**
   - Managed PostgreSQL (AWS RDS, Azure Database, etc.)
   - Managed Redis (AWS ElastiCache, Azure Cache, etc.)
   - Pinecone serverless or pod-based index
   - Strong, randomly generated `SECRET_KEY`
   - HTTPS-only `ALLOWED_ORIGINS`
   - `DEBUG=false` and `DEV_MODE=false` (critical for security)
   - LLM API keys with appropriate quota and rate limits
   - Proper logging configuration and monitoring

See `.env.production.example` for all available configuration options and detailed documentation.

### Database Initialization

The database schema is automatically initialized on backend startup. To manually run migrations:

```bash
cd apps/api-backend
python -m migrations.cli upgrade
```

### Poetry Dependency Management (Backend)

Dependencies are managed via Poetry for the backend:

```bash
cd apps/api-backend

# Install dependencies
poetry install

# Add a new dependency
poetry add package_name

# Update dependencies
poetry update
```

**Dependency Lock Policy:**

The `pyproject.toml` file defines all backend dependencies with version constraints. The `poetry.lock` file is **not committed to the repository** (excluded via `.gitignore`). Poetry automatically resolves and locks versions at build and install time:

- **Local Development:** `poetry install` creates a local lock file for reproducible local environments
- **Docker Builds:** `poetry install` in the Dockerfile resolves dependencies at build time, ensuring consistency
- **CI/CD:** Each build resolves dependencies from `pyproject.toml`, ensuring all environments use compatible versions

This approach maintains flexibility during active development while leveraging Poetry's built-in locking mechanism for reproducibility. If production deployments require strict version pinning across environments in the future, the lock file can be committed.

## Authentication & Authorization

SamvadQL implements a comprehensive ABAC (Attribute-Based Access Control) system for fine-grained access control.

### Resource Types

- **database**: Database-level access control
- **table**: Table-level access control
- **column**: Column-level access control
- **query**: Query-level access control
- **api**: API endpoint access control

### Permission Types

- **read**: View and query resources
- **write**: Modify existing resources
- **delete**: Remove resources
- **execute**: Execute queries or operations
- **admin**: Full administrative access

### Resource ID Convention

Resource IDs follow a consistent, hierarchical format:

| Resource Type | Format                               | Example                     | Description                |
| ------------- | ------------------------------------ | --------------------------- | -------------------------- |
| **Database**  | `database_id`                        | `postgres_prod`             | Unique database identifier |
| **Table**     | `database_id:table_name`             | `postgres_prod:users`       | Database + table name      |
| **Column**    | `database_id:table_name:column_name` | `postgres_prod:users:email` | Database + table + column  |
| **Query**     | `<uuid>`                             | `123e4567-...`              | UUID for saved queries     |
| **API**       | `/path/to/endpoint`                  | `/api/v1/query/submit`      | API endpoint path          |

**Helper Functions** (in `apps/api-backend/utils/resource_ids.py`):

```python
from utils.resource_ids import (
    format_table_resource_id,
    parse_table_resource_id,
    format_column_resource_id,
    parse_column_resource_id,
    validate_resource_id
)

# Format resource IDs
table_id = format_table_resource_id("postgres_prod", "users")
# Returns: "postgres_prod:users"

column_id = format_column_resource_id("postgres_prod", "users", "email")
# Returns: "postgres_prod:users:email"

# Parse resource IDs
database_id, table_name = parse_table_resource_id("postgres_prod:users")
database_id, table_name, column_name = parse_column_resource_id("postgres_prod:users:email")

# Validate resource IDs
validate_resource_id("postgres_prod:users", ResourceType.TABLE)
# Raises ValueError if format is invalid
```

**Important Notes**:

- Component names (database_id, table_name, column_name) **must not contain colons** (`:`)
- Use helper functions to prevent formatting errors
- Helper functions validate inputs and raise descriptive errors

### Permission Hierarchy

Permissions can be inherited from parent resources:

- **Database permissions** → apply to all tables and columns within that database
- **Table permissions** → apply to all columns within that table

### Granting Permissions

Permissions can be granted at user or role level:

```bash
# Grant database READ permission to a user
POST /api/v1/permissions/users/{user_id}/grant
{
  "resource_type": "database",
  "resource_id": "postgres_prod",
  "permission": "read"
}

# Grant table WRITE permission to a role
POST /api/v1/permissions/roles/{role_id}/grant
{
  "resource_type": "table",
  "resource_id": "postgres_prod:users",
  "permission": "write"
}

# Grant column READ permission to a user
POST /api/v1/permissions/users/{user_id}/grant
{
  "resource_type": "column",
  "resource_id": "postgres_prod:users:email",
  "permission": "read"
}
```

### Permission Checks

All API endpoints are protected with permission checks:

- `/api/v1/query` - Requires READ permission on the selected database
- `/api/v1/tables/{database_id}` - Requires READ permission on the database
- `/api/v1/validate` - Requires authentication
- `/api/v1/feedback` - Requires authentication
- `/api/v1/feedback/stats` - Requires superuser/admin privileges

### Permission Management API

The `/api/v1/permissions/*` endpoints allow admins to manage permissions:

- `POST /api/v1/permissions/users/{user_id}/grant` - Grant permission to user
- `DELETE /api/v1/permissions/users/{user_id}/revoke` - Revoke permission from user
- `GET /api/v1/permissions/users/{user_id}` - Get all user permissions
- `POST /api/v1/permissions/users/{user_id}/check` - Check if user has permission
- `POST /api/v1/permissions/roles/{role_id}/grant` - Grant permission to role
- `DELETE /api/v1/permissions/roles/{role_id}/revoke` - Revoke permission from role
- `GET /api/v1/permissions/hierarchy` - Manage permission hierarchies
- `POST /api/v1/permissions/bulk-grant` - Grant multiple permissions at once

## Layout Structure

The frontend uses separate layouts for different user states:

### AuthLayout

Used for authentication pages (signin, signup, forgot-password, reset-password):

- Centered content with logo branding
- Minimal design focused on authentication flow
- Footer with terms, privacy, and help links

### AppLayout

Used for authenticated app pages with side navigation:

- Persistent sidebar (collapsible on mobile)
- Navigation items: Dashboard, Query, Tables, History, Settings
- User profile section with logout
- Responsive design with mobile hamburger menu

## Running Migrations

The ABAC system requires running database migrations:

```bash
# Run all pending migrations
cd apps/api-backend
python -m migrations.cli upgrade

# Or with Docker
docker-compose exec backend python -m migrations.cli upgrade
```

The ABAC migration (`20250207_create_abac_tables.sql`) creates:

- `resource_permissions` - User-level resource permissions
- `role_resource_permissions` - Role-level resource permissions
- `permission_hierarchy` - Parent-child resource relationships

After running migrations, you can grant initial permissions to users through the API or directly in the database.

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

This project follows a spec-driven development approach. See the architecture documentation in `docs/` for detailed requirements and design.

### Development Workflow

1. Read the architecture and setup guides in `docs/`
2. Follow the branch naming conventions (feature/*, bugfix/*, etc.)
3. Ensure all tests pass before submitting PRs
4. Include clear commit messages referencing related issues

## License

[License information to be added]

## Support

- 📖 [Documentation](docs/) - Architecture guides and development setup
- 🐛 [Issues](https://github.com/ujjwalgoyal19/SamvadQL/issues) - Bug reports and feature requests
- 💬 [Discussions](https://github.com/ujjwalgoyal19/SamvadQL/discussions) - Community discussions
