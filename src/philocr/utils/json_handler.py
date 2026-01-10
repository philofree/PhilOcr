import datetime
import json
from typing import TYPE_CHECKING, Any

from philocr.utils.document_ai_formatter import format_document_ai_json

# Import the new markdown handler
from philocr.utils.markdown_converter.markdown_handler import MarkdownHandler

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)


class JSONHandler:
    """Class to handle JSON operations for document processing results."""

    @staticmethod
    def save_to_json(data: dict[str, Any], file_path: str) -> bool:
        """
        Save data to a JSON file.

        Args:
            data (dict): Data to save
            file_path (str): Path where to save the JSON file

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(file_path, "w", encoding="utf-8") as json_file:
                json.dump(data, json_file, indent=2, ensure_ascii=False)
            logger.info(
                "json_file_saved",
                file_path=file_path,
            )
            return True
        except Exception as e:
            logger.error(
                "json_file_save_failed",
                file_path=file_path,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            return False

    @staticmethod
    def load_from_json(file_path: str) -> dict[str, Any] | None:
        """
        Load data from a JSON file.

        Args:
            file_path (str): Path to the JSON file

        Returns:
            dict: Loaded data or None if loading failed
        """
        try:
            with open(file_path, encoding="utf-8") as json_file:
                data: dict[str, Any] = json.load(json_file)
            logger.info(
                "json_file_loaded",
                file_path=file_path,
            )
            return data
        except Exception as e:
            logger.error(
                "json_file_load_failed",
                file_path=file_path,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            return None

    @staticmethod
    def text_to_json(
        text: str,
        metadata: dict[str, Any] | None = None,
        document_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Convert extracted text to JSON format with metadata.

        Args:
            text (str): The extracted text
            metadata (dict, optional): Additional metadata to include
            document_data (dict, optional): Document AI layout data

        Returns:
            dict: JSON-compatible dictionary with text and metadata
        """
        result: dict[str, Any] = {
            "text": text,
            "timestamp": datetime.datetime.now().isoformat(),
            "metadata": metadata or {},
        }
        if document_data:
            result["document_data"] = document_data
        return result

    @staticmethod
    def convert_to_html(json_data: dict[str, Any]) -> str:
        """
        Convert JSON data to HTML format with academic text formatting.

        Args:
            json_data (dict): JSON data to convert

        Returns:
            str: HTML representation of the data
        """
        if json_data:
            try:
                html_result: str = MarkdownHandler.convert_to_html(json_data)
                return html_result
            except Exception as e:
                logger.error(
                    "html_conversion_markdown_handler_failed",
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True,
                    using_fallback=True,
                )
                fallback_result: str = format_document_ai_json(
                    json_data, debug_mode=False
                )
                return fallback_result
        else:
            return "<html><body><p>No data available</p></body></html>"

    @staticmethod
    def convert_to_markdown(json_data: dict[str, Any]) -> str:
        """
        Convert JSON data to Markdown format.

        Args:
            json_data (dict): JSON data to convert

        Returns:
            str: Markdown representation of the data
        """
        if json_data:
            markdown_result: str = MarkdownHandler.convert_to_markdown(json_data)
            return markdown_result
        else:
            return "No data available"

    @staticmethod
    def save_as_html(json_data: dict[str, Any], file_path: str) -> bool:
        """
        Convert JSON data to HTML and save to file.

        Args:
            json_data (dict): JSON data to convert
            file_path (str): Path where to save the HTML file

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            html_content: str = JSONHandler.convert_to_html(json_data)
            with open(file_path, "w", encoding="utf-8") as html_file:
                _ = html_file.write(html_content)
            logger.info(
                "html_file_saved",
                file_path=file_path,
                content_size_bytes=len(html_content),
            )
            return True
        except Exception as e:
            logger.error(
                "html_file_save_failed",
                file_path=file_path,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            return False

    @staticmethod
    def save_as_markdown(json_data: dict[str, Any], file_path: str) -> bool:
        """
        Convert JSON data to Markdown and save to file.

        Args:
            json_data (dict): JSON data to convert
            file_path (str): Path where to save the markdown file

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            markdown_content: str = MarkdownHandler.convert_to_markdown(json_data)
            with open(file_path, "w", encoding="utf-8") as md_file:
                _ = md_file.write(markdown_content)
            logger.info(
                "markdown_file_saved",
                file_path=file_path,
                content_size_bytes=len(markdown_content),
            )
            return True
        except Exception as e:
            logger.error(
                "markdown_file_save_failed",
                file_path=file_path,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            return False
