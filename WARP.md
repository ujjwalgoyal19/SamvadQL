# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

Project overview
- Monorepo with three primary apps:
  - apps/api-backend: FastAPI (Python 3.11) backend with async DB connectors, migrations, and LLM/vector integrations
  - apps/web-frontend: React + TypeScript + Vite + Tailwind + shadcn/ui
  - docs: Mintlify-based documentation site with generators
- Orchestrated dev stack via docker-compose (Postgres, Redis, Qdrant, optional OpenSearch, backend, frontend, docs)

Common commands
Root (Docker Compose)
- Start full stack in background
  - docker compose up -d
- Stop stack and remove containers
  - docker compose down
- Follow logs for a specific service (e.g., backend)
  - docker compose logs -f backend

Frontend (apps/web-frontend)
- Install deps (pnpm recommended as per packageManager)
  - pnpm install
- Start dev server
  - pnpm dev
- Build and preview production
  - pnpm build
  - pnpm preview
- Lint and type-check
  - pnpm lint
  - pnpm type-check
- Test all / single
  - pnpm test            # watch mode
  - pnpm test:run        # CI/non-watch
  - pnpm test:run src/components/__tests__/QueryInput.test.tsx
  - pnpm test:run -t "QueryInput"   # name pattern

Backend (apps/api-backend)
- Create venv and install deps (Python 3.11)
  - python -m venv .venv
  - .venv\Scripts\Activate.ps1   # Windows PowerShell
  - pip install -r requirements.txt
- Run API locally (hot reload for development)
  - uvicorn main:app --reload --host 0.0.0.0 --port 8000
- Test all / single
  - pytest
  - pytest apps/api-backend/tests/test_api_v1_integration.py
  - pytest -k "metadata_service"   # name pattern
- Database migrations (custom CLI)
  - python apps/api-backend/migrations/cli.py status
  - python apps/api-backend/migrations/cli.py up
  - python apps/api-backend/migrations/cli.py down <target_version>

Docs (docs)
- Local dev server (Mintlify)
  - npm start
- Generate docs
  - npm run generate-all-docs
  - node scripts/watch-and-generate.js
- With Docker (from repo root)
  - docker compose up -d docs

High-level architecture and flow
- Backend API (FastAPI)
  - Entry: apps/api-backend/main.py defines app, CORS/GZip middleware, and health (/health) and readiness (/ready) probes
  - Versioned routes: apps/api-backend/api/v1.py mounted under /api/v1
    - POST /api/v1/query: Streams incremental QueryResponse chunks (Server-Sent Events via StreamingResponse) for progressive SQL generation and explanations
    - GET /api/v1/tables/{database_id}: Lists tables with pagination/filtering; integrates with metadata service
    - POST /api/v1/validate: Validates SQL (syntax/safety) and estimates cost
  - Auth routes: apps/api-backend/api/auth.py under /api/v1/auth (signup, login, password reset)
  - Services (business logic): services/* (e.g., QueryGenerationService, MetadataExtractionService)
  - Repositories (data access): repositories/* (e.g., UserRepository, UserRoleRepository)
  - Models (Pydantic): models/* (request/response, domain models)
  - Config and DB:
    - core/config settings (env-driven: DATABASE_URL, REDIS_URL, QDRANT_URL, etc.)
    - core/db/* manages async connections and transactions
  - Migrations:
    - apps/api-backend/migrations/sql/*.sql, tracked in schema_migrations
    - apps/api-backend/migrations/migration_manager.py provides apply/rollback/status
    - apps/api-backend/migrations/cli.py wraps operations (status/up/down/create)

- Frontend (React + Vite + TypeScript)
  - Build tooling: Vite (vite, vitest), tsconfig with strict settings and @ path alias to src
  - UI: Tailwind + shadcn/ui components (src/components/ui)
  - Routing: React Router v7 (pages/*)
  - State: Redux Toolkit (store/slices/*)
  - Services: src/services
    - api.ts: REST client (Axios) targeting VITE_API_URL (default http://localhost:8000)
    - websocket.ts: Socket.io client targeting VITE_WS_URL (if used)
    - streamingClient.ts: client-side aggregator for progressive/streamed responses
  - Testing: Vitest + Testing Library, jsdom, setup at src/test/setup.ts

- Documentation (docs)
  - Mintlify site with scripts to generate API/component docs from backend/frontend sources
  - Automation helpers in docs/scripts (generate-api-docs.js, generate-component-docs.js, watch-and-generate.js)

- Docker Compose (docker-compose.yml)
  - Services: frontend, docs, backend, postgres, redis, qdrant, optional opensearch, celery worker and scheduler
  - Environment flows
    - Frontend: VITE_API_URL, VITE_WS_URL, VITE_HMR_PORT
    - Backend: DATABASE_URL, REDIS_URL, QDRANT_URL, OPENSEARCH_URL, OPENAI_API_KEY, ANTHROPIC_API_KEY, LLM_* knobs
  - Data volumes for persistence (postgres_data, redis_data, qdrant_data, opensearch_data)

Essential environment
- Create a .env at repo root for docker-compose (no secrets in this file; use your secret manager to populate values at runtime)
- Frontend: apps/web-frontend/.env
  - VITE_API_URL=http://localhost:8000
  - VITE_WS_URL=http://localhost:8000
- Backend: expects DATABASE_URL, REDIS_URL, vector DB URLs, and LLM provider keys via environment

Key entry points and paths
- Backend app: apps/api-backend/main.py
- API v1 routes: apps/api-backend/api/v1.py
- Auth routes: apps/api-backend/api/auth.py
- Migrations: apps/api-backend/migrations/ (cli.py, migration_manager.py, sql/*.sql)
- Frontend app shell: apps/web-frontend/src/App.tsx and pages/*
- Frontend UI library: apps/web-frontend/src/components/ui
- Docs site: docs/
- DB bootstrap: scripts/init-db.sql

Testing specifics
- Frontend (Vitest)
  - Config: apps/web-frontend/vitest.config.ts (jsdom, setup file, @ alias)
  - Run a focused test
    - pnpm test:run src/components/__tests__/QueryInput.test.tsx
    - pnpm test:run -t "QueryInput"
- Backend (pytest)
  - Async tests supported (pytest-asyncio)
  - Run a focused test
    - pytest apps/api-backend/tests/test_api_v1_integration.py
    - pytest -k "metadata_service"

Conventions and rules (project-specific)
- Service boundaries: keep business logic in services/*; repositories/* should only handle DB access; models/* define Pydantic schemas
- Validation and safety: SQL checked via sqlglot/sqlfluff; destructive ops and performance heuristics flagged in /api/v1/validate
- Streaming: progressive responses emitted as SSE; frontend aggregates via streamingClient
- UI components: prefer shadcn/ui for new components (src/components/ui)

Agent preferences and MCP tools
- Use up-to-date documentation when referencing libraries (Context7 MCP for docs lookup) per project preference
- For UI work, prefer shadcn components and consult shadcn MCP where appropriate

Notes
- Postgres, Redis, and vector DBs (Qdrant or OpenSearch) are part of the default dev stack
- Health endpoints
  - GET /health (liveness)
  - GET /ready (readiness; validates DB/Redis connectivity when configured)
- When running locally without containers, ensure DATABASE_URL/REDIS_URL/etc. match your local services

