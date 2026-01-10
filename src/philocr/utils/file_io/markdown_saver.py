"""Markdown file saving utilities."""

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


class MarkdownSaver:
    """Handles markdown file save operations without UI dependencies."""

    @staticmethod
    def save_markdown(
        content: str | None,
        file_path: str | Path,
        fallback_json: dict[str, Any] | None = None,
    ) -> None:
        """Save markdown content to a file.

        Args:
            content: Markdown content to save. If None, will use fallback_json
            file_path: Path where to save the file
            fallback_json: JSON data to convert to markdown if content is None

        Raises:
            FileSaveError: If the file cannot be saved
            ValueError: If both content and fallback_json are None
        """
        file_path = Path(file_path)

        if content:
            try:
                logger.info(
                    "markdown_file_saving",
                    file_path=str(file_path),
                    content_length=len(content),
                    source="provided_content",
                )
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content, encoding="utf-8")
                logger.info("markdown_file_saved", file_path=str(file_path))
            except PermissionError as e:
                logger.error(
                    "markdown_file_save_permission_error",
                    file_path=str(file_path),
                    error=str(e),
                )
                flush_loggers()
                raise FileSaveError(str(file_path), f"Permission denied: {e}") from e
            except OSError as e:
                logger.error(
                    "markdown_file_save_os_error",
                    file_path=str(file_path),
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True,
                )
                flush_loggers()
                raise FileSaveError(str(file_path), f"OS error: {e}") from e
            except Exception as e:
                logger.error(
                    "markdown_file_save_failed",
                    file_path=str(file_path),
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True,
                )
                flush_loggers()
                raise FileSaveError(str(file_path), f"Unexpected error: {e}") from e
        elif fallback_json:
            try:
                logger.info(
                    "markdown_file_saving",
                    file_path=str(file_path),
                    source="json_handler",
                )
                markdown_content: str = JSONHandler.convert_to_markdown(fallback_json)
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(markdown_content, encoding="utf-8")
                logger.info("markdown_file_saved", file_path=str(file_path))
            except PermissionError as e:
                logger.error(
                    "markdown_file_save_permission_error",
                    file_path=str(file_path),
                    error=str(e),
                )
                flush_loggers()
                raise FileSaveError(str(file_path), f"Permission denied: {e}") from e
            except OSError as e:
                logger.error(
                    "markdown_file_save_os_error",
                    file_path=str(file_path),
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True,
                )
                flush_loggers()
                raise FileSaveError(str(file_path), f"OS error: {e}") from e
            except Exception as e:
                logger.error(
                    "markdown_file_save_failed",
                    file_path=str(file_path),
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True,
                )
                flush_loggers()
                raise FileSaveError(str(file_path), f"Unexpected error: {e}") from e
        else:
            error_msg = "Cannot save markdown: no content or fallback JSON provided"
            logger.error(
                "markdown_file_save_failed_no_content", file_path=str(file_path)
            )
            raise ValueError(error_msg)
