"""
Structured Logging Configuration — Phase 5 Production Hardening
===============================================================
Provides JSON-structured logging with request ID tracking,
execution timing, and exception formatting.
"""

import sys
import logging
import structlog
from typing import Dict, Any

def setup_logging(debug: bool = False) -> None:
    """Configures structlog for production JSON output or dev console output."""
    log_level = logging.DEBUG if debug else logging.INFO

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if debug:
        # Development: Human-readable colorful console logging
        renderer = structlog.dev.ConsoleRenderer()
    else:
        # Production: Structured JSON for log aggregators (ELK, Datadog)
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=shared_processors + [renderer],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )

    # Standard library logging redirection
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

def get_logger(name: str = "hdip"):
    """Get a bound structlog logger instance."""
    return structlog.get_logger(name)
