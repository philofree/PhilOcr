"""Stage 3: OCR on masked body region images."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from google.api_core import exceptions as google_exceptions
from google.cloud import documentai

from philocr.models.config import PipelineConfig
from philocr.models.ocr_result import OCRResult
from philocr.models.page import CroppedPage, MaskedPage
from philocr.pipeline.utils.docai_helpers import (
    calculate_average_confidence,
    extract_blocks,
    extract_lines,
    extract_paragraphs,
)
from philocr.pipeline.utils.image_io import load_image_bytes
from philocr.processing.document_ai import (
    RateLimiter,
    _create_document_ai_client,
    _load_processing_config,
)

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)


def ocr_masked_page(
    masked_page: MaskedPage | CroppedPage,
    rate_limiter: RateLimiter,
    config: PipelineConfig,
    project_id: str | None = None,
    location: str | None = None,
    processor_id: str | None = None,
) -> OCRResult:
    """Send masked page to Document AI for OCR.

    Document AI handles:
    - Line detection
    - Word detection
    - Character recognition

    We just send the image and receive text.

    Args:
        masked_page: MaskedPage or CroppedPage object with path to masked image
        rate_limiter: Rate limiter for API calls
        config: Pipeline configuration
        project_id: Optional Google Cloud project ID
        location: Optional Document AI location
        processor_id: Optional Document AI processor ID

    Returns:
        OCRResult with extracted text and structure
    """
    # Apply rate limiting
    rate_limiter.wait_if_needed()

    # Load image bytes
    image_path = (
        masked_page.masked_path
        if isinstance(masked_page, MaskedPage)
        else masked_page.cropped_path
    )
    image_bytes = load_image_bytes(image_path)

    try:
        # Load configuration
        resolved_project_id, resolved_location, resolved_processor_id = (
            _load_processing_config(project_id, location, processor_id)
        )

        # Create client
        client = _create_document_ai_client(resolved_location)

        # Process image (not PDF)
        name = (
            f"projects/{resolved_project_id}/locations/{resolved_location}/"
            f"processors/{resolved_processor_id}"
        )
        request = documentai.ProcessRequest(
            name=name,
            raw_document=documentai.RawDocument(
                content=image_bytes, mime_type="image/png"
            ),
        )

        result = client.process_document(request=request)
        document = result.document

        full_text = document.text if document.text else ""

        return OCRResult(
            page_num=masked_page.page_num,
            text=full_text,
            blocks=extract_blocks(document, full_text),
            paragraphs=extract_paragraphs(document, full_text),
            lines=extract_lines(document, full_text),
            confidence=calculate_average_confidence(document),
            raw_response=document,
        )

    except google_exceptions.InvalidArgument as e:
        error_msg = str(e)
        logger.error(
            "ocr_invalid_argument",
            page_num=masked_page.page_num,
            error=error_msg,
            exc_info=True,
        )
        return OCRResult(
            page_num=masked_page.page_num,
            text="",
            blocks=[],
            paragraphs=[],
            lines=[],
            confidence=0.0,
            error=f"Invalid argument: {error_msg}",
        )
    except Exception as e:
        logger.error(
            "ocr_processing_failed",
            page_num=masked_page.page_num,
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True,
        )
        from philocr.utils.logging_config import flush_loggers

        flush_loggers()
        raise RuntimeError(
            f"CRITICAL: OCR processing failed for page {masked_page.page_num} - {e}"
        ) from e


def ocr_with_retry(
    masked_page: MaskedPage | CroppedPage,
    rate_limiter: RateLimiter,
    config: PipelineConfig,
    project_id: str | None = None,
    location: str | None = None,
    processor_id: str | None = None,
) -> OCRResult:
    """OCR with retry logic for transient failures.

    Args:
        masked_page: MaskedPage or CroppedPage to process
        rate_limiter: Rate limiter instance
        config: Pipeline configuration
        project_id: Optional Google Cloud project ID
        location: Optional Document AI location
        processor_id: Optional Document AI processor ID

    Returns:
        OCRResult (may have error if all retries failed)
    """
    for attempt in range(config.ocr_max_retries):
        try:
            result = ocr_masked_page(
                masked_page,
                rate_limiter,
                config,
                project_id,
                location,
                processor_id,
            )

            if result.error is None:
                return result

        except ConnectionError as e:
            logger.warning(
                "ocr_retry_attempt_failed_transient",
                page_num=masked_page.page_num,
                attempt=attempt + 1,
                max_retries=config.ocr_max_retries,
                error=str(e),
                error_type=type(e).__name__,
            )
        except Exception as e:
            logger.error(
                "ocr_retry_attempt_failed_non_transient",
                page_num=masked_page.page_num,
                attempt=attempt + 1,
                max_retries=config.ocr_max_retries,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            from philocr.utils.logging_config import flush_loggers

            flush_loggers()
            raise RuntimeError(
                f"CRITICAL: OCR processing failed (non-transient error) for page {masked_page.page_num} - {e}"
            ) from e

        # Exponential backoff
        if attempt < config.ocr_max_retries - 1:
            backoff_time = config.ocr_retry_backoff_base**attempt
            time.sleep(backoff_time)

    # All retries failed
    logger.error(
        "ocr_all_retries_failed",
        page_num=masked_page.page_num,
        max_retries=config.ocr_max_retries,
    )
    return OCRResult(
        page_num=masked_page.page_num,
        text="",
        blocks=[],
        paragraphs=[],
        lines=[],
        confidence=0.0,
        error=f"Failed after {config.ocr_max_retries} attempts",
    )


def ocr_all_pages(
    masked_pages: list[MaskedPage] | list[CroppedPage],
    rate_limiter: RateLimiter,
    config: PipelineConfig,
    project_id: str | None = None,
    location: str | None = None,
    processor_id: str | None = None,
) -> list[OCRResult]:
    """Process OCR for multiple pages with rate limiting.

    Note: Rate limiting prevents true parallelization, but sequential
    processing with rate limiting is efficient for API calls.

    Args:
        masked_pages: List of masked/cropped pages to process
        rate_limiter: Rate limiter instance (configured for API rate limits)
        config: Pipeline configuration
        project_id: Optional Google Cloud project ID
        location: Optional Document AI location
        processor_id: Optional Document AI processor ID

    Returns:
        List of OCRResult objects
    """
    results: list[OCRResult] = []

    for i, page in enumerate(masked_pages):
        logger.debug(
            "ocr_processing_page",
            page_num=page.page_num,
            page_index=i + 1,
            total_pages=len(masked_pages),
        )

        result = ocr_with_retry(
            page,
            rate_limiter,
            config,
            project_id,
            location,
            processor_id,
        )
        results.append(result)

    return results
