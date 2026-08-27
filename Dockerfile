# ==============================================================================
# ZeroSQL AI V2 — Production Backend Container
# Multi-stage, non-root, Python 3.11-slim container with connection pooling
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Build & Dependency Installation
# ------------------------------------------------------------------------------
FROM python:3.11-slim AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ------------------------------------------------------------------------------
# Stage 2: Minimal Production Runtime
# ------------------------------------------------------------------------------
FROM python:3.11-slim AS runner

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH=/home/zerosql/.local/bin:$PATH \
    PORT=8000

# Create dedicated unprivileged system user and group
RUN groupadd -g 1001 zerosql && \
    useradd -u 1001 -g zerosql -s /bin/bash -m zerosql

# Copy installed Python packages from builder stage
COPY --from=builder /root/.local /home/zerosql/.local

# Copy only required runtime application files
COPY --chown=zerosql:zerosql backend/ /app/backend/
COPY --chown=zerosql:zerosql database.py /app/database.py
COPY --chown=zerosql:zerosql agents.py /app/agents.py
COPY --chown=zerosql:zerosql sql_validator.py /app/sql_validator.py

# Create writable dataset upload directory
RUN mkdir -p /app/data/uploads && \
    chown -R zerosql:zerosql /app/data

USER zerosql

EXPOSE 8000

# Container Healthcheck using standard library urllib (no curl dependency required)
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python3 -c "import urllib.request, os; port=os.environ.get('PORT', '8000'); urllib.request.urlopen(f'http://localhost:{port}/health')" || exit 1

# Production startup using exec to forward OS signals directly to Uvicorn for graceful pool drainage
CMD ["sh", "-c", "exec uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2 --proxy-headers --forwarded-allow-ips '*'"]
