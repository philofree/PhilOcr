"""JSON file saving utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from philocr.utils.exceptions import FileSaveError
from philocr.utils.logging_config import flush_loggers

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)


class JSONSaver:
    """Handles JSON file save operations without UI dependencies."""

    @staticmethod
    def save_json(data: dict[str, Any], file_path: str | Path) -> None:
        """Save data to a JSON file.

        Args:
            data: Dictionary data to save
            file_path: Path where to save the JSON file

        Raises:
            FileSaveError: If the file cannot be saved
            TypeError: If data is not JSON serializable
        """
        file_path = Path(file_path)
        try:
            logger.info(
                "json_file_saving",
                file_path=str(file_path),
                data_keys=list(data.keys()) if isinstance(data, dict) else None,
            )
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with file_path.open("w", encoding="utf-8") as json_file:
                json.dump(data, json_file, indent=2, ensure_ascii=False)
            logger.info("json_file_saved", file_path=str(file_path))
        except TypeError as e:
            logger.error(
                "json_file_save_type_error",
                file_path=str(file_path),
                error=str(e),
            )
            flush_loggers()
            raise FileSaveError(
                str(file_path), f"Data not JSON serializable: {e}"
            ) from e
        except PermissionError as e:
            logger.error(
                "json_file_save_permission_error",
                file_path=str(file_path),
                error=str(e),
            )
            flush_loggers()
            raise FileSaveError(str(file_path), f"Permission denied: {e}") from e
        except OSError as e:
            logger.error(
                "json_file_save_os_error",
                file_path=str(file_path),
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            flush_loggers()
            raise FileSaveError(str(file_path), f"OS error: {e}") from e
        except Exception as e:
            logger.error(
                "json_file_save_failed",
                file_path=str(file_path),
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            flush_loggers()
            raise FileSaveError(str(file_path), f"Unexpected error: {e}") from e
