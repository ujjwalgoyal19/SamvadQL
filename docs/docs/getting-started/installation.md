# Installation Guide

Get SamvadQL up and running on your local machine in just a few minutes.

## Prerequisites

Before installing SamvadQL, make sure you have the following installed:

- **Docker** and **Docker Compose** (recommended for development)
- **Node.js** 18+ and **pnpm** (for frontend development)
- **Python** 3.11+ and **pip** (for backend development)
- **PostgreSQL** 15+ (if not using Docker)
- **Redis** 7+ (if not using Docker)

## Quick Start with Docker

The fastest way to get SamvadQL running is with Docker Compose:

1. **Clone the repository**

   ```bash
   git clone https://github.com/your-org/samvadql.git
   cd samvadql
   ```

2. **Copy environment configuration**

   ```bash
   cp .env.example .env
   ```

3. **Start all services**

   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Manual Installation

If you prefer to run services individually:

### Backend Setup

1. **Navigate to backend directory**

   ```bash
   cd apps/api-backend
   ```

2. **Create virtual environment**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up database**

   ```bash
   # Make sure PostgreSQL is running
   python migrations/cli.py up
   ```

5. **Start the backend server**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Setup

1. **Navigate to frontend directory**

   ```bash
   cd apps/web-frontend
   ```

2. **Install dependencies**

   ```bash
   pnpm install
   ```

3. **Start development server**
   ```bash
   pnpm dev
   ```

### Background Services

1. **Start Redis** (required for background jobs)

   ```bash
   redis-server
   ```

2. **Start Celery worker** (for background processing)
   ```bash
   cd apps/api-backend
   celery -A worker worker --loglevel=info
   ```

## Environment Configuration

Configure your environment by editing the `.env` file:

```bash
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/samvadql
REDIS_URL=redis://localhost:6379/0

# LLM Configuration
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key

# Vector Database
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your-qdrant-api-key

# Application Settings
SECRET_KEY=your-secret-key-here
DEBUG=true
CORS_ORIGINS=http://localhost:3000

# Frontend Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

## Verification

After installation, verify everything is working:

1. **Check backend health**

   ```bash
   curl http://localhost:8000/health
   ```

2. **Check frontend**
   Open http://localhost:3000 in your browser

3. **Test API endpoints**
   Visit http://localhost:8000/docs for interactive API documentation

## Troubleshooting

### Common Issues

**Port conflicts**

- Change ports in `docker-compose.yml` or `.env` file
- Make sure ports 3000, 8000, 5432, and 6379 are available

**Database connection errors**

- Verify PostgreSQL is running and accessible
- Check database credentials in `.env` file
- Run migrations: `python migrations/cli.py up`

**Frontend build errors**

- Clear node_modules: `rm -rf node_modules && pnpm install`
- Check Node.js version: `node --version` (should be 18+)

**Backend import errors**

- Activate virtual environment: `source .venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`

### Getting Help

- 📖 Check the [troubleshooting guide](../development/troubleshooting.md)
- 🐛 [Report issues](https://github.com/your-org/samvadql/issues)
- 💬 [Join discussions](https://github.com/your-org/samvadql/discussions)

## Next Steps

- [Quick Start Guide](./quick-start.md) - Try your first query
- [Configuration](./configuration.md) - Customize your setup
- [Development Setup](../development/setup.md) - Set up for development
