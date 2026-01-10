"""
Custom exceptions for markdown conversion operations.

This module defines a hierarchy of exceptions for handling various
error conditions during markdown conversion from Google Document AI JSON.

Note: These exceptions are now part of the main exception hierarchy.
This module is kept for backward compatibility and re-exports from
philocr.utils.exceptions.
"""

from philocr.utils.exceptions import (
    AlternativeFormatError,
    ChunkProcessingError,
    FormatDetectionError,
    HTMLConversionError,
    MarkdownConversionError,
)

__all__ = [
    "MarkdownConversionError",
    "FormatDetectionError",
    "AlternativeFormatError",
    "ChunkProcessingError",
    "HTMLConversionError",
]

# All exceptions are re-exported from philocr.utils.exceptions
# No need to redefine them here
