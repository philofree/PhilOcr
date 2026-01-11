from __future__ import annotations

import os
import time
from collections import deque
from typing import TYPE_CHECKING, Any

from google.api_core import exceptions as google_exceptions
from google.cloud import documentai

from philocr.utils.exceptions import (
    ConfigurationError,
    PDFParseError,
    PDFProcessingError,
)
from philocr.utils.logging_config import flush_loggers
from philocr.utils.unicode_normalizer import normalize_to_nfc

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)

# Export the client class for backward compatibility
DocumentProcessorServiceClient = documentai.DocumentProcessorServiceClient

# Google rate limiting constants
MAX_REQUESTS_PER_MINUTE = 15
RATE_LIMIT_SECONDS = 60


def _get_document_ai_api_endpoint(location: str) -> str:
    """
    Get the Document AI API endpoint to use for a given processor location.

    Document AI processors are regional/multi-regional. If the client is pointed
    at the wrong endpoint (e.g. US endpoint with an EU processor resource name),
    the API can return errors like:
      "Invalid location: 'eu' must match the server deployment 'us'".

    Args:
        location: Processor location (e.g. "eu", "us").

    Returns:
        API endpoint hostname (no scheme), e.g. "eu-documentai.googleapis.com".
    """
    loc = location.strip().lower()
    if loc in {"eu", "us"}:
        return f"{loc}-documentai.googleapis.com"
    return "documentai.googleapis.com"


class RateLimiter:
    """Class to manage rate limiting for API calls."""

    calls: deque[float]

    def __init__(self, max_calls: int, period: float) -> None:
        """
        Initialize the rate limiter.

        Args:
            max_calls: Maximum number of calls allowed per period
            period: Time period in seconds
        """
        super().__init__()
        self.max_calls = max_calls
        self.period = period
        self.calls = deque()

    def wait_if_needed(self) -> None:
        """Wait if necessary to respect rate limits."""
        now = time.time()

        # Remove calls that are outside the current period
        while self.calls and now - self.calls[0] >= self.period:
            _ = self.calls.popleft()

        # If we're at the limit, wait until we can make another call
        if len(self.calls) >= self.max_calls:
            wait_time = self.period - (now - self.calls[0])
            if wait_time > 0:
                logger.debug(
                    "rate_limit_wait",
                    wait_time_seconds=round(wait_time, 2),
                    max_calls=self.max_calls,
                    period_seconds=self.period,
                )
                _ = time.sleep(wait_time)

        # Record this call
        self.calls.append(now)


def _load_processing_config(
    project_id: str | None,
    location: str | None,
    processor_id: str | None,
) -> tuple[str, str, str]:
    """Load Document AI configuration from environment if not provided.

    Args:
        project_id: Optional project ID
        location: Optional location
        processor_id: Optional processor ID

    Returns:
        Tuple of (project_id, location, processor_id)

    Raises:
        ConfigurationError: If required configuration is missing
    """
    resolved_project_id = project_id or os.getenv(
        "DOCUMENT_AI_PROJECT_ID", os.getenv("GOOGLE_CLOUD_PROJECT_ID")
    )
    resolved_location = location or os.getenv("DOCUMENT_AI_LOCATION", "us")
    resolved_processor_id = processor_id or os.getenv("DOCUMENT_AI_PROCESSOR_ID")

    if not resolved_project_id or not resolved_processor_id:
        logger.error(
            "document_ai_config_missing",
            project_id_set=resolved_project_id is not None,
            processor_id_set=resolved_processor_id is not None,
        )
        raise ConfigurationError(
            "Document AI configuration missing. Please check ENV.local file or environment variables."
        )

    return resolved_project_id, resolved_location, resolved_processor_id


def _validate_file_for_processing(file_path: str) -> None:
    """Validate that a file exists and log file information.

    Args:
        file_path: Path to the file to validate

    Raises:
        PDFParseError: If file doesn't exist
    """
    if not os.path.exists(file_path):
        logger.error("file_not_found", file_path=file_path)
        raise PDFParseError(file_path, "File not found")

    file_size = os.path.getsize(file_path)
    file_size_mb = file_size / (1024 * 1024)
    logger.debug(
        "file_processing_started",
        file_path=file_path,
        file_size_bytes=file_size,
        file_size_mb=round(file_size_mb, 2),
    )


def _create_document_ai_client(
    location: str,
) -> documentai.DocumentProcessorServiceClient:
    """Create and configure a Document AI client.

    Args:
        location: Document AI location

    Returns:
        Configured Document AI client
    """
    api_endpoint = _get_document_ai_api_endpoint(location)
    return documentai.DocumentProcessorServiceClient(
        client_options={"api_endpoint": api_endpoint}
    )


def _process_document_with_client(
    client: documentai.DocumentProcessorServiceClient,
    project_id: str,
    location: str,
    processor_id: str,
    pdf_content: bytes,
) -> documentai.Document:
    """Process a PDF document using the Document AI client.

    Args:
        client: Document AI client
        project_id: Google Cloud project ID
        location: Document AI location
        processor_id: Document AI processor ID
        pdf_content: PDF file content as bytes

    Returns:
        Processed Document AI document

    Raises:
        PDFProcessingError: If processing fails
        ValueError: If configuration errors occur
    """
    name = f"projects/{project_id}/locations/{location}/processors/{processor_id}"
    request = documentai.ProcessRequest(
        name=name,
        raw_document=documentai.RawDocument(
            content=pdf_content, mime_type="application/pdf"
        ),
    )

    try:
        result = client.process_document(request=request)
        return result.document
    except google_exceptions.InvalidArgument as e:
        error_msg = str(e)
        if "server deployment" in error_msg and "invalid location" in error_msg.lower():
            api_endpoint = _get_document_ai_api_endpoint(location)
            raise ValueError(
                "Document AI endpoint/location mismatch detected. "
                "This usually means the client is using the wrong regional "
                "API endpoint for the configured processor location. "
                f"Configured location={location!r}, api_endpoint={api_endpoint!r}. "
                f"Raw error: {error_msg}"
            ) from e
        logger.error(
            "document_ai_invalid_argument",
            error=error_msg,
            error_type=type(e).__name__,
            exc_info=True,
        )
        flush_loggers()
        raise PDFProcessingError("", f"Invalid argument: {error_msg}") from e
    except google_exceptions.NotFound as e:
        error_msg = str(e)
        logger.exception(
            "processor_not_found",
            processor_id=processor_id,
            location=location,
            project_id=project_id,
            error=error_msg,
        )
        flush_loggers()
        raise ValueError(
            f"Processor '{processor_id}' not found in location '{location}' "
            f"for project '{project_id}'. "
            f"Please verify the processor exists in this location using "
            f"Google Cloud Console. Error: {error_msg}"
        ) from e
    except Exception as e:
        logger.error(
            "document_processing_failed",
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True,
        )
        flush_loggers()
        raise PDFProcessingError("", f"Document processing failed: {str(e)}") from e


def _extract_text_with_page_markers(document: documentai.Document) -> str:
    """Extract text from document with page markers.

    Args:
        document: Document AI document

    Returns:
        Text content with page markers
    """
    text_with_page_markers = ""
    raw_text = normalize_to_nfc(document.text)
    pages = document.pages

    logger.debug("document_ai_pages_extracted", page_count=len(pages))

    for i, page in enumerate(pages):
        page_number = i + 1
        page_height = page.dimension.height

        if i > 0:
            text_with_page_markers += f"\n\n----- Page {page_number} -----\n\n"

        blocks = _extract_page_blocks(page, raw_text, page_height)
        blocks.sort()  # Sort by vertical position

        for _, block_text in blocks:
            text_with_page_markers += block_text + " "

    return text_with_page_markers


def _extract_block_text(block: Any, raw_text: str) -> str | None:
    """Extract text from a single block.

    Args:
        block: Document AI block object
        raw_text: Full document text

    Returns:
        Block text if valid, None otherwise
    """
    if not block.layout.text_anchor:
        return None

    start_index = block.layout.text_anchor.text_segments[0].start_index
    end_index = block.layout.text_anchor.text_segments[0].end_index

    if start_index == end_index:
        return None

    return normalize_to_nfc(raw_text[start_index:end_index])


def _get_block_vertical_position(block: Any, page_height: float) -> float | None:
    """Get normalized vertical position of a block.

    Args:
        block: Document AI block object
        page_height: Height of the page for normalization

    Returns:
        Normalized vertical position (0-1) or None if unavailable
    """
    if not (block.layout.bounding_poly and block.layout.bounding_poly.vertices):
        return None

    vertices = block.layout.bounding_poly.vertices
    top_y = min(v.y for v in vertices) / page_height
    return top_y


def _extract_page_blocks(
    page: documentai.Document.Page, raw_text: str, page_height: float
) -> list[tuple[float, str]]:
    """Extract and sort text blocks from a page.

    Args:
        page: Document AI page object
        raw_text: Full document text
        page_height: Height of the page for normalization

    Returns:
        List of tuples (vertical_position, block_text)
    """
    blocks: list[tuple[float, str]] = []

    for block in page.blocks:
        block_text = _extract_block_text(block, raw_text)
        if not block_text:
            continue

        vertical_pos = _get_block_vertical_position(block, page_height)
        if vertical_pos is not None:
            blocks.append((vertical_pos, block_text))

    return blocks


def process_pdf(
    file_path: str,
    rate_limiter: RateLimiter | None = None,
    max_pages: int = 15,
    project_id: str | None = None,
    location: str | None = None,
    processor_id: str | None = None,
    include_layout: bool = True,
) -> tuple[str, dict[str, Any] | None]:
    """
    Process a PDF file through Google's Document AI and return the extracted text with page markers.

    Args:
        file_path: Path to the PDF file
        rate_limiter: Optional rate limiter for API calls
        max_pages: Maximum number of pages to process (default: 15)
        project_id: Google Cloud project ID
        location: Document AI location
        processor_id: Document AI processor ID
        include_layout: Whether to include layout information in the response

    Returns:
        Tuple of (text_with_page_markers, document_json)

    Raises:
        PDFProcessingError: If processing fails
        ConfigurationError: If configuration is missing
        PDFParseError: If file cannot be processed
    """
    # Load and validate configuration early
    try:
        resolved_project_id, resolved_location, resolved_processor_id = (
            _load_processing_config(project_id, location, processor_id)
        )
    except ConfigurationError:
        raise

    # Validate file early
    try:
        _validate_file_for_processing(file_path)
    except PDFParseError:
        raise

    # Apply rate limiting if provided
    if rate_limiter:
        rate_limiter.wait_if_needed()

    # Process the document
    try:
        client = _create_document_ai_client(resolved_location)

        with open(file_path, "rb") as pdf_file:
            pdf_content = pdf_file.read()

        document = _process_document_with_client(
            client,
            resolved_project_id,
            resolved_location,
            resolved_processor_id,
            pdf_content,
        )
    except (PDFProcessingError, ValueError) as e:
        raise PDFProcessingError(file_path, str(e)) from e

    # Extract and process text
    text_with_page_markers = _extract_text_with_page_markers(document)
    raw_text = normalize_to_nfc(document.text)

    # Handle empty text fallback
    if not text_with_page_markers.strip() and raw_text:
        text_with_page_markers = raw_text
        logger.warning(
            "fallback_text_extraction_used",
            file_path=file_path,
            reason="page_markers_empty",
        )

    logger.info(
        "document_processing_completed",
        file_path=file_path,
        characters_extracted=len(raw_text),
        page_count=len(document.pages),
    )

    # Convert to JSON if requested
    document_json = _document_to_dict(document) if include_layout else None

    return text_with_page_markers, document_json


def _extract_text_from_anchor(text_anchor: Any, document_text: str) -> str:
    """Extract text from a text anchor.

    Args:
        text_anchor: Document AI text anchor object
        document_text: Full document text

    Returns:
        Extracted and normalized text
    """
    if not text_anchor:
        return ""

    text_parts: list[str] = []
    for segment in text_anchor.text_segments:
        start_index = segment.start_index
        end_index = segment.end_index
        if start_index < end_index:
            text_parts.append(document_text[start_index:end_index])

    return normalize_to_nfc("".join(text_parts))


def _process_text_elements(
    elements: list[Any], document_text: str
) -> list[dict[str, Any]]:
    """Process a list of text elements (blocks, paragraphs, lines, tokens).

    Args:
        elements: List of text elements to process
        document_text: Full document text

    Returns:
        List of dictionaries containing layout and text
    """
    result: list[dict[str, Any]] = []
    for element in elements:
        element_text = _extract_text_from_anchor(
            element.layout.text_anchor, document_text
        )
        element_dict = {
            "layout": _layout_to_dict(element.layout, document_text),
            "text": element_text,
        }
        result.append(element_dict)
    return result


def _process_page_to_dict(
    page: documentai.Document.Page, page_idx: int, document_text: str
) -> dict[str, Any]:
    """Process a single page to dictionary format.

    Args:
        page: Document AI page object
        page_idx: Page index (0-based)
        document_text: Full document text

    Returns:
        Dictionary representation of the page
    """
    page_dict: dict[str, Any] = {
        "page_number": page_idx + 1,
        "dimension": {
            "width": page.dimension.width,
            "height": page.dimension.height,
        },
        "blocks": _process_text_elements(page.blocks, document_text),
        "paragraphs": _process_text_elements(page.paragraphs, document_text),
        "lines": _process_text_elements(page.lines, document_text),
        "tokens": _process_text_elements(page.tokens, document_text),
        "text": "",
    }

    # Extract page text from blocks
    page_text_blocks = [block["text"] for block in page_dict["blocks"] if block["text"]]
    page_dict["text"] = normalize_to_nfc(" ".join(page_text_blocks))

    return page_dict


def _document_to_dict(document: documentai.Document) -> dict[str, Any]:
    """
    Convert a Document AI document to a JSON-serializable dictionary.

    Args:
        document: The Document AI document object

    Returns:
        dict: A JSON-serializable dictionary representation of the document
    """
    doc_dict: dict[str, Any] = {
        "text": normalize_to_nfc(document.text),
        "pages": [],
    }

    document_text = document.text
    for page_idx, page in enumerate(document.pages):
        page_dict = _process_page_to_dict(page, page_idx, document_text)
        doc_dict["pages"].append(page_dict)

    return doc_dict


def _layout_to_dict(
    layout: documentai.Document.Page.Layout, document_text: str
) -> dict[str, Any]:
    """
    Convert a Document AI layout to a JSON-serializable dictionary.

    Args:
        layout: The Document AI layout object
        document_text: The document text for extracting text segments

    Returns:
        dict: A JSON-serializable dictionary representation of the layout
    """
    layout_dict: dict[str, Any] = {
        "confidence": layout.confidence,
        "bounding_poly": None,
        "text": "",
    }

    # Convert bounding poly if present
    if layout.bounding_poly and layout.bounding_poly.vertices:
        layout_dict["bounding_poly"] = {
            "vertices": [
                {"x": vertex.x, "y": vertex.y}
                for vertex in layout.bounding_poly.vertices
            ]
        }

    # Extract text if text anchor is present
    if layout.text_anchor:
        text_segments = []
        for segment in layout.text_anchor.text_segments:
            start_index = segment.start_index
            end_index = segment.end_index
            if start_index < end_index:
                text_segments.append(
                    normalize_to_nfc(document_text[start_index:end_index])
                )

        layout_dict["text"] = normalize_to_nfc(" ".join(text_segments))

    return layout_dict


def get_document_ai_client() -> documentai.DocumentProcessorServiceClient:
    """
    Create and return a Document AI client with regional endpoint configured.

    Returns:
        A Document AI client instance configured for the processor location
    """
    # Get location from environment, defaulting to 'us' if not set
    location = os.getenv("DOCUMENT_AI_LOCATION", "us")

    # Configure the client with the regional endpoint
    api_endpoint = _get_document_ai_api_endpoint(location)
    return documentai.DocumentProcessorServiceClient(
        client_options={"api_endpoint": api_endpoint}
    )
