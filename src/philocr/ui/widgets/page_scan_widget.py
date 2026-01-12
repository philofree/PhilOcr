"""Widget for displaying a page with draggable scan area rectangle."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np
else:
    import numpy as np

from PyQt6.QtCore import QPoint, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QImage, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import QWidget

from philocr.models.scan_area import ManualScanArea

# Handle size for corners and edges (in pixels)
HANDLE_SIZE = 10
EDGE_HANDLE_SIZE = 8

# Image dimensions
GRAYSCALE_DIMS = 2
RGB_DIMS = 3


class PageScanAreaWidget(QWidget):
    """Widget displaying a page with draggable scan area rectangle.

    The rectangle has 4 draggable corners (for rotation/skew) and
    4 draggable edges (for resizing). Coordinates are stored relative
    to the original page image dimensions.
    """

    scan_area_changed = pyqtSignal(int, ManualScanArea)

    def __init__(
        self,
        page_num: int,
        page_image: np.ndarray,
        initial_scan_area: ManualScanArea | None = None,
        display_width: int = 400,
    ) -> None:
        """Initialize the page scan area widget.

        Args:
            page_num: Page number (0-indexed)
            page_image: Page image as numpy array (grayscale or RGB)
            initial_scan_area: Initial scan area (or None for default)
            display_width: Width to display page at (height scales proportionally)
        """
        super().__init__()
        self.page_num = page_num
        self.original_image = page_image
        self.original_height, self.original_width = page_image.shape[:2]

        # Zoom state
        self.zoom_level = 1.0
        self.base_display_width = display_width

        # Calculate display dimensions maintaining aspect ratio
        aspect_ratio = self.original_height / self.original_width
        self.display_width = display_width
        self.display_height = int(display_width * aspect_ratio)

        # Scale factor for coordinate conversion
        self.scale_x = self.display_width / self.original_width
        self.scale_y = self.display_height / self.original_height

        # Initialize scan area
        if initial_scan_area is None:
            self.scan_area = ManualScanArea.create_default(
                self.original_width, self.original_height
            )
        else:
            self.scan_area = initial_scan_area

        # Dragging state
        self.dragging = False
        self.drag_target: str | None = None  # 'corner_*', 'edge_*', 'body', or 'mask'
        self.drag_start_pos: QPoint | None = None
        self.drag_start_corners: list[tuple[int, int]] | None = None

        # Mask drawing state
        self.mask_mode = False
        self.drawing_mask = False
        self.current_mask_start: QPoint | None = None
        self.current_mask_end: QPoint | None = None

        # Line break mode state
        self.line_break_mode = False
        self.paragraph_break_mode = False

        # Create display pixmap
        self._create_display_pixmap()

        # Set up widget
        self.setMinimumSize(self.display_width, self.display_height)
        self.setMaximumSize(self.display_width, self.display_height)
        self.setMouseTracking(True)

    def _create_display_pixmap(self) -> None:
        """Create QPixmap from numpy array for display."""
        # Convert numpy array to QImage
        if len(self.original_image.shape) == GRAYSCALE_DIMS:
            # Grayscale
            height, width = self.original_image.shape
            q_image = QImage(
                self.original_image.data,
                width,
                height,
                width,
                QImage.Format.Format_Grayscale8,
            )
        elif self.original_image.shape[2] == RGB_DIMS:
            # RGB
            height, width = self.original_image.shape[:2]
            q_image = QImage(
                self.original_image.data,
                width,
                height,
                width * 3,
                QImage.Format.Format_RGB888,
            ).rgbSwapped()
        else:
            # RGBA
            height, width = self.original_image.shape[:2]
            q_image = QImage(
                self.original_image.data,
                width,
                height,
                width * 4,
                QImage.Format.Format_RGBA8888,
            )

        # Scale to display size
        pixmap = QPixmap.fromImage(q_image)
        self.display_pixmap = pixmap.scaled(
            self.display_width,
            self.display_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

    def _update_zoom(self, new_zoom: float) -> None:
        """Update zoom level and recalculate display dimensions.

        Args:
            new_zoom: New zoom level (1.0 = 100%)
        """
        # Clamp zoom between 50% and 300%
        self.zoom_level = max(0.5, min(3.0, new_zoom))

        # Recalculate display dimensions
        aspect_ratio = self.original_height / self.original_width
        self.display_width = int(self.base_display_width * self.zoom_level)
        self.display_height = int(self.display_width * aspect_ratio)

        # Update scale factors
        self.scale_x = self.display_width / self.original_width
        self.scale_y = self.display_height / self.original_height

        # Recreate pixmap at new size
        self._create_display_pixmap()

        # Update widget size
        self.setMinimumSize(self.display_width, self.display_height)
        self.setMaximumSize(self.display_width, self.display_height)
        self.updateGeometry()
        self.update()

    def _image_to_display(self, x: int, y: int) -> tuple[int, int]:
        """Convert image coordinates to display coordinates.

        Args:
            x: X coordinate in original image
            y: Y coordinate in original image

        Returns:
            (x, y) in display coordinates
        """
        return (int(x * self.scale_x), int(y * self.scale_y))

    def _display_to_image(self, x: int, y: int) -> tuple[int, int]:
        """Convert display coordinates to image coordinates.

        Args:
            x: X coordinate in display
            y: Y coordinate in display

        Returns:
            (x, y) in original image coordinates
        """
        return (int(x / self.scale_x), int(y / self.scale_y))

    def _get_corner_positions(self) -> list[QPoint]:
        """Get display positions of all 4 corners.

        Returns:
            List of QPoint for [top_left, top_right, bottom_right, bottom_left]
        """
        corners = self.scan_area.to_list()
        return [QPoint(*self._image_to_display(x, y)) for x, y in corners]

    def _get_edge_centers(self) -> list[QPoint]:
        """Get display positions of edge centers.

        Returns:
            List of QPoint for [top, right, bottom, left] edge centers
        """
        corners = self._get_corner_positions()
        return [
            QPoint(
                (corners[0].x() + corners[1].x()) // 2,
                (corners[0].y() + corners[1].y()) // 2,
            ),  # Top
            QPoint(
                (corners[1].x() + corners[2].x()) // 2,
                (corners[1].y() + corners[2].y()) // 2,
            ),  # Right
            QPoint(
                (corners[2].x() + corners[3].x()) // 2,
                (corners[2].y() + corners[3].y()) // 2,
            ),  # Bottom
            QPoint(
                (corners[0].x() + corners[3].x()) // 2,
                (corners[0].y() + corners[3].y()) // 2,
            ),  # Left
        ]

    def _hit_test_masks(self, pos: QPoint) -> int | None:
        """Test if mouse position hits a mask rectangle.

        Args:
            pos: Mouse position in widget coordinates

        Returns:
            Index of mask rectangle, or None if no hit
        """
        if not self.scan_area.mask_rects:
            return None

        # Test masks in reverse order (most recent first)
        for i in range(len(self.scan_area.mask_rects) - 1, -1, -1):
            x, y, width, height = self.scan_area.mask_rects[i]
            display_x, display_y = self._image_to_display(x, y)
            display_width = int(width * self.scale_x)
            display_height = int(height * self.scale_y)

            if (
                display_x <= pos.x() <= display_x + display_width
                and display_y <= pos.y() <= display_y + display_height
            ):
                return i

        return None

    def _point_in_rectangle(self, pos: QPoint) -> bool:
        """Test if point is inside the scan area rectangle.

        Args:
            pos: Mouse position in widget coordinates

        Returns:
            True if point is inside the rectangle
        """
        corners = self._get_corner_positions()
        
        # Simple rectangle check (works for non-rotated rectangles)
        # Get bounding box
        min_x = min(c.x() for c in corners)
        max_x = max(c.x() for c in corners)
        min_y = min(c.y() for c in corners)
        max_y = max(c.y() for c in corners)
        
        return min_x <= pos.x() <= max_x and min_y <= pos.y() <= max_y

    def _hit_test(self, pos: QPoint) -> str | None:
        """Test if mouse position hits a corner or edge handle.

        Args:
            pos: Mouse position in widget coordinates

        Returns:
            'corner_0', 'corner_1', etc., 'edge_top', 'edge_right', etc., 'body', or None
        """
        # Test corners first (they have priority)
        corners = self._get_corner_positions()
        for i, corner in enumerate(corners):
            if (
                abs(pos.x() - corner.x()) <= HANDLE_SIZE // 2
                and abs(pos.y() - corner.y()) <= HANDLE_SIZE // 2
            ):
                return f"corner_{i}"

        # Test edges
        edges = self._get_edge_centers()
        edge_names = ["edge_top", "edge_right", "edge_bottom", "edge_left"]
        for i, edge in enumerate(edges):
            if (
                abs(pos.x() - edge.x()) <= EDGE_HANDLE_SIZE // 2
                and abs(pos.y() - edge.y()) <= EDGE_HANDLE_SIZE // 2
            ):
                return edge_names[i]

        # Test if inside rectangle body
        if self._point_in_rectangle(pos):
            return "body"

        return None

    def mousePressEvent(self, event) -> None:
        """Handle mouse press for starting drag, mask drawing, or line break insertion."""
        if event.button() == Qt.MouseButton.RightButton:
            # Right-click inserts paragraph break
            pos = event.position().toPoint()
            _, y_img = self._display_to_image(pos.x(), pos.y())
            
            if self.scan_area.paragraph_breaks is None:
                self.scan_area.paragraph_breaks = []
            
            # Add paragraph break (sorted for easier processing)
            self.scan_area.paragraph_breaks.append(y_img)
            self.scan_area.paragraph_breaks.sort()
            
            self.scan_area_changed.emit(self.page_num, self.scan_area)
            self.update()
        elif event.button() == Qt.MouseButton.LeftButton:
            if self.line_break_mode:
                # Insert line break at click position
                pos = event.position().toPoint()
                _, y_img = self._display_to_image(pos.x(), pos.y())
                
                if self.scan_area.line_breaks is None:
                    self.scan_area.line_breaks = []
                
                # Add line break (sorted for easier processing)
                self.scan_area.line_breaks.append(y_img)
                self.scan_area.line_breaks.sort()
                
                self.scan_area_changed.emit(self.page_num, self.scan_area)
                self.update()
            elif self.mask_mode:
                # Start drawing a mask rectangle
                self.drawing_mask = True
                self.current_mask_start = event.position().toPoint()
                self.setCursor(Qt.CursorShape.CrossCursor)
            else:
                # Normal scan area dragging
                target = self._hit_test(event.position().toPoint())
                if target:
                    self.dragging = True
                    self.drag_target = target
                    self.drag_start_pos = event.position().toPoint()
                    self.drag_start_corners = self.scan_area.to_list()
                    self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseDoubleClickEvent(self, event) -> None:
        """Handle double-click to delete a mask rectangle, line break, or paragraph break."""
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            
            # Check for paragraph break deletion first (thicker, higher priority)
            if self.scan_area.paragraph_breaks:
                _, y_img = self._display_to_image(pos.x(), pos.y())
                for i, pb_y in enumerate(self.scan_area.paragraph_breaks):
                    if abs(pb_y - y_img) <= 7 / self.scale_y:  # Larger hit area for thicker line
                        del self.scan_area.paragraph_breaks[i]
                        if not self.scan_area.paragraph_breaks:
                            self.scan_area.paragraph_breaks = None
                        self.scan_area_changed.emit(self.page_num, self.scan_area)
                        self.update()
                        return
            
            # Check for line break deletion
            if self.scan_area.line_breaks:
                _, y_img = self._display_to_image(pos.x(), pos.y())
                # Find line break within 5 pixels
                for i, lb_y in enumerate(self.scan_area.line_breaks):
                    if abs(lb_y - y_img) <= 5 / self.scale_y:
                        del self.scan_area.line_breaks[i]
                        if not self.scan_area.line_breaks:
                            self.scan_area.line_breaks = None
                        self.scan_area_changed.emit(self.page_num, self.scan_area)
                        self.update()
                        return
            
            # Check for mask deletion
            mask_index = self._hit_test_masks(pos)
            if mask_index is not None:
                if self.scan_area.mask_rects:
                    del self.scan_area.mask_rects[mask_index]
                    if not self.scan_area.mask_rects:
                        self.scan_area.mask_rects = None
                    self.scan_area_changed.emit(self.page_num, self.scan_area)
                    self.update()

    def mouseMoveEvent(self, event) -> None:
        """Handle mouse move for dragging and hover feedback."""
        pos = event.position().toPoint()

        if self.drawing_mask:
            # Update end position and repaint
            self.current_mask_end = pos
            self.update()
        elif self.dragging and self.drag_target and self.drag_start_pos:
            # Calculate drag delta in image coordinates
            delta_x = (pos.x() - self.drag_start_pos.x()) / self.scale_x
            delta_y = (pos.y() - self.drag_start_pos.y()) / self.scale_y

            # Get starting corners
            corners = list(self.drag_start_corners) if self.drag_start_corners else []

            # Apply drag based on target
            if self.drag_target == "body":
                # Move entire rectangle
                for i in range(4):
                    corners[i] = (
                        int(corners[i][0] + delta_x),
                        int(corners[i][1] + delta_y),
                    )
            elif self.drag_target.startswith("corner_"):
                corner_idx = int(self.drag_target.split("_")[1])
                corners[corner_idx] = (
                    int(corners[corner_idx][0] + delta_x),
                    int(corners[corner_idx][1] + delta_y),
                )
            elif self.drag_target == "edge_top":
                # Move top edge (affects top_left and top_right)
                corners[0] = (
                    int(corners[0][0] + delta_x),
                    int(corners[0][1] + delta_y),
                )
                corners[1] = (
                    int(corners[1][0] + delta_x),
                    int(corners[1][1] + delta_y),
                )
            elif self.drag_target == "edge_right":
                # Move right edge (affects top_right and bottom_right)
                corners[1] = (
                    int(corners[1][0] + delta_x),
                    int(corners[1][1] + delta_y),
                )
                corners[2] = (
                    int(corners[2][0] + delta_x),
                    int(corners[2][1] + delta_y),
                )
            elif self.drag_target == "edge_bottom":
                # Move bottom edge (affects bottom_right and bottom_left)
                corners[2] = (
                    int(corners[2][0] + delta_x),
                    int(corners[2][1] + delta_y),
                )
                corners[3] = (
                    int(corners[3][0] + delta_x),
                    int(corners[3][1] + delta_y),
                )
            elif self.drag_target == "edge_left":
                # Move left edge (affects top_left and bottom_left)
                corners[0] = (
                    int(corners[0][0] + delta_x),
                    int(corners[0][1] + delta_y),
                )
                corners[3] = (
                    int(corners[3][0] + delta_x),
                    int(corners[3][1] + delta_y),
                )

            # Clamp to image bounds
            for i, (x, y) in enumerate(corners):
                corners[i] = (
                    max(0, min(self.original_width, x)),
                    max(0, min(self.original_height, y)),
                )

            # Update scan area
            self.scan_area = ManualScanArea.from_list(corners)
            self.scan_area_changed.emit(self.page_num, self.scan_area)
            self.update()
        else:
            # Hover feedback
            if self.line_break_mode:
                self.setCursor(Qt.CursorShape.CrossCursor)
            elif self.mask_mode:
                self.setCursor(Qt.CursorShape.CrossCursor)
            else:
                # Check if hovering over a mask (for deletion)
                mask_index = self._hit_test_masks(pos)
                if mask_index is not None:
                    self.setCursor(Qt.CursorShape.PointingHandCursor)
                else:
                    target = self._hit_test(pos)
                    if target:
                        if target == "body":
                            self.setCursor(Qt.CursorShape.SizeAllCursor)
                        else:
                            self.setCursor(Qt.CursorShape.PointingHandCursor)
                    else:
                        self.setCursor(Qt.CursorShape.ArrowCursor)

    def mouseReleaseEvent(self, event) -> None:
        """Handle mouse release to end drag or finish mask drawing."""
        if event.button() == Qt.MouseButton.LeftButton:
            if self.drawing_mask and self.current_mask_start:
                # Finish drawing mask rectangle
                end_pos = event.position().toPoint()
                
                # Convert to image coordinates
                x1, y1 = self._display_to_image(
                    self.current_mask_start.x(), self.current_mask_start.y()
                )
                x2, y2 = self._display_to_image(end_pos.x(), end_pos.y())
                
                # Calculate rectangle (x, y, width, height)
                x = min(x1, x2)
                y = min(y1, y2)
                width = abs(x2 - x1)
                height = abs(y2 - y1)
                
                # Only add if rectangle has size
                if width > 5 and height > 5:
                    if self.scan_area.mask_rects is None:
                        self.scan_area.mask_rects = []
                    self.scan_area.mask_rects.append((x, y, width, height))
                    self.scan_area_changed.emit(self.page_num, self.scan_area)
                
                self.drawing_mask = False
                self.current_mask_start = None
                self.current_mask_end = None
                self.update()
                self.setCursor(Qt.CursorShape.CrossCursor)
            else:
                # Normal drag end
                self.dragging = False
                self.drag_target = None
                self.drag_start_pos = None
                self.drag_start_corners = None
                self.setCursor(Qt.CursorShape.ArrowCursor)

    def wheelEvent(self, event) -> None:
        """Handle mouse wheel for zooming.

        Args:
            event: QWheelEvent
        """
        # Get wheel delta (positive = zoom in, negative = zoom out)
        delta = event.angleDelta().y()

        # Calculate zoom change (10% per wheel step)
        zoom_factor = 1.1 if delta > 0 else 0.9

        # Update zoom
        self._update_zoom(self.zoom_level * zoom_factor)

    def paintEvent(self, _event) -> None:
        """Paint the page image and scan area rectangle."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw page image
        painter.drawPixmap(0, 0, self.display_pixmap)

        # Draw scan area rectangle
        corners = self._get_corner_positions()
        pen = QPen(QColor(0, 255, 0), 2)  # Green, 2px width
        painter.setPen(pen)

        # Draw rectangle edges
        for i in range(4):
            painter.drawLine(corners[i], corners[(i + 1) % 4])

        # Draw corner handles
        brush = painter.brush()
        painter.setBrush(QColor(0, 255, 0, 200))  # Semi-transparent green
        for corner in corners:
            painter.drawEllipse(
                corner.x() - HANDLE_SIZE // 2,
                corner.y() - HANDLE_SIZE // 2,
                HANDLE_SIZE,
                HANDLE_SIZE,
            )

        # Draw edge handles
        edges = self._get_edge_centers()
        for edge in edges:
            painter.drawEllipse(
                edge.x() - EDGE_HANDLE_SIZE // 2,
                edge.y() - EDGE_HANDLE_SIZE // 2,
                EDGE_HANDLE_SIZE,
                EDGE_HANDLE_SIZE,
            )

        painter.setBrush(brush)

        # Draw mask rectangles (whiteout areas)
        if self.scan_area.mask_rects:
            painter.setPen(QPen(QColor(255, 0, 0), 2))  # Red border
            painter.setBrush(QColor(255, 255, 255, 180))  # Semi-transparent white
            for rect in self.scan_area.mask_rects:
                x, y, width, height = rect
                display_x, display_y = self._image_to_display(x, y)
                display_width = int(width * self.scale_x)
                display_height = int(height * self.scale_y)
                painter.drawRect(display_x, display_y, display_width, display_height)

        # Draw current mask being drawn
        if self.drawing_mask and self.current_mask_start and self.current_mask_end:
            from PyQt6.QtCore import QRect

            painter.setPen(QPen(QColor(255, 0, 0), 2, Qt.PenStyle.DashLine))
            painter.setBrush(QColor(255, 255, 255, 100))
            rect = QRect(self.current_mask_start, self.current_mask_end).normalized()
            painter.drawRect(rect)

        # Draw line breaks
        if self.scan_area.line_breaks:
            painter.setPen(QPen(QColor(0, 0, 255), 2))  # Blue line, 2px width
            for y_img in self.scan_area.line_breaks:
                _, display_y = self._image_to_display(0, y_img)
                # Draw horizontal line across the width
                painter.drawLine(0, display_y, self.display_width, display_y)

        # Draw paragraph breaks (thicker, different color)
        if self.scan_area.paragraph_breaks:
            painter.setPen(QPen(QColor(0, 200, 0), 5))  # Green line, 5px width
            for y_img in self.scan_area.paragraph_breaks:
                _, display_y = self._image_to_display(0, y_img)
                # Draw horizontal line across the width
                painter.drawLine(0, display_y, self.display_width, display_y)

    def get_scan_area(self) -> ManualScanArea:
        """Get the current scan area.

        Returns:
            Current ManualScanArea
        """
        return self.scan_area

    def set_scan_area(self, area: ManualScanArea) -> None:
        """Set the scan area.

        Args:
            area: ManualScanArea to set
        """
        self.scan_area = area
        self.update()
        self.scan_area_changed.emit(self.page_num, self.scan_area)

    def set_mask_mode(self, enabled: bool) -> None:
        """Enable or disable mask drawing mode.

        Args:
            enabled: True to enable mask drawing mode
        """
        self.mask_mode = enabled
        self.line_break_mode = False  # Disable line break mode
        if enabled:
            self.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        self.update()

    def set_line_break_mode(self, enabled: bool) -> None:
        """Enable or disable line break insertion mode.

        Args:
            enabled: True to enable line break mode
        """
        self.line_break_mode = enabled
        self.mask_mode = False  # Disable mask mode
        if enabled:
            self.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        self.update()

    def clear_masks(self) -> None:
        """Clear all mask rectangles."""
        self.scan_area.mask_rects = None
        self.scan_area_changed.emit(self.page_num, self.scan_area)
        self.update()

    def clear_line_breaks(self) -> None:
        """Clear all line breaks."""
        self.scan_area.line_breaks = None
        self.scan_area_changed.emit(self.page_num, self.scan_area)
        self.update()

    def clear_paragraph_breaks(self) -> None:
        """Clear all paragraph breaks."""
        self.scan_area.paragraph_breaks = None
        self.scan_area_changed.emit(self.page_num, self.scan_area)
        self.update()
