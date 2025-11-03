# Development Setup

This guide will help you set up a complete development environment for SamvadQL, including the automated documentation system.

## Prerequisites

Before starting, ensure you have:

- **Node.js** 18+ and **pnpm** (or npm)
- **Python** 3.11+ and **pip**
- **Docker** and **Docker Compose**
- **Git** for version control
- **VS Code** (recommended) with Python and TypeScript extensions

## Quick Setup

### 1. Clone and Setup

```bash
git clone https://github.com/your-org/samvadql.git
cd samvadql
cp .env.example .env
```

### 2. Start Documentation System

```bash
# Linux/Mac
./scripts/dev-docs.sh

# Windows
scripts\dev-docs.bat

# Or manually
cd docs
npm install
npm run generate-all-docs
npm start
```

### 3. Start Development Environment

```bash
# Start all services with Docker
docker-compose up -d

# Or start services individually (see below)
```

## Individual Service Setup

### Backend Development

1. **Navigate to backend directory**

   ```bash
   cd apps/api-backend
   ```

2. **Create virtual environment**

   ```bash
   python -m venv .venv

   # Activate (Linux/Mac)
   source .venv/bin/activate

   # Activate (Windows)
   .venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   cd apps/api-backend
   poetry install
   cd ../..
   ```

4. **Set up database**

   ```bash
   # Start PostgreSQL (if not using Docker)
   # Then run migrations
   python migrations/cli.py up
   ```

5. **Start development server**

   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Development

1. **Navigate to frontend directory**

   ```bash
   cd apps/web-frontend
   ```

2. **Install dependencies**

   ```bash
   pnpm install
   # or: npm install
   ```

3. **Start development server**

   ```bash
   pnpm dev
   # or: npm run dev
   ```

### Documentation Development

1. **Navigate to docs directory**

   ```bash
   cd docs
   ```

2. **Install dependencies**

   ```bash
   npm install
   ```

3. **Generate documentation**

   ```bash
   npm run generate-all-docs
   ```

4. **Start documentation server**

   ```bash
   npm start
   ```

5. **Enable auto-generation** (in another terminal)

   ```bash
   node scripts/watch-and-generate.js
   ```

## Development Workflow

### Daily Development

1. **Start documentation system**

   ```bash
   ./scripts/dev-docs.sh  # Starts docs server + file watcher
   ```

2. **Start main application**

   ```bash
   docker-compose up -d  # All services
   # OR start individual services as needed
   ```

3. **Make changes to code**

   - Backend changes in `apps/api-backend/`
   - Frontend changes in `apps/web-frontend/src/`
   - Documentation automatically updates

4. **View documentation**
   - Visit <http://localhost:3000>
   - API docs update automatically from Python code
   - Component docs update from React components

### Documentation-Driven Development

The documentation system supports a documentation-first approach:

1. **Write documentation first**

   - Create API documentation in `docs/docs/api/`
   - Define component interfaces in `docs/docs/components/`

2. **Generate code stubs**

   - Use documentation as specification
   - Implement features to match documented APIs

3. **Auto-update documentation**
   - File watcher updates docs as you implement
   - Ensures documentation stays in sync

## Environment Configuration

### Development Environment Variables

Create a `.env` file with:

```bash
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/samvadql
REDIS_URL=redis://localhost:6379/0

# LLM Services
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key

# Vector Database
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your-qdrant-key

# Application
SECRET_KEY=your-secret-key-for-development
DEBUG=true
CORS_ORIGINS=http://localhost:3000

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### Docker Compose Services

The `docker-compose.yml` includes:

- **PostgreSQL**: Primary database
- **Redis**: Caching and job queue
- **Qdrant**: Vector database for semantic search
- **Backend**: FastAPI application
- **Frontend**: Next.js application
- **Worker**: Celery background worker

## IDE Setup

### VS Code Configuration

Recommended extensions:

- Python
- TypeScript and JavaScript
- Docker
- GitLens
- Thunder Client (for API testing)

Workspace settings (`.vscode/settings.json`):

```json
{
  "python.defaultInterpreterPath": "./apps/api-backend/.venv/bin/python",
  "typescript.preferences.importModuleSpecifier": "relative",
  "editor.formatOnSave": true,
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true
}
```

### Debugging Configuration

Backend debugging (`.vscode/launch.json`):

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/apps/api-backend/.venv/bin/uvicorn",
      "args": ["main:app", "--reload"],
      "cwd": "${workspaceFolder}/apps/api-backend",
      "env": {
        "PYTHONPATH": "${workspaceFolder}/apps/api-backend"
      }
    }
  ]
}
```

## Testing Setup

### Backend Testing

```bash
cd apps/api-backend

# Run all tests
python test_runner.py

# Run specific test file
python -m pytest tests/test_models.py -v

# Run with coverage
python -m pytest --cov=. tests/
```

### Frontend Testing

```bash
cd apps/web-frontend

# Run tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage
```

### Documentation Testing

```bash
cd docs

# Build documentation (tests for errors)
npm run build

# Test documentation generation
npm run generate-all-docs
```

## Troubleshooting

### Common Issues

**Port conflicts**

- Change ports in `docker-compose.yml`
- Check what's running on ports 3000, 8000, 5432, 6379

**Database connection errors**

- Verify PostgreSQL is running
- Check connection string in `.env`
- Run migrations: `python migrations/cli.py up`

**Documentation generation fails**

- Check Node.js version (18+ required)
- Verify source files have proper docstrings/comments
- Run generation scripts manually to see errors

**Frontend build errors**

- Clear node_modules: `rm -rf node_modules && npm install`
- Check TypeScript errors: `npm run type-check`

**Backend import errors**

- Activate virtual environment
- Check PYTHONPATH is set correctly
- Reinstall dependencies: `cd apps/api-backend && poetry install`

### Getting Help

1. **Check documentation**: <http://localhost:3000> (after starting docs)
2. **Review logs**: `docker-compose logs -f [service-name]`
3. **Check issues**: GitHub issues for known problems
4. **Ask questions**: GitHub discussions for help

## Next Steps

- [Backend Development](./backend-dev.md) - Backend-specific development guide
- [Frontend Development](./frontend-dev.md) - Frontend-specific development guide
- [Testing Guide](./testing.md) - Comprehensive testing strategies
- [Deployment](./deployment.md) - Production deployment guide
