"""Structured logging via structlog + optional Langfuse integration."""
from __future__ import annotations

import logging
import sys

import structlog

from helix.core.config import settings


def configure_logging() -> None:
    """Idempotent global logging setup."""
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            (
                structlog.dev.ConsoleRenderer()
                if not settings.is_production
                else structlog.processors.JSONRenderer()
            ),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level.upper(), logging.INFO)
        ),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = "helix") -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
