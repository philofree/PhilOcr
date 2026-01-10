"""HTML file saving utilities."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from philocr.utils.exceptions import FileSaveError
from philocr.utils.json_handler import JSONHandler
from philocr.utils.logging_config import flush_loggers

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)


class HTMLSaver:
    """Handles HTML file save operations without UI dependencies."""

    @staticmethod
    def save_html(json_data: dict[str, Any], file_path: str | Path) -> None:
        """Convert JSON data to HTML and save to file.

        Args:
            json_data: JSON data to convert to HTML
            file_path: Path where to save the HTML file

        Raises:
            FileSaveError: If the file cannot be saved
        """
        file_path = Path(file_path)
        try:
            logger.info("html_file_saving", file_path=str(file_path))
            html_content: str = JSONHandler.convert_to_html(json_data)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(html_content, encoding="utf-8")
            logger.info(
                "html_file_saved",
                file_path=str(file_path),
                content_size_bytes=len(html_content),
            )
        except PermissionError as e:
            logger.error(
                "html_file_save_permission_error",
                file_path=str(file_path),
                error=str(e),
            )
            flush_loggers()
            raise FileSaveError(str(file_path), f"Permission denied: {e}") from e
        except OSError as e:
            logger.error(
                "html_file_save_os_error",
                file_path=str(file_path),
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            flush_loggers()
            raise FileSaveError(str(file_path), f"OS error: {e}") from e
        except Exception as e:
            logger.error(
                "html_file_save_failed",
                file_path=str(file_path),
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            flush_loggers()
            raise FileSaveError(str(file_path), f"Unexpected error: {e}") from e
