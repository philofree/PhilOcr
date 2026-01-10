"""Result processing utilities for document processing.

This module handles result formatting and finalization without UI dependencies.
"""

from __future__ import annotations

import datetime
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from philocr.utils.json_handler import JSONHandler

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)


class ResultProcessor:
    """Processes and formats document processing results."""

    @staticmethod
    def build_result_json(
        text: str,
        document_layout: dict[str, Any] | None,
        metadata: dict[str, Any],
        file_name: str,
        page_count: int,
        chunks: int,
    ) -> dict[str, Any]:
        """Build JSON result from processing data.

        Args:
            text: Extracted text content
            document_layout: Layout data from document AI
            metadata: Additional metadata
            file_name: Name of the processed file
            page_count: Total page count
            chunks: Number of chunks processed

        Returns:
            Dictionary containing formatted JSON result
        """
        result_metadata = metadata.copy()
        result_metadata.update(
            {
                "filename": file_name,
                "page_count": page_count,
                "chunks": chunks,
            }
        )
        return JSONHandler.text_to_json(text, result_metadata, document_layout or {})

    @staticmethod
    def build_text_from_layout(
        document_layout: dict[str, Any] | None,
    ) -> str:
        """Build text content from layout data if text is missing.

        Args:
            document_layout: Layout data from document AI

        Returns:
            Reconstructed text content, or empty string if no text found
        """
        if not document_layout or "pages" not in document_layout:
            return ""

        text_fragments: list[str] = []
        pages = document_layout.get("pages", [])
        for page_idx, page in enumerate(pages):
            if page_idx > 0:
                text_fragments.append(f"\n\n----- Page {page_idx + 1} -----\n\n")

            if "text" in page and page["text"]:
                text_fragments.append(page["text"])
            elif "blocks" in page:
                block_texts: list[str] = []
                for block in page.get("blocks", []):
                    if "text" in block and block["text"]:
                        block_texts.append(block["text"])
                if block_texts:
                    text_fragments.append(" ".join(block_texts))

        if text_fragments:
            result = "".join(text_fragments)
            logger.debug(
                "text_built_from_layout",
                fragment_count=len(text_fragments),
                text_length=len(result),
            )
            return result

        return ""

    @staticmethod
    def finalize_single_result(
        text: str,
        document_layout: dict[str, Any] | None,
        metadata: dict[str, Any],
        file_name: str,
        page_count: int,
        chunks: int,
        on_json_ready: Callable[[dict[str, Any]], None],
        on_progress_update: Callable[[int], None],
    ) -> dict[str, Any]:
        """Finalize results for a single document.

        Args:
            text: Extracted text content
            document_layout: Layout data from document AI
            metadata: Base metadata dictionary
            file_name: Name of the file
            page_count: Total page count
            chunks: Number of chunks processed
            on_json_ready: Callback to emit JSON result
            on_progress_update: Callback to update progress (100)

        Returns:
            Finalized JSON result dictionary
        """
        result_metadata = metadata.copy()
        result_metadata.update(
            {
                "filename": file_name,
                "page_count": page_count,
                "chunks": chunks,
            }
        )
        result_json = JSONHandler.text_to_json(
            text, result_metadata, document_layout or {}
        )
        on_json_ready(result_json)
        on_progress_update(100)
        return result_json

    @staticmethod
    def finalize_batch_result(
        all_text: str,
        all_json_results: list[dict[str, Any]],
        metadata: dict[str, Any],
        total_files: int,
        total_chunks: int,
        on_json_ready: Callable[[dict[str, Any]], None],
        on_status_update: Callable[[str], None],
        on_progress_update: Callable[[int], None],
    ) -> dict[str, Any]:
        """Finalize batch processing results.

        Args:
            all_text: Combined text from all files
            all_json_results: JSON results for all files
            metadata: Base metadata dictionary
            total_files: Total number of files processed
            total_chunks: Total chunks processed
            on_json_ready: Callback to emit JSON result
            on_status_update: Callback to update status
            on_progress_update: Callback to update progress (100)

        Returns:
            Finalized batch JSON result dictionary
        """
        on_progress_update(100)
        on_status_update(f"Completed processing {total_files} documents")

        combined_metadata = metadata.copy()
        combined_metadata.update(
            {
                "total_files": total_files,
                "total_chunks": total_chunks,
                "timestamp": datetime.datetime.now().isoformat(),
            }
        )

        result_json: dict[str, Any] = {
            "text": all_text,
            "metadata": combined_metadata,
            "files": all_json_results,
        }
        on_json_ready(result_json)
        return result_json
