# Use Python 3.12 slim image
FROM python:3.12-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=1.6.1

# Install system dependencies and Poetry
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    make \
    curl \
    && pip install poetry==$POETRY_VERSION \
    && rm -rf /var/lib/apt/lists/*

# Configure Poetry
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VENV_IN_PROJECT=1 \
    POETRY_CACHE_DIR=/app/.cache

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set work directory
WORKDIR /app

# Copy Poetry files
COPY pyproject.toml poetry.lock* ./

# Install dependencies
RUN poetry install --only=main

# Copy application code
COPY Makefile ./
COPY app/ ./app/
COPY alembic.ini ./
COPY migrations/ ./migrations/

# Create cache directory and change ownership
RUN mkdir -p /app/.cache && chown -R appuser:appuser /app

USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application using Makefile
CMD ["make", "run-docker"]