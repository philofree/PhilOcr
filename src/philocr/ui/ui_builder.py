#!/usr/bin/env python3
"""UI Builder for MainWindow components.

This module handles the construction and configuration of all UI widgets
and layouts for the MainWindow.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, NamedTuple

from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QTabWidget,
)

from philocr.ui.tab_factory import TabFactory
from philocr.ui.widget_factory import WidgetFactory


class ButtonConfig(NamedTuple):
    """Configuration for a button.

    Attributes:
        key: Dictionary key for the button
        text: Button label text
        callback: Click callback function
        enabled: Initial enabled state
        tooltip: Optional tooltip text
        max_width: Optional maximum width
    """

    key: str
    text: str
    callback: Callable[[], None]
    enabled: bool = True
    tooltip: str | None = None
    max_width: int | None = None


@dataclass
class UICallbacks:
    """Configuration for UI builder callbacks.

    Attributes:
        on_settings_clicked: Callback for settings button
        on_about_clicked: Callback for about button
        on_select_file: Callback for select file button
        on_batch_files: Callback for batch files button
        on_load_json: Callback for load JSON button
        on_save_text: Callback for save text button
        on_save_markdown: Callback for save markdown button
        on_save_json: Callback for save JSON button
        on_save_html: Callback for save HTML button
        on_clear: Callback for clear button
        on_debug_markdown: Callback for debug markdown button
        on_pipeline_config: Callback for pipeline configuration button
    """

    on_settings_clicked: Callable[[], None]
    on_about_clicked: Callable[[], None]
    on_select_file: Callable[[], None]
    on_batch_files: Callable[[], None]
    on_load_json: Callable[[], None]
    on_save_text: Callable[[], None]
    on_save_markdown: Callable[[], None]
    on_save_json: Callable[[], None]
    on_save_html: Callable[[], None]
    on_clear: Callable[[], None]
    on_debug_markdown: Callable[[], None]
    on_pipeline_config: Callable[[], None]


class UIBuilder:
    """Builder for creating and configuring MainWindow UI components."""

    def __init__(
        self,
        app_name: str,
        app_version: str,
        callbacks: UICallbacks,
    ) -> None:
        """Initialize the UI Builder.

        Args:
            app_name: Application name
            app_version: Application version
            callbacks: Configuration object containing all UI callbacks
        """
        self.app_name = app_name
        self.app_version = app_version
        self.on_settings_clicked = callbacks.on_settings_clicked
        self.on_about_clicked = callbacks.on_about_clicked
        self.on_select_file = callbacks.on_select_file
        self.on_batch_files = callbacks.on_batch_files
        self.on_load_json = callbacks.on_load_json
        self.on_save_text = callbacks.on_save_text
        self.on_save_markdown = callbacks.on_save_markdown
        self.on_save_json = callbacks.on_save_json
        self.on_save_html = callbacks.on_save_html
        self.on_clear = callbacks.on_clear
        self.on_debug_markdown = callbacks.on_debug_markdown
        self.on_pipeline_config = callbacks.on_pipeline_config

    def create_header_section(self) -> QFrame:
        """Create the application header section.

        Returns:
            Configured header frame with title, version, and buttons.
        """
        return WidgetFactory.create_header_frame(
            self.app_name,
            self.app_version,
            self.on_settings_clicked,
            self.on_about_clicked,
        )

    def _create_button(self, config: ButtonConfig) -> QPushButton:
        """Create a button from configuration.

        Args:
            config: Button configuration

        Returns:
            Configured button widget
        """
        return WidgetFactory.create_button(
            text=config.text,
            callback=config.callback,
            enabled=config.enabled,
            tooltip=config.tooltip,
            max_width=config.max_width,
        )

    def create_button_section(
        self,
    ) -> tuple[QHBoxLayout, dict[str, QPushButton]]:
        """Create the button section.

        Returns:
            Tuple of (button layout, dictionary of button widgets).
        """
        button_configs = [
            ButtonConfig("select", "Select PDF", self.on_select_file),
            ButtonConfig("batch", "Batch Process", self.on_batch_files),
            ButtonConfig("load_json", "Load JSON", self.on_load_json),
            ButtonConfig("save", "Save Text", self.on_save_text, False),
            ButtonConfig(
                "save_markdown", "Save Markdown", self.on_save_markdown, False
            ),
            ButtonConfig("save_json", "Save JSON", self.on_save_json, False),
            ButtonConfig("save_html", "Save HTML", self.on_save_html, False),
            ButtonConfig("clear", "Clear", self.on_clear),
            ButtonConfig(
                "debug_md",
                "Debug MD",
                self.on_debug_markdown,
                tooltip="Run a debug test of the markdown conversion",
                max_width=80,
            ),
        ]

        button_layout = QHBoxLayout()
        buttons = {}

        for config in button_configs:
            button = self._create_button(config)
            button_layout.addWidget(button)
            buttons[config.key] = button

        return button_layout, buttons

    def create_status_section(self) -> tuple[QFrame, QLabel]:
        """Create the status section.

        Returns:
            Tuple of (status frame, status label widget).
        """
        return WidgetFactory.create_status_frame()

    def create_tabs(self) -> tuple[QTabWidget, dict[str, Any]]:
        """Create the tab widget with all preview tabs.

        Returns:
            Tuple of (tab widget, dictionary of tab widgets).
        """
        return TabFactory.create_all_tabs()

    def create_progress_bar(self) -> QProgressBar:
        """Create the progress bar widget.

        Returns:
            Configured progress bar widget.
        """
        return WidgetFactory.create_progress_bar()
