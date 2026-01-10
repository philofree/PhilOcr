"""Configuration dataclass for Document AI processing."""

from __future__ import annotations

from dataclasses import dataclass

from philocr.processing.document_ai import RateLimiter


@dataclass
class DocumentAIProcessingConfig:
    """Configuration for Document AI processing operations.

    Attributes:
        file_path: Path to the PDF file to process
        rate_limiter: Optional rate limiter for API calls
        max_pages: Maximum number of pages to process (default: 15)
        project_id: Google Cloud project ID
        location: Document AI location (default: "us")
        processor_id: Document AI processor ID
        include_layout: Whether to include layout information in response
    """

    file_path: str
    rate_limiter: RateLimiter | None = None
    max_pages: int = 15
    project_id: str | None = None
    location: str | None = None
    processor_id: str | None = None
    include_layout: bool = True
