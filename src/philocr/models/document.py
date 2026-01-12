"""Document output data structures for Stage 4."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from philocr.models.bounding_box import BoundingBox
    from philocr.models.template import DocumentTemplate
else:
    from philocr.models.bounding_box import BoundingBox


class GenreHint(Enum):
    """Genre classification for downstream formatting."""

    PROSE = "prose"
    VERSE = "verse"
    SPEAKERS = "speakers"
    VERSE_SPEAKERS = "verse_speakers"
    FRAGMENTS = "fragments"
    UNKNOWN = "unknown"


@dataclass
class GenreDetectionResult:
    """Result of genre detection with confidence scores.

    Attributes:
        primary_genre: Detected primary genre
        confidence: Confidence score (0.0 to 1.0)
        signals: Evidence that led to classification
    """

    primary_genre: GenreHint
    confidence: float  # 0.0 to 1.0
    signals: dict[str, Any]  # Evidence that led to classification


@dataclass
class Paragraph:
    """Processed paragraph with indent classification.

    Attributes:
        text: Paragraph text content
        indent_class: Indent classification (0=flush, 1=standard, 2=deep)
        confidence: OCR confidence score
        bbox: Bounding box of the paragraph
    """

    text: str
    indent_class: int  # 0=flush, 1=standard, 2=deep
    confidence: float
    bbox: BoundingBox


@dataclass
class PageOutput:
    """Final processed output for a single page.

    Attributes:
        page_num: Page number (0-indexed)
        paragraphs: List of processed paragraphs
        full_text: Full text content of the page
        confidence: Average confidence score
        genre_hint: Optional genre classification hint
        genre_confidence: Confidence of genre classification
        genre_signals: Optional genre detection signals for debugging
    """

    page_num: int
    paragraphs: list[Paragraph]
    full_text: str
    confidence: float
    genre_hint: GenreHint | None = None  # Advisory, not authoritative
    genre_confidence: float = 0.0
    genre_signals: dict[str, Any] | None = None  # For debugging/inspection


@dataclass
class DocumentMetadata:
    """Metadata about the source document.

    Attributes:
        title: Document title
        source_path: Path to source PDF
        author: Optional author name
        edition: Optional edition information
        year: Optional publication year
    """

    title: str
    source_path: str
    author: str | None = None
    edition: str | None = None
    year: int | None = None


@dataclass
class DocumentStatistics:
    """Statistics about the processed document.

    Attributes:
        total_pages: Total number of pages processed
        total_paragraphs: Total number of paragraphs
        average_confidence: Average OCR confidence across all pages
        pages_with_errors: List of page numbers that had errors
    """

    total_pages: int
    total_paragraphs: int
    average_confidence: float
    pages_with_errors: list[int]


@dataclass
class Document:
    """Complete processed document.

    Attributes:
        metadata: Document metadata
        template: Document template used for processing
        pages: List of page outputs
        full_text: Complete assembled text
        statistics: Document processing statistics
    """

    metadata: DocumentMetadata
    template: DocumentTemplate
    pages: list[PageOutput]
    full_text: str
    statistics: DocumentStatistics

    def to_json(self, path: str) -> None:
        """Save document to JSON file.

        Args:
            path: Path to save JSON file
        """
        # Convert dataclasses to dicts for JSON serialization
        data: dict[str, Any] = {
            "metadata": {
                "title": self.metadata.title,
                "source_path": self.metadata.source_path,
                "author": self.metadata.author,
                "edition": self.metadata.edition,
                "year": self.metadata.year,
            },
            "template": self.template.__dict__,
            "pages": [
                {
                    "page_num": p.page_num,
                    "paragraphs": [
                        {
                            "text": para.text,
                            "indent_class": para.indent_class,
                            "confidence": para.confidence,
                            "bbox": {
                                "x1": para.bbox.x1,
                                "y1": para.bbox.y1,
                                "x2": para.bbox.x2,
                                "y2": para.bbox.y2,
                            },
                        }
                        for para in p.paragraphs
                    ],
                    "full_text": p.full_text,
                    "confidence": p.confidence,
                    "genre_hint": p.genre_hint.value if p.genre_hint else None,
                    "genre_confidence": p.genre_confidence,
                    "genre_signals": p.genre_signals,
                }
                for p in self.pages
            ],
            "full_text": self.full_text,
            "statistics": {
                "total_pages": self.statistics.total_pages,
                "total_paragraphs": self.statistics.total_paragraphs,
                "average_confidence": self.statistics.average_confidence,
                "pages_with_errors": self.statistics.pages_with_errors,
            },
        }
        import json

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
