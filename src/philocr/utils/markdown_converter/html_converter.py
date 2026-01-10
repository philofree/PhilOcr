"""
HTML converter for Google Document AI JSON.

This module provides functionality to convert Google Document AI JSON
to HTML format with academic layout.
"""

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from philocr.utils.logging_config import flush_loggers
from philocr.utils.markdown_converter.academic_doc_parser import AcademicDocumentParser
from philocr.utils.markdown_converter.exceptions import HTMLConversionError

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)


class HTMLConverter:
    """Converts Google Document AI JSON to HTML format."""

    @staticmethod
    def convert(
        json_data: dict[str, Any],
        convert_alternative_format_func: Callable[[dict[str, Any]], str],
    ) -> str:
        """
        Convert Google Document AI JSON to HTML format with academic layout.

        Args:
            json_data: JSON data from Google Document AI
            convert_alternative_format_func: Function to convert alternative format

        Returns:
            HTML representation of the document

        Raises:
            HTMLConversionError: If conversion fails
        """
        logger.info("html_conversion_starting")

        if not json_data:
            logger.error("json_data_missing_for_html")
            raise HTMLConversionError("JSON data is empty or None")

        try:
            # Check for alternative format
            if "files" in json_data:
                logger.info("alternative_format_detected_html_conversion")
                # Convert to markdown first, then simple HTML
                markdown = convert_alternative_format_func(json_data)

                # Convert markdown to simple HTML
                return HTMLConverter._markdown_to_html(markdown)

            # Create parser with the JSON data directly
            logger.info("academic_parser_creating_html_conversion")
            parser = AcademicDocumentParser(json_data)

            # Convert to HTML
            logger.info("parser_to_html_calling")
            html: str = parser.to_html()
            html_length = len(html)

            if html_length == 0:
                logger.error("html_conversion_returned_empty")
                raise HTMLConversionError("HTML conversion produced empty content")

            logger.info(
                "html_conversion_completed",
                html_length=html_length,
                layout_type="academic",
            )

            return html

        except (KeyError, ValueError, AttributeError) as e:
            logger.error(
                "html_conversion_failed",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            flush_loggers()
            raise HTMLConversionError(f"Failed to convert to HTML: {e}") from e

    @staticmethod
    def _markdown_to_html(markdown: str) -> str:
        """
        Convert markdown to simple HTML.

        Args:
            markdown: Markdown content

        Returns:
            HTML representation
        """
        html_lines = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            '<meta charset="UTF-8">',
            "<title>Document</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; line-height: 1.6; margin: 2em; }",
            "h1 { text-align: center; font-size: 24px; }",
            "h2 { margin-top: 2em; }",
            "h3 { margin-top: 1.5em; }",
            "hr { margin: 2em 0; }",
            "</style>",
            "</head>",
            "<body>",
        ]

        try:
            # Simple markdown to HTML conversion
            for line in markdown.split("\n"):
                if line.startswith("# "):
                    html_lines.append(f"<h1>{line[2:]}</h1>")
                elif line.startswith("## "):
                    html_lines.append(f"<h2>{line[3:]}</h2>")
                elif line.startswith("### "):
                    html_lines.append(f"<h3>{line[4:]}</h3>")
                elif line.startswith("#### "):
                    html_lines.append(f"<h4>{line[5:]}</h4>")
                elif line.startswith("---"):
                    html_lines.append("<hr>")
                elif line.strip():
                    html_lines.append(f"<p>{line}</p>")

            html_lines.append("</body></html>")
            return "\n".join(html_lines)

        except (AttributeError, TypeError) as e:
            logger.error(
                "markdown_to_html_conversion_failed",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            flush_loggers()
            raise HTMLConversionError(f"Failed to convert markdown to HTML: {e}") from e
