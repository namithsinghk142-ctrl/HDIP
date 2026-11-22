# Hospital Decision Intelligence Platform (HDIP)

> **Enterprise AI-Powered Decision Intelligence Platform for Hospital Operations**
> An end-to-end platform that transforms raw hospital operational data into quantitative, explainable, and actionable decision intelligence.

---

## Overview

The **Hospital Decision Intelligence Platform (HDIP)** is a production-ready, full-stack enterprise web application that integrates Machine Learning, Explainable AI (XAI), MLOps, and Decision Intelligence into a unified operational governance platform for healthcare administrators and clinical managers.

HDIP moves beyond conventional dashboards by not only **predicting** future operational states but **recommending specific operational actions**, **simulating what-if scenarios**, **estimating 7-domain cascading impacts**, and maintaining a **complete decision audit trail** with feedback loops for continuous improvement.

---

## Key Capabilities

| Capability | Description |
|---|---|
| **Demand Forecasting** | 3-14 day patient volume prediction using Prophet + ensemble methods |
| **Bed Occupancy Prediction** | Department-level peak occupancy forecasting with capacity analytics |
| **ED Wait Time Prediction** | Emergency department wait time estimation from real-time census |
| **Readmission Risk Scoring** | 30-day patient readmission risk classification with SHAP attribution |
| **Explainable AI (XAI)** | SHAP-based feature attribution with clinical plain-language reasoning |
| **Scenario Simulation** | 8 operational what-if scenario types with model re-execution |
| **Cascading Impact Analysis** | 7-domain downstream operational impact estimation |
| **Decision Intelligence** | Quantitative, formula-driven recommendations ranked P1–P4 |
| **Multi-Level Confidence** | 4-layer confidence profiling (Prediction, Recommendation, Scenario, Overall) |
| **Decision Audit Trail** | Complete governance history of all accepted/rejected/deferred decisions |
| **Feedback Loop** | Actual vs. predicted outcome comparison with effectiveness scoring |
| **MLOps & Model Registry** | Versioned model registration, performance tracking, drift detection |
| **Executive Decision Center** | Unified governance dashboard for hospital administrators |

---

## Technology Stack

### Backend
- **Python 3.11** · FastAPI (async REST API framework)
- **PostgreSQL 16** · SQLAlchemy (async ORM) · Alembic (migrations)
- **Redis 7** · Celery 5 (background ML training, drift detection)
- **Scikit-learn · XGBoost · Prophet · SHAP** (ML/XAI)
- **Structlog** (structured JSON logging)
- **JWT / Passlib / bcrypt** (authentication & security)

### Frontend
- **React 18 · TypeScript 5** · Vite 5 (build toolchain)
- **Ant Design 5** (enterprise UI component library)
- **Apache ECharts / echarts-for-react** (data visualization)
- **React Router v6** (SPA routing)
- **Axios** (typed API client)

### Infrastructure
- **Docker · Docker Compose** (containerization & orchestration)
- **Nginx 1.25** (reverse proxy, static asset serving, gzip)
- **GitHub Actions** (CI/CD pipeline)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                          Browser                             │
│  React 18 + TypeScript + Ant Design + ECharts              │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/HTTPS
┌────────────────────────▼────────────────────────────────────┐
│                      Nginx 1.25                              │
│  Reverse Proxy + Static Assets + Gzip + Cache               │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    FastAPI Backend                           │
│  Auth · Analytics · Predictions · Decisions · Data          │
│  Security Headers · Request Tracing · Structured Logging     │
└─────────────┬──────────────────────────┬───────────────────┘
              │                          │
┌─────────────▼────────┐    ┌────────────▼────────────────────┐
│   PostgreSQL 16       │    │   Redis 7 + Celery Workers       │
│   Async ORM           │    │   ML Training · Drift Detection  │
│   Indexed Queries     │    │   Background Task Queue          │
└──────────────────────┘    └──────────────────────────────────┘
```

---

## Quick Start

### Prerequisites
- Docker Desktop ≥ 24.x
- Node.js ≥ 20.x (for local development)
- Python 3.11+ (for local development)

### 1. Clone and Configure
```bash
git clone https://github.com/namithsinghk142-ctrl/HDIP.git
cd HDIP
cp .env.example .env
# Edit .env — set SECRET_KEY, database passwords, CORS origins
```

### 2. Build Frontend
```bash
cd frontend && npm ci && npm run build
```

### 3. Launch All Services
```bash
docker compose up --build -d
```

### 4. Initialize Database & Seed Data
```bash
docker compose exec api python scripts/init_db.py
docker compose exec api python scripts/seed_data.py
docker compose exec api python scripts/init_models.py
```

### 5. Access the Platform
- **Dashboard**: http://localhost
- **API Docs**: http://localhost/api/v1/docs
- **Default Login**: `admin@hospital.org` / `admin123`

Or use the developer Makefile:
```bash
make docker-up
make init-db
make seed
make train
```

---

## Developer Workflow

```bash
make setup           # Create Python virtualenv
make install         # Install all dependencies (backend + frontend)
make dev-backend     # Start FastAPI with hot-reload (port 8000)
make dev-frontend    # Start Vite dev server (port 5173)
make test            # Run full test suite
make test-cov        # Run tests + generate HTML coverage report
make lint            # Lint backend code (ruff)
make format          # Auto-format backend code
make build-frontend  # Build production frontend bundle
```

---

## Project Structure

```
HDIP/
├── backend/
│   ├── app/
│   │   ├── core/           # Database, Auth, Middleware, RBAC, Logging, Indexes
│   │   ├── models/         # SQLAlchemy ORM Models (8 tables)
│   │   ├── schemas/        # Pydantic Request/Response Schemas
│   │   └── modules/
│   │       ├── auth/       # JWT Authentication, User Management
│   │       ├── analytics/  # Staffing, Financial, ED Flow, Quality Safety
│   │       ├── data/       # Dataset Management, Data Profiling, Health
│   │       ├── predictions/ # 4 ML Models + Monitoring + Model Registry
│   │       └── decisions/  # Decision Engine, Recommendation Engine,
│   │                       # Cascade Analyzer, Scenario Simulator
│   ├── tests/              # Comprehensive pytest suite (40+ tests)
│   ├── scripts/            # init_db, seed_data, init_models
│   └── Dockerfile          # Multi-stage production Docker build
├── frontend/
│   └── src/
│       ├── features/       # Analytics, Auth, Dashboard, Predictions, Decisions
│       ├── services/       # Typed API service modules
│       ├── components/     # Shared components (AppShell, Charts, Tables)
│       └── config/         # API endpoints, theme configuration
├── nginx/nginx.conf         # Reverse proxy + static asset configuration
├── docs/                   # Complete documentation (Architecture, API, ML, Deploy)
├── .github/workflows/      # GitHub Actions CI/CD pipeline
├── docker-compose.yml      # Production Docker Compose
├── .env.example            # Environment variable template
└── Makefile                # Developer workflow automation
```

---

## Testing

```bash
make test        # All tests
make test-unit   # Unit tests only
make test-cov    # Coverage report (HTML output: backend/htmlcov/index.html)
```

Test suite covers:
- Health Probes & Security Headers
- Authentication & RBAC
- All 4 ML Model predict/explain pipelines
- Recommendation Engine (confidence, priority, reasoning chain)
- Cascade Analyzer (7 domains)
- Scenario Simulator (all 8 scenario types)
- Effectiveness Scoring (Feedback Loop)

---

## API Documentation

After starting the application, the interactive API documentation is available at:
- **Swagger UI**: http://localhost/api/v1/docs
- **ReDoc**: http://localhost/api/v1/redoc

Full API reference: [docs/API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md)

---

## Documentation

| Document | Description |
|---|---|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture, component diagrams, data flow |
| [API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md) | Complete REST API reference with endpoints and schemas |
| [ML_DECISION_INTELLIGENCE.md](docs/ML_DECISION_INTELLIGENCE.md) | ML models, XAI, MLOps, Decision Intelligence design |
| [DEVELOPER_AND_DEPLOYMENT_GUIDE.md](docs/DEVELOPER_AND_DEPLOYMENT_GUIDE.md) | Setup, environment, deployment, and operations guide |
| [PORTFOLIO_AND_INTERVIEW_GUIDE.md](docs/PORTFOLIO_AND_INTERVIEW_GUIDE.md) | Resume highlights, technical talking points, architecture rationale |

---

## CI/CD Pipeline

GitHub Actions pipeline runs on every push to `main` and `develop`:
1. **Backend Lint** — ruff linting + mypy type checking
2. **Backend Tests** — pytest with PostgreSQL + Redis services
3. **Frontend Type Check** — tsc --noEmit
4. **Frontend Build** — production Vite build
5. **Docker Build Validation** — Multi-stage Dockerfile build

---

## Security Features

- **JWT Bearer Authentication** with configurable token expiry
- **Role-Based Access Control (RBAC)** — 5 roles: analyst, clinician, manager, executive, admin
- **Security Headers** — HSTS, X-Frame-Options DENY, X-Content-Type-Options, CSP, XSS Protection
- **Request Tracing** — X-Request-ID propagation for distributed tracing
- **Non-root Docker container** execution for runtime isolation
- **Secrets via environment variables** (never hardcoded)

---

## License

This project is intended for educational and healthcare operational intelligence demonstration purposes. All rights reserved.