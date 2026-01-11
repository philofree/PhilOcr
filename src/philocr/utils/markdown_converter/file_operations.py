"""
File operations for markdown conversion.

This module provides functionality to save markdown content to files
with proper error handling for file I/O operations.
"""

import json
import os
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)


class FileOperations:
    """Handles file operations for markdown conversion."""

    # Maximum file size in MB before using streaming parser
    LARGE_FILE_THRESHOLD_MB = 5

    @staticmethod
    def save_markdown(
        json_data: dict[str, Any],
        file_path: str,
        conversion_func: Callable[[dict[str, Any]], str],
    ) -> bool:
        """
        Convert JSON data to Markdown and save to file.

        Args:
            json_data: JSON data to convert
            file_path: Path where to save the markdown file
            conversion_func: Function to convert JSON to markdown

        Returns:
            True if successful, False otherwise
        """
        logger.info(
            "markdown_save_starting",
            file_path=file_path,
        )

        try:
            # Convert JSON to markdown
            markdown_content = conversion_func(json_data)

            markdown_length = len(markdown_content)
            logger.info(
                "markdown_content_ready",
                markdown_length=markdown_length,
                file_path=file_path,
            )

            if markdown_length == 0:
                logger.error("markdown_content_empty_cannot_save", file_path=file_path)
                from philocr.utils.logging_config import flush_loggers

                flush_loggers()
                raise ValueError(f"CRITICAL: Markdown content is empty, cannot save to {file_path}")

            # Write to file
            FileOperations._write_file(file_path, markdown_content)

            logger.info(
                "markdown_save_completed",
                file_path=file_path,
                markdown_length=markdown_length,
            )
            return True

        except (FileNotFoundError, PermissionError, OSError) as e:
            logger.error(
                "file_save_failed",
                file_path=file_path,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            from philocr.utils.logging_config import flush_loggers

            flush_loggers()
            raise RuntimeError(f"CRITICAL: File save failed for {file_path} - {e}") from e

    @staticmethod
    def save_file(
        json_file_path: str,
        output_file_path: str,
        convert_func: Callable[[str], str],
        convert_markdown_func: Callable[[dict[str, Any]], str],
    ) -> bool:
        """
        Convert a JSON file to Markdown and save to file.

        This method automatically chooses between regular and streaming conversion
        based on file size.

        Args:
            json_file_path: Path to the JSON file to convert
            output_file_path: Path where to save the markdown file
            convert_func: Function to convert large JSON file to markdown
            convert_markdown_func: Function to convert JSON data to markdown

        Returns:
            True if successful, False otherwise
        """
        logger.info(
            "json_file_to_markdown_starting",
            json_file_path=json_file_path,
            output_file_path=output_file_path,
        )

        try:
            # Check file size
            file_size_bytes = os.path.getsize(json_file_path)
            file_size_mb = file_size_bytes / (1024 * 1024)
            logger.info(
                "json_file_size_check",
                file_size_mb=round(file_size_mb, 2),
                file_size_bytes=file_size_bytes,
                threshold_mb=FileOperations.LARGE_FILE_THRESHOLD_MB,
            )

            # Try regular parser first for smaller files
            if file_size_mb <= FileOperations.LARGE_FILE_THRESHOLD_MB:
                success = FileOperations._try_regular_conversion(
                    json_file_path,
                    output_file_path,
                    file_size_mb,
                    convert_markdown_func,
                )
                if success:
                    return True

            # Use specialized processing for large files
            logger.info(
                "large_file_processing_using",
                json_file_path=json_file_path,
            )
            markdown_content = convert_func(json_file_path)

            markdown_length = len(markdown_content)
            logger.info(
                "markdown_content_ready_save_large",
                markdown_length=markdown_length,
                output_file_path=output_file_path,
            )

            if markdown_length == 0 or markdown_content.startswith("Error:"):
                logger.error(
                    "markdown_content_invalid_cannot_save",
                    output_file_path=output_file_path,
                    is_empty=markdown_length == 0,
                    starts_with_error=markdown_content.startswith("Error:"),
                )
                from philocr.utils.logging_config import flush_loggers

                flush_loggers()
                raise ValueError(
                    f"CRITICAL: Markdown content is invalid (empty or error) for {output_file_path}"
                )

            FileOperations._write_file(output_file_path, markdown_content)

            logger.info(
                "markdown_file_saved",
                output_file_path=output_file_path,
                markdown_length=markdown_length,
                method="large_file_processing",
            )
            return True

        except FileNotFoundError as e:
            logger.error(
                "file_not_found",
                json_file_path=json_file_path,
                output_file_path=output_file_path,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            from philocr.utils.logging_config import flush_loggers

            flush_loggers()
            raise RuntimeError(
                f"CRITICAL: File not found: {json_file_path} - {e}"
            ) from e

        except PermissionError as e:
            logger.error(
                "permission_denied",
                json_file_path=json_file_path,
                output_file_path=output_file_path,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            from philocr.utils.logging_config import flush_loggers

            flush_loggers()
            raise RuntimeError(
                f"CRITICAL: Permission denied for {json_file_path} - {e}"
            ) from e

        except OSError as e:
            logger.error(
                "io_error",
                json_file_path=json_file_path,
                output_file_path=output_file_path,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            from philocr.utils.logging_config import flush_loggers

            flush_loggers()
            raise RuntimeError(f"CRITICAL: I/O error for {json_file_path} - {e}") from e

    @staticmethod
    def _try_regular_conversion(
        json_file_path: str,
        output_file_path: str,
        file_size_mb: float,
        convert_markdown_func: Callable[[dict[str, Any]], str],
    ) -> bool:
        """Try regular conversion for small files."""
        try:
            logger.info(
                "regular_conversion_using",
                file_size_mb=round(file_size_mb, 2),
                threshold_mb=FileOperations.LARGE_FILE_THRESHOLD_MB,
            )

            with open(json_file_path, encoding="utf-8") as f:
                json_data = json.load(f)

            markdown_content = convert_markdown_func(json_data)

            if markdown_content and not markdown_content.startswith("Error:"):
                markdown_length = len(markdown_content)
                logger.info(
                    "markdown_content_ready_save",
                    markdown_length=markdown_length,
                    output_file_path=output_file_path,
                )

                FileOperations._write_file(output_file_path, markdown_content)

                logger.info(
                    "markdown_file_saved",
                    output_file_path=output_file_path,
                    markdown_length=markdown_length,
                    method="regular_conversion",
                )
                return True
            else:
                logger.error("regular_conversion_failed_or_errors")
                from philocr.utils.logging_config import flush_loggers

                flush_loggers()
                raise RuntimeError(
                    f"CRITICAL: Regular conversion failed - markdown content is invalid or empty"
                )

        except json.JSONDecodeError as e:
            logger.error(
                "json_decode_error",
                json_file_path=json_file_path,
                error=str(e),
                error_type=type(e).__name__,
                line=e.lineno if hasattr(e, "lineno") else None,
                column=e.colno if hasattr(e, "colno") else None,
                exc_info=True,
            )
            from philocr.utils.logging_config import flush_loggers

            flush_loggers()
            raise RuntimeError(
                f"CRITICAL: JSON decode error in {json_file_path} at line {e.lineno}, "
                f"column {e.colno} - {e}"
            ) from e

        except (FileNotFoundError, PermissionError, OSError) as e:
            logger.error(
                "regular_conversion_failed",
                json_file_path=json_file_path,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            from philocr.utils.logging_config import flush_loggers

            flush_loggers()
            raise RuntimeError(
                f"CRITICAL: Regular conversion failed for {json_file_path} - {e}"
            ) from e

    @staticmethod
    def _write_file(file_path: str, content: str) -> None:
        """
        Write content to file with proper error handling.

        Args:
            file_path: Path to write to
            content: Content to write

        Raises:
            FileNotFoundError: If directory doesn't exist
            PermissionError: If write permission denied
            OSError: If other OS error occurs
            IOError: If I/O error occurs
        """
        try:
            with open(file_path, "w", encoding="utf-8") as md_file:
                md_file.write(content)
        except FileNotFoundError:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as md_file:
                md_file.write(content)

    @staticmethod
    def determine_conversion_method(file_size_mb: float) -> str:
        """
        Determine conversion method based on file size.

        Args:
            file_size_mb: File size in megabytes

        Returns:
            Conversion method string ("regular" or "large_file")
        """
        if file_size_mb <= FileOperations.LARGE_FILE_THRESHOLD_MB:
            return "regular"
        else:
            return "large_file"
