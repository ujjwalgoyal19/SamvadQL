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
- **Authentication & Authorization**: JWT-based authentication with ABAC (Attribute-Based Access Control)
- **Resource-Level Permissions**: Fine-grained access control at database, table, and column levels
- **Role-Based Access**: Flexible role management with permission inheritance

## Architecture

The system follows a microservices architecture with:

- **Frontend**: React with TypeScript, Vite, and Tailwind CSS
  - Separate layouts for authentication and app pages
  - Side navigation for authenticated users
  - Redux for UI state management
  - WebSocket for real-time streaming
- **Backend**: FastAPI with Python, async/await support
  - JWT-based authentication
  - ABAC (Attribute-Based Access Control) for resource-level permissions
  - Role-based access control with permission inheritance
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

## Documentation

Comprehensive documentation is available using Mintlify:

### Quick Start Documentation

```bash
# Start documentation server with Docker (recommended)
./scripts/dev-docs.sh    # Linux/Mac
scripts\dev-docs.bat     # Windows

# Or with Docker Compose directly:
docker-compose up -d docs

# Or manually (local development):
cd docs && npm install && npm start
```

Visit [http://localhost:3001](http://localhost:3001) (Docker) or [http://localhost:3000](http://localhost:3000) (local) for:

- 📖 **Getting Started**: Installation and quick start guides
- 🏗️ **Architecture**: System design and component overview
- 📚 **API Reference**: Auto-generated from backend code
- 🧩 **Components**: Auto-generated from frontend components
- 🛠️ **Development**: Setup, testing, and deployment guides

### Auto-Generated Documentation

The documentation system automatically generates:

- **API docs** from Python docstrings and FastAPI routes
- **Component docs** from React TypeScript interfaces
- **Real-time updates** when source code changes

```bash
# With Docker (automatic generation)
docker-compose up -d docs

# Or generate manually (local development)
cd docs && npm run generate-all-docs

# Watch for changes and auto-generate (local development)
cd docs && node scripts/watch-and-generate.js
```

## Contributing

This project follows a spec-driven development approach. See `.kiro/specs/samvadql-text-to-sql/` for detailed requirements, design, and implementation tasks.

### Development Workflow

1. Read the [Development Setup](docs/docs/development/setup.md) guide
2. Check the [Architecture Overview](docs/docs/architecture/overview.md)
3. Follow the [Contributing Guidelines](docs/docs/development/contributing.md)
4. Use the documentation system to understand APIs and components

## License

[License information to be added]

## Support

- 📖 [Documentation](http://localhost:3000) (after running docs server)
- 🐛 [Issues](https://github.com/your-org/samvadql/issues)
- 💬 [Discussions](https://github.com/your-org/samvadql/discussions)
