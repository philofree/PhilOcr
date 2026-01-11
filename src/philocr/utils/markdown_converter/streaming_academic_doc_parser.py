"""
Streaming Academic Document Parser for Google Document AI JSON

This parser processes academic documents from Google Document AI JSON format to markdown
using a streaming approach that is memory-efficient for large files.

IMPORTANT: This module requires the 'ijson' package.
Before using, install with: pip install ijson
"""

import importlib.util
import os
from collections.abc import Generator
from typing import Any

from philocr.utils.logging_config import get_logger
from philocr.utils.unicode_normalizer import normalize_to_nfc

# Get logger first (before ijson check to avoid unbound logger)
logger = get_logger(__name__)

# Check if ijson is installed and import it
_ijson_spec = importlib.util.find_spec("ijson")
if _ijson_spec is not None:
    try:
        import ijson  # type: ignore[reportMissingImports]  # noqa: F401

        # ijson.parse exists, so use the module directly
        IjsonPlaceholder = ijson
    except ImportError:
        logger.error(
            "ijson_import_failed",
            error_type="ImportError",
            package_found=True,
            import_failed=True,
            exc_info=True,
        )

        # Define placeholder if import fails
        class IjsonPlaceholder:  # type: ignore[no-redef]
            """Placeholder class for ijson when import fails.

            This class provides a stub implementation that raises ImportError
            when attempting to use ijson functionality. Used when the ijson
            package is found but cannot be imported successfully.
            """

            @staticmethod
            def parse(*args: Any, **kwargs: Any) -> Any:
                """Raise ImportError indicating ijson is not available.

                Args:
                    *args: Variable length argument list (unused).
                    **kwargs: Arbitrary keyword arguments (unused).

                Raises:
                    ImportError: Always raised to indicate ijson is not installed.
                """
                raise ImportError(
                    "ijson is not installed. Please install with: pip install ijson"
                )

else:
    logger.error(
        "ijson_package_missing",
        package_name="ijson",
        package_required=True,
        installation_command="pip install ijson",
    )

    # Define a placeholder to avoid syntax errors if imported without ijson
    class IjsonPlaceholder:
        """Placeholder class for ijson when package is not installed.

        This class provides a stub implementation that raises ImportError when
        attempting to use ijson functionality. Used when the ijson package
        cannot be found in the Python environment.

        The streaming parser requires ijson for memory-efficient processing of
        large JSON files. This placeholder ensures the module can be imported
        even without ijson, but will raise clear error messages when used.
        """

        @staticmethod
        def parse(*args: Any, **kwargs: Any) -> Any:
            """Raise ImportError indicating ijson is not available.

            Args:
                *args: Variable length argument list (unused).
                **kwargs: Arbitrary keyword arguments (unused).

            Raises:
                ImportError: Always raised to indicate ijson is not installed.
            """
            raise ImportError(
                "ijson is not installed. Please install with: pip install ijson"
            )


class StreamingAcademicDocumentParser:
    """Parser for large JSON files from Google Document AI that uses streaming."""

    def __init__(self, json_file_path: str) -> None:
        """
        Initialize with path to JSON file.
        """
        super().__init__()
        self.json_file_path: str = json_file_path
        self.file_size: int = os.path.getsize(json_file_path)
        file_size_mb = self.file_size / 1024 / 1024
        logger.info(
            "streaming_parser_initialized",
            json_file_path=json_file_path,
            file_size_bytes=self.file_size,
            file_size_mb=round(file_size_mb, 2),
        )
        self.px_to_cm: float = 2.54 / 96  # approx. 0.026 cm per pixel

    def _check_document_structure(self, file_handle: Any) -> bool:
        """Check if JSON has document_data structure.

        Args:
            file_handle: Open file handle to check.

        Returns:
            True if document_data exists, False otherwise.
        """
        for prefix, event, _ in IjsonPlaceholder.parse(file_handle):
            if prefix == "document_data" and event == "start_map":
                logger.info("document_data_structure_found")
                return True
        return False

    def _handle_page_start(
        self,
        current_page: dict[str, Any] | None,
        current_lines: list[dict[str, Any]],
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """Handle start of a new page event.

        Args:
            current_page: Current page being built.
            current_lines: Current lines for the page.

        Returns:
            Tuple of (new_page, new_lines).
        """
        return {}, []

    def _handle_page_field(
        self,
        current_page: dict[str, Any] | None,
        prefix: str,
        event: str,
        value: Any,
    ) -> None:
        """Handle page-level field updates.

        Args:
            current_page: Current page being built.
            prefix: JSON prefix path.
            event: Event type.
            value: Field value.
        """
        if current_page is None:
            return

        if prefix.endswith(".pages.item.page_number") and event in ("number", "string"):
            current_page["page_number"] = value
            return

        if prefix.endswith(".pages.item.dimension.width") and event == "number":
            if "dimension" not in current_page:
                current_page["dimension"] = {}
            current_page["dimension"]["width"] = value
            return

        if prefix.endswith(".pages.item.dimension.height") and event == "number":
            if "dimension" not in current_page:
                current_page["dimension"] = {}
            current_page["dimension"]["height"] = value

    def _handle_line_start(self) -> dict[str, Any]:
        """Handle start of a new line event.

        Returns:
            New line dictionary.
        """
        return {}

    def _handle_line_text(
        self, current_line: dict[str, Any] | None, value: str
    ) -> None:
        """Handle line text field.

        Args:
            current_line: Current line being built.
            value: Text value.
        """
        if current_line is not None:
            current_line["text"] = normalize_to_nfc(value)

    def _handle_line_layout(
        self,
        current_line: dict[str, Any] | None,
        prefix: str,
        event: str,
        value: Any,
    ) -> None:
        """Handle line layout fields.

        Args:
            current_line: Current line being built.
            prefix: JSON prefix path.
            event: Event type.
            value: Field value.
        """
        if current_line is None:
            return

        if prefix.endswith(".lines.item.layout") and event == "start_map":
            current_line["layout"] = {"bounding_poly": {"vertices": []}}
            return

        if prefix.endswith(".lines.item.layout.confidence") and event == "number":
            if "layout" in current_line:
                current_line["layout"]["confidence"] = value

    def _handle_vertex_field(
        self,
        current_vertex: dict[str, Any] | None,
        prefix: str,
        event: str,
        value: Any,
    ) -> dict[str, Any] | None:
        """Handle bounding polygon vertex fields.

        Args:
            current_vertex: Current vertex being built.
            prefix: JSON prefix path.
            event: Event type.
            value: Field value.

        Returns:
            Updated vertex or None if vertex complete.
        """
        if prefix.endswith(".vertices.item") and event == "start_map":
            return {}

        if current_vertex is None:
            return None

        if prefix.endswith(".vertices.item.x") and event == "number":
            current_vertex["x"] = value
            return current_vertex

        if prefix.endswith(".vertices.item.y") and event == "number":
            current_vertex["y"] = value
            return current_vertex

        return current_vertex

    def _complete_vertex(
        self,
        current_line: dict[str, Any] | None,
        current_vertex: dict[str, Any] | None,
    ) -> None:
        """Complete a vertex and add it to the current line.

        Args:
            current_line: Current line being built.
            current_vertex: Vertex to add.
        """
        if current_line is None:
            return
        if "layout" not in current_line:
            return
        if "bounding_poly" not in current_line["layout"]:
            return
        if current_vertex is None:
            return

        bounding_poly = current_line["layout"]["bounding_poly"]
        if "vertices" not in bounding_poly:
            bounding_poly["vertices"] = []
        bounding_poly["vertices"].append(current_vertex)

    def _complete_line(
        self,
        current_line: dict[str, Any] | None,
        current_lines: list[dict[str, Any]],
    ) -> None:
        """Complete a line and add it to current lines.

        Args:
            current_line: Line to complete.
            current_lines: List to add line to.
        """
        if current_line is not None:
            current_lines.append(current_line)

    def _complete_page(
        self,
        current_page: dict[str, Any] | None,
        current_lines: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Complete a page and return it.

        Args:
            current_page: Page to complete.
            current_lines: Lines for the page.

        Returns:
            Completed page dictionary.
        """
        if current_page is None:
            current_page = {}

        current_page["lines"] = current_lines.copy()
        return current_page

    def stream_pages(self) -> Generator[dict[str, Any], None, None]:
        """
        Stream the pages from the JSON file one at a time.

        This generator yields one page at a time from the JSON file, avoiding
        loading the entire file into memory.

        Yields:
            Dict[str, Any]: A single page from the document
        """
        logger.info("streaming_pages_started", json_file_path=self.json_file_path)

        try:
            with open(self.json_file_path, "rb") as f:
                has_document_data = self._check_document_structure(f)
                _ = f.seek(0)

                logger.info(
                    "streaming_pages_prefix",
                    prefix=(
                        "document_data.pages.item"
                        if has_document_data
                        else "pages.item"
                    ),
                    has_document_data=has_document_data,
                )

                current_page: dict[str, Any] | None = None
                current_lines: list[dict[str, Any]] = []
                current_line: dict[str, Any] | None = None
                current_vertex: dict[str, Any] | None = None
                page_count = 0

                for prefix, event, value in IjsonPlaceholder.parse(f):
                    # Page events
                    if prefix.endswith(".pages.item"):
                        if event == "start_map":
                            current_page, current_lines = self._handle_page_start(
                                current_page, current_lines
                            )
                        elif event == "end_map":
                            completed_page = self._complete_page(
                                current_page, current_lines
                            )
                            page_count += 1
                            logger.info("page_yielded", page_number=page_count)
                            yield completed_page
                            current_page = None
                            current_lines = []
                            current_line = None
                        continue

                    if prefix.endswith(".pages.item."):
                        self._handle_page_field(current_page, prefix, event, value)
                        continue

                    # Line events
                    if prefix.endswith(".lines.item"):
                        if event == "start_map":
                            current_line = self._handle_line_start()
                        elif event == "end_map":
                            self._complete_line(current_line, current_lines)
                            current_line = None
                        continue

                    if prefix.endswith(".lines.item.text") and event == "string":
                        self._handle_line_text(current_line, value)
                        continue

                    if prefix.endswith(".lines.item.layout"):
                        self._handle_line_layout(current_line, prefix, event, value)
                        continue

                    # Vertex events
                    if prefix.endswith(".vertices.item"):
                        if event == "start_map":
                            current_vertex = self._handle_vertex_field(
                                current_vertex, prefix, event, value
                            )
                        elif event == "end_map":
                            self._complete_vertex(current_line, current_vertex)
                            current_vertex = None
                        continue

                    if ".vertices.item." in prefix:
                        current_vertex = self._handle_vertex_field(
                            current_vertex, prefix, event, value
                        )
                        continue

                logger.info("streaming_pages_completed", total_pages=page_count)

        except Exception as e:
            logger.error(
                "streaming_pages_error",
                json_file_path=self.json_file_path,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            from philocr.utils.logging_config import flush_loggers

            flush_loggers()
            raise RuntimeError(f"CRITICAL: Streaming pages failed - {e}") from e

    def calculate_page_dimensions(self, page: dict[str, Any]) -> dict[str, Any]:
        """
        Calculate the dimensions of a page based on the dimensions in the page data.
        Converts pixels to centimeters and scales down to a reasonable size.
        """
        if "dimension" in page:  # Some JSON formats include this information directly
            width_px = int(page["dimension"].get("width", 1000))
            height_px = int(page["dimension"].get("height", 1400))
            # Convert to cm and scale down
            width_cm = width_px * self.px_to_cm * 0.5
            height_cm = height_px * self.px_to_cm * 0.5
            return {
                "width_px": width_px,
                "height_px": height_px,
                "width_cm": width_cm,
                "height_cm": height_cm,
            }

        # Default dimensions if not provided
        return {
            "width_px": 1000,
            "height_px": 1400,
            "width_cm": 21.0,  # ~A4 width
            "height_cm": 29.7,  # ~A4 height
        }

    def detect_headings(self, lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Perform basic heading detection on the lines of a page.
        A much simpler version of the full parser's detection.
        """
        for line in lines:
            if not line.get("type"):
                # Simple detection of all caps text (likely section headers)
                if line["text"].strip().isupper() and len(line["text"]) > 3:
                    line["type"] = "header"
                # Check for page numbers (isolated numbers at the top)
                elif line["text"].strip().isdigit() and len(line["text"]) <= 2:
                    line["type"] = "page_number"
                else:
                    line["type"] = "line"

        return lines

    def to_markdown(self) -> str:
        """
        Convert the document to Markdown format using streaming processing.
        Each page is processed individually to minimize memory usage.
        """
        logger.info("to_markdown_streaming_started", json_file_path=self.json_file_path)
        md_output = []

        try:
            page_count = 0

            # Process pages one at a time from the stream
            for page in self.stream_pages():
                page_count += 1
                logger.info("page_converting_to_markdown", page_number=page_count)

                # Extract lines
                lines = page.get("lines", [])
                if not lines:
                    logger.warning("page_no_lines_found", page_number=page_count)
                    continue

                # Calculate page dimensions
                dimensions = self.calculate_page_dimensions(page)

                # Get page number if available
                page_num_str = str(page.get("page_number", page_count))

                # Header for new page
                _ = md_output.append(f"# Page {page_num_str}\n")
                _ = md_output.append(
                    f"<!-- Page dimensions: {dimensions['width_cm']:.2f}cm x {dimensions['height_cm']:.2f}cm -->\n"
                )

                # Process lines with simple heading detection
                processed_lines = self.detect_headings(lines)

                # Convert lines to markdown
                content_lines = []
                for line in processed_lines:
                    text = normalize_to_nfc(line.get("text", "").strip())
                    if not text:
                        continue

                    line_type = line.get("type", "line")

                    if line_type == "header":
                        _ = content_lines.append(f"\n## {text}\n")
                    elif line_type == "page_number":
                        _ = content_lines.append(f"**{text}**")
                    else:
                        _ = content_lines.append(text)

                # Add content with proper line breaks
                _ = md_output.append("\n".join(content_lines))

                # Add page separator
                _ = md_output.append("\n\n---\n")

                # Log progress for large files
                if page_count % 10 == 0:
                    logger.info(
                        "markdown_conversion_progress", pages_processed=page_count
                    )

            logger.info("markdown_conversion_completed", total_pages=page_count)

            # Combine all output parts
            result = "\n".join(md_output)
            result_length = len(result)

            if result_length == 0:
                logger.error("markdown_content_empty")
                return "Error: No content could be extracted."

            logger.info(
                "markdown_content_generated",
                content_length=result_length,
                json_file_path=self.json_file_path,
            )

            # Log a sample of the output to check for errors
            preview = result[:200].replace("\n", "\\n")
            logger.info(
                "markdown_content_preview", preview=preview, preview_length=len(preview)
            )

            return result
        except Exception as e:
            logger.error(
                "to_markdown_streaming_error",
                json_file_path=self.json_file_path,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            from philocr.utils.logging_config import flush_loggers

            flush_loggers()
            raise RuntimeError(
                f"CRITICAL: Streaming markdown conversion failed - {e}"
            ) from e


def convert_large_json(
    json_file_path: str,
    output_format: str = "markdown",
    output_file_path: str | None = None,
) -> str:
    """
    Convert a large JSON file from Google Document AI to markdown or HTML.

    Args:
        json_file_path: Path to the JSON file
        output_format: 'markdown' or 'html' (only markdown supported currently)
        output_file_path: Path where to save the output file (optional)

    Returns:
        The converted document in the specified format
    """
    if output_format.lower() != "markdown":
        logger.warning(
            "unsupported_format_fallback",
            requested_format=output_format,
            fallback_format="markdown",
        )
        output_format = "markdown"

    # Create parser with the file path
    parser = StreamingAcademicDocumentParser(json_file_path)

    # Generate markdown
    output = parser.to_markdown()

    # Save to file if requested
    if output_file_path:
        with open(output_file_path, "w", encoding="utf-8") as f:
            _ = f.write(output)
        logger.info(
            "output_file_saved",
            output_file_path=output_file_path,
            output_length=len(output),
        )

    return output


# Example usage
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Convert large Google Document AI JSON to markdown"
    )
    _ = parser.add_argument("json_file", help="Path to the input JSON file")
    _ = parser.add_argument("--output", "-o", help="Path to the output file")
    args = parser.parse_args()

    result = convert_large_json(args.json_file, output_file_path=args.output)

    if not args.output:
        # Use logger for CLI output preview instead of print
        logger.info(
            "cli_output_preview",
            preview=result[:1000],
            total_length=len(result),
            truncated=True,
        )
