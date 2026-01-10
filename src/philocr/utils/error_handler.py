"""
Error handling utilities for the PhilOcr application.
This module provides functions for handling errors and implementing retry logic.
"""

import random
import time
from collections.abc import Callable
from functools import wraps
from typing import TYPE_CHECKING, Any, TypeVar, cast

from philocr.utils.exceptions import APIRateLimitError
from philocr.utils.logging_config import flush_loggers

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)

# Generic type for the return value of functions
T = TypeVar("T")


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    exceptions_to_retry: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to retry a function with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        backoff_factor: Factor by which to increase the delay on each retry
        exceptions_to_retry: Tuple of exception types to retry on

    Returns:
        Callable: Decorated function
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    if attempt > 0:
                        logger.info(
                            "retry_attempt",
                            function_name=func.__name__,
                            attempt=attempt,
                            max_retries=max_retries,
                        )

                    return func(*args, **kwargs)

                except exceptions_to_retry as e:
                    last_exception = e

                    if attempt == max_retries:
                        logger.exception(
                            "max_retries_reached",
                            function_name=func.__name__,
                            max_retries=max_retries,
                            error=str(e),
                            error_type=type(e).__name__,
                        )
                        raise

                    # Add some randomness to the delay to avoid thundering herd problem
                    jitter = random.uniform(0.8, 1.2)
                    current_delay = min(delay * jitter, max_delay)

                    logger.warning(
                        "retry_scheduled",
                        function_name=func.__name__,
                        attempt=attempt,
                        max_retries=max_retries,
                        error=str(e),
                        error_type=type(e).__name__,
                        retry_delay_seconds=round(current_delay, 2),
                    )

                    time.sleep(current_delay)
                    delay = min(delay * backoff_factor, max_delay)

            # This code should never be reached, but is needed for type checking
            if last_exception:
                raise last_exception

            # This is to satisfy the type checker
            return cast(T, None)

        return wrapper

    return decorator


def handle_api_errors(
    func: Callable[..., T],
    fallback_value: T | None = None,
    fallback_func: Callable[..., T] | None = None,
) -> Callable[..., T]:
    """
    Decorator to handle API errors and provide fallback behavior.

    Args:
        func: Function to decorate
        fallback_value: Value to return if the function fails
        fallback_func: Function to call if the primary function fails

    Returns:
        Callable: Decorated function
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception(
                "api_error_occurred",
                function_name=func.__name__,
                error=str(e),
                error_type=type(e).__name__,
            )

            if fallback_func:
                logger.info(
                    "using_fallback_function",
                    function_name=func.__name__,
                )
                return fallback_func(*args, **kwargs)
            elif fallback_value is not None:
                logger.info(
                    "using_fallback_value",
                    function_name=func.__name__,
                )
                return fallback_value
            else:
                logger.exception(
                    "no_fallback_available",
                    function_name=func.__name__,
                    error=str(e),
                    error_type=type(e).__name__,
                )
                flush_loggers()
                raise

    return wrapper


def log_exceptions(
    log_level: str = "error",
    include_traceback: bool = True,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to log exceptions raised by a function.

    Args:
        log_level: Logging level to use (debug, info, warning, error, critical)
        include_traceback: Whether to include the traceback in the log

    Returns:
        Callable: Decorated function
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Use the appropriate log method based on level
                log_method = getattr(logger, log_level.lower(), logger.error)
                log_method(
                    "function_exception",
                    function_name=func.__name__,
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=include_traceback,
                )

                # Flush logger before re-raising to ensure log is written
                from philocr.utils.logging_config import flush_loggers

                flush_loggers()
                raise

        return wrapper

    return decorator


def is_recoverable_error(error: Exception) -> bool:
    """
    Determine if an error is recoverable (can be retried).

    Args:
        error: The exception to check

    Returns:
        bool: True if the error is recoverable, False otherwise
    """
    from google.api_core import exceptions as google_exceptions

    # Google API transient errors
    if isinstance(
        error,
        (
            google_exceptions.DeadlineExceeded,
            google_exceptions.ServiceUnavailable,
            google_exceptions.ResourceExhausted,
            google_exceptions.GatewayTimeout,
            APIRateLimitError,
        ),
    ):
        return True

    # Network errors
    if isinstance(
        error,
        (
            ConnectionError,
            TimeoutError,
        ),
    ):
        return True

    # Check error message for specific patterns
    error_message = str(error).lower()
    recoverable_patterns = [
        "timeout",
        "temporary",
        "rate limit",
        "too many requests",
        "retry",
        "try again",
        "server busy",
    ]

    for pattern in recoverable_patterns:
        if pattern in error_message:
            return True

    return False
