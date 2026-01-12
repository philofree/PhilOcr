#!/usr/bin/env python3
"""Template Preview Handler for MainWindow.

This module handles template visualization and preview operations,
extracting template-related functionality from MainWindow.
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from PyQt6.QtGui import QPixmap
    from PyQt6.QtWidgets import QLabel, QTextEdit, QWidget

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)


class TemplatePreviewHandler:
    """Handles template visualization and preview operations.

    Manages template preview text and image display, including
    context menus, saving, and opening template visualizations.
    """

    def __init__(
        self,
        template_preview_text: QTextEdit | None,  # noqa: F821
        template_preview_image: QLabel | None,  # noqa: F821
        parent_widget: QWidget,  # noqa: F821
        on_status_update: Any,  # Callable[[str], None]
        on_error: Any,  # Callable[[str], None]
    ) -> None:
        """Initialize the Template Preview Handler.

        Args:
            template_preview_text: Optional text edit widget for template preview text
            template_preview_image: Optional label widget for template preview image
            parent_widget: Parent widget for dialogs and menus
            on_status_update: Callback for status message updates
            on_error: Callback for error messages
        """
        self.template_preview_text = template_preview_text
        self.template_preview_image = template_preview_image
        self.parent_widget = parent_widget
        self.on_status_update = on_status_update
        self.on_error = on_error

    def handle_template_ready(self, template_dict: dict[str, Any]) -> None:
        """Handle template ready signal.

        Args:
            template_dict: Template metadata dictionary
        """
        # Update template text preview
        if self.template_preview_text:
            template_text = self._format_preview_text(template_dict)
            self.template_preview_text.setPlainText(template_text)

        # Update template image preview
        if self.template_preview_image:
            visualization_path = template_dict.get("visualization_path")
            if visualization_path:
                from PyQt6.QtCore import Qt
                from PyQt6.QtGui import QPixmap

                vis_path = Path(visualization_path)
                if vis_path.exists():
                    try:
                        pixmap = QPixmap(str(vis_path))
                        if not pixmap.isNull():
                            # Scale to fit while maintaining aspect ratio
                            scaled_pixmap = pixmap.scaled(
                                800,
                                1200,
                                Qt.AspectRatioMode.KeepAspectRatio,
                                Qt.TransformationMode.SmoothTransformation,
                            )
                            self.template_preview_image.setPixmap(scaled_pixmap)
                            self.template_preview_image.setText("")
                            # Store the original path for saving/opening
                            self.template_preview_image.visualization_path = str(
                                vis_path
                            )
                            # Set up context menu
                            self.template_preview_image.customContextMenuRequested.connect(
                                lambda pos: self._show_image_menu(
                                    pos, self.template_preview_image
                                )
                            )
                        else:
                            logger.warning(
                                "template_visualization_load_failed",
                                path=str(vis_path),
                            )
                    except Exception as e:
                        logger.warning(
                            "template_visualization_display_failed",
                            path=str(vis_path),
                            error=str(e),
                            error_type=type(e).__name__,
                            exc_info=True,
                        )

    def _show_image_menu(
        self, pos: Any, image_label: QLabel  # noqa: F821
    ) -> None:
        """Show context menu for template image.

        Args:
            pos: Position where context menu was requested
            image_label: The image label widget
        """
        from PyQt6.QtWidgets import QMenu

        if not hasattr(image_label, "visualization_path"):
            return

        menu = QMenu(self.parent_widget)
        save_action = menu.addAction("Save Image As...")
        open_action = menu.addAction("Open in Window")

        action = menu.exec(image_label.mapToGlobal(pos))
        if action == save_action:
            self._save_image(image_label.visualization_path)
        elif action == open_action:
            self._open_image_window(image_label.visualization_path)

    def _save_image(self, image_path: str) -> None:
        """Save template visualization image to a user-selected location.

        Args:
            image_path: Path to the visualization image
        """
        from PyQt6.QtWidgets import QFileDialog
        from shutil import copyfile

        default_filename = Path(image_path).name
        file_path, _ = QFileDialog.getSaveFileName(
            self.parent_widget,
            "Save Template Visualization",
            str(Path.home() / default_filename),
            "PNG Images (*.png);;All Files (*)",
        )

        if file_path:
            try:
                copyfile(image_path, file_path)
                self.on_status_update(f"Template image saved to {file_path}")
                logger.info("template_image_saved", path=file_path)
            except Exception as e:
                logger.error(
                    "template_image_save_failed",
                    path=file_path,
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True,
                )
                from philocr.utils.logging_config import flush_loggers

                flush_loggers()
                self.on_error(f"Failed to save image: {e}")

    def _open_image_window(self, image_path: str) -> None:
        """Open template visualization in a separate window.

        Args:
            image_path: Path to the visualization image
        """
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QPixmap
        from PyQt6.QtWidgets import QDialog, QLabel, QVBoxLayout

        dialog = QDialog(self.parent_widget)
        dialog.setWindowTitle("Template Visualization")
        dialog.setMinimumSize(800, 1000)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(0, 0, 0, 0)

        image_label = QLabel()
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_label.setScaledContents(False)

        try:
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                # Use original pixmap for better quality
                image_label.setPixmap(pixmap)
                image_label.setMinimumSize(600, 800)
                layout.addWidget(image_label)

                # Add right-click context menu to save
                image_label.setContextMenuPolicy(
                    Qt.ContextMenuPolicy.CustomContextMenu
                )
                image_label.customContextMenuRequested.connect(
                    lambda pos: self._show_image_menu(pos, image_label)
                )
                image_label.visualization_path = image_path

                dialog.exec()
            else:
                self.on_error("Failed to load template visualization image")
        except Exception as e:
            logger.error(
                "template_image_window_open_failed",
                path=image_path,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            from philocr.utils.logging_config import flush_loggers

            flush_loggers()
            self.on_error(f"Failed to open image window: {e}")

    def _format_preview_text(self, template_dict: dict[str, Any]) -> str:
        """Format template information for preview display.

        Args:
            template_dict: Template metadata dictionary

        Returns:
            Formatted template preview text
        """
        lines = [
            "Template Preview",
            "=" * 50,
            "",
            f"Confidence: {template_dict.get('confidence', 0.0):.2f}",
            f"Pages Analysed: {template_dict.get('pages_analysed', 0)}",
            "",
            "Note: Zone detection is applied individually to each page.",
        ]
        return "\n".join(lines)
