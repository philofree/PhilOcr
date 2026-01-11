"""
Centralized structlog configuration for PhilOcr.

This module provides structured logging configuration following strict
standards: event-driven logging, proper processor ordering, and JSON
output support.

Critical rules:
- Event name is first positional argument (never use "event" keyword)
- Context as keyword arguments (never wrap in "extra" dictionary)
- Configure once at startup only
- Renderer must be last processor
"""

from __future__ import annotations

import logging
import sys

import structlog


def configure_logging(json_logs: bool | None = None, log_level: str = "INFO") -> None:
    """
    Configure structlog once at application startup.

    Args:
        json_logs: If True, output JSON. If None, auto-detect based on TTY.
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Raises:
        ValueError: If log_level is invalid
    """
    # Validate log level
    valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    if log_level.upper() not in valid_levels:
        raise ValueError(
            f"Invalid log_level: {log_level}. " f"Must be one of {valid_levels}"
        )

    # Auto-detect JSON output if not specified
    if json_logs is None:
        json_logs = not sys.stderr.isatty()

    # Standard library integration
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

    # Core processors - order matters!
    processors = [
        # First - merges context variables
        structlog.contextvars.merge_contextvars,
        # Filter by log level
        structlog.stdlib.filter_by_level,
        # Add logger name
        structlog.stdlib.add_logger_name,
        # Add log level
        structlog.stdlib.add_log_level,
        # Format positional arguments (event name)
        structlog.stdlib.PositionalArgumentsFormatter(),
        # Add timestamp
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        # Add stack info for exceptions
        structlog.processors.StackInfoRenderer(),
        # Format exceptions
        structlog.processors.format_exc_info,
        # Decode Unicode
        structlog.processors.UnicodeDecoder(),
    ]

    # Add environment-specific renderer (always last)
    if json_logs:
        processors.append(structlog.processors.JSONRenderer())  # type: ignore[arg-type]
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))  # type: ignore[arg-type]

    # Configure structlog
    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.BoundLogger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name (typically __name__). If None, uses root logger.

    Returns:
        Configured structlog BoundLogger instance
    """
    return structlog.get_logger(name)


def flush_loggers() -> None:
    """
    Flush all logging handlers.

    Critical for ensuring logs are written before process exit,
    especially in exception handlers that re-raise.

    Should be called in exception handlers before re-raising to ensure
    diagnostic data is not lost on process exit.
    """
    # Get logger for error reporting (structlog should be configured by now)
    logger = structlog.get_logger(__name__)

    # Flush standard library handlers
    for handler in logging.root.handlers[:]:
        handler.flush()
        if hasattr(handler, "close"):
            try:
                handler.close()
            except Exception as e:
                # Log but don't fail - handler cleanup is best-effort
                logger.warning(
                    "logging_handler_close_failed",
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True,
                )

    # Also flush structlog processors
    try:
        # Clear context to ensure all buffered data is processed
        structlog.get_logger()._context.clear()
    except Exception as e:
        # Log but don't fail - context clearing is best-effort
        logger.warning(
            "structlog_context_clear_failed",
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True,
        )
