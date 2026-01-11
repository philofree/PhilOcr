#!/usr/bin/env python3
"""Memory management utilities for the PhilOcr application.

This module provides functions for optimizing memory usage during processing.
"""
from __future__ import annotations

import gc
import os
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)

# Constants for memory thresholds
SMALL_FILE_THRESHOLD_MB = 5
MEDIUM_FILE_THRESHOLD_MB = 20
LARGE_FILE_THRESHOLD_MB = 50

# Define a type variable for the callable's return type
R = TypeVar("R")


def estimate_memory_usage() -> float:
    """
    Estimate current memory usage of the process.

    Returns:
        float: Memory usage in MB

    Raises:
        RuntimeError: If psutil is not available (required dependency)
    """
    try:
        import psutil

        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        return float(memory_info.rss / (1024 * 1024))  # Convert to MB
    except ImportError as e:
        logger.error(
            "psutil_not_available",
            operation="estimate_memory_usage",
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True,
        )
        from philocr.utils.logging_config import flush_loggers

        flush_loggers()
        raise RuntimeError(
            "CRITICAL: psutil is required for memory estimation. "
            "Install with: pip install psutil"
        ) from e


def force_garbage_collection() -> None:
    """
    Force a garbage collection cycle to free up memory.
    This is more aggressive than letting Python's automatic garbage collection run.
    """
    logger.debug("gc_forcing")

    # Run garbage collection multiple times to ensure references are cleaned up
    for _ in range(3):
        _ = gc.collect()

    memory_after = estimate_memory_usage()
    logger.debug("gc_completed", memory_mb=memory_after)


def determine_processing_mode(file_size_mb: float) -> str:
    """
    Determine the appropriate processing mode based on file size.

    Args:
        file_size_mb: Size of the file in MB

    Returns:
        str: Processing mode ('standard', 'chunked', or 'streaming')
    """
    if file_size_mb < SMALL_FILE_THRESHOLD_MB:
        return "standard"
    elif file_size_mb < LARGE_FILE_THRESHOLD_MB:
        return "chunked"
    else:
        # Check if ijson is available for streaming
        try:
            import importlib.util

            _ = importlib.util.find_spec("ijson")
            if _ is not None:
                return "streaming"
            else:
                logger.warning(
                    "ijson_not_available",
                    fallback_mode="chunked",
                    file_size_mb=file_size_mb,
                    processing_strategy="chunked_processing",
                    reason="ijson_not_installed",
                )
                return "chunked"
        except ImportError as e:
            logger.error(
                "importlib_unavailable",
                file_size_mb=file_size_mb,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            from philocr.utils.logging_config import flush_loggers

            flush_loggers()
            raise RuntimeError(
                "CRITICAL: importlib.util is required (part of standard library). "
                f"This indicates a system configuration problem - {e}"
            ) from e


def memory_managed_operation(func: Callable[..., R]) -> Callable[..., R]:
    """
    Decorator for memory-intensive operations.
    This decorator ensures garbage collection is run before and after the operation.

    Args:
        func: Function to decorate

    Returns:
        Callable: Decorated function
    """

    def wrapper(*args: Any, **kwargs: Any) -> R:
        # Run garbage collection before operation
        start_memory = estimate_memory_usage()
        logger.debug(
            "memory_managed_op_start",
            function_name=func.__name__,
            memory_before_mb=start_memory,
        )
        force_garbage_collection()

        # Run the operation
        result = func(*args, **kwargs)

        # Run garbage collection after operation
        force_garbage_collection()
        end_memory = estimate_memory_usage()
        logger.debug(
            "memory_managed_op_end",
            function_name=func.__name__,
            memory_after_mb=end_memory,
        )

        return result

    return wrapper


def check_available_memory() -> float:
    """
    Check available system memory.

    Returns:
        float: Available memory in MB

    Raises:
        RuntimeError: If psutil is not available (required dependency)
    """
    try:
        import psutil

        memory = psutil.virtual_memory()
        return float(memory.available / (1024 * 1024))  # Convert to MB
    except ImportError as e:
        logger.error(
            "psutil_not_available",
            operation="check_available_memory",
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True,
        )
        from philocr.utils.logging_config import flush_loggers

        flush_loggers()
        raise RuntimeError(
            "CRITICAL: psutil is required for memory checking. "
            "Install with: pip install psutil"
        ) from e


def check_memory_threshold(threshold_mb: float = 100.0) -> bool:
    """
    Check if available memory is above a threshold.

    Args:
        threshold_mb: Threshold in MB

    Returns:
        bool: True if available memory is above threshold, False otherwise
    """
    available_mb = check_available_memory()
    is_above_threshold = available_mb > threshold_mb

    if not is_above_threshold:
        logger.warning(
            "low_memory_warning",
            available_mb=available_mb,
            threshold_mb=threshold_mb,
        )

    return is_above_threshold
