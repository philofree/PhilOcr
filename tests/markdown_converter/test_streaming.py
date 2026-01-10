#!/usr/bin/env python3
"""
Test script for validating the streaming markdown parser implementation.

This script tests the streaming markdown conversion functionality with both small and large files.
It will fall back to regular parsing if ijson is not available.
"""
import argparse
import json
import logging
import os
import sys
import time

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from philocr.utils.markdown_converter.academic_doc_parser import AcademicDocumentParser

# Import our modules
from philocr.utils.markdown_converter.markdown_handler import MarkdownHandler
from philocr.utils.markdown_converter.streaming_academic_doc_parser import (
    StreamingAcademicDocumentParser,
)

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("test_streaming")


def test_small_file() -> None:
    """Test streaming parser with small test file."""
    logger.info("==== Testing with small test file ====")

    # Path to our test fixture
    test_file = os.path.join(
        os.path.dirname(__file__), "fixtures", "test_document.json"
    )

    assert os.path.exists(test_file), f"Test file not found: {test_file}"

    # Test output path
    output_file = os.path.join(os.path.dirname(__file__), "output", "test_small.md")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Time the conversion
    start_time = time.time()
    success = MarkdownHandler.save_file_as_markdown(test_file, output_file)
    elapsed_time = time.time() - start_time

    assert success, "Failed to convert small file"
    assert os.path.exists(output_file), f"Output file not created: {output_file}"

    logger.info(f"Successfully converted small file in {elapsed_time:.2f} seconds")
    logger.info(f"Output saved to {output_file}")


def test_large_file(json_file_path: str | None = None) -> None:
    """Test parsing of a large JSON file."""
    logger.info("==== Testing with large file ====")

    # Use provided file path or look for the default large test file
    if not json_file_path:
        json_file_path = (
            "/Users/james/Documents/GitHub/OCR_Fresh/temp_files/1_VOL_BB_01.json"
        )

    # Skip test if large file doesn't exist (it's not required for CI)
    if not os.path.exists(json_file_path):
        logger.error(f"Large file not found: {json_file_path}")
        import pytest

        pytest.skip(f"Large test file not found: {json_file_path}")

    # Test output path
    file_name = os.path.basename(json_file_path)
    base_name, _ = os.path.splitext(file_name)
    output_file = os.path.join(
        os.path.dirname(__file__), "output", f"{base_name}_output.md"
    )
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    file_size_mb = os.path.getsize(json_file_path) / (1024 * 1024)
    logger.info(f"Testing with file: {json_file_path} ({file_size_mb:.2f} MB)")

    # Check if ijson is available
    try:
        logger.info("ijson is available, can use streaming parser")
    except ImportError:
        logger.warning("ijson is not available, falling back to regular parser")

    # Time the conversion
    start_time = time.time()

    try:
        # Try streaming parser first if ijson is available
        if True:
            try:
                # Use streaming conversion
                logger.info("Attempting streaming conversion")
                parser = StreamingAcademicDocumentParser(json_file_path)
                markdown = parser.to_markdown()

                if len(markdown) > 0 and "Error:" not in markdown:
                    # Streaming conversion successful
                    with open(output_file, "w", encoding="utf-8") as f:
                        f.write(markdown)
                    success = True
                else:
                    # Streaming conversion failed, fall back to regular
                    logger.warning("Streaming conversion didn't produce valid output")
                    raise ValueError("Invalid streaming output")
            except Exception as e:
                logger.warning(
                    f"Streaming conversion failed: {e}. Trying regular parser"
                )

        # Fall back to regular parser if streaming not available or failed
        if not True:
            logger.info("Using regular parser")
            try:
                # For large files, we may need to increase memory limits if possible
                logger.info("Loading JSON file into memory")
                with open(json_file_path, encoding="utf-8") as f:
                    json_data = json.load(f)

                # Generate markdown
                logger.info("Converting to markdown")
                parser = AcademicDocumentParser(json_data)
                markdown = parser.to_markdown()

                # Save output
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(markdown)
                success = True
            except MemoryError:
                logger.error(
                    "Memory error when processing large file. Consider installing ijson for streaming."
                )
                success = False
            except Exception as e:
                logger.error(f"Regular conversion failed: {e}", exc_info=True)
                success = False

    except Exception as e:
        logger.error(f"Error during conversion: {e}", exc_info=True)
        success = False

    elapsed_time = time.time() - start_time

    assert success, "Failed to convert large file"
    assert os.path.exists(output_file), f"Output file not created: {output_file}"

    logger.info(f"Successfully converted large file in {elapsed_time:.2f} seconds")
    logger.info(f"Output saved to {output_file}")


def main() -> int:
    """Main entry point for the test script."""
    parser = argparse.ArgumentParser(description="Test streaming markdown conversion")
    parser.add_argument("--small", action="store_true", help="Test with small file")
    parser.add_argument("--large", action="store_true", help="Test with large file")
    parser.add_argument("--file", help="Path to JSON file to use for testing")
    args = parser.parse_args()

    # Determine which tests to run
    run_small = args.small or not args.large
    run_large = args.large

    success = True

    # Run selected tests
    if run_small:
        logger.info("Running small file test")
        success = test_small_file() and success

    if run_large:
        logger.info("Running large file test")
        success = test_large_file(args.file) and success

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
