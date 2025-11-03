# 🚀 SamvadQL - Quick Start (5 Minutes)

## Prerequisites ✅

- Node.js 24.6.0
- Python 3.11.7
- Docker 28.3.3
- pnpm 10.13.1 (installed)

## Start Everything

### Step 1: Start Infrastructure (Terminal 1)

```bash
cd c:\Users\accou\Documents\products\SamvadQL
docker-compose up -d
# Wait 5 seconds for services to be ready
docker-compose ps  # Verify both are "healthy"
```

### Step 2: Start Applications (Terminal 2)

```bash
cd c:\Users\accou\Documents\products\SamvadQL
pnpm dev
```

**Wait for output**:

```
✔ Frontend running at http://localhost:3000
✔ Backend running at http://localhost:8000
```

### Step 3: Verify Everything Works

**Frontend** - Open browser:

```
http://localhost:3000
```

Should see React app loading with Vite

**Backend API** - Open browser:

```
http://localhost:8000/docs
```

Should see Swagger UI with API endpoints

**PostgreSQL** - Test connection:

```bash
# From new terminal
psql postgresql://postgres:postgres@localhost:5432/samvadql
# Should connect successfully
```

## Stop Everything

```bash
# Stop applications: Ctrl+C in terminal 2
# Stop infrastructure:
docker-compose down
```

## Common Commands

```bash
# View backend logs
docker-compose logs -f postgres

# View frontend in VS Code browser
# Open http://localhost:3000 in VS Code Simple Browser

# Rebuild dependencies
rm -r node_modules pnpm-lock.yaml
pnpm install

# Reset database
docker-compose down -v
docker-compose up -d
```

## File Locations

| Component | Location |
|-----------|----------|
| Frontend | `apps/web-frontend/src/` |
| Backend | `apps/api-backend/` |
| API Routes | `apps/api-backend/api/v1.py` |
| Models | `apps/api-backend/models/` |
| Config | `apps/api-backend/core/config.py` |
| Environment | `.env.example` → `.env` |

## Environment Setup

1. Copy `.env.example` to `.env`:

```bash
copy .env.example .env
```

2. Add credentials:

```
PINECONE_API_KEY=your_key
OPENAI_API_KEY=your_key
```

3. Restart applications

## Status Dashboard

| Service | Port | Status | URL |
|---------|------|--------|-----|
| Frontend | 3000 | ✅ | <http://localhost:3000> |
| Backend | 8000 | ✅ | <http://localhost:8000> |
| API Docs | 8000 | ✅ | <http://localhost:8000/docs> |
| PostgreSQL | 5432 | ✅ | localhost |
| Redis | 6379 | ✅ | localhost |

## Next Steps

1. ✅ **Running** - Everything should be operational now
2. 📝 **Configure** - Add API keys to `.env`
3. 🔌 **Integrate** - Connect to Pinecone and LLM APIs
4. 🧪 **Test** - Run backend tests: `cd apps/api-backend && pytest`
5. 🚢 **Deploy** - Use `docker-compose.prod.yml` for production

## Troubleshooting

**Port in use?**

```bash
# Find process on port
netstat -ano | findstr :3000
# Kill it
taskkill /PID <PID> /F
```

**Module not found?**

```bash
# Reinstall
cd apps/api-backend
python install_deps.py
```

**Docker not running?**

```bash
# Start Docker Desktop or...
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
```

---

**See DEPLOYMENT_READY.md for detailed guide**
