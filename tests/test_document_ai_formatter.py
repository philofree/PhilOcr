#!/usr/bin/env python3
"""
Test script for the Document AI Academic Formatter.

This script demonstrates how to use the DocumentAIFormatter
to properly style academic texts from Document AI JSON output.
"""
import json
import logging
import os
from typing import Any

from philocr.utils.document_ai_formatter import format_document_ai_json

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("test_formatter")


def create_sample_json_with_bounding_polygons() -> dict[str, Any]:
    """
    Creates a sample JSON with bounding polygons for testing.

    The original sample lacks bounding polygons, so we'll create
    a modified version with synthetic bounding polygon data.

    Returns:
        dict: A sample JSON with bounding polygons
    """
    # Base structure
    sample = {
        "text": (
            "ZENO CITIEUS.\n"
            "ἐπὶ δὲ τὴν οἰκοδομὴν κεχειροτόνηται Θράσων Ανακαιεύς, Φιλο\n"
            "κλῆς Πειραιεύς, Φαίδρος Αναφλύστιος, Μέδων Αχαρνεύς, Μίκυθος\n"
            "Συπαληττεύς, Δίων Παιανιεύς.\n"
            "9 Themistius Or. XXIII 295 D. Hard.\n"
            "τὰ δὲ ἀμφὶ Ζήνωνος ἀρί\n"
            "δηλά τέ ἐστι καὶ ἀδόμενα ὑπὸ πολλῶν ὅτι αὐτὸν ἡ Σωκράτους ἀπο\n"
            "λογία ἐκ Φοινίκης εἰς τὴν Ποικίλην ἤγαγεν."
        ),
        "timestamp": "2023-03-24T12:00:00.000Z",
        "metadata": {"filename": "sample_academic_text.pdf", "page_count": 1},
        "document_data": {
            "pages": [
                {
                    "page_number": 1,
                    "dimension": {"width": 1000, "height": 1500},
                    "blocks": [
                        # Line number
                        {
                            "text": "8",
                            "layout": {
                                "bounding_poly": {
                                    "vertices": [
                                        {"x": 20, "y": 50},
                                        {"x": 40, "y": 50},
                                        {"x": 40, "y": 70},
                                        {"x": 20, "y": 70},
                                    ]
                                }
                            },
                        },
                        # Header
                        {
                            "text": "ZENO CITIEUS.",
                            "layout": {
                                "bounding_poly": {
                                    "vertices": [
                                        {"x": 300, "y": 50},
                                        {"x": 700, "y": 50},
                                        {"x": 700, "y": 90},
                                        {"x": 300, "y": 90},
                                    ]
                                }
                            },
                        },
                        # Greek text - regular content
                        {
                            "text": "ἐπὶ δὲ τὴν οἰκοδομὴν κεχειροτόνηται Θράσων Ανακαιεύς, Φιλο",
                            "layout": {
                                "bounding_poly": {
                                    "vertices": [
                                        {"x": 100, "y": 130},
                                        {"x": 900, "y": 130},
                                        {"x": 900, "y": 160},
                                        {"x": 100, "y": 160},
                                    ]
                                }
                            },
                        },
                        # More Greek text - regular content
                        {
                            "text": "κλῆς Πειραιεύς, Φαίδρος Αναφλύστιος, Μέδων Αχαρνεύς, Μίκυθος",
                            "layout": {
                                "bounding_poly": {
                                    "vertices": [
                                        {"x": 100, "y": 170},
                                        {"x": 900, "y": 170},
                                        {"x": 900, "y": 200},
                                        {"x": 100, "y": 200},
                                    ]
                                }
                            },
                        },
                        # More Greek text - regular content
                        {
                            "text": "Συπαληττεύς, Δίων Παιανιεύς.",
                            "layout": {
                                "bounding_poly": {
                                    "vertices": [
                                        {"x": 100, "y": 210},
                                        {"x": 900, "y": 210},
                                        {"x": 900, "y": 240},
                                        {"x": 100, "y": 240},
                                    ]
                                }
                            },
                        },
                        # Fragment reference
                        {
                            "text": "9 Themistius Or. XXIII 295 D. Hard.",
                            "layout": {
                                "bounding_poly": {
                                    "vertices": [
                                        {"x": 200, "y": 280},
                                        {"x": 700, "y": 280},
                                        {"x": 700, "y": 310},
                                        {"x": 200, "y": 310},
                                    ]
                                }
                            },
                        },
                        # More Greek text - with indentation
                        {
                            "text": "τὰ δὲ ἀμφὶ Ζήνωνος ἀρί",
                            "layout": {
                                "bounding_poly": {
                                    "vertices": [
                                        {"x": 200, "y": 350},
                                        {"x": 500, "y": 350},
                                        {"x": 500, "y": 380},
                                        {"x": 200, "y": 380},
                                    ]
                                }
                            },
                        },
                        # More Greek text
                        {
                            "text": "δηλά τέ ἐστι καὶ ἀδόμενα ὑπὸ πολλῶν ὅτι αὐτὸν ἡ Σωκράτους ἀπο",
                            "layout": {
                                "bounding_poly": {
                                    "vertices": [
                                        {"x": 100, "y": 390},
                                        {"x": 900, "y": 390},
                                        {"x": 900, "y": 420},
                                        {"x": 100, "y": 420},
                                    ]
                                }
                            },
                        },
                        # More Greek text
                        {
                            "text": "λογία ἐκ Φοινίκης εἰς τὴν Ποικίλην ἤγαγεν.",
                            "layout": {
                                "bounding_poly": {
                                    "vertices": [
                                        {"x": 100, "y": 430},
                                        {"x": 700, "y": 430},
                                        {"x": 700, "y": 460},
                                        {"x": 100, "y": 460},
                                    ]
                                }
                            },
                        },
                        # Footnote at bottom of page
                        {
                            "text": "1 This is a sample footnote with smaller text",
                            "layout": {
                                "bounding_poly": {
                                    "vertices": [
                                        {"x": 100, "y": 1400},
                                        {"x": 700, "y": 1400},
                                        {"x": 700, "y": 1420},
                                        {"x": 100, "y": 1420},
                                    ]
                                }
                            },
                        },
                    ],
                }
            ]
        },
    }

    return sample


def load_real_json(file_path: str) -> dict[str, Any] | None:
    """
    Load a real Document AI JSON file.

    Args:
        file_path (str): Path to the JSON file

    Returns:
        dict: The loaded JSON data
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            data: dict[str, Any] = json.load(f)
            return data
    except Exception as e:
        logger.error(f"Error loading JSON file: {e}")
        return None


def fix_json_bounding_polygons(json_data: dict[str, Any]) -> dict[str, Any]:
    """
    Fixes a JSON file by adding missing bounding polygons.
    This is necessary for testing when the original JSON lacks proper coordinates.

    Args:
        json_data (dict): The original JSON data

    Returns:
        dict: The fixed JSON data with added bounding polygons
    """
    if not json_data or "document_data" not in json_data:
        return json_data

    # Get page dimensions from the first page
    pages = json_data["document_data"].get("pages", [])
    if not pages:
        return json_data

    for page_idx, page in enumerate(pages):
        width = page.get("dimension", {}).get("width", 1000)
        height = page.get("dimension", {}).get("height", 1500)

        # Process blocks to add bounding polygons
        blocks = page.get("blocks", [])
        y_offset = 100  # Starting y position

        for block_idx, block in enumerate(blocks):
            # Skip if already has proper bounding polygon
            if (
                "layout" in block
                and "bounding_poly" in block["layout"]
                and block["layout"]["bounding_poly"]
                and "vertices" in block["layout"]["bounding_poly"]
                and block["layout"]["bounding_poly"]["vertices"]
            ):
                continue

            # Create a layout section if none exists
            if "layout" not in block:
                block["layout"] = {}

            # Determine if this is a potential line number, footnote, or header
            text = block.get("text", "").strip()
            is_line_number = text.isdigit() and len(text) < 4
            is_footnote = (
                block_idx > len(blocks) - 3
            )  # Assume last 2 blocks might be footnotes
            is_header = block_idx < 2 and (text.isupper() or len(text) < 20)

            # Set left margin based on what this block might be
            left_margin = 50 if is_line_number else (200 if is_footnote else 100)
            # Adjust indentation for some blocks to simulate fragment references
            if block_idx % 5 == 0 and not is_line_number and not is_header:
                left_margin = 200  # More indented

            # Set the block height based on content
            block_height = (
                20 if is_line_number or is_footnote else (50 if is_header else 30)
            )

            # Text width is proportional to text length, but capped
            text_width = min(len(text) * 10, width - left_margin - 50)

            # For footnotes, position at bottom of page
            if is_footnote:
                y_pos = height - 100 + (block_idx * 30)
            else:
                y_pos = y_offset
                y_offset += block_height + 10  # Increment for next block

            # Create synthetic bounding polygon
            block["layout"]["bounding_poly"] = {
                "vertices": [
                    {"x": left_margin, "y": y_pos},
                    {"x": left_margin + text_width, "y": y_pos},
                    {"x": left_margin + text_width, "y": y_pos + block_height},
                    {"x": left_margin, "y": y_pos + block_height},
                ]
            }

    return json_data


def main() -> None:
    """
    Main function to test the DocumentAIFormatter.
    """
    output_dir = "test_output"
    os.makedirs(output_dir, exist_ok=True)

    # First test with our synthetic sample
    logger.info("Testing with synthetic sample...")
    sample_json = create_sample_json_with_bounding_polygons()

    # Format the sample and save to file
    html_output = format_document_ai_json(sample_json, debug_mode=True)

    with open(
        os.path.join(output_dir, "synthetic_sample_output.html"), "w", encoding="utf-8"
    ) as f:
        f.write(html_output)

    logger.info(
        "Synthetic sample HTML output saved to test_output/synthetic_sample_output.html"
    )

    # Now try to load and process a real file
    real_json_path = "doc_ai_json_samples/1 page themestius.json"
    logger.info(f"Loading real JSON file: {real_json_path}")

    real_json = load_real_json(real_json_path)
    if real_json:
        # First check if it has proper bounding polygons
        has_polygons = False
        if "document_data" in real_json and "pages" in real_json["document_data"]:
            for page in real_json["document_data"]["pages"]:
                for block in page.get("blocks", []):
                    if (
                        "layout" in block
                        and "bounding_poly" in block["layout"]
                        and block["layout"]["bounding_poly"]
                        and "vertices" in block["layout"]["bounding_poly"]
                        and block["layout"]["bounding_poly"]["vertices"]
                    ):
                        has_polygons = True
                        break
                if has_polygons:
                    break

        if not has_polygons:
            logger.warning(
                "The real JSON file lacks proper bounding polygons. Fixing..."
            )
            real_json = fix_json_bounding_polygons(real_json)

        # Now process the real file
        real_html_output = format_document_ai_json(real_json, debug_mode=True)

        with open(
            os.path.join(output_dir, "themistius_output.html"), "w", encoding="utf-8"
        ) as f:
            f.write(real_html_output)

        logger.info("Real JSON HTML output saved to test_output/themistius_output.html")

    logger.info("Testing complete!")


if __name__ == "__main__":
    main()
