# ── Stage 1: Dependency Builder ──────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .

# Install into a local prefix for clean copy into runtime stage
RUN pip install --no-cache-dir --prefix=/install .


# ── Stage 2: Production Runtime ───────────────────────────────────────────────
FROM python:3.11-slim AS runtime

# Metadata
LABEL maintainer="HDIP Engineering <engineering@hdip.health>"
LABEL description="Hospital Decision Intelligence Platform — Production API"
LABEL version="1.0.0"

# Minimal runtime OS dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --no-create-home --shell /bin/false hdip

WORKDIR /app

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY . .

# Create storage directory and set ownership
RUN mkdir -p /app/storage && chown -R hdip:hdip /app

# Run as non-root user
USER hdip

EXPOSE 8000

# Healthcheck for Docker engine
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8000/health/liveness || exit 1

# Production: multiple Uvicorn workers via Gunicorn orchestration
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--workers", "2", "--loop", "uvloop", "--http", "h11", \
     "--access-log", "--log-level", "info"]
