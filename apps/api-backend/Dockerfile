# syntax=docker/dockerfile:1.4
FROM python:3.11-slim

# Build argument to control dev dependency installation
ARG INSTALL_DEV=false

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first to maximize layer cache reuse
COPY requirements.txt requirements.txt
COPY requirements-dev.txt requirements-dev.txt

# Use BuildKit cache mount for pip to speed repeated installs during image rebuilds.
# When building locally enable BuildKit: $env:DOCKER_BUILDKIT = "1" (PowerShell)
RUN --mount=type=cache,id=pipcache,target=/root/.cache/pip \
    pip install --upgrade pip && \
    pip install -r requirements.txt && \
    if [ "$INSTALL_DEV" = "true" ]; then pip install -r requirements-dev.txt; fi

# Copy application code after dependencies
COPY . .

# Create non-root user and set ownership
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

EXPOSE 8000

# Default command
CMD ["sh", "-c", "python /tmp/debugpy --wait-for-client --listen 0.0.0.0:5679 -m uvicorn main:app --host 0.0.0.0 --port 8000"]