"""Alternative format converter for Google Document AI JSON.

This module handles conversion of alternative JSON formats including
chunked formats, hybrid formats, and files array formats.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from philocr.utils.markdown_converter.alternative_format_detector import (
    AlternativeFormatDetector,
)
from philocr.utils.markdown_converter.alternative_metadata_extractor import (
    AlternativeMetadataExtractor,
)
from philocr.utils.markdown_converter.chunked_text_processor import ChunkedTextProcessor
from philocr.utils.markdown_converter.exceptions import AlternativeFormatError
from philocr.utils.markdown_converter.files_array_processor import FilesArrayProcessor
from philocr.utils.markdown_converter.hybrid_format_processor import (
    HybridFormatProcessor,
)

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)


class AlternativeFormatConverter:
    """Converts alternative JSON formats to Markdown."""

    @staticmethod
    def convert(json_data: dict[str, Any]) -> str:
        """Convert alternative JSON format to Markdown.

        Args:
            json_data: JSON data in the alternative format.

        Returns:
            Markdown representation of the document.

        Raises:
            AlternativeFormatError: If conversion fails.
        """
        logger.info("alternative_format_conversion_starting")

        try:
            markdown_parts: list[str] = []
            page_content_map: dict[int, str] = {}

            # Add document metadata if available
            AlternativeMetadataExtractor.add_document_metadata(
                json_data, markdown_parts
            )

            # Detect format type
            is_chunked_format = AlternativeFormatDetector.detect_chunked(json_data)
            has_hybrid_format = AlternativeFormatDetector.detect_hybrid(
                json_data, is_chunked_format
            )

            # Process based on format type
            if has_hybrid_format:
                return HybridFormatProcessor.process(
                    json_data, markdown_parts, page_content_map
                )
            elif "files" in json_data and isinstance(json_data["files"], list):
                return FilesArrayProcessor.process(
                    json_data, markdown_parts, is_chunked_format, page_content_map
                )
            elif "text" in json_data:
                return ChunkedTextProcessor.process_chunked(
                    json_data, markdown_parts, is_chunked_format
                )
            else:
                raise AlternativeFormatError("Unknown alternative format structure")

        except (KeyError, ValueError, re.error) as e:
            logger.error(
                "alternative_format_conversion_failed",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            from philocr.utils.logging_config import flush_loggers

            flush_loggers()
            raise AlternativeFormatError(
                f"Failed to convert alternative format: {e}"
            ) from e
