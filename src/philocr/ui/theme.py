"""Theme-aware styling helpers for light and dark system appearances."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette
from PyQt6.QtWidgets import QApplication


def is_dark_mode() -> bool:
    """Return True when the application is using a dark color scheme.

    Returns:
        True if the active palette or style hints indicate dark mode
    """
    app = QApplication.instance()
    if app is None:
        return False

    style_hints = app.styleHints()
    color_scheme = getattr(style_hints, "colorScheme", None)
    if color_scheme is not None and callable(color_scheme):
        return color_scheme() == Qt.ColorScheme.Dark

    window = app.palette().color(QPalette.ColorRole.Window)
    return window.lightness() < 128


def style_primary_label(extra: str = "") -> str:
    """Return stylesheet for primary status and section labels.

    Args:
        extra: Additional CSS declarations to append

    Returns:
        Stylesheet string using theme-appropriate text color
    """
    if is_dark_mode():
        base = "color: #dce4f0;"
    else:
        base = "color: #1e3a6e;"
    if extra:
        return f"{base} {extra}"
    return base


def style_scan_save_button() -> str:
    """Return stylesheet for the Save Scan Areas button.

    Returns:
        Stylesheet string with explicit background and text colors
    """
    if is_dark_mode():
        return (
            "QPushButton { background-color: #2a4570; color: #e8eef8; "
            "border: 1px solid #3d5a80; }"
            "QPushButton:hover { background-color: #3d5a80; }"
            "QPushButton:disabled { background-color: #1e2d44; color: #8090a8; }"
        )
    return (
        "QPushButton { background-color: #E6F0FF; color: #1e3a6e; "
        "border: 1px solid #b8cff0; }"
        "QPushButton:hover { background-color: #CCE0FF; }"
        "QPushButton:disabled { background-color: #f0f4fa; color: #8090a8; }"
    )


def style_scan_send_button() -> str:
    """Return stylesheet for the Send Scan Areas button.

    Returns:
        Stylesheet string with explicit background and text colors
    """
    if is_dark_mode():
        return (
            "QPushButton { background-color: #2a5035; color: #e8f5ea; "
            "border: 1px solid #3d6b48; }"
            "QPushButton:hover { background-color: #3d6b48; }"
            "QPushButton:disabled { background-color: #1e3324; color: #809880; }"
        )
    return (
        "QPushButton { background-color: #E6FFE6; color: #1a4a1a; "
        "border: 1px solid #b8e0b8; }"
        "QPushButton:hover { background-color: #CCFFCC; }"
        "QPushButton:disabled { background-color: #f0faf0; color: #809880; }"
    )
