import argparse
import html
import json
from typing import Any

from philocr.processing.parsers.page_parser import PageParser
from philocr.processing.parsers.structure_extractor import StructureExtractor
from philocr.utils.logging_config import get_logger
from philocr.utils.unicode_normalizer import normalize_to_nfc

# Import PX_TO_CM for backward compatibility
PX_TO_CM = PageParser.PX_TO_CM


logger = get_logger(__name__)

"""
Academic Document Parser for Google Document AI JSON

This parser processes academic documents from Google Document AI JSON format to markdown and HTML.
NOTE: Line number detection has been intentionally removed from this parser and is now handled
by the 'anthropic-line-number-processor.py' using Claude API, which provides more accurate results
for line number identification in classical texts.
"""


class AcademicDocumentParser:
    """Parser for academic documents from Google Document AI JSON format.

    This parser processes academic documents and converts them to markdown and
    HTML formats. It handles document structure identification including line
    numbers, footnotes, headers, indentation levels, and references.

    Note: Line number detection has been intentionally removed from this parser
    and is now handled by external processing using Claude API, which provides
    more accurate results for line number identification in classical texts.

    Attributes:
        doc_data: Raw document data from Google Document AI.
        document: Processed document data (either from document_data key or top level).
        text: Full text content of the document (NFC normalized).
        px_to_cm: Conversion factor from pixels to centimeters.
        line_number_values: Expected line number values for detection.
        ocr_digit_corrections: Common OCR misreadings for digits in line numbers.
    """

    def __init__(self, json_data: dict[str, Any] | str):
        """Initialize with Google Document AI JSON response.

        Args:
            json_data: Either a dictionary or JSON string containing Document AI
                      response data.
        """
        super().__init__()
        logger.info("academic_parser_initializing")

        if isinstance(json_data, str):
            logger.info("json_string_to_dict_converting")
            self.doc_data = json.loads(json_data)
        else:
            self.doc_data = json_data

        # Extract the document_data if available, otherwise use the top level
        if "document_data" in self.doc_data:
            logger.info("document_data_key_found")
            self.document = self.doc_data["document_data"]
        else:
            logger.info("document_data_key_not_found_using_top_level")
            self.document = self.doc_data

        # Get the full text content and normalize
        self.text = normalize_to_nfc(self.document.get("text", ""))
        if self.text:
            text_length = len(self.text)
            logger.info(
                "text_field_found",
                text_length=text_length,
            )
        else:
            logger.info("text_field_not_found")

        # Initialize parser components
        self.page_parser = PageParser()
        self.structure_extractor = StructureExtractor()
        # Initialize px_to_cm conversion factor (used in to_html method)
        self.px_to_cm: float = PX_TO_CM

    def get_pages(self) -> list[dict[str, Any]]:
        """Get all pages from the document."""
        pages = self.document.get("pages", [])
        if not isinstance(pages, list):
            return []
        return pages

    def calculate_page_dimensions(
        self, page: dict[str, Any], elements: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Calculate page dimensions based on page data or elements.

        Args:
            page: Page data dictionary
            elements: List of elements on the page

        Returns:
            Dictionary with width and height in cm
        """
        return self.page_parser.calculate_dimensions(page, elements)

    def get_elements_by_position(self, page: dict[str, Any]) -> list[dict[str, Any]]:
        """Get all text elements from a page, sorted by reading position.

        Args:
            page: Page data dictionary

        Returns:
            List of elements sorted by position
        """
        return self.page_parser.get_elements_by_position(page)

    def detect_references(self, text: str) -> bool:
        """Detect if a line is a reference/citation.

        Args:
            text: Text to analyze

        Returns:
            True if text matches reference pattern
        """
        return self.structure_extractor.detect_references(text)

    def detect_actual_page_number(self, elements: list[dict[str, Any]]) -> int | None:
        """Detect the actual page number from page content.

        Args:
            elements: List of text elements on the page

        Returns:
            Page number if found, None otherwise
        """
        return self.structure_extractor.detect_actual_page_number(elements)

    def identify_line_numbers_by_position(
        self, elements: list[dict[str, Any]], page_idx: int
    ) -> list[dict[str, Any]]:
        """Stub method - line number detection handled externally.

        Args:
            elements: List of text elements on the page
            page_idx: Page index (0-based)

        Returns:
            The input elements unchanged
        """
        return elements

    def detect_headings(
        self, elements: list[dict[str, Any]], page_idx: int
    ) -> list[dict[str, Any]]:
        """Detect headers and other structural elements in the document.

        Args:
            elements: List of text elements
            page_idx: Page index (0-based)

        Returns:
            Elements with type annotations added
        """
        # First identify line numbers by position (stub - handled externally)
        elements = self.identify_line_numbers_by_position(elements, page_idx)

        # Delegate to structure extractor
        return self.structure_extractor.detect_headings(elements, page_idx)

    def to_markdown(self) -> str:
        """Convert the document to Markdown format preserving original line breaks and positioning."""
        logger.debug("to_markdown method called")
        md_output: list[str] = []

        try:
            # Get all pages
            pages = self.get_pages()
            page_count = len(pages)
            logger.info(
                "pages_processing_for_markdown",
                page_count=page_count,
            )

            if page_count == 0:
                logger.warning("no_pages_found_in_document")
                return "No pages found in document."

            for page_idx, page in enumerate(pages):
                logger.info(
                    "page_converting_to_markdown",
                    page_number=page_idx + 1,
                    total_pages=page_count,
                )

                # Get and sort all text elements
                elements = self.get_elements_by_position(page)
                logger.info(
                    "text_elements_found_on_page",
                    page_number=page_idx + 1,
                    element_count=len(elements),
                )

                # Detect element types
                elements = self.detect_headings(elements, page_idx)

                # Calculate page dimensions
                dimensions = self.calculate_page_dimensions(page, elements)

                # Detect actual page number
                actual_page_number = self.detect_actual_page_number(elements)
                page_num_str = (
                    str(actual_page_number) if actual_page_number else str(page_idx + 1)
                )

                # Header for new page
                md_output.append(f"# Page {page_num_str}\n")
                md_output.append(
                    f"<!-- Page dimensions: {dimensions['width_cm']:.2f}cm x {dimensions['height_cm']:.2f}cm -->\n"
                )

                # Separate elements by type
                main_content = []
                footnotes = []

                # Group elements by their approximate line position (y-coordinate)
                # This helps us maintain original line breaks
                y_groups: dict[int, list[dict[str, Any]]] = {}
                for e in elements:
                    # Round y-position to nearest 5 pixels to group nearby elements
                    y_key = round(e["y_position"] / 5) * 5
                    if y_key not in y_groups:
                        y_groups[y_key] = []
                    y_groups[y_key].append(e)

                # Sort each group by x-position
                for y_key in y_groups:
                    y_groups[y_key].sort(key=lambda e: e["x_position"])

                # Process elements by line
                logger.info(
                    "text_lines_processing_on_page",
                    page_number=page_idx + 1,
                    line_count=len(y_groups),
                )
                for y_key in sorted(y_groups.keys()):
                    line_elements = y_groups[y_key]
                    content = line_elements  # All elements are now treated as content

                    # Process content based on type
                    for e in content:
                        element_type = e.get("type", "line")
                        text = normalize_to_nfc(e["text"].strip())
                        indent_level = e.get("indent_level", 0)

                        # Add appropriate amount of indentation
                        indent = " " * (indent_level * 2)

                        if element_type == "page_number":
                            main_content.append(f"{indent}**{text}**")
                        elif element_type == "header":
                            main_content.append(f"\n## {text}\n")
                        elif element_type == "reference":
                            main_content.append(f"{indent}> {text}")
                        elif element_type == "footnote":
                            footnotes.append(f"   {text}")
                        else:  # Regular text
                            main_content.append(f"{indent}{text}")

                    # Add a line break after each group to maintain original line structure
                    main_content.append("")

                md_output.append("\n".join(main_content))

                # Add footnotes at the bottom if there are any
                if footnotes:
                    logger.info(
                        "footnotes_adding_to_page",
                        page_number=page_idx + 1,
                        footnote_count=len(footnotes),
                    )
                    md_output.append("\n---\n\n*Footnotes:*\n")
                    md_output.append("\n".join(footnotes))

                # Add page separator
                md_output.append("\n\n---\n")

            # Combine all output parts
            result = "\n".join(md_output)
            result_length = len(result)

            if result_length == 0:
                logger.error("markdown_content_empty_generated")
                return "Error: No content could be extracted."

            logger.info(
                "markdown_content_generated",
                content_length=result_length,
            )

            # Log a sample of the output to check for errors
            preview = result[:200].replace("\n", "\\n")
            logger.info(
                "markdown_content_preview",
                preview=preview,
                preview_length=len(preview),
            )

            return result
        except Exception as e:
            logger.error(
                "to_markdown_error",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            from philocr.utils.logging_config import flush_loggers

            flush_loggers()
            raise RuntimeError(f"CRITICAL: Markdown conversion failed - {e}") from e

    def to_html(self) -> str:
        """Convert the document to HTML with absolute positioning to match original layout."""
        html_output = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            '<meta charset="UTF-8">',
            "<title>Academic Document</title>",
            "<style>",
            "body { font-family: serif; line-height: 1.6; margin: 2em; }",
            "h1 { text-align: center; font-size: 24px; }",
            "h2 { text-align: center; font-weight: bold; }",
            ".page { margin: 0 auto 3em auto; border: 1px solid #ccc; padding: 0; position: relative; }",
            ".page-content { position: relative; }",
            ".text-element { position: absolute; margin: 0; padding: 0; }",
            '.regular-text { text-align: justify; font-family: "Times New Roman", Times, serif; width: 100%; }',
            ".page-number { font-weight: bold; text-align: center; }",
            ".reference { text-align: left; font-style: italic; }",
            ".footnote { text-align: justify; font-size: 0.85em; }",
            ".footnote-section { margin-top: 1em; border-top: 1px solid #ddd; padding-top: 1em; }",
            '.greek { font-family: "Times New Roman", Times, serif; }',
            ".header { font-weight: bold; text-align: center; }",
            ".text-container { width: 80%; margin: 0 auto; position: relative; }",
            ".text-line { display: block; text-align: justify; }",
            "</style>",
            "</head>",
            "<body>",
        ]

        pages = self.get_pages()
        for page_idx, page in enumerate(pages):
            # Get and sort all text elements
            elements = self.get_elements_by_position(page)

            # Detect element types
            elements = self.detect_headings(elements, page_idx)

            # Calculate page dimensions with proper proportions
            dimensions = self.calculate_page_dimensions(page, elements)

            # Get actual page number if available
            actual_page_number = self.detect_actual_page_number(elements)
            page_num_str = (
                str(actual_page_number) if actual_page_number else str(page_idx + 1)
            )

            # Start page div with fixed dimensions in centimeters
            html_output.append(
                f'<div class="page" id="page-{page_num_str}" style="width:{dimensions["width_cm"]:.2f}cm; height:{dimensions["height_cm"]:.2f}cm;">'
            )
            html_output.append(f"<h1>Page {page_num_str}</h1>")
            html_output.append('<div class="page-content">')

            # Calculate scaling factor to convert from original pixels to the scaled dimensions
            scale_factor = dimensions["width_cm"] / (dimensions["width_px"] * PX_TO_CM)

            # Process all elements with standard positioning
            for element in elements:
                element_type = element.get("type", "line")
                text = html.escape(normalize_to_nfc(element["text"].strip()))

                # Convert pixel positions to centimeters with scaling
                x_pos_cm = element["x_position"] * self.px_to_cm * scale_factor
                y_pos_cm = element["y_position"] * self.px_to_cm * scale_factor

                # Set CSS class based on element type
                css_class = "text-element "
                if element_type == "page_number":
                    css_class += "page-number"
                elif element_type == "header":
                    css_class += "header"
                elif element_type == "reference":
                    css_class += "reference"
                elif element_type == "footnote":
                    css_class += "footnote"
                else:
                    css_class += "regular-text"

                # Generate element with absolute positioning in centimeters
                html_output.append(
                    f'<div class="{css_class}" style="left:{x_pos_cm:.2f}cm; top:{y_pos_cm:.2f}cm;">{text}</div>'
                )

            # End page content and page div
            html_output.append("</div>")  # page-content
            html_output.append("</div>")  # page

        html_output.append("</body></html>")
        return "\n".join(html_output)


def reconstruct_document(
    json_file_path: str,
    output_format: str = "markdown",
    output_file_path: str | None = None,
) -> str | None:
    """
    Reconstruct an academic document from Google Document AI JSON.

    Args:
        json_file_path: Path to the JSON file from Document AI
        output_format: 'markdown' or 'html'
        output_file_path: Path where to save the output file (optional)

    Returns:
        The reconstructed document in the specified format, or None on error
    """
    # Load JSON data
    with open(json_file_path, encoding="utf-8") as f:
        json_data = json.load(f)

    # Create parser
    parser = AcademicDocumentParser(json_data)

    # Generate output
    if output_format.lower() == "html":
        output = parser.to_html()
    else:
        output = parser.to_markdown()

    # Save to file if requested
    if output_file_path:
        with open(output_file_path, "w", encoding="utf-8") as f:
            _ = f.write(output)

    return output


# Example usage
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert Google Document AI JSON to markdown or HTML"
    )
    _ = parser.add_argument("json_file", help="Path to the input JSON file")
    _ = parser.add_argument("output_format", help="Output format (markdown or html)")
    _ = parser.add_argument("output_file", help="Path to the output file")
    args = parser.parse_args()

    result = reconstruct_document(args.json_file, args.output_format, args.output_file)

    if not args.output_file:
        # Use logger for CLI output instead of print
        logger.info(
            "cli_output_preview",
            preview=result[:1000] if len(result) > 1000 else result,
            total_length=len(result),
            truncated=len(result) > 1000,
        )
