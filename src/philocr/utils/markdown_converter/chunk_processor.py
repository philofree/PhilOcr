"""
Chunk processor for large JSON files.

This module provides functionality to process large Google Document AI JSON
files in chunks to reduce memory usage.
"""

import json
from collections.abc import Generator
from typing import TYPE_CHECKING, Any

from philocr.utils.markdown_converter.exceptions import ChunkProcessingError

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)


class ChunkProcessor:
    """Processes large JSON files in chunks."""

    # Default chunk size: process 10 pages at a time
    DEFAULT_CHUNK_SIZE = 10

    # Size of initial read to detect structure (10KB)
    STRUCTURE_DETECTION_SIZE = 10000

    @staticmethod
    def process_in_chunks(file_path: str) -> Generator[dict[str, Any], None, None]:
        """
        Process a large JSON file in chunks to reduce memory usage.

        This is a fallback method when ijson is not available.

        Args:
            file_path: Path to the large JSON file

        Yields:
            Chunks of pages from the document

        Raises:
            ChunkProcessingError: If processing fails
        """
        logger.info(
            "json_chunk_processing_starting",
            file_path=file_path,
        )

        try:
            with open(file_path, encoding="utf-8") as f:
                # Read first chunk to determine structure
                chunk = f.read(ChunkProcessor.STRUCTURE_DETECTION_SIZE)

                # Check for different JSON formats
                has_document_data = '"document_data"' in chunk
                has_files_array = '"files"' in chunk

                logger.info(
                    "document_structure_detected",
                    has_document_data=has_document_data,
                    has_files_array=has_files_array,
                )

                # Reset file position
                f.seek(0)

                # Read the full file but process only necessary parts
                data = json.load(f)

                # Handle alternative format with files array
                if has_files_array:
                    logger.info("alternative_format_processing_one_go")
                    yield data
                    return

                # Standard format with document_data
                if has_document_data:
                    document = data["document_data"]
                else:
                    document = data

                # Check if pages exist
                if "pages" not in document:
                    logger.error("no_pages_found_in_document")
                    raise ChunkProcessingError("No pages found in document")

                # Process pages in chunks
                all_pages = document["pages"]
                chunk_size = ChunkProcessor.DEFAULT_CHUNK_SIZE

                for i in range(0, len(all_pages), chunk_size):
                    chunk_pages = all_pages[i : i + chunk_size]

                    # Create a smaller document with just these pages
                    chunk_doc: dict[str, Any] = {
                        "document_data": {"pages": chunk_pages}
                    }
                    if "text" in data:
                        chunk_doc["text"] = data["text"]

                    chunk_number = i // chunk_size + 1
                    total_chunks = (len(all_pages) - 1) // chunk_size + 1
                    logger.info(
                        "page_chunk_processing",
                        chunk_number=chunk_number,
                        total_chunks=total_chunks,
                        pages_in_chunk=len(chunk_pages),
                        total_pages=len(all_pages),
                    )
                    yield chunk_doc

        except FileNotFoundError as e:
            logger.error(
                "file_not_found",
                file_path=file_path,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            from philocr.utils.logging_config import flush_loggers

            flush_loggers()
            raise ChunkProcessingError(f"File not found: {file_path}") from e

        except json.JSONDecodeError as e:
            logger.error(
                "json_decode_error",
                file_path=file_path,
                error=str(e),
                error_type=type(e).__name__,
                line=e.lineno if hasattr(e, "lineno") else None,
                column=e.colno if hasattr(e, "colno") else None,
                exc_info=True,
            )
            from philocr.utils.logging_config import flush_loggers

            flush_loggers()
            raise ChunkProcessingError(f"Invalid JSON in file {file_path}: {e}") from e

        except OSError as e:
            logger.error(
                "os_error_during_chunk_processing",
                file_path=file_path,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            from philocr.utils.logging_config import flush_loggers

            flush_loggers()
            raise ChunkProcessingError(
                f"OS error processing file {file_path}: {e}"
            ) from e

        except (KeyError, ValueError) as e:
            logger.error(
                "chunk_processing_failed",
                file_path=file_path,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            from philocr.utils.logging_config import flush_loggers

            flush_loggers()
            raise ChunkProcessingError(
                f"Failed to process chunks from {file_path}: {e}"
            ) from e

    @staticmethod
    def determine_chunk_size(file_size_bytes: int) -> int:
        """
        Determine appropriate chunk size based on file size.

        Args:
            file_size_bytes: Size of the file in bytes

        Returns:
            Number of pages to process per chunk
        """
        # For very large files (>100MB), use smaller chunks
        if file_size_bytes > 100 * 1024 * 1024:
            return 5
        # For large files (>50MB), use medium chunks
        elif file_size_bytes > 50 * 1024 * 1024:
            return 7
        # Default chunk size
        else:
            return ChunkProcessor.DEFAULT_CHUNK_SIZE
