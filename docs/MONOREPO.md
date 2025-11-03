# Monorepo Guide

This project uses **Turborepo + pnpm workspaces** for managing a TypeScript/React frontend and Python backend together as a unified monorepo.

## Why Monorepo?

- **Atomic commits**: Frontend and backend changes in a single PR
- **Shared code**: Common types and utilities available to all apps
- **Consistent tooling**: Single build system, linting, testing
- **Dependency management**: pnpm workspaces with efficient hoisting

## Structure

```
SamvadQL/
├── apps/                    # Applications
│   ├── web-frontend/       # React + TypeScript frontend
│   │   ├── src/
│   │   ├── package.json    # @samvadql/web
│   │   └── vite.config.ts
│   └── api-backend/        # FastAPI backend
│       ├── main.py
│       ├── package.json    # @samvadql/api (proxy for turbo)
│       └── pyproject.toml  # Poetry dependencies
├── packages/                # Shared libraries (future)
├── package.json            # Root monorepo config
├── pnpm-workspace.yaml     # pnpm workspace definition
├── turbo.json              # Turborepo config
└── poetry.lock             # Python lockfile (if tracking in git)
```

## Turborepo

### What Turborepo Does

- **Task orchestration**: Runs tasks (build, dev, lint, test) in the right order
- **Caching**: Skips tasks whose inputs haven't changed
- **Parallelization**: Runs independent tasks in parallel
- **Remote caching**: Optional team cache via Vercel

### Task Pipeline

Defined in `turbo.json`:

- `build`: Builds frontend and backend. Depends on `^build` (dependencies build first)
- `dev`: Runs dev servers. No caching, persistent task
- `lint`: Lints code. Caches based on file changes
- `test`: Runs tests. Caches coverage output
- `type-check`: Type checking with TypeScript/mypy
- `clean`: Removes build artifacts

### Running Tasks

```bash
# Run all dev servers
pnpm dev

# Run build for all apps
pnpm build

# Run lint on all apps
pnpm lint

# Run tests on all apps
pnpm test

# Run type checking
pnpm type-check

# Clean all build artifacts
pnpm clean

# Run task for specific app (filter)
turbo run build --filter=@samvadql/web

# Run task for backend only
turbo run dev --filter=@samvadql/api
```

## pnpm Workspaces

### Workspace Protocol

Internal dependencies use the `workspace:*` protocol in package.json:

```json
{
  "dependencies": {
    "@samvadql/shared-types": "workspace:*"
  }
}
```

This creates a symlink during development and resolves to the exact version at build time.

### Installing Dependencies

```bash
# Install all dependencies across all apps
pnpm install

# Add to specific app
cd apps/web-frontend
pnpm add lodash

# Add to backend (Python via Poetry, not pnpm)
cd apps/api-backend
poetry add requests

# Add to root (devDependencies for monorepo tools)
cd ../..
pnpm add -D turbo
```

### Monorepo Commands from Root

```bash
# Run in all apps
pnpm -r lint

# Run in specific app
pnpm -F @samvadql/web build

# List all packages
pnpm list --depth=-1
```

## Python + Node.js Integration

The backend uses **Poetry** for Python dependency management, but has a `package.json` to integrate with Turborepo.

### Backend package.json

Proxy scripts that call Python tools:

```json
{
  "name": "@samvadql/api",
  "scripts": {
    "dev": "uvicorn main:app --reload",
    "build": "echo 'Python build complete'",
    "lint": "ruff check . && ruff format --check .",
    "test": "pytest",
    "type-check": "mypy ."
  }
}
```

Turborepo sees these scripts and orchestrates Python tasks alongside JavaScript tasks.

### Setting Up Backend

```bash
cd apps/api-backend

# Install Python dependencies (requires Poetry)
poetry install

# Add new dependency
poetry add requests

# Add dev dependency
poetry add -D pytest

# Run tests
poetry run pytest

# Run linting
poetry run ruff check .
```

## Adding New Packages

### Add a Shared UI Component Library

1. **Create package structure**:

```bash
mkdir packages/ui-components
cd packages/ui-components
npm init -y
```

2. **Update package.json**:

```json
{
  "name": "@samvadql/ui-components",
  "version": "1.0.0",
  "main": "./dist/index.ts",
  "scripts": {
    "build": "tsc",
    "dev": "tsc --watch"
  }
}
```

3. **Update root `pnpm-workspace.yaml`**:

```yaml
packages:
  - 'apps/*'
  - 'packages/*'
```

4. **Use in frontend**:

```json
{
  "dependencies": {
    "@samvadql/ui-components": "workspace:*"
  }
}
```

### Add a Python Utility Package

1. **Create package**:

```bash
mkdir packages/python-utils
cd packages/python-utils
poetry init
```

2. **Structure**:

```
packages/python-utils/
├── samvadql_utils/
│   ├── __init__.py
│   └── helpers.py
├── pyproject.toml
└── poetry.lock
```

3. **Use in backend** - Add to `apps/api-backend/pyproject.toml`:

```toml
dependencies = [
  "samvadql_utils = { path = '../../packages/python-utils' }"
]
```

## Best Practices

### Package Naming

- Frontend: `@samvadql/web`, `@samvadql/ui-components`
- Backend: `@samvadql/api`, `@samvadql/auth`
- Python utilities: Standard pip names in scope

### Dependency Isolation

- **Frontend** only depends on Node/JavaScript packages
- **Backend** only depends on Python packages via Poetry
- **Shared** code lives in `packages/` (e.g., type definitions)

### Keep Packages Focused

Each app should:

- Have a single clear responsibility
- Export a clean public API
- Be independently testable
- Have its own documentation

### Commit Guidelines

When making changes:

- Commit atomic changes to related apps together
- Include package.json, pyproject.toml, lock files
- Reference monorepo impacts in commit messages

## Troubleshooting

### "Package not found"

```bash
# Regenerate lockfiles
pnpm install

# Check workspace structure
pnpm list --depth=-1
```

### Tasks not running

```bash
# Check task definition in turbo.json
cat turbo.json

# Run with verbose output
turbo run build --verbose
```

### Python dependencies not installing

```bash
cd apps/api-backend
poetry install --no-cache

# Clear cache if needed
rm -rf ~/.cache/pypoetry
```

### Circular dependencies

Check `packages/*/package.json` for interdependencies. Use dependency graph:

```bash
turbo run build --dry  # See task order
```

## Resources

- [Turborepo Documentation](https://turbo.build)
- [pnpm Workspaces](https://pnpm.io/workspaces)
- [Poetry Documentation](https://python-poetry.org)
