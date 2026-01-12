#!/usr/bin/env python3
"""UI Composer for MainWindow components.

This module handles the composition of all UI widgets and layouts
for the MainWindow, extracting UI setup logic from MainWindow.
"""
from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from philocr.ui.ui_builder import UIBuilder, UICallbacks
from philocr.ui.widgets.stage_progress import StageProgressWidget


@dataclass
class MainWindowUI:
    """Container for all MainWindow UI widget references.

    Attributes:
        main_widget: Main central widget
        progress_bar: Progress bar widget (for standard mode, kept for compatibility)
        stage_progress: Stage progress widget (for pipeline mode)
        tab_widget: Tab widget container
        text_edit: Text display widget
        markdown_preview: Markdown preview widget
        html_preview: HTML preview widget
        json_preview: JSON preview widget
        scan_area_tab: Scan area selection tab container widget
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
        mode_selector: Processing mode selector (radio button group)
        standard_mode_radio: Standard OCR mode radio button
        pipeline_mode_radio: Advanced Pipeline mode radio button
    """

    main_widget: QWidget
    progress_bar: QProgressBar
    stage_progress: StageProgressWidget
    tab_widget: QTabWidget
    text_edit: QTextEdit
    markdown_preview: QTextEdit
    html_preview: QTextEdit
    json_preview: QTextEdit
    scan_area_tab: QWidget
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
    mode_selector: QWidget
    standard_mode_radio: QRadioButton
    pipeline_mode_radio: QRadioButton


class MainWindowUIComposer:
    """Composes MainWindow UI components from a UIBuilder.

    Handles all UI construction logic, extracting this responsibility
    from MainWindow to improve cohesion and maintainability.
    """

    INITIAL_INSTRUCTIONS = """
PhilOcr

This application processes scanned PDFs of ancient Greek texts using
Google's Document AI service.

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

        # Create left panel container
        left_panel = QWidget()
        left_panel.setFixedWidth(250)
        left_panel_layout = QVBoxLayout(left_panel)
        left_panel_layout.setContentsMargins(10, 3, 5, 3)
        left_panel_layout.setSpacing(0)

        # Create right panel container
        right_panel = QWidget()
        right_panel_layout = QVBoxLayout(right_panel)
        right_panel_layout.setContentsMargins(0, 0, 0, 0)
        right_panel_layout.setSpacing(0)

        # Add panels to main layout
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel, 1)

        # Setup widgets for left panel
        self._setup_header(left_panel_layout)
        # Add spacing before mode selector
        left_panel_layout.addSpacing(15)
        mode_selector_widget, mode_radios = self._setup_mode_selector(
            left_panel_layout
        )
        buttons = self._setup_buttons(left_panel_layout)
        left_panel_layout.addStretch()

        # Setup widgets for right panel
        tabs, status_text = self._setup_tabs_and_status(right_panel_layout)

        # Create stage progress widget
        stage_progress = StageProgressWidget()
        stage_progress.setVisible(False)

        return MainWindowUI(
            main_widget=main_widget,
            progress_bar=tabs["progress_bar"],
            stage_progress=stage_progress,
            tab_widget=tabs["tab_widget"],
            text_edit=tabs["text_edit"],
            markdown_preview=tabs["markdown_preview"],
            html_preview=tabs["html_preview"],
            json_preview=tabs["json_preview"],
            scan_area_tab=tabs.get("scan_area_tab"),
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
            mode_selector=mode_selector_widget,
            standard_mode_radio=mode_radios["standard"],
            pipeline_mode_radio=mode_radios["pipeline"],
        )

    def setup_initial_content(self, text_edit: QTextEdit) -> None:
        """Set up initial content in the text edit widget.

        Args:
            text_edit: Text edit widget to populate
        """
        text_edit.setPlainText(self.INITIAL_INSTRUCTIONS.strip())

    def _setup_main_layout(self) -> tuple[QWidget, QHBoxLayout]:
        """Set up the main widget and layout.

        Returns:
            Tuple of (main widget, main layout)
        """
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        return main_widget, main_layout

    def _setup_header(self, main_layout: QVBoxLayout) -> None:
        """Set up the header section.

        Args:
            main_layout: Main layout to add header to
        """
        header_frame = self.ui_builder.create_header_section()
        main_layout.addWidget(header_frame)

    def _setup_buttons(self, main_layout: QVBoxLayout) -> dict[str, QPushButton]:
        """Set up button section.

        Args:
            main_layout: Main layout to add buttons to

        Returns:
            Dictionary of button widgets keyed by button name
        """
        button_layout, buttons = self.ui_builder.create_button_section()
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addStretch()
        container_layout.addLayout(button_layout)
        container_layout.addStretch()
        main_layout.addWidget(container)
        return buttons

    def _setup_mode_selector(
        self, main_layout: QVBoxLayout
    ) -> tuple[QWidget, dict[str, QRadioButton]]:
        """Set up processing mode selector.

        Args:
            main_layout: Main layout to add mode selector to

        Returns:
            Tuple of (mode selector widget, dictionary of radio buttons)
        """
        from PyQt6.QtWidgets import QFrame

        mode_frame = QFrame()
        mode_layout = QVBoxLayout(mode_frame)
        mode_layout.setContentsMargins(50, 0, 0, 10)
        mode_layout.setSpacing(8)

        gentium_font = QFont("Gentium", 14)

        standard_radio = QRadioButton("Standard OCR")
        standard_radio.setFont(gentium_font)
        standard_radio.setChecked(True)
        standard_radio.setToolTip("Full-page OCR - sends entire page to Document AI")

        pipeline_radio = QRadioButton("Manual Scan Area")
        pipeline_radio.setFont(gentium_font)
        pipeline_radio.setToolTip(
            "User-defined scan areas - crop pages before OCR to exclude "
            "margins/footnotes"
        )

        mode_group = QButtonGroup()
        mode_group.addButton(standard_radio, 0)
        mode_group.addButton(pipeline_radio, 1)

        mode_layout.addWidget(standard_radio)
        mode_layout.addWidget(pipeline_radio)

        main_layout.addWidget(mode_frame)

        return mode_frame, {
            "standard": standard_radio,
            "pipeline": pipeline_radio,
        }

    def _setup_tabs_and_status(
        self, right_panel_layout: QVBoxLayout
    ) -> tuple[dict[str, QWidget | QProgressBar | QTabWidget | QTextEdit | None], QLabel]:
        """Set up tab widget with status above.

        Args:
            right_panel_layout: Right panel layout to add tabs to

        Returns:
            Tuple of (dictionary containing progress_bar, tab_widget, and tab widgets, status_text label)
        """
        progress_bar = self.ui_builder.create_progress_bar()

        tab_widget, tabs = self.ui_builder.create_tabs()

        # Create compact status label
        status_text = QLabel("PhilOcr v3.0")
        status_text.setFont(QFont("Gentium", 12))
        status_text.setStyleSheet("color: #1e3a6e; padding: 2px 10px;")
        status_text.setMaximumHeight(24)

        # Add status above tabs
        right_panel_layout.addWidget(status_text, 0)
        right_panel_layout.addWidget(tab_widget, 1)

        return {
            "progress_bar": progress_bar,
            "tab_widget": tab_widget,
            "text_edit": tabs["text_edit"],
            "markdown_preview": tabs["markdown_preview"],
            "html_preview": tabs["html_preview"],
            "json_preview": tabs["json_preview"],
            "scan_area_tab": tabs.get("scan_area_tab"),
        }, status_text
