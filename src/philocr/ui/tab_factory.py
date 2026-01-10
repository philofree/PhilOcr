"""Tab factory for creating tab widgets.

This module provides factory methods for creating tab widgets
with consistent structure and styling.
"""

from __future__ import annotations

from typing import Any

from PyQt6.QtWidgets import QTabWidget, QTextEdit, QVBoxLayout, QWidget

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
        markdown_preview = WidgetFactory.create_text_edit(
            font_families=[
                "Courier New",
                "DejaVu Sans Mono",
                "Menlo",
                "Consolas",
                "Liberation Mono",
                "monospace",
            ],
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
        json_preview = WidgetFactory.create_text_edit()
        json_layout.addWidget(json_preview)
        _ = tab_widget.addTab(json_tab, "JSON")
        return json_preview

    @staticmethod
    def create_all_tabs() -> tuple[QTabWidget, dict[str, Any]]:
        """Create all preview tabs.

        Returns:
            Tuple of (tab widget, dictionary of tab widgets)
        """
        tab_widget = QTabWidget()
        tabs: dict[str, Any] = {}

        tabs["text_edit"] = TabFactory.create_text_tab(tab_widget)
        tabs["markdown_preview"] = TabFactory.create_markdown_tab(tab_widget)
        tabs["html_preview"] = TabFactory.create_html_tab(tab_widget)
        tabs["json_preview"] = TabFactory.create_json_tab(tab_widget)

        return tab_widget, tabs
