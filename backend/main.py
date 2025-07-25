"""
Main FastAPI application entry point for SamvadQL.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import uvicorn

from core.config import settings
from models import QueryRequest


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


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "samvadql-backend"}


# API v1 routes
@app.get("/api/v1/status")
async def get_status():
    """Get API status."""
    return {
        "status": "running",
        "version": settings.api_version,
        "environment": "development" if settings.debug else "production",
    }


# Placeholder endpoints - will be implemented in later tasks
@app.post("/api/v1/query")
async def submit_query(request: QueryRequest):
    """Submit natural language query for SQL generation."""
    # Placeholder implementation
    raise HTTPException(status_code=501, detail="Query generation not implemented yet")


@app.get("/api/v1/tables/{database_id}")
async def get_tables(database_id: str):
    """Get available tables for a database."""
    # Placeholder implementation
    raise HTTPException(status_code=501, detail="Table listing not implemented yet")


@app.post("/api/v1/validate")
async def validate_sql(sql: str, database_id: str):
    """Validate SQL query."""
    # Placeholder implementation
    raise HTTPException(status_code=501, detail="SQL validation not implemented yet")


@app.post("/api/v1/feedback")
async def submit_feedback(feedback: dict):
    """Submit user feedback."""
    # Placeholder implementation
    raise HTTPException(
        status_code=501, detail="Feedback submission not implemented yet"
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app", host="0.0.0.0", port=8000, reload=settings.debug, log_level="info"
    )
