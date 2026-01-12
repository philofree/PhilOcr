"""Tab factory for creating tab widgets.

This module provides factory methods for creating tab widgets
with consistent structure and styling.
"""

from __future__ import annotations

from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QLabel, QTabWidget, QTextEdit, QVBoxLayout, QWidget

from philocr.ui.widget_factory import WidgetFactory


class TabFactory:
    """Factory for creating tab widgets."""

    @staticmethod
    def create_text_tab(tab_widget: QTabWidget) -> QTextEdit:
        """Create the text display tab.

        Args:
            tab_widget: The tab widget to add the tab to

        Returns:
            The text edit widget for the text tab
        """
        from PyQt6.QtWidgets import QVBoxLayout, QWidget

        text_tab = QWidget()
        text_layout = QVBoxLayout(text_tab)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_frame, text_edit = WidgetFactory.create_text_area_frame()
        text_layout.addWidget(text_frame)
        _ = tab_widget.addTab(text_tab, "Text")
        return text_edit

    @staticmethod
    def create_markdown_tab(tab_widget: QTabWidget) -> QTextEdit:
        """Create the markdown preview tab.

        Args:
            tab_widget: The tab widget to add the tab to

        Returns:
            The text edit widget for the markdown tab
        """
        markdown_tab = QWidget()
        markdown_layout = QVBoxLayout(markdown_tab)
        markdown_layout.setContentsMargins(0, 0, 0, 0)
        markdown_preview = WidgetFactory.create_text_edit(
            font_families=["Gentium"],
            font_size=12,
        )
        markdown_layout.addWidget(markdown_preview)
        _ = tab_widget.addTab(markdown_tab, "Markdown")
        return markdown_preview

    @staticmethod
    def create_html_tab(tab_widget: QTabWidget) -> QTextEdit:
        """Create the HTML preview tab.

        Args:
            tab_widget: The tab widget to add the tab to

        Returns:
            The text edit widget for the HTML tab
        """
        html_tab = QWidget()
        html_layout = QVBoxLayout(html_tab)
        html_layout.setContentsMargins(0, 0, 0, 0)
        html_preview = WidgetFactory.create_text_edit()
        html_layout.addWidget(html_preview)
        _ = tab_widget.addTab(html_tab, "HTML")
        return html_preview

    @staticmethod
    def create_json_tab(tab_widget: QTabWidget) -> QTextEdit:
        """Create the JSON preview tab.

        Args:
            tab_widget: The tab widget to add the tab to

        Returns:
            The text edit widget for the JSON tab
        """
        json_tab = QWidget()
        json_layout = QVBoxLayout(json_tab)
        json_layout.setContentsMargins(0, 0, 0, 0)
        json_preview = WidgetFactory.create_text_edit()
        json_layout.addWidget(json_preview)
        _ = tab_widget.addTab(json_tab, "JSON")
        return json_preview

    @staticmethod
    def create_scan_area_tab(
        tab_widget: QTabWidget,
    ) -> QWidget:
        """Create the scan area selection tab container.

        This tab will be populated with ScanAreaViewerWidget when a PDF is selected.

        Args:
            tab_widget: The tab widget to add the tab to

        Returns:
            Container widget that can hold the scan area viewer
        """
        scan_area_tab = QWidget()
        main_layout = QVBoxLayout(scan_area_tab)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Placeholder label
        placeholder = QLabel(
            "Select a PDF file to begin defining scan areas for each page.\n\n"
            "You can drag corners to adjust for rotation/skew, "
            "and drag edges to resize the scan area."
        )
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet(
            "background-color: #f0f0f0; padding: 40px; font-size: 14px;"
        )
        placeholder.setWordWrap(True)
        main_layout.addWidget(placeholder)

        _ = tab_widget.addTab(scan_area_tab, "Scan Area Selection")
        return scan_area_tab

    @staticmethod
    def create_all_tabs() -> tuple[QTabWidget, dict[str, Any]]:
        """Create all preview tabs.

        Returns:
            Tuple of (tab widget, dictionary of tab widgets)
        """
        tab_widget = QTabWidget()
        tab_font = QFont("Gentium", 15)
        tab_widget.setFont(tab_font)
        tab_widget.setStyleSheet(
            "QTabBar::tab { padding: 6px 12px; text-align: center; }"
            "QTabBar::tab:selected { background-color: #1e3a6e; color: white; }"
            "QTabBar { margin-bottom: 0px; }"
            "QTabWidget::pane { border: 0px; padding: 0px; margin: 0px; }"
        )
        tabs: dict[str, Any] = {}

        tabs["text_edit"] = TabFactory.create_text_tab(tab_widget)
        tabs["markdown_preview"] = TabFactory.create_markdown_tab(tab_widget)
        tabs["html_preview"] = TabFactory.create_html_tab(tab_widget)
        tabs["json_preview"] = TabFactory.create_json_tab(tab_widget)
        scan_area_tab = TabFactory.create_scan_area_tab(tab_widget)
        tabs["scan_area_tab"] = scan_area_tab

        return tab_widget, tabs
