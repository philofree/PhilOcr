"""
Unicode normalization utilities for text processing.

This module provides Unicode normalization functions to ensure consistent
representation of polytonic Greek characters and other Unicode text throughout
the text processing pipeline.
"""

import unicodedata
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)


def normalize_to_nfc(text: str) -> str:
    """Normalize text to Unicode NFC (Canonical Composition) form.

    NFC normalization ensures that characters are represented in their
    canonical composed form, which is the recommended form for most text
    processing applications. This is particularly important for polytonic
    Greek characters, which can be represented in multiple Unicode forms.

    Args:
        text: Input text to normalize. Can be empty string.

    Returns:
        Text normalized to NFC form. Returns empty string if input is empty.

    Examples:
        >>> normalize_to_nfc("") == ""
        True
        >>> normalize_to_nfc("α") == "α"
        True
        >>> # NFC normalization is idempotent
        >>> normalized = normalize_to_nfc("ἀ")
        >>> normalize_to_nfc(normalized) == normalized
        True
    """
    if not text:
        return text
    return unicodedata.normalize("NFC", text)
