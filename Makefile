# ══════════════════════════════════════════════════════════════════════════════
# Hospital Decision Intelligence Platform — Developer Makefile
# ══════════════════════════════════════════════════════════════════════════════

.PHONY: setup seed train init-db dev-backend dev-frontend test test-unit test-cov \
        lint format type-check docker-up docker-down docker-logs docker-ps \
        build-frontend docs clean help

PYTHON ?= python
PIP    ?= pip
NPM    ?= npm

# ── Environment Setup ──────────────────────────────────────────────────────────
setup:
	@echo "Setting up HDIP development environment..."
	$(PYTHON) -m venv venv
	@echo "Activate venv: source venv/bin/activate (Linux/Mac) or venv\\Scripts\\activate (Windows)"
	@echo "Then run: make install"

install:
	@echo "Installing backend dependencies..."
	$(PIP) install -e "backend/.[dev]"
	@echo "Installing frontend dependencies..."
	$(NPM) --prefix frontend ci
	@echo "Installation complete."

# ── Database & Data ────────────────────────────────────────────────────────────
init-db:
	@echo "Initializing database schema..."
	$(PYTHON) scripts/init_db.py

seed:
	@echo "Generating synthetic hospital dataset..."
	$(PYTHON) scripts/seed_data.py

train:
	@echo "Training ML models..."
	$(PYTHON) scripts/init_models.py

# ── Development Servers ────────────────────────────────────────────────────────
dev-backend:
	@echo "Starting FastAPI development server..."
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	@echo "Starting Vite development server..."
	cd frontend && npm run dev

# ── Testing ───────────────────────────────────────────────────────────────────
test:
	@echo "Running full test suite..."
	cd backend && pytest tests/ -v --tb=short

test-unit:
	@echo "Running unit tests only..."
	cd backend && pytest tests/ -m unit -v

test-cov:
	@echo "Running tests with coverage report..."
	cd backend && pytest tests/ --cov=app --cov-report=term-missing --cov-report=html:htmlcov -v
	@echo "HTML coverage report: backend/htmlcov/index.html"

# ── Code Quality ──────────────────────────────────────────────────────────────
lint:
	@echo "Linting backend with ruff..."
	cd backend && ruff check app/ tests/

format:
	@echo "Formatting backend code..."
	cd backend && ruff format app/ tests/

type-check:
	@echo "Running mypy type checker..."
	cd backend && mypy app/ --ignore-missing-imports

# ── Frontend Build ─────────────────────────────────────────────────────────────
build-frontend:
	@echo "Building frontend production bundle..."
	cd frontend && npm run build
	@echo "Build output: frontend/dist/"

type-check-frontend:
	@echo "Running TypeScript type check..."
	cd frontend && npx tsc --noEmit

# ── Docker ────────────────────────────────────────────────────────────────────
docker-up:
	@echo "Starting all HDIP services..."
	docker compose up --build -d
	@echo "Services running. API: http://localhost:80"

docker-down:
	@echo "Stopping all HDIP services..."
	docker compose down

docker-down-volumes:
	@echo "Stopping and removing all data volumes..."
	docker compose down -v

docker-logs:
	docker compose logs -f api

docker-ps:
	docker compose ps

docker-restart-api:
	docker compose restart api

# ── Utilities ─────────────────────────────────────────────────────────────────
clean:
	@echo "Cleaning build artefacts..."
	rm -rf frontend/dist backend/htmlcov backend/__pycache__
	find backend -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find backend -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "Clean complete."

# ── Help ──────────────────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "Hospital Decision Intelligence Platform — Make Targets"
	@echo "══════════════════════════════════════════════════════════"
	@echo "  setup            : Create Python virtual environment"
	@echo "  install          : Install backend + frontend dependencies"
	@echo "  init-db          : Initialize PostgreSQL database schema"
	@echo "  seed             : Generate synthetic hospital dataset"
	@echo "  train            : Train all ML models"
	@echo "  dev-backend      : Start FastAPI dev server (hot reload)"
	@echo "  dev-frontend     : Start Vite dev server"
	@echo "  test             : Run full test suite"
	@echo "  test-unit        : Run unit tests only"
	@echo "  test-cov         : Run tests + generate HTML coverage"
	@echo "  lint             : Lint backend code (ruff)"
	@echo "  format           : Auto-format backend code (ruff format)"
	@echo "  type-check       : Backend type checking (mypy)"
	@echo "  build-frontend   : Build frontend production bundle"
	@echo "  docker-up        : Start all Docker services (build)"
	@echo "  docker-down      : Stop all Docker services"
	@echo "  docker-logs      : Stream API service logs"
	@echo "  docker-ps        : Show service status"
	@echo "  clean            : Remove build artefacts"
	@echo ""

