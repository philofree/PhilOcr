#!/usr/bin/env python3
"""Format detector for alternative JSON formats.

This module provides functionality to detect chunked and hybrid format types
in alternative JSON structures.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)


class AlternativeFormatDetector:
    """Detects alternative format types (chunked, hybrid)."""

    @staticmethod
    def detect_chunked(json_data: dict[str, Any]) -> bool:
        """Detect if the format is chunked.

        Args:
            json_data: JSON data to analyze.

        Returns:
            True if format contains chunk markers, False otherwise.
        """
        try:
            if "text" in json_data:
                return "--- Chunk " in json_data["text"]
        except (KeyError, TypeError):
            pass
        return False

    @staticmethod
    def detect_hybrid(json_data: dict[str, Any], is_chunked_format: bool) -> bool:
        """Detect if the format is hybrid (chunk markers + document_data).

        Args:
            json_data: JSON data to analyze.
            is_chunked_format: Whether the format contains chunk markers.

        Returns:
            True if format is hybrid, False otherwise.
        """
        try:
            return (
                is_chunked_format
                and "files" in json_data
                and any(
                    "document_data" in file_data
                    for file_data in json_data["files"]
                    if isinstance(file_data, dict)
                )
            )
        except (KeyError, TypeError):
            return False
