"""
Format detection for Google Document AI JSON structures.

This module provides functionality to detect and analyze the structure
of Google Document AI JSON files to determine the appropriate conversion strategy.
"""

from typing import TYPE_CHECKING, Any, NamedTuple

from philocr.utils.logging_config import flush_loggers
from philocr.utils.markdown_converter.exceptions import FormatDetectionError

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)


class FormatType:
    """Enumeration of supported JSON format types."""

    STANDARD = "standard"
    ALTERNATIVE = "alternative"
    UNKNOWN = "unknown"


class StructureInfo(NamedTuple):
    """Information about the JSON structure."""

    has_document_data: bool
    has_files_array: bool
    has_text: bool
    has_pages: bool
    page_count: int


class FormatDetector:
    """Detects and analyzes Google Document AI JSON format structures."""

    @staticmethod
    def detect_format(json_data: dict[str, Any]) -> str:
        """
        Detect the format type of the JSON data.

        Args:
            json_data: JSON data from Google Document AI

        Returns:
            Format type string ("standard" or "alternative")

        Raises:
            FormatDetectionError: If format detection fails due to invalid data
        """
        try:
            if not json_data:
                raise FormatDetectionError("JSON data is empty or None")

            has_document_data = "document_data" in json_data
            has_files_array = "files" in json_data
            has_top_level_pages = "pages" in json_data and "text" in json_data

            if has_files_array:
                logger.info(
                    "alternative_json_format_detected", format_type="files_array"
                )
                return FormatType.ALTERNATIVE

            if has_document_data:
                logger.info("standard_json_format_detected", format_type="standard")
                return FormatType.STANDARD

            # Recognize top-level pages/text format as standard (PhilOcr format)
            if has_top_level_pages:
                logger.info(
                    "standard_json_format_detected",
                    format_type="standard",
                    variant="top_level_structure",
                )
                return FormatType.STANDARD

            logger.warning(
                "unknown_json_format_detected", json_keys=list(json_data.keys())
            )
            return FormatType.UNKNOWN

        except (TypeError, AttributeError) as e:
            logger.error(
                "format_detection_failed",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            flush_loggers()
            raise FormatDetectionError(f"Failed to detect format: {e}") from e

    @staticmethod
    def analyze_structure(json_data: dict[str, Any]) -> StructureInfo:
        """
        Analyze the structure of JSON data.

        Args:
            json_data: JSON data from Google Document AI

        Returns:
            StructureInfo containing structure analysis results

        Raises:
            FormatDetectionError: If structure analysis fails
        """
        try:
            has_document_data = "document_data" in json_data
            has_files_array = "files" in json_data
            has_text = "text" in json_data
            has_pages = False
            page_count = 0

            if has_document_data:
                doc_data = json_data["document_data"]
                if not isinstance(doc_data, dict):
                    raise FormatDetectionError("document_data is not a dictionary")
                has_pages = "pages" in doc_data
                if has_pages and isinstance(doc_data["pages"], list):
                    page_count = len(doc_data["pages"])
            else:
                # Check for top-level pages when document_data is not present
                has_pages = "pages" in json_data
                if has_pages and isinstance(json_data["pages"], list):
                    page_count = len(json_data["pages"])

            structure_info = StructureInfo(
                has_document_data=has_document_data,
                has_files_array=has_files_array,
                has_text=has_text,
                has_pages=has_pages,
                page_count=page_count,
            )

            logger.info(
                "json_structure_analyzed",
                has_document_data=has_document_data,
                has_text=has_text,
                has_pages=has_pages,
                page_count=page_count,
            )

            return structure_info

        except (KeyError, TypeError, AttributeError) as e:
            logger.error(
                "structure_analysis_failed",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            flush_loggers()
            raise FormatDetectionError(f"Failed to analyze structure: {e}") from e
