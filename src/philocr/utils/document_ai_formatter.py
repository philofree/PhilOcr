"""
Simple, Reliable Document AI Text Formatter

This module focuses on reliable text extraction from any Document AI JSON format.
It prioritizes getting the text content displayed correctly over advanced formatting.
"""

import os
import shutil
from typing import TYPE_CHECKING, Any

from philocr.utils.unicode_normalizer import normalize_to_nfc

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)

# Create a backup of this file if it doesn't exist already
current_file = os.path.abspath(__file__)
backup_file = current_file + ".backup"
if not os.path.exists(backup_file):
    try:
        _ = shutil.copy2(current_file, backup_file)
        logger.info(
            "formatter_backup_created",
            backup_file=backup_file,
            original_file=current_file,
        )
    except Exception as e:
        logger.error(
            "formatter_backup_failed",
            backup_file=backup_file,
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True,
        )


# Extremely simplified formatter - only extracts text and creates basic HTML
def format_document_ai_json(
    json_data: dict[str, Any],
    debug_mode: bool = False,
    use_simple_formatting: bool = True,
) -> str:
    """
    Convert Document AI JSON to very basic HTML with minimal formatting.

    Args:
        json_data (dict): Document AI JSON data
        debug_mode (bool): Whether to include debug information
        use_simple_formatting (bool): Ignored

    Returns:
        str: HTML with minimal formatting
    """
    logger.info("document_formatting_starting", format_type="simplified")

    if not json_data:
        logger.error("json_data_missing")
        return "<html><body><p>No data available</p></body></html>"

    # Extract raw text only - no fancy formatting
    raw_text = extract_text_only(json_data)

    logger.info(
        "raw_text_extracted",
        text_length=len(raw_text),
    )

    # Extract filename and timestamp from metadata if available
    filename = ""
    timestamp = ""
    if "metadata" in json_data and isinstance(json_data["metadata"], dict):
        filename = json_data["metadata"].get("filename", "")

    # Check for timestamp in multiple possible locations
    if "timestamp" in json_data:
        timestamp = str(json_data["timestamp"])
    elif "metadata" in json_data and isinstance(json_data["metadata"], dict):
        timestamp = str(json_data["metadata"].get("timestamp", ""))

    # Convert to very simple HTML
    title = f"Document Text - {filename}" if filename else "Document Text"

    # Build metadata section
    metadata_parts = []
    if filename:
        metadata_parts.append(f"Source: {html_escape(filename)}")
    if timestamp:
        metadata_parts.append(f"Processed: {html_escape(timestamp)}")

    metadata_html = ""
    if metadata_parts:
        metadata_html = f'<div class="metadata">{" | ".join(metadata_parts)}</div>'

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{html_escape(title)}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        pre {{ white-space: pre-wrap; font-family: monospace; }}
        .metadata {{ font-size: 12px; color: #666; margin-bottom: 10px; }}
    </style>
</head>
<body>
    <h1>Document Text</h1>
    {metadata_html}
    <pre>{html_escape(raw_text)}</pre>
</body>
</html>"""

    return html


def html_escape(text: str) -> str:
    """Basic HTML escaping to prevent rendering issues"""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _process_page_text(
    page: dict[str, Any], page_num: int, page_content_map: dict[int, list[str]]
) -> None:
    """Process page-level text content.

    Args:
        page: Page data dictionary.
        page_num: Page number.
        page_content_map: Map of page numbers to content lists.
    """
    if page_num not in page_content_map:
        page_content_map[page_num] = []

    if "text" in page and page["text"]:
        text = normalize_to_nfc(str(page["text"]).strip())
        if text:
            page_content_map[page_num].append(text)
            logger.info(
                "page_text_added",
                page_number=page_num,
                text_length=len(text),
            )


def _extract_block_text_content(block: dict[str, Any]) -> str | None:
    """Extract text content from a block.

    Args:
        block: Block data dictionary

    Returns:
        Normalized text content or None if not available
    """
    # Try direct text field first
    if "text" in block and block["text"]:
        text = normalize_to_nfc(str(block["text"]).strip())
        if text:
            return text

    # Try layout.text field
    if "layout" in block and isinstance(block["layout"], dict):
        if "text" in block["layout"] and block["layout"]["text"]:
            text = normalize_to_nfc(str(block["layout"]["text"]).strip())
            if text:
                return text

    return None


def _process_page_blocks(
    page: dict[str, Any], page_num: int, page_content_map: dict[int, list[str]]
) -> None:
    """Process blocks within a page.

    Args:
        page: Page data dictionary.
        page_num: Page number.
        page_content_map: Map of page numbers to content lists.
    """
    if "blocks" not in page:
        return

    processed_blocks: list[str] = []
    standard_blocks = 0
    layout_blocks = 0

    for block in page["blocks"]:
        block_text = _extract_block_text_content(block)
        if block_text:
            processed_blocks.append(block_text)
            # Count based on where text came from
            if "text" in block and block.get("text"):
                standard_blocks += 1
            else:
                layout_blocks += 1

    if not processed_blocks:
        return

    if page_num not in page_content_map:
        page_content_map[page_num] = []
    page_content_map[page_num].append("\n\n".join(processed_blocks))
    logger.info(
        "page_blocks_processed",
        page_number=page_num,
        standard_blocks=standard_blocks,
        layout_blocks=layout_blocks,
        total_blocks=len(processed_blocks),
    )


def _process_document_data_pages(
    doc_data: dict[str, Any], page_content_map: dict[int, list[str]]
) -> None:
    """Process pages from document_data.

    Args:
        doc_data: Document data dictionary.
        page_content_map: Map of page numbers to content lists.
    """
    if "pages" not in doc_data:
        return

    page_count = len(doc_data["pages"])
    logger.info("pages_processing_started", page_count=page_count)

    for page in doc_data["pages"]:
        page_num = page.get("page_number", 1)
        _process_page_text(page, page_num, page_content_map)
        _process_page_blocks(page, page_num, page_content_map)


def _process_files_array(json_data: dict[str, Any]) -> str | None:
    """Process files array in batch mode.

    Args:
        json_data: Document AI JSON data.

    Returns:
        Combined text from all files, or None if not in batch mode.
    """
    if "files" not in json_data or not isinstance(json_data["files"], list):
        return None

    logger.info(
        "batch_mode_text_extraction_started",
        file_count=len(json_data["files"]),
    )

    all_text_parts: list[str] = []
    for file_idx, file_data in enumerate(json_data["files"]):
        file_name = file_data.get("metadata", {}).get("filename", f"File {file_idx+1}")

        logger.info(
            "batch_file_processing",
            file_index=file_idx + 1,
            file_name=file_name,
            total_files=len(json_data["files"]),
        )
        all_text_parts.append(f"\n\n--- Document {file_idx+1}: {file_name} ---\n\n")

        if "document_data" in file_data:
            file_text = process_file_doc_data(file_data["document_data"], {}, file_name)
            all_text_parts.append(file_text)
        elif "text" in file_data and file_data["text"]:
            all_text_parts.append(normalize_to_nfc(str(file_data["text"])))

    if all_text_parts:
        combined_text = normalize_to_nfc("\n".join(all_text_parts))
        logger.info(
            "batch_mode_text_extraction_completed",
            text_length=len(combined_text),
            file_count=len(json_data["files"]),
        )
        return combined_text

    return None


def _build_final_text(page_content_map: dict[int, list[str]]) -> str | None:
    """Build final text output from page content map.

    Args:
        page_content_map: Map of page numbers to content lists.

    Returns:
        Combined text with page markers, or None if no content.
    """
    page_numbers = sorted(page_content_map.keys())
    if not page_numbers:
        return None

    page_text_parts: list[str] = []
    for page_num in page_numbers:
        if page_content_map[page_num]:
            page_text_parts.append(f"\n\n----- Page {page_num} -----\n")
            page_text_parts.append("\n\n".join(page_content_map[page_num]))

    combined_text = normalize_to_nfc("\n".join(page_text_parts))
    logger.info(
        "text_extraction_completed",
        text_length=len(combined_text),
        page_count=len(page_numbers),
    )
    return combined_text


def _get_fallback_text(json_data: dict[str, Any]) -> str:
    """Get fallback text from root level.

    Args:
        json_data: Document AI JSON data.

    Returns:
        Fallback text or error message.
    """
    if "text" in json_data and json_data["text"]:
        text_value = json_data["text"]
        if isinstance(text_value, str):
            logger.info(
                "fallback_root_text_used",
                text_length=len(text_value),
                reason="no_page_content_extracted",
            )
            return normalize_to_nfc(str(text_value))
        logger.warning(
            "root_text_field_invalid_type", text_type=type(text_value).__name__
        )
        return "Invalid text format found in document"

    logger.warning("no_text_content_found")
    return "No text content found in document."


def extract_text_only(json_data: dict[str, Any]) -> str:
    """
    Extract text from Document AI JSON focusing on the page content.
    Provides proper spacing between text blocks for better readability.

    Args:
        json_data (dict): Document AI JSON data

    Returns:
        str: Raw extracted text with proper block formatting
    """
    page_content_map: dict[int, list[str]] = {}

    # Process document data if present
    if "document_data" in json_data:
        _process_document_data_pages(json_data["document_data"], page_content_map)

    # Check for batch mode (files array) - this takes precedence
    batch_result = _process_files_array(json_data)
    if batch_result is not None:
        return batch_result

    # Build final text from page content map
    final_text = _build_final_text(page_content_map)
    if final_text is not None:
        return final_text

    # Fallback to root text field if nothing else worked
    return _get_fallback_text(json_data)


def process_file_doc_data(
    doc_data: dict[str, Any],
    page_content_map: dict[int, list[str]] | None = None,
    file_name: str = "",
) -> str:
    """Helper function to process document_data from a file in batch mode

    Args:
        doc_data (dict): Document data containing pages and blocks
        page_content_map (dict, optional): Existing page content map to update, or None to create a new one
        file_name (str): Name of the file for logging

    Returns:
        str: Formatted text with page markers
    """
    # Create a new page content map if none was provided
    if page_content_map is None:
        page_content_map = {}

    if "pages" in doc_data:
        logger.info(
            "file_pages_processing_started",
            file_name=file_name,
            page_count=len(doc_data["pages"]),
        )

        for page in doc_data["pages"]:
            page_num = page.get("page_number", 1)

            # Initialize this page's content if not already
            if page_num not in page_content_map:
                page_content_map[page_num] = []

            # Try page text
            if "text" in page and page["text"]:
                text = normalize_to_nfc(str(page["text"]).strip())
                if text:
                    page_content_map[page_num].append(text)

            # Try blocks
            if "blocks" in page:
                processed_blocks = []
                standard_blocks = 0
                layout_blocks = 0

                for block in page["blocks"]:
                    # Standard format
                    if "text" in block and block["text"]:
                        text = normalize_to_nfc(str(block["text"]).strip())
                        if text:
                            processed_blocks.append(text)
                            standard_blocks += 1

                    # Google Document AI layout format
                    elif "layout" in block and isinstance(block["layout"], dict):
                        if "text" in block["layout"] and block["layout"]["text"]:
                            text = normalize_to_nfc(
                                str(block["layout"]["text"]).strip()
                            )
                            if text:
                                processed_blocks.append(text)
                                layout_blocks += 1

                if processed_blocks:
                    page_content_map[page_num].append("\n\n".join(processed_blocks))
                    logger.info(
                        "file_page_blocks_processed",
                        file_name=file_name,
                        page_number=page_num,
                        standard_blocks=standard_blocks,
                        layout_blocks=layout_blocks,
                        total_blocks=len(processed_blocks),
                    )

    # Construct the final text with page markers in order
    all_text_parts: list[str] = []

    # Get all page numbers and sort them
    page_numbers = sorted(page_content_map.keys())

    if page_numbers:
        for page_num in page_numbers:
            if page_content_map[page_num]:
                # Add page marker with distinctive formatting
                all_text_parts.append(f"\n\n----- Page {page_num} -----\n")
                all_text_parts.append("\n\n".join(page_content_map[page_num]))

        # Join all parts with appropriate spacing and normalize
        return normalize_to_nfc("\n".join(all_text_parts))
    else:
        return "No text content found in document."
