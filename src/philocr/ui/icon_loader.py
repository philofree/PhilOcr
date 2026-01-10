"""
Icon loader for the application.
"""

from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)


def _get_icons_base_path() -> str:
    """Get the base path for icon files.

    Returns:
        Base path string for icon directory
    """
    if getattr(sys, "frozen", False):
        # Running in a bundled application
        return os.path.join(sys._MEIPASS, "philocr_icons")  # type: ignore
    else:
        # Running in development
        return "philocr_icons"


def _get_icon_candidates() -> list[str]:
    """Get list of icon file paths to try in order of preference.

    Returns:
        List of icon file paths
    """
    icon_base_path = _get_icons_base_path()
    return [
        os.path.join(icon_base_path, "app-icon.icns"),  # macOS bundle icon
        os.path.join(icon_base_path, "app-icon-512.svg"),
        os.path.join(icon_base_path, "app-icon-192.svg"),
        os.path.join(icon_base_path, "icon-circle.svg"),
        os.path.join(icon_base_path, "icon-rounded.svg"),
        os.path.join(icon_base_path, "favicon-32.svg"),
        os.path.join(icon_base_path, "favicon-16.svg"),
    ]


def load_application_icon(app: QApplication) -> bool:
    """
    Load application icon from the icons directory.

    Args:
        app: The QApplication instance

    Returns:
        bool: True if icon was loaded successfully, False otherwise
    """
    try:
        icon_files = _get_icon_candidates()

        # Try to load the icon from one of the files
        for icon_path in icon_files:
            if os.path.exists(icon_path):
                logger.debug(
                    "icon_loading",
                    icon_path=icon_path,
                    frozen=getattr(sys, "frozen", False),
                )
                app.setWindowIcon(QIcon(icon_path))
                return True

        logger.warning("icon_not_found", tried_paths=icon_files)
        return False

    except Exception as e:
        logger.error(
            "icon_load_failed",
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True,
        )
        return False


def get_splash_image_path() -> str | None:
    """
    Get the path to the splash screen image.

    Returns:
        Optional[str]: Path to splash image or None if not found
    """
    icon_base_path = _get_icons_base_path()
    splash_image_path = os.path.join(icon_base_path, "splash.png")

    if os.path.exists(splash_image_path):
        return splash_image_path

    # Try alternative icon files that can be used for splash
    alternatives = [
        "app-icon-512.svg",
        "app-icon-192.svg",
        "icon-circle.svg",
        "icon-rounded.svg",
    ]

    for alt in alternatives:
        if getattr(sys, "frozen", False):
            alt_path = os.path.join(sys._MEIPASS, "philocr_icons", alt)  # type: ignore
        else:
            alt_path = os.path.join("philocr_icons", alt)

        if os.path.exists(alt_path):
            return alt_path

    return None
