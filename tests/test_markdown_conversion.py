#!/usr/bin/env python3
"""
Test the markdown conversion functionality.

This script loads a JSON file and converts it to markdown using the new converter.
For large files, it automatically uses the streaming parser if available.
"""
import argparse
import json
import logging
import unicodedata

import pytest

from philocr.utils.markdown_converter.markdown_handler import MarkdownHandler

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_markdown")


def test_conversion(sample_json_response, temp_dir) -> None:
    """
    Test the conversion of a Google Document AI JSON file to markdown.
    """
    logger.info("Testing conversion of sample JSON to markdown")

    # Create a temporary JSON file from the sample response
    json_file_path = temp_dir / "test_document.json"
    with open(json_file_path, "w", encoding="utf-8") as f:
        json.dump(sample_json_response, f)

    # Create output file path
    output_file_path = temp_dir / "output.md"

    # Test the conversion
    try:
        # Use the markdown converter
        output = MarkdownHandler.convert_to_markdown(sample_json_response)
        assert output is not None, "Conversion returned None"
        assert len(output) > 0, "Conversion returned empty string"

        # Test file-to-file conversion
        success = MarkdownHandler.save_file_as_markdown(
            str(json_file_path), str(output_file_path)
        )
        assert success, "File-to-file conversion failed"
        assert output_file_path.exists(), "Output file was not created"

        logger.info("Successfully tested markdown conversion")
    except Exception as e:
        logger.error(f"Error during conversion: {e}", exc_info=True)
        raise


@pytest.mark.integration()
def test_nfc_normalization_in_markdown_pipeline(sample_json_response, temp_dir) -> None:
    """Test that NFC normalization is applied through the markdown conversion pipeline."""
    # Create test data with decomposed polytonic Greek
    # α (U+03B1) + smooth breathing (U+0313) should normalize to ἀ (U+1F00)
    alpha = "\u03B1"
    smooth_breathing = "\u0313"
    decomposed_text = alpha + smooth_breathing + " " + "βγδε"

    # Create modified JSON with decomposed text
    test_json = sample_json_response.copy()
    if "document_data" in test_json and "pages" in test_json["document_data"]:
        page = test_json["document_data"]["pages"][0]
        if "blocks" in page and len(page["blocks"]) > 0:
            # Modify first block text to include decomposed Greek
            page["blocks"][0]["text"] = decomposed_text
            if "layout" in page["blocks"][0] and "text" in page["blocks"][0]["layout"]:
                page["blocks"][0]["layout"]["text"] = decomposed_text

    # Convert to markdown
    markdown = MarkdownHandler.convert_to_markdown(test_json)

    # Verify that the output is in NFC form
    # Check if ἀ (U+1F00) is in the output instead of decomposed form
    expected_composed = "\u1F00"  # ἀ
    assert (
        expected_composed in markdown
        or unicodedata.normalize("NFC", markdown) == markdown
    ), "Output should be in NFC normalized form"

    # Verify all text in markdown is NFC normalized
    for line in markdown.split("\n"):
        normalized_line = unicodedata.normalize("NFC", line)
        assert normalized_line == line, f"Line not in NFC form: {line[:50]}"


@pytest.mark.integration()
def test_nfc_normalization_in_html_pipeline(sample_json_response) -> None:
    """Test that NFC normalization is applied through the HTML conversion pipeline."""
    # Create test data with decomposed polytonic Greek
    alpha = "\u03B1"
    smooth_breathing = "\u0313"
    decomposed_text = alpha + smooth_breathing + " " + "test"

    # Create modified JSON with decomposed text
    test_json = sample_json_response.copy()
    if "document_data" in test_json and "pages" in test_json["document_data"]:
        page = test_json["document_data"]["pages"][0]
        if "blocks" in page and len(page["blocks"]) > 0:
            page["blocks"][0]["text"] = decomposed_text

    # Convert to HTML
    html = MarkdownHandler.convert_to_html(test_json)

    # Verify that the output is in NFC form
    # Extract text content (simple approach - look for text in HTML)
    assert html is not None and len(html) > 0, "HTML output should not be empty"

    # Verify the text part is normalized (after HTML escaping)
    # The composed character should appear in the HTML
    expected_composed = "\u1F00"  # ἀ
    normalized_html = unicodedata.normalize("NFC", html)
    assert normalized_html == html, "HTML output should be in NFC normalized form"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Test Document AI JSON to Markdown conversion"
    )
    parser.add_argument("json_file", help="Path to the input JSON file")
    parser.add_argument("--output", "-o", help="Path to the output file")
    parser.add_argument(
        "--format",
        "-f",
        default="markdown",
        choices=["markdown", "html"],
        help="Output format (markdown or html)",
    )
    parser.add_argument(
        "--force-stream",
        action="store_true",
        help="Force using streaming parser even for small files",
    )
    args = parser.parse_args()

    # Temporarily override threshold if --force-stream is used
    if args.force_stream and args.format.lower() == "markdown":
        logger.info("Forcing streaming conversion as requested")
        original_threshold = MarkdownHandler.LARGE_FILE_THRESHOLD_MB
        MarkdownHandler.LARGE_FILE_THRESHOLD_MB = 0

    success = test_conversion(args.json_file, args.format, args.output)

    # Restore original threshold
    if args.force_stream and args.format.lower() == "markdown":
        MarkdownHandler.LARGE_FILE_THRESHOLD_MB = original_threshold

    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
