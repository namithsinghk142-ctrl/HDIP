from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.core.database import engine, Base
from app.core.logging import setup_logging, get_logger
from app.core.middleware import SecurityHeadersMiddleware, RequestTracingMiddleware

from app.modules.auth.router import router as auth_router
from app.modules.data.router import router as data_router
from app.modules.analytics.router import router as analytics_router
from app.modules.predictions.router import router as predictions_router
from app.modules.decisions.router import router as decisions_router

# Setup structured logging
setup_logging(debug=settings.DEBUG)
logger = get_logger("hdip.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    logger.info("app_startup_begin", project=settings.PROJECT_NAME, version=settings.VERSION)
    from app.models import user, dataset, operational, ml_model, decision  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("app_startup_complete", database_url=settings.DATABASE_URL.split("@")[-1])
    yield
    logger.info("app_shutdown_begin")


app = FastAPI(
    lifespan=lifespan,
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc"
)

# Attach Security & Request Tracing Middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestTracingMiddleware)

# Set CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    req_id = getattr(request.state, "request_id", "unknown")
    logger.error("unhandled_exception", error=str(exc), path=request.url.path, request_id=req_id, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred.",
            "request_id": req_id,
            "error_type": type(exc).__name__
        }
    )


# Include Routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(data_router, prefix=settings.API_V1_STR)
app.include_router(analytics_router, prefix=settings.API_V1_STR)
app.include_router(predictions_router, prefix=settings.API_V1_STR)
app.include_router(decisions_router, prefix=settings.API_V1_STR)


# Health Probes for Kubernetes / Docker
@app.get("/health")
@app.get("/health/liveness")
def liveness_check():
    """Liveness probe to check if service container is running."""
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION
    }


@app.get("/health/readiness")
async def readiness_check():
    """Readiness probe to check if database connection pool is functional."""
    try:
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
        return {
            "status": "ready",
            "database": "connected",
            "project": settings.PROJECT_NAME,
            "version": settings.VERSION
        }
    except Exception as e:
        logger.error("readiness_check_failed", error=str(e))
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "database": "disconnected", "detail": str(e)}
        )

