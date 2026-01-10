"""JSON file loading utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from philocr.utils.exceptions import FileLoadError
from philocr.utils.exceptions import FileNotFoundError as PhilOcrFileNotFoundError
from philocr.utils.exceptions import JSONValidationError
from philocr.utils.logging_config import flush_loggers

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)


class JSONLoader:
    """Handles JSON file load operations without UI dependencies."""

    @staticmethod
    def load_json(file_path: str | Path) -> dict[str, Any]:
        """Load data from a JSON file.

        Args:
            file_path: Path to the JSON file

        Returns:
            Dictionary containing the loaded JSON data

        Raises:
            FileNotFoundError: If the file does not exist
            FileLoadError: If the file cannot be read or parsed
            JSONValidationError: If the JSON is invalid
        """
        file_path = Path(file_path)
        if not file_path.exists():
            logger.error("json_file_not_found", file_path=str(file_path))
            raise PhilOcrFileNotFoundError(str(file_path))

        try:
            logger.info("json_file_loading", file_path=str(file_path))
            with file_path.open("r", encoding="utf-8") as json_file:
                data: dict[str, Any] = json.load(json_file)
            logger.info(
                "json_file_loaded",
                file_path=str(file_path),
                data_keys=list(data.keys()) if isinstance(data, dict) else None,
            )
            return data
        except json.JSONDecodeError as e:
            logger.error(
                "json_file_parse_error",
                file_path=str(file_path),
                error=str(e),
                line=e.lineno,
                column=e.colno,
            )
            flush_loggers()
            raise JSONValidationError(
                f"Invalid JSON at line {e.lineno}, column {e.colno}: {e.msg}"
            ) from e
        except PermissionError as e:
            logger.error(
                "json_file_load_permission_error",
                file_path=str(file_path),
                error=str(e),
            )
            flush_loggers()
            raise FileLoadError(str(file_path), f"Permission denied: {e}") from e
        except OSError as e:
            logger.error(
                "json_file_load_os_error",
                file_path=str(file_path),
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            flush_loggers()
            raise FileLoadError(str(file_path), f"OS error: {e}") from e
        except Exception as e:
            logger.error(
                "json_file_load_failed",
                file_path=str(file_path),
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            flush_loggers()
            raise FileLoadError(str(file_path), f"Unexpected error: {e}") from e
