"""Tab factory for creating tab widgets.

This module provides factory methods for creating tab widgets
with consistent structure and styling.
"""

from __future__ import annotations

from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QLabel,
    QScrollArea,
    QSplitter,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

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
    def create_template_preview_tab(
        tab_widget: QTabWidget,
    ) -> tuple[QLabel, QTextEdit]:
        """Create the template preview tab with image and text.

        Args:
            tab_widget: The tab widget to add the tab to

        Returns:
            Tuple of (image_label, text_edit) widgets
        """
        template_tab = QWidget()
        main_layout = QVBoxLayout(template_tab)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Create splitter for image and text
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Image area (left side)
        image_scroll = QScrollArea()
        image_scroll.setWidgetResizable(True)
        image_label = QLabel()
        image_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop
        )
        image_label.setText("Template visualization will appear here.")
        image_label.setStyleSheet("background-color: #f0f0f0; padding: 10px;")
        image_label.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        image_scroll.setWidget(image_label)
        splitter.addWidget(image_scroll)
        splitter.setStretchFactor(0, 2)

        # Text area (right side)
        text_preview = WidgetFactory.create_text_edit()
        text_preview.setPlainText(
            "Template preview will appear here after pipeline processing."
        )
        splitter.addWidget(text_preview)
        splitter.setStretchFactor(1, 1)

        # Set initial sizes (60% image, 40% text)
        splitter.setSizes([600, 400])

        main_layout.addWidget(splitter)
        _ = tab_widget.addTab(template_tab, "Template Preview")
        return image_label, text_preview

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
        template_image, template_text = TabFactory.create_template_preview_tab(
            tab_widget
        )
        tabs["template_preview_image"] = template_image
        tabs["template_preview_text"] = template_text

        return tab_widget, tabs
