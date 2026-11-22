# HDIP — Developer & Deployment Guide

## Local Development Setup

### Prerequisites
- Python 3.11+
- Node.js 20+
- Docker Desktop 24+
- Git

### 1. Clone Repository
```bash
git clone <repository-url>
cd "PROJECT 1"
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv

# Activate venv
# Windows:   venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

pip install -e .
```

### 3. Frontend Setup
```bash
cd frontend
npm install
```

### 4. Environment Configuration
```bash
cp .env.example .env
# Edit .env with your values
```

### 5. Start Development Servers

**Terminal 1 — Backend:**
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
```

Frontend dev server: http://localhost:5173
API: http://localhost:8000
API Docs: http://localhost:8000/api/v1/docs

---

## Docker Production Deployment

### Prerequisites
- Docker Desktop or Docker Engine + Compose Plugin
- `.env` file configured from `.env.example`

### Step-by-Step

```bash
# 1. Configure environment
cp .env.example .env
# Edit SECRET_KEY, POSTGRES_PASSWORD, CORS_ORIGINS

# 2. Build frontend
cd frontend && npm ci && npm run build && cd ..

# 3. Build and start all services
docker compose up --build -d

# 4. Initialize database
docker compose exec api python scripts/init_db.py

# 5. Seed data (optional for demo)
docker compose exec api python scripts/seed_data.py

# 6. Train ML models
docker compose exec api python scripts/init_models.py

# 7. Verify health
curl http://localhost/health/liveness
curl http://localhost/health/readiness
```

### Service Ports

| Service | Internal Port | External Port |
|---|---|---|
| Nginx (HTTP) | 80 | 80 (configurable via NGINX_HTTP_PORT) |
| FastAPI | 8000 | Not exposed directly |
| PostgreSQL | 5432 | 5432 (configurable) |
| Redis | 6379 | 6379 (configurable) |

---

## Makefile Reference

```bash
make help              # Show all available targets
make setup             # Create Python virtualenv
make install           # Install all dependencies
make init-db           # Initialize DB schema
make seed              # Generate synthetic data
make train             # Train all ML models
make dev-backend       # Start API with hot reload
make dev-frontend      # Start Vite dev server
make test              # Run full test suite
make test-cov          # Run tests + HTML coverage
make lint              # Ruff linting
make format            # Ruff auto-formatting
make type-check        # mypy type checking
make build-frontend    # Build production frontend
make docker-up         # Start all Docker services
make docker-down       # Stop all services
make docker-logs       # Stream API logs
make clean             # Remove build artifacts
```

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `SECRET_KEY` | YES | — | JWT signing secret (256-bit random) |
| `DATABASE_URL` | YES | — | PostgreSQL async URL |
| `REDIS_URL` | YES | — | Redis connection URL |
| `DEBUG` | No | `false` | Enable debug logging and hot-reload |
| `POSTGRES_USER` | YES | `hip_user` | PostgreSQL user |
| `POSTGRES_PASSWORD` | YES | — | PostgreSQL password |
| `POSTGRES_DB` | No | `hip_db` | PostgreSQL database name |
| `CORS_ORIGINS` | YES | `http://localhost` | Comma-separated allowed origins |
| `NGINX_HTTP_PORT` | No | `80` | Nginx HTTP port mapping |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `60` | JWT access token TTL |

---

## Generating a Secure SECRET_KEY

```bash
# Python (recommended)
python -c "import secrets; print(secrets.token_hex(32))"

# OpenSSL
openssl rand -hex 32
```

---

## Running Tests

```bash
cd backend

# Full test suite
pytest tests/ -v

# With coverage
pytest tests/ --cov=app --cov-report=term-missing

# HTML coverage report
pytest tests/ --cov=app --cov-report=html:htmlcov
open htmlcov/index.html  # Mac
start htmlcov/index.html # Windows
```

---

## Monitoring & Operations

### Health Check Endpoints

```bash
# Liveness — is the container running?
GET /health/liveness

# Readiness — is the database reachable?
GET /health/readiness
```

### View Logs

```bash
# All services
docker compose logs -f

# API only
docker compose logs -f api

# Worker only
docker compose logs -f celery-worker
```

### Database Access

```bash
docker compose exec postgres psql -U hip_user -d hip_db
```

### Redis Inspection

```bash
docker compose exec redis redis-cli
> KEYS *
> INFO server
```

---

## CI/CD Pipeline

The GitHub Actions pipeline (`.github/workflows/ci.yml`) runs on push to `main` and `develop`:

1. **Backend Lint** → `ruff check`
2. **Backend Type Check** → `mypy`
3. **Backend Tests** → `pytest` with PostgreSQL + Redis services
4. **Coverage Upload** → Codecov
5. **Frontend Type Check** → `tsc --noEmit`
6. **Frontend Build** → `npm run build`
7. **Docker Build** → Multi-stage Dockerfile validation (main branch only)

---

## Scaling Considerations

| Component | Scaling Approach |
|---|---|
| FastAPI API | Increase `--workers` in Dockerfile CMD, or add Gunicorn |
| Celery Workers | Add worker containers in docker-compose, or use Kubernetes |
| PostgreSQL | Add read replicas for analytics queries |
| Redis | Use Redis Cluster for high-throughput queueing |
| ML Inference | Move models to dedicated inference containers (TorchServe/BentoML) |
| Frontend | CDN deployment for static assets (Cloudflare, Vercel) |
