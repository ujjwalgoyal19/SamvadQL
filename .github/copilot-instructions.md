# Copilot Instructions for SamvadQL

## Big Picture Architecture

- **Microservices**: Backend (FastAPI/Python), Frontend (React/TypeScript), Docs (Mintlify/MDX), and shared Python utilities.
- **Backend** (`apps/api-backend/`):
  - API endpoints in `main.py` and `api/v1.py`.
  - Services (business logic) in `services/`, repositories (DB access) in `repositories/`, models in `models/`.
  - Migrations managed via SQL scripts and `migrations/cli.py`.
  - Caching via Redis, vector search via Qdrant/OpenSearch, LLM integration via OpenAI/Llama/DeepSeek clients.
- **Frontend** (`apps/web-frontend/`):
  - React + TypeScript, Vite, Tailwind CSS, shadcn/ui, Redux Toolkit/Zustand.
  - WebSocket streaming via Socket.io, API calls via Axios.
  - TypeScript interfaces mirror backend models.
- **Docs** (`docs/`):
  - Mintlify-based, auto-generated from code and components.
  - Scripts for doc generation in `docs/scripts/`.
- **Shared** (`shared/`):
  - Python utilities and types for cross-service use.

## Developer Workflows

- **Build/Run**:
  - Local: `docker-compose up -d` (root), access frontend at `localhost:3000`, backend at `localhost:8000`.
  - Frontend: `pnpm install`, `pnpm dev` (in `apps/web-frontend/`).
  - Backend: Python 3.11+, FastAPI, run via Docker or locally.
- **Testing**:
  - Backend: `pytest` in `apps/api-backend/tests/`.
  - Frontend: `pnpm test` in `apps/web-frontend/`.
- **Migrations**:
  - Add SQL scripts to `apps/api-backend/migrations/`, run with `cli.py`.
- **Docs**:
  - `docker-compose up -d docs` or run scripts in `docs/scripts/`.

## Project-Specific Conventions

- **Service boundaries**: Each service is a Python module in `services/`, repositories only handle DB logic.
- **Data models**: Python dataclasses (backend), TypeScript interfaces (frontend), validation via Pydantic.
- **Caching**: Redis for query, metadata, and session caching.
- **Streaming**: WebSocket endpoints for progressive query/results.
- **Validation/Safety**: SQL validation via `sqlglot`/`sqlfluff`, safety checks for destructive queries, LLM-based error correction planned.

## Integration Points

- **LLM Providers**: OpenAI, Llama, DeepSeek clients in backend services.
- **Vector DBs**: Qdrant, OpenSearch for semantic search.
- **Database Connectors**: PostgreSQL, MySQL, Snowflake, BigQuery connectors.

## Key Files & Directories

- `apps/api-backend/main.py` – FastAPI entrypoint
- `apps/api-backend/services/` – Business logic
- `apps/api-backend/models/` – Data models
- `apps/api-backend/repositories/` – DB access
- `apps/api-backend/migrations/` – Schema migrations
- `apps/web-frontend/src/` – React components
- `shared/` – Cross-service utilities
- `docs/` – Mintlify documentation

## Example Patterns

- Add API endpoint: update `api/v1.py` and corresponding service/repository.
- Add DB connector: subclass base connector in `core/db/`.
- Update schema: add migration SQL to `migrations/`, run migration manager.
- Frontend API types: update TypeScript interfaces to match backend models.

## Recommended MCP Tools

When working on this project, use these MCP tools for enhanced productivity:

- **mcp_memory**: Store and retrieve project context, user requirements, and architectural decisions across sessions
- **mcp_sequentialthinking**: Break down complex implementation tasks into logical steps, especially for multi-component features
- **mcp_context7**: Get up-to-date documentation for React Router v7, shadcn/ui components, and React patterns
- **mcp_shadcn-ui**: Access latest shadcn/ui component code and examples when adding new UI components

### Tool Usage Patterns

- Use **sequential thinking** for complex flows like onboarding step implementation or authentication state management
- Use **memory** to track progress on multi-step tasks and remember project-specific conventions
- Use **context7** for React Router v7 patterns, form handling, and TypeScript best practices
- Use **shadcn-ui MCP** when implementing new components or updating existing UI patterns

---
