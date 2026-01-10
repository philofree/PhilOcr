#!/usr/bin/env python3
"""PDF utility functions for splitting and processing PDFs."""
from __future__ import annotations

import os
import tempfile
from typing import TYPE_CHECKING

import fitz  # PyMuPDF

from philocr.utils.logging_config import flush_loggers

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)


def split_pdf(
    file_path: str, max_pages: int = 15, temp_dir: str | None = None
) -> list[str]:
    """
    Split a PDF into smaller chunks if it exceeds the maximum page count.

    Args:
        file_path (str): Path to the PDF file
        max_pages (int): Maximum number of pages per chunk
        temp_dir (Optional[str]): Directory to store temporary files

    Returns:
        List[str]: List of temporary file paths containing the split PDFs
    """
    logger.info("pdf_splitting_started", file_path=file_path)
    doc = fitz.open(file_path)
    total_pages = len(doc)
    logger.info("pdf_pages_counted", total_pages=total_pages, file_path=file_path)

    # If the document is small enough, don't split it
    if total_pages <= max_pages:
        logger.info("pdf_no_split_needed", total_pages=total_pages, max_pages=max_pages)
        return [file_path]

    # Calculate how many chunks we'll need
    chunk_count = (total_pages + max_pages - 1) // max_pages
    logger.info(
        "pdf_split_required",
        chunk_count=chunk_count,
        max_pages=max_pages,
        total_pages=total_pages,
    )

    temp_files: list[str] = []

    # Create each chunk
    for i in range(chunk_count):
        start_page = i * max_pages
        end_page = min((i + 1) * max_pages - 1, total_pages - 1)

        logger.info(
            "pdf_chunk_creating",
            chunk_index=i + 1,
            start_page=start_page,
            end_page=end_page,
        )

        # Create a new PDF document
        new_doc = fitz.open()

        # Insert the pages from the original document
        new_doc.insert_pdf(doc, from_page=start_page, to_page=end_page)

        # Save to a temporary file
        if temp_dir is not None:
            os.makedirs(temp_dir, exist_ok=True)
            temp_file = os.path.join(temp_dir, f"temp_chunk_{i+1}.pdf")
        else:
            temp_file_obj = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            temp_file = temp_file_obj.name
            temp_file_obj.close()

        logger.info("pdf_chunk_saving", temp_file=temp_file, chunk_index=i + 1)
        new_doc.save(temp_file)
        new_doc.close()

        temp_files.append(temp_file)
        chunk_pages = end_page - start_page + 1
        logger.info(
            "pdf_chunk_saved",
            chunk_index=i + 1,
            chunk_pages=chunk_pages,
            temp_file=temp_file,
        )

    logger.info("pdf_split_completed", chunk_count=len(temp_files), file_path=file_path)
    return temp_files


def get_pdf_page_count(file_path: str) -> int:
    """
    Get the number of pages in a PDF file.

    Args:
        file_path (str): Path to the PDF file

    Returns:
        int: Number of pages in the PDF
    """
    try:
        doc = fitz.open(file_path)
        page_count = len(doc)
        doc.close()
        return page_count
    except Exception as e:
        logger.error(
            "pdf_page_count_error",
            file_path=file_path,
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True,
        )
        flush_loggers()
        raise
