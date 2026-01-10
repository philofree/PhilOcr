#!/usr/bin/env python3
"""Dialog Manager for MainWindow.

This module handles all dialog interactions including settings
and about dialogs, extracting this responsibility from MainWindow.
"""
from __future__ import annotations

from collections.abc import Callable

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QDialog, QWidget

from philocr.ui.dialogs import AboutDialog, CredentialsDialog
from philocr.utils.env_utils import load_env_file


class DialogManager:
    """Manages dialog interactions for MainWindow.

    Handles settings and about dialogs to improve cohesion
    and maintainability in MainWindow.
    """

    def __init__(
        self,
        parent_widget: QWidget,
        app_name: str,
        app_version: str,
        app_copyright: str,
        app_description: str,
        on_config_check: Callable[[], None],
    ) -> None:
        """Initialize the Dialog Manager.

        Args:
            parent_widget: Parent widget for dialogs
            app_name: Application name
            app_version: Application version
            app_copyright: Copyright string
            app_description: Application description
            on_config_check: Callback to check configuration after
                settings dialog is accepted
        """
        self.parent_widget = parent_widget
        self.app_name = app_name
        self.app_version = app_version
        self.app_copyright = app_copyright
        self.app_description = app_description
        self.on_config_check = on_config_check

    def show_settings(self) -> None:
        """Show the settings/credentials dialog."""
        dialog = CredentialsDialog(self.parent_widget)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            _ = load_env_file()
            _ = QTimer.singleShot(100, self.on_config_check)

    def show_about(self) -> None:
        """Show the about dialog."""
        dialog = AboutDialog(
            self.parent_widget,
            self.app_name,
            self.app_version,
            self.app_description,
            self.app_copyright,
        )
        _ = dialog.exec()
