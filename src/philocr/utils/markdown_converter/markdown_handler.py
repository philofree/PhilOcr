"""
Markdown Handler for Google Document AI JSON output.

This module provides utilities for converting Google Document AI JSON
to Markdown format, based on the AcademicDocumentParser.

This is a facade class that orchestrates conversion operations by delegating
to specialized modules for format detection, alternative format conversion,
chunk processing, file operations, and HTML conversion.
"""

import os
from collections.abc import Generator
from typing import TYPE_CHECKING, Any

from philocr.utils.markdown_converter.academic_doc_parser import AcademicDocumentParser
from philocr.utils.markdown_converter.alternative_format_converter import (
    AlternativeFormatConverter,
)
from philocr.utils.markdown_converter.chunk_processor import ChunkProcessor
from philocr.utils.markdown_converter.exceptions import (
    AlternativeFormatError,
    ChunkProcessingError,
    FormatDetectionError,
    MarkdownConversionError,
)
from philocr.utils.markdown_converter.file_operations import FileOperations
from philocr.utils.markdown_converter.format_detector import FormatDetector, FormatType
from philocr.utils.markdown_converter.html_converter import HTMLConverter
from philocr.utils.markdown_converter.streaming_academic_doc_parser import (
    StreamingAcademicDocumentParser,
)

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)

# Check if ijson is available
_ijson_available_check = True
try:
    import ijson  # type: ignore[reportMissingImports]  # noqa: F401

    logger.info(
        "ijson_available",
        package_name="ijson",
        will_use_for="large_file_processing",
        streaming_parser_available=True,
    )
except ImportError as e:
    _ijson_available_check = False
    logger.error(
        "ijson_required_but_not_available",
        package_name="ijson",
        error=str(e),
        error_type=type(e).__name__,
        exc_info=True,
    )
    from philocr.utils.logging_config import flush_loggers

    flush_loggers()
    raise RuntimeError(
        "CRITICAL: ijson is required for large file processing. "
        "Install with: pip install ijson"
    ) from e

IJSON_AVAILABLE: bool = _ijson_available_check


class MarkdownHandler:
    """Handles conversion between Google Document AI JSON and markdown format."""

    # Maximum size in MB before using streaming parser
    LARGE_FILE_THRESHOLD_MB = 5

    # Chunk size for reading large files (in bytes)
    CHUNK_SIZE = 1024 * 1024 * 10  # 10MB chunks

    @staticmethod
    def convert_to_markdown(json_data: dict[str, Any]) -> str:
        """
        Convert Google Document AI JSON to Markdown format.

        Args:
            json_data: JSON data from Google Document AI

        Returns:
            Markdown representation of the document

        Raises:
            MarkdownConversionError: If conversion fails
            FormatDetectionError: If format detection fails
        """
        logger.info("markdown_conversion_starting")

        if not json_data:
            logger.error("json_data_missing_for_markdown")
            raise MarkdownConversionError("JSON data is empty or None")

        try:
            # Detect format type
            format_type = FormatDetector.detect_format(json_data)

            # If alternative format, use alternative converter
            if format_type == FormatType.ALTERNATIVE:
                return AlternativeFormatConverter.convert(json_data)

            # Analyze structure for logging
            structure_info = FormatDetector.analyze_structure(json_data)

            # Use standard parser for standard format
            logger.info("academic_parser_creating")
            parser = AcademicDocumentParser(json_data)

            logger.info("parser_to_markdown_calling")
            markdown: str = parser.to_markdown()
            markdown_length = len(markdown)

            if markdown_length == 0:
                logger.error("markdown_conversion_returned_empty")
                raise MarkdownConversionError(
                    "Markdown conversion produced empty content"
                )

            logger.info(
                "markdown_conversion_completed",
                markdown_length=markdown_length,
            )

            preview = markdown[:200].replace("\n", "\\n")
            logger.info(
                "markdown_preview",
                preview=preview,
                total_length=markdown_length,
            )

            return markdown

        except (FormatDetectionError, AlternativeFormatError) as e:
            logger.error(
                "markdown_conversion_failed",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            from philocr.utils.logging_config import flush_loggers

            flush_loggers()
            raise

        except (KeyError, ValueError, AttributeError) as e:
            logger.error(
                "markdown_conversion_failed",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            from philocr.utils.logging_config import flush_loggers

            flush_loggers()
            raise MarkdownConversionError(f"Failed to convert to markdown: {e}") from e

    @staticmethod
    def convert_alternative_format(json_data: dict[str, Any]) -> str:
        """
        Convert alternative JSON format to Markdown.

        Args:
            json_data: JSON data in the alternative format

        Returns:
            Markdown representation of the document

        Raises:
            AlternativeFormatError: If conversion fails
        """
        return AlternativeFormatConverter.convert(json_data)

    @staticmethod
    def process_json_in_chunks(file_path: str) -> Generator[dict[str, Any], None, None]:
        """
        Process a large JSON file in chunks to reduce memory usage.

        Args:
            file_path: Path to the large JSON file

        Yields:
            Chunks of pages from the document

        Raises:
            ChunkProcessingError: If processing fails
        """
        yield from ChunkProcessor.process_in_chunks(file_path)

    @staticmethod
    def convert_large_json_to_markdown(json_file_path: str) -> str:
        """
        Convert large Google Document AI JSON file to Markdown format.

        Args:
            json_file_path: Path to the JSON file

        Returns:
            Markdown representation of the document

        Raises:
            MarkdownConversionError: If conversion fails
            ChunkProcessingError: If chunk processing fails
        """
        logger.info(
            "large_file_markdown_conversion_starting",
            json_file_path=json_file_path,
        )

        try:
            file_size_bytes = os.path.getsize(json_file_path)
            file_size_mb = file_size_bytes / (1024 * 1024)
            logger.info(
                "large_file_size_check",
                file_size_mb=round(file_size_mb, 2),
                file_size_bytes=file_size_bytes,
            )

            # Try streaming parser if ijson is available
            if IJSON_AVAILABLE:
                try:
                    logger.info(
                        "streaming_parser_using",
                        parser_type="ijson",
                        parser_implementation="StreamingAcademicDocumentParser",
                        file_size_mb=file_size_mb,
                    )
                    parser = StreamingAcademicDocumentParser(json_file_path)
                    markdown: str = parser.to_markdown()
                    markdown_length = len(markdown)

                    if markdown_length == 0:
                        logger.error("streaming_conversion_returned_empty")
                        logger.warning("falling_back_to_chunked_processing")
                    else:
                        logger.info(
                            "streaming_conversion_completed",
                            markdown_length=markdown_length,
                            method="ijson_streaming",
                        )
                        return markdown

                except (OSError, ValueError, KeyError) as e:
                    logger.error(
                        "streaming_conversion_failed",
                        error=str(e),
                        error_type=type(e).__name__,
                        exc_info=True,
                    )
                    from philocr.utils.logging_config import flush_loggers

                    flush_loggers()
                    raise RuntimeError(
                        f"CRITICAL: Streaming conversion failed - {e}"
                    ) from e
            else:
                logger.info(
                    "ijson_not_available_using_chunked",
                    fallback_mode="chunked_processing",
                    file_size_mb=file_size_mb,
                    reason="ijson_not_installed",
                )

            # Use chunked processing as fallback
            logger.info("chunked_processing_starting", reason="large_file")

            all_markdown_parts = []
            page_count = 0

            for chunk_idx, chunk in enumerate(
                ChunkProcessor.process_in_chunks(json_file_path)
            ):
                logger.info("chunk_converting", chunk_number=chunk_idx + 1)

                chunk_markdown = MarkdownHandler.convert_to_markdown(chunk)

                if "document_data" in chunk and "pages" in chunk["document_data"]:
                    page_count += len(chunk["document_data"]["pages"])

                if chunk_markdown:
                    all_markdown_parts.append(chunk_markdown)

            if all_markdown_parts:
                markdown = "\n\n".join(all_markdown_parts)
                logger.info(
                    "chunked_processing_completed",
                    page_count=page_count,
                    method="chunked_processing",
                )
                return markdown
            else:
                logger.error("chunked_processing_no_output")
                raise MarkdownConversionError(
                    "Conversion failed - no valid markdown generated"
                )

        except (ChunkProcessingError, MarkdownConversionError) as e:
            logger.error(
                "large_file_markdown_conversion_failed",
                json_file_path=json_file_path,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            from philocr.utils.logging_config import flush_loggers

            flush_loggers()
            raise

        except (OSError, ValueError) as e:
            logger.error(
                "large_file_markdown_conversion_failed",
                json_file_path=json_file_path,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            from philocr.utils.logging_config import flush_loggers

            flush_loggers()
            raise MarkdownConversionError(f"Failed to convert large file: {e}") from e

    @staticmethod
    def convert_to_html(json_data: dict[str, Any]) -> str:
        """
        Convert Google Document AI JSON to HTML format with academic layout.

        Args:
            json_data: JSON data from Google Document AI

        Returns:
            HTML representation of the document

        Raises:
            HTMLConversionError: If conversion fails
        """
        return HTMLConverter.convert(json_data, AlternativeFormatConverter.convert)

    @staticmethod
    def save_as_markdown(json_data: dict[str, Any], file_path: str) -> bool:
        """
        Convert JSON data to Markdown and save to file.

        Args:
            json_data: JSON data to convert
            file_path: Path where to save the markdown file

        Returns:
            True if successful, False otherwise
        """
        return FileOperations.save_markdown(
            json_data, file_path, MarkdownHandler.convert_to_markdown
        )

    @staticmethod
    def save_file_as_markdown(json_file_path: str, output_file_path: str) -> bool:
        """
        Convert a JSON file to Markdown and save to file.

        This method automatically chooses between regular and streaming conversion
        based on file size.

        Args:
            json_file_path: Path to the JSON file to convert
            output_file_path: Path where to save the markdown file

        Returns:
            True if successful, False otherwise
        """
        return FileOperations.save_file(
            json_file_path,
            output_file_path,
            MarkdownHandler.convert_large_json_to_markdown,
            MarkdownHandler.convert_to_markdown,
        )

    @staticmethod
    def debug_markdown_conversion() -> str:
        """
        Run a debug conversion with a simple test document.

        Returns:
            Debug information and test conversion result
        """
        logger.info("debug_markdown_conversion_starting", test_data=True)

        test_document = {
            "document_data": {
                "pages": [
                    {
                        "page_number": 1,
                        "lines": [
                            {
                                "text": "This is a test header",
                                "layout": {
                                    "bounding_poly": {
                                        "vertices": [
                                            {"x": 100, "y": 100},
                                            {"x": 500, "y": 100},
                                            {"x": 500, "y": 120},
                                            {"x": 100, "y": 120},
                                        ]
                                    },
                                    "confidence": 0.98,
                                },
                            },
                            {
                                "text": "This is a test paragraph.",
                                "layout": {
                                    "bounding_poly": {
                                        "vertices": [
                                            {"x": 100, "y": 150},
                                            {"x": 500, "y": 150},
                                            {"x": 500, "y": 170},
                                            {"x": 100, "y": 170},
                                        ]
                                    },
                                    "confidence": 0.95,
                                },
                            },
                        ],
                    }
                ]
            }
        }

        try:
            logger.info("debug_parser_creating")
            parser = AcademicDocumentParser(test_document)

            logger.info("debug_test_document_converting")
            markdown = parser.to_markdown()

            markdown_length = len(markdown)
            logger.info(
                "debug_markdown_conversion_result",
                markdown_length=markdown_length,
                preview=markdown[:200] if markdown else "",
            )

            return (
                f"Debug conversion successful, content length: "
                f"{markdown_length} characters.\nContent:\n\n{markdown}"
            )

        except (KeyError, ValueError, AttributeError) as e:
            logger.error(
                "debug_conversion_failed",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            from philocr.utils.logging_config import flush_loggers

            flush_loggers()
            raise RuntimeError(f"CRITICAL: Debug conversion failed - {e}") from e
