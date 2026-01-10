"""Page-level parsing utilities for document processing.

This module provides functionality for parsing individual pages,
extracting elements, and calculating dimensions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from philocr.utils.unicode_normalizer import normalize_to_nfc

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)


class PageParser:
    """Parser for individual page elements and dimensions."""

    # Conversion factor: pixels to centimeters (approximate)
    # Common standard is 96 DPI, and 1 inch = 2.54 cm
    PX_TO_CM = 2.54 / 96  # approx. 0.026 cm per pixel

    @staticmethod
    def calculate_dimensions(
        page: dict[str, Any], elements: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Calculate page dimensions based on page data or elements.

        Args:
            page: Page data dictionary
            elements: List of elements on the page

        Returns:
            Dictionary with width/height in both px and cm
        """
        # Check if dimensions are directly available
        if "dimension" in page:
            width_px = int(page["dimension"].get("width", 1000))
            height_px = int(page["dimension"].get("height", 1400))
            width_cm = width_px * PageParser.PX_TO_CM * 0.5
            height_cm = height_px * PageParser.PX_TO_CM * 0.5
            return {
                "width_px": width_px,
                "height_px": height_px,
                "width_cm": width_cm,
                "height_cm": height_cm,
            }

        # Calculate from elements if available
        if elements:
            max_x = max(
                (
                    e.get("bounding_poly", {}).get("vertices", [{}])[-1].get("x", 0)
                    for e in elements
                ),
                default=1000,
            )
            max_y = max(
                (
                    e.get("bounding_poly", {}).get("vertices", [{}])[-1].get("y", 0)
                    for e in elements
                ),
                default=1400,
            )
            width_px = max_x
            height_px = max_y
        else:
            # Default A4 size
            width_px = 1000
            height_px = 1400

        width_cm = width_px * PageParser.PX_TO_CM * 0.5
        height_cm = height_px * PageParser.PX_TO_CM * 0.5

        return {
            "width_px": width_px,
            "height_px": height_px,
            "width_cm": width_cm,
            "height_cm": height_cm,
        }

    @staticmethod
    def get_elements_by_position(page: dict[str, Any]) -> list[dict[str, Any]]:
        """Get all text elements from a page, sorted by reading position.

        Args:
            page: Page data dictionary

        Returns:
            List of elements sorted by position (top to bottom, left to right)
        """
        elements: list[dict[str, Any]] = []

        # Extract lines with positional information
        for line in page.get("lines", []):
            if (
                "layout" in line
                and "bounding_poly" in line["layout"]
                and line.get("text", "").strip()
            ):
                bounding_poly = line["layout"]["bounding_poly"]
                vertices = bounding_poly.get("vertices", [])
                if not vertices:
                    continue

                x_position = vertices[0].get("x", 0)
                y_position = vertices[0].get("y", 0)
                width = (
                    vertices[1].get("x", x_position) - x_position
                    if len(vertices) > 1
                    else 0
                )
                height = (
                    vertices[2].get("y", y_position) - y_position
                    if len(vertices) > 2
                    else 0
                )

                elements.append(
                    {
                        "type": "line",
                        "text": normalize_to_nfc(line["text"]),
                        "bounding_poly": bounding_poly,
                        "confidence": line["layout"].get("confidence", 0),
                        "x_position": x_position,
                        "y_position": y_position,
                        "width": width,
                        "height": height,
                    }
                )

        # Sort by vertical position (top to bottom), then horizontal (left to right)
        elements.sort(
            key=lambda e: (
                e["bounding_poly"].get("vertices", [{}])[0].get("y", 0),
                e["bounding_poly"].get("vertices", [{}])[0].get("x", 0),
            )
        )

        return elements
