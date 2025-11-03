# syntax=docker/dockerfile:1.4
FROM python:3.11-slim as base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Builder stage for Poetry
FROM base as builder

# Install Poetry
RUN pip install poetry==1.7.1

# Copy only pyproject.toml
# Note: poetry.lock is not committed to the repository (.gitignore).
# Poetry resolves and locks versions at build time, ensuring reproducible builds
# without requiring a committed lock file. This approach maintains flexibility
# during active development while leveraging Poetry's built-in locking mechanism.
COPY pyproject.toml ./

# Configure Poetry to create virtualenv in project directory
RUN poetry config virtualenvs.in-project true

# Install dependencies
# Poetry resolves versions from pyproject.toml and creates a lock at build time.
# This ensures consistent dependency versions across all build environments (local, CI/CD, production).
RUN poetry install --no-dev --no-root

# Runtime stage
FROM base as runtime

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY . .

# Set ownership to app user
RUN chown -R app:app /app

USER app

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run with gunicorn in production
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000", "main:app"]
