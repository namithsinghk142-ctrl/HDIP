"""
Security & Observability Middleware — Phase 5 Hardening
======================================================
Implements:
  1. SecurityHeadersMiddleware — HSTS, CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy
  2. RequestTracingMiddleware — Request ID injection (X-Request-ID), timing (X-Process-Time-MS), and structured access logging
"""

import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from app.core.logging import get_logger

logger = get_logger("hdip.middleware")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Applies enterprise security headers to every HTTP response."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Enterprise Security Headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' http: https:;"
        )

        return response


class RequestTracingMiddleware(BaseHTTPMiddleware):
    """
    Injects a unique X-Request-ID into request state and response headers,
    measures processing latency, and records structured access logs.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Extract or generate Request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        start_time = time.time()
        try:
            response = await call_next(request)
            duration_ms = round((time.time() - start_time) * 1000, 2)

            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time-MS"] = str(duration_ms)

            # Log non-healthcheck requests
            if not request.url.path.startswith("/health"):
                logger.info(
                    "http_request_handled",
                    method=request.method,
                    path=request.url.path,
                    status_code=response.status_code,
                    duration_ms=duration_ms,
                    request_id=request_id,
                    client_host=request.client.host if request.client else "unknown",
                )

            return response
        except Exception as exc:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            logger.error(
                "http_request_failed",
                method=request.method,
                path=request.url.path,
                error=str(exc),
                duration_ms=duration_ms,
                request_id=request_id,
                exc_info=True,
            )
            raise exc
