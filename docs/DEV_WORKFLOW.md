# Development Workflow Guide

This guide explains the proper development workflow for SamvadQL to ensure fast iteration and minimal rebuild times.

## Table of Contents

1. [Understanding the Architecture](#understanding-the-architecture)
2. [First-Time Setup](#first-time-setup)
3. [Daily Development Workflow](#daily-development-workflow)
4. [When to Rebuild](#when-to-rebuild)
5. [Troubleshooting](#troubleshooting)
6. [Alternative: Hybrid Development](#alternative-hybrid-development)
7. [Performance Tips](#performance-tips)

---

## Understanding the Architecture

### The Key Concept: Volume Mounts = Live Updates

SamvadQL uses **Docker volume mounts** to map your local code into running containers. This means:

- ✅ **Code changes are LIVE** - Save a Python or TypeScript file, and the change is immediately available in the container
- ✅ **No rebuild needed** - FastAPI's `--reload` flag and Vite's HMR detect changes automatically
- ✅ **Fast iteration** - Changes are visible in 1-2 seconds, not 10-15 minutes

### Docker Layer Caching Strategy

Our Dockerfile is structured to maximize cache reuse:

```
┌─────────────────────────────────────┐
│ System Dependencies (rarely change) │  ← Cached unless Dockerfile changes
├─────────────────────────────────────┤
│ Core Requirements (FastAPI, DB)    │  ← Cached unless requirements-core.txt changes
├─────────────────────────────────────┤
│ ML Requirements (LangChain, etc.)  │  ← Cached unless requirements-ml.txt changes
├─────────────────────────────────────┤
│ Dev Requirements (pytest, etc.)    │  ← Cached unless requirements-dev.txt changes
└─────────────────────────────────────┘
           ▼
    [Application Code]  ← NOT in image, mounted via volume!
```

**Why This Matters:**

- Heavy ML libraries (500MB+) are in a separate layer
- If you add a FastAPI dependency, only the core layer rebuilds (2-3 min)
- The ML layer stays cached, saving 8-10 minutes

### Architecture Diagram

```
┌──────────────────┐
│   Your Editor    │
│  (VSCode/PyCharm)│
└────────┬─────────┘
         │ Save file
         ▼
┌─────────────────────────────────────┐
│      Volume Mount (Live Sync)       │
│   ./apps/api-backend:/app           │
└────────┬────────────────────────────┘
         │ File change detected
         ▼
┌─────────────────────────────────────┐
│    Docker Container (Backend)       │
│  ┌──────────────────────────────┐   │
│  │ Uvicorn --reload             │   │
│  │ (auto-restarts on change)    │   │
│  └──────────────────────────────┘   │
└─────────────────────────────────────┘
         │
         ▼ 1-2 seconds later
   Changes live at localhost:8000
```

---

## First-Time Setup

This takes **10-15 minutes** and is only done once.

### Windows (PowerShell)

```powershell
# 1. Enable BuildKit for faster builds
$env:DOCKER_BUILDKIT = "1"
$env:COMPOSE_DOCKER_CLI_BUILD = "1"

# Make it permanent (add to PowerShell profile)
Add-Content $PROFILE "`n`$env:DOCKER_BUILDKIT = '1'"
Add-Content $PROFILE "`$env:COMPOSE_DOCKER_CLI_BUILD = '1'"

# 2. Copy and configure environment
Copy-Item .env.example .env
# Edit .env and add your API keys (OPENAI_API_KEY, etc.)

# 3. Build images (this takes 10-15 minutes on first run)
docker-compose build

# 4. Start services
docker-compose up -d

# 5. Verify everything is running
docker-compose ps
```

**Or use the automated setup script:**

```powershell
.\scripts\dev-setup.ps1
```

### Linux/Mac (Bash)

```bash
# 1. Enable BuildKit
echo 'export DOCKER_BUILDKIT=1' >> ~/.bashrc
echo 'export COMPOSE_DOCKER_CLI_BUILD=1' >> ~/.bashrc
source ~/.bashrc

# 2. Copy and configure environment
cp .env.example .env
# Edit .env and add your API keys

# 3. Build images
docker-compose build

# 4. Start services
docker-compose up -d

# 5. Verify
docker-compose ps
```

**Or use the automated setup script:**

```bash
chmod +x scripts/dev-setup.sh
./scripts/dev-setup.sh
```

---

## Daily Development Workflow

This takes **30 seconds** and should be your normal routine.

### Starting Work

```bash
# Start all services (NO --build flag!)
docker-compose up -d
```

**That's it!** No rebuild needed. The containers start from cached images in ~30 seconds.

### Making Code Changes

1. **Open your editor** (VSCode, PyCharm, etc.)
2. **Edit Python files** in `apps/api-backend/`
3. **Save the file**
4. **Wait 1-2 seconds** - Uvicorn auto-reloads
5. **Test at** `http://localhost:8000`

**No rebuild. No restart. Just save and test.**

### Viewing Logs

```bash
# View backend logs (live tail)
docker-compose logs -f backend

# View all services
docker-compose logs -f

# View specific service
docker-compose logs -f frontend
docker-compose logs -f postgres
```

### Stopping Work

```bash
# Stop all services (keeps data)
docker-compose down

# Stop and remove volumes (fresh start next time)
docker-compose down -v
```

---

## When to Rebuild

**⚠️ ONLY rebuild when these specific files change:**

### 1. Backend Dependencies Changed

**File changed:** `requirements-core.txt`, `requirements-ml.txt`, or `requirements-dev.txt`

```bash
docker-compose build backend
docker-compose up -d
```

**Time:** 2-3 minutes (if only core changed), 10 minutes (if ML changed)

### 2. Frontend Dependencies Changed

**File changed:** `package.json` in `apps/web-frontend/`

```bash
docker-compose build frontend
docker-compose up -d
```

**Time:** 3-5 minutes

### 3. Dockerfile Changed

**File changed:** `Dockerfile` or `Dockerfile.dev` in any service

```bash
docker-compose build <service-name>
docker-compose up -d
```

### 4. System Dependencies Changed

**File changed:** `apt-get install` commands in Dockerfile

```bash
docker-compose build <service-name> --no-cache
docker-compose up -d
```

**Time:** 10-15 minutes (rebuilds everything)

### What Does NOT Require Rebuild

- ✅ Editing `.py` files in `apps/api-backend/`
- ✅ Editing `.tsx` or `.ts` files in `apps/web-frontend/src/`
- ✅ Changing environment variables in `.env` (restart service: `docker-compose restart backend`)
- ✅ Adding new Python files or modules
- ✅ Modifying API endpoints, services, or repositories
- ✅ Changing SQL migrations

**If you're rebuilding for these, you're doing it wrong!**

---

## Troubleshooting

### Problem: Code changes aren't showing up

**Solution 1: Verify volume mount**

```bash
# Check that volume is mounted
docker-compose ps backend

# Should show: ./apps/api-backend:/app
```

**Solution 2: Restart the service**

```bash
docker-compose restart backend
```

**Solution 3: Check uvicorn logs**

```bash
docker-compose logs -f backend

# You should see "Uvicorn running on http://0.0.0.0:8000"
# And "Application startup complete"
```

### Problem: "Build is taking forever"

**Cause:** BuildKit not enabled, or Docker cache corrupted

**Solution:**

```powershell
# Windows: Enable BuildKit
$env:DOCKER_BUILDKIT = "1"
$env:COMPOSE_DOCKER_CLI_BUILD = "1"

# Check Docker is using BuildKit
docker buildx version

# If build is stuck, try without cache
docker-compose build --no-cache backend
```

### Problem: "Error: No space left on device"

**Cause:** Docker images and volumes fill disk

**Solution:**

```bash
# See disk usage
docker system df

# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Nuclear option: remove everything
docker system prune -a --volumes
```

### Problem: "Backend container exits immediately"

**Cause:** Usually a Python import error or missing dependency

**Solution:**

```bash
# View container logs
docker-compose logs backend

# Check for import errors
docker-compose run --rm backend python -c "import main"

# If missing dependency, rebuild
docker-compose build backend
```

### Problem: "Frontend shows white screen"

**Cause:** Vite dev server not running or HMR not working

**Solution:**

```bash
# Check frontend logs
docker-compose logs -f frontend

# Restart frontend
docker-compose restart frontend

# If persists, rebuild
docker-compose build frontend
docker-compose up -d frontend
```

---

## Alternative: Hybrid Development

Some developers prefer running Python **locally** (not in Docker) for instant startup and native debugging. Docker only runs infrastructure services (Postgres, Redis, etc.).

### Pros

- ⚡ **Instant startup** - No container overhead (~2 seconds vs 30 seconds)
- 🐛 **Native debugging** - Use PyCharm or VSCode debugger directly
- 🔥 **Fastest iteration** - Changes reflect immediately
- 💻 **Direct REPL access** - `python` command works instantly

### Cons

- 🔧 **Manual environment setup** - Need to manage Python venv
- 🏗️ **Less production-like** - Local Python version might differ from Docker
- 🌐 **Environment variables** - Need to update URLs to `localhost` instead of service names

### Setup

1. **Create `docker-compose.override.yml`:**

```yaml
version: '3.9'
services:
  # Don't start backend, worker, scheduler
  backend:
    profiles:
      - disabled
  worker:
    profiles:
      - disabled
  scheduler:
    profiles:
      - disabled
  
  # Expose infrastructure ports
  postgres:
    ports:
      - '5432:5432'
  
  redis:
    ports:
      - '6379:6379'
  
  qdrant:
    ports:
      - '6333:6333'
      - '6334:6334'
  
  opensearch:
    ports:
      - '9200:9200'
      - '9600:9600'
```

2. **Start infrastructure services:**

```bash
docker-compose up -d
# Only starts Postgres, Redis, Qdrant, OpenSearch
```

3. **Setup Python locally:**

```powershell
# Windows
cd apps\api-backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-dev.txt
```

```bash
# Linux/Mac
cd apps/api-backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

4. **Update `.env` for local development:**

```env
DATABASE_URL=postgresql://samvadql:password@localhost:5432/samvadql
REDIS_URL=redis://localhost:6379
QDRANT_URL=http://localhost:6333
OPENSEARCH_URL=http://localhost:9200
```

5. **Run backend locally:**

```bash
cd apps/api-backend
uvicorn main:app --reload
```

Access at `http://localhost:8000` - changes reflect instantly!

### Switching Back to Docker

```bash
# Remove override file
rm docker-compose.override.yml

# Start all services
docker-compose up -d
```

---

## Performance Tips

### 1. Use WSL2 on Windows

Docker Desktop with WSL2 backend is **10x faster** than Hyper-V on Windows.

**Setup:**

```powershell
# Install WSL2
wsl --install

# Set WSL2 as default
wsl --set-default-version 2

# In Docker Desktop settings:
# Settings → General → Use WSL2 based engine (enable)
```

**Why:** File I/O operations are 10x faster, making volume mounts much more responsive.

### 2. Allocate More Memory to Docker

**Recommended:** 8GB RAM for Docker

**Setup in Docker Desktop:**

- Settings → Resources → Memory → 8GB

**Why:** Prevents OOM (Out of Memory) errors when building ML dependencies.

### 3. Use `.dockerignore` Properly

Ensure your `.dockerignore` excludes:

```
**/__pycache__
**/*.pyc
**/.pytest_cache
**/.venv
**/node_modules
**/.git
```

**Why:** Reduces Docker context size from 500MB to 50MB, speeding up builds.

### 4. Prune Docker Regularly

```bash
# Weekly maintenance
docker system prune -a --volumes

# This removes:
# - Stopped containers
# - Unused networks
# - Dangling images
# - Unused volumes
```

**Why:** Frees disk space and prevents "no space left" errors.

### 5. Use BuildKit Cache Mounts

Already configured in `Dockerfile.dev`, but ensure BuildKit is enabled:

```powershell
$env:DOCKER_BUILDKIT = "1"
```

**Why:** BuildKit caches pip downloads across builds, saving bandwidth and time.

### 6. Pin Base Image Versions

Use `python:3.11` (not `python:3.11-slim` or `python:latest`) in dev.

**Why:** Full Python image includes build tools, avoiding reinstalls. Pinned version prevents unexpected changes.

---

## Summary: The Golden Rules

1. **🚫 NEVER use `docker-compose up --build`** - Volume mounts make rebuilds unnecessary
2. **✅ Use `docker-compose up -d`** for daily work (30 seconds)
3. **🔧 Only rebuild when dependencies change** (2-15 minutes, rare)
4. **⚡ Enable BuildKit** for 3-5x faster builds
5. **📝 Read logs with `docker-compose logs -f backend`** to understand what's happening
6. **🐛 Use debugpy on port 5679** for breakpoint debugging (already configured)
7. **🔄 Restart, don't rebuild** when troubleshooting: `docker-compose restart backend`

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────┐
│                   DAILY DEVELOPMENT                          │
├─────────────────────────────────────────────────────────────┤
│ Start services    → docker-compose up -d                    │
│ View logs         → docker-compose logs -f backend          │
│ Edit code         → Save file in editor (auto-reloads!)     │
│ Stop services     → docker-compose down                     │
├─────────────────────────────────────────────────────────────┤
│                   WHEN THINGS BREAK                          │
├─────────────────────────────────────────────────────────────┤
│ Restart service   → docker-compose restart backend          │
│ Rebuild service   → docker-compose build backend            │
│ Fresh start       → docker-compose down -v                  │
│                     docker-compose up -d                     │
│ Nuclear option    → docker-compose down -v                  │
│                     docker-compose build --no-cache          │
│                     docker-compose up -d                     │
└─────────────────────────────────────────────────────────────┘
```

**Need help?** Check the troubleshooting section or ask in team chat!
