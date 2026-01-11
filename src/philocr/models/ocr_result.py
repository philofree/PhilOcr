"""OCR result data structures."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from philocr.models.bounding_box import BoundingBox


@dataclass
class TextBlock:
    """Block-level text structure from OCR.

    Attributes:
        text: Extracted text content
        confidence: OCR confidence score (0.0 to 1.0)
        bbox: Bounding box of the text block
    """

    text: str
    confidence: float
    bbox: BoundingBox


@dataclass
class TextParagraph:
    """Paragraph-level text structure from OCR.

    Attributes:
        text: Extracted text content
        confidence: OCR confidence score (0.0 to 1.0)
        bbox: Bounding box of the paragraph
    """

    text: str
    confidence: float
    bbox: BoundingBox


@dataclass
class TextLine:
    """Line-level text structure from OCR.

    Attributes:
        text: Extracted text content
        confidence: OCR confidence score (0.0 to 1.0)
        bbox: Bounding box of the line
    """

    text: str
    confidence: float
    bbox: BoundingBox


@dataclass
class OCRResult:
    """Complete OCR result for a single page.

    Attributes:
        page_num: Page number (0-indexed)
        text: Full extracted text
        blocks: List of text blocks
        paragraphs: List of paragraphs
        lines: List of text lines
        confidence: Average confidence score (0.0 to 1.0)
        error: Error message if OCR failed (None if successful)
        raw_response: Raw Document AI response (optional)
    """

    page_num: int
    text: str
    blocks: list[TextBlock]
    paragraphs: list[TextParagraph]
    lines: list[TextLine]
    confidence: float
    error: str | None = None
    raw_response: Any | None = None
