"""
Main FastAPI application entry point for SamvadQL.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import logging

from core.config import settings
from api.v1 import router as v1_router
from api.auth import router as auth_router
from api.permissions import router as permissions_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print("Starting SamvadQL backend...")
    yield
    # Shutdown
    print("Shutting down SamvadQL backend...")


# Create FastAPI application
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    debug=settings.debug,
    lifespan=lifespan,
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include API routers
app.include_router(v1_router)
app.include_router(auth_router)
app.include_router(permissions_router)


# Health / readiness endpoint
@app.get("/health")
async def health_check():
    """Lightweight liveness probe (no external dependencies)."""
    return {"status": "ok", "service": "samvadql-backend"}


@app.get("/ready")
async def readiness_check():
    """Readiness probe that validates critical dependencies.

    Returns:
        JSON containing component status (ok / error) and overall ready flag.
    """
    components = {}
    overall_ok = True

    # Database connectivity (optional import to avoid circulars at startup)
    try:
        from core.config import settings as _settings
        import asyncpg  # lightweight check without pulling full ORM
        dsn = _settings.database_url
        # Only attempt if postgres URL pattern
        if dsn and dsn.startswith("postgresql"):
            conn = await asyncpg.connect(dsn)
            await conn.execute("SELECT 1")
            await conn.close()
        components["database"] = "ok"
    except Exception as e:  # pragma: no cover - defensive
        components["database"] = f"error: {e}"; overall_ok = False

    # Redis connectivity
    try:
        import redis.asyncio as redis  # type: ignore
        from core.config import settings as _settings2
        if _settings2.redis_url:
            r = redis.from_url(_settings2.redis_url, decode_responses=True)
            await r.ping()
        components["redis"] = "ok"
    except Exception as e:  # pragma: no cover
        components["redis"] = f"error: {e}"; overall_ok = False

    status_code = 200 if overall_ok else 503
    return {"status": "ok" if overall_ok else "degraded", "ready": overall_ok, "components": components}, status_code

