FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    CONFIG_DIR=/app/config \
    DATA_DIR=/app/data

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy project files
COPY pyproject.toml README.md ./
COPY pentest_agent ./pentest_agent
COPY docker_entrypoint.sh ./

# Make entrypoint executable
RUN chmod +x ./docker_entrypoint.sh

# Install dependencies (including optional local LLM support)
RUN pip install --upgrade pip setuptools wheel && \
    pip install -e . && \
    pip install -e ".[local]" && \
    pip install fastapi uvicorn

# Create necessary directories for volumes
RUN mkdir -p /app/config /app/data /app/sessions /app/models /app/kb-data

# Expose API port
EXPOSE 8080

# Health check: poll daemon health endpoint
HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:47291/health || exit 1

# Run entrypoint script
ENTRYPOINT ["/app/docker_entrypoint.sh"]
