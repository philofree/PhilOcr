#!/usr/bin/env python3
"""UI Composer for MainWindow components.

This module handles the composition of all UI widgets and layouts
for the MainWindow, extracting UI setup logic from MainWindow.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

from PyQt6.QtWidgets import (
    QLabel,
    QProgressBar,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from philocr.ui.ui_builder import UIBuilder, UICallbacks

if TYPE_CHECKING:
    pass


@dataclass
class MainWindowUI:
    """Container for all MainWindow UI widget references.

    Attributes:
        main_widget: Main central widget
        progress_bar: Progress bar widget
        tab_widget: Tab widget container
        text_edit: Text display widget
        markdown_preview: Markdown preview widget
        html_preview: HTML preview widget
        json_preview: JSON preview widget
        select_button: Select PDF button
        batch_button: Batch process button
        load_json_button: Load JSON button
        save_button: Save text button
        save_markdown_button: Save markdown button
        save_json_button: Save JSON button
        save_html_button: Save HTML button
        clear_button: Clear button
        debug_md_button: Debug markdown button
        status_text: Status label widget
    """

    main_widget: QWidget
    progress_bar: QProgressBar
    tab_widget: QTabWidget
    text_edit: QTextEdit
    markdown_preview: QTextEdit
    html_preview: QTextEdit
    json_preview: QTextEdit
    select_button: QPushButton
    batch_button: QPushButton
    load_json_button: QPushButton
    save_button: QPushButton
    save_markdown_button: QPushButton
    save_json_button: QPushButton
    save_html_button: QPushButton
    clear_button: QPushButton
    debug_md_button: QPushButton
    status_text: QLabel


class MainWindowUIComposer:
    """Composes MainWindow UI components from a UIBuilder.

    Handles all UI construction logic, extracting this responsibility
    from MainWindow to improve cohesion and maintainability.
    """

    INITIAL_INSTRUCTIONS = """
PhilOcr

This application processes scanned PDFs of ancient Greek texts using Google's Document AI service.

To get started:
1. Click 'Select PDF' to process a single document
2. Click 'Batch Process' to process multiple documents
3. After processing, click 'Save Text' to save the extracted text
4. You can also save JSON, HTML, or Markdown versions of the results

Note: 
- Processing times depend on document size and complexity
- The application respects Google's rate limits (15 requests/minute)
- Documents larger than 15 pages are automatically split into smaller chunks
  and processed separately, then combined back into a single result
- Google Document AI has a 15-page limit per document
"""

    def __init__(
        self,
        app_name: str,
        app_version: str,
        callbacks: UICallbacks,
    ) -> None:
        """Initialize the UI Composer.

        Args:
            app_name: Application name
            app_version: Application version
            callbacks: UI callback configuration
        """
        self.app_name = app_name
        self.app_version = app_version
        self.ui_builder = UIBuilder(
            app_name=app_name,
            app_version=app_version,
            callbacks=callbacks,
        )

    def compose_ui(self) -> MainWindowUI:
        """Compose the complete MainWindow UI.

        Returns:
            MainWindowUI dataclass containing all widget references
        """
        main_widget, main_layout = self._setup_main_layout()

        self._setup_header(main_layout)
        buttons = self._setup_buttons(main_layout)
        status_text = self._setup_status_section(main_layout)
        tabs = self._setup_tabs(main_layout)

        return MainWindowUI(
            main_widget=main_widget,
            progress_bar=tabs["progress_bar"],
            tab_widget=tabs["tab_widget"],
            text_edit=tabs["text_edit"],
            markdown_preview=tabs["markdown_preview"],
            html_preview=tabs["html_preview"],
            json_preview=tabs["json_preview"],
            select_button=buttons["select"],
            batch_button=buttons["batch"],
            load_json_button=buttons["load_json"],
            save_button=buttons["save"],
            save_markdown_button=buttons["save_markdown"],
            save_json_button=buttons["save_json"],
            save_html_button=buttons["save_html"],
            clear_button=buttons["clear"],
            debug_md_button=buttons["debug_md"],
            status_text=status_text,
        )

    def setup_initial_content(self, text_edit: QTextEdit) -> None:
        """Set up initial content in the text edit widget.

        Args:
            text_edit: Text edit widget to populate
        """
        text_edit.setPlainText(self.INITIAL_INSTRUCTIONS.strip())

    def _setup_main_layout(self) -> tuple[QWidget, QVBoxLayout]:
        """Set up the main widget and layout.

        Returns:
            Tuple of (main widget, main layout)
        """
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        return main_widget, main_layout

    def _setup_header(self, main_layout: QVBoxLayout) -> None:
        """Set up the header section.

        Args:
            main_layout: Main layout to add header to
        """
        header_frame = self.ui_builder.create_header_section()
        main_layout.addWidget(header_frame)

    def _setup_buttons(
        self, main_layout: QVBoxLayout
    ) -> dict[str, QPushButton]:
        """Set up button section.

        Args:
            main_layout: Main layout to add buttons to

        Returns:
            Dictionary of button widgets keyed by button name
        """
        button_layout, buttons = self.ui_builder.create_button_section()
        main_layout.addLayout(button_layout)
        return buttons

    def _setup_status_section(self, main_layout: QVBoxLayout) -> QLabel:
        """Set up the status section.

        Args:
            main_layout: Main layout to add status to

        Returns:
            Status text label widget
        """
        status_frame, status_text = self.ui_builder.create_status_section()
        main_layout.addWidget(status_frame)
        return status_text

    def _setup_tabs(
        self, main_layout: QVBoxLayout
    ) -> dict[str, QWidget | QProgressBar | QTabWidget]:
        """Set up tab widget and progress bar.

        Args:
            main_layout: Main layout to add tabs to

        Returns:
            Dictionary containing progress_bar, tab_widget, and tab widgets
        """
        progress_bar = self.ui_builder.create_progress_bar()
        main_layout.addWidget(progress_bar)

        tab_widget, tabs = self.ui_builder.create_tabs()
        main_layout.addWidget(tab_widget, 1)

        return {
            "progress_bar": progress_bar,
            "tab_widget": tab_widget,
            "text_edit": tabs["text_edit"],
            "markdown_preview": tabs["markdown_preview"],
            "html_preview": tabs["html_preview"],
            "json_preview": tabs["json_preview"],
        }
