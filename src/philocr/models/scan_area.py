"""Manual scan area data structures for user-defined page regions."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Number of corners required for a scan area
NUM_SCAN_AREA_CORNERS = 4


@dataclass
class ManualScanArea:
    """Manual scan area defined by 4 corner points.

    Allows for rectangular or non-rectangular (skewed) scan areas.
    Coordinates are relative to the original page image dimensions.

    Attributes:
        top_left: Top-left corner (x, y)
        top_right: Top-right corner (x, y)
        bottom_right: Bottom-right corner (x, y)
        bottom_left: Bottom-left corner (x, y)
        mask_rects: List of rectangles to mask out (x, y, width, height)
        line_breaks: List of y-coordinates where line breaks should be inserted
        paragraph_breaks: List of y-coordinates where paragraph breaks (double newline) should be inserted
    """

    top_left: tuple[int, int]
    top_right: tuple[int, int]
    bottom_right: tuple[int, int]
    bottom_left: tuple[int, int]
    mask_rects: list[tuple[int, int, int, int]] | None = None
    line_breaks: list[int] | None = None
    paragraph_breaks: list[int] | None = None

    def to_list(self) -> list[tuple[int, int]]:
        """Convert to list of corners in order.

        Returns:
            List of (x, y) tuples: [top_left, top_right, bottom_right, bottom_left]
        """
        return [
            self.top_left,
            self.top_right,
            self.bottom_right,
            self.bottom_left,
        ]

    @classmethod
    def from_list(cls, corners: list[tuple[int, int]]) -> ManualScanArea:
        """Create from list of corners.

        Args:
            corners: List of 4 (x, y) tuples in order:
                    [top_left, top_right, bottom_right, bottom_left]

        Returns:
            ManualScanArea instance
        """
        if len(corners) != NUM_SCAN_AREA_CORNERS:
            raise ValueError(
                f"Must provide exactly {NUM_SCAN_AREA_CORNERS} corner points"
            )
        return cls(
            top_left=corners[0],
            top_right=corners[1],
            bottom_right=corners[2],
            bottom_left=corners[3],
        )

    @classmethod
    def create_default(cls, page_width: int, page_height: int) -> ManualScanArea:
        """Create default centered rectangle (60% of page size).

        Args:
            page_width: Page width in pixels
            page_height: Page height in pixels

        Returns:
            ManualScanArea with centered rectangle
        """
        margin_x = int(page_width * 0.2)
        margin_y = int(page_height * 0.2)

        return cls(
            top_left=(margin_x, margin_y),
            top_right=(page_width - margin_x, margin_y),
            bottom_right=(page_width - margin_x, page_height - margin_y),
            bottom_left=(margin_x, page_height - margin_y),
        )


@dataclass
class ManualScanAreas:
    """Collection of manual scan areas for multiple pages.

    Attributes:
        areas: Dictionary mapping page_num (0-indexed) to ManualScanArea
    """

    areas: dict[int, ManualScanArea]

    def get(self, page_num: int) -> ManualScanArea | None:
        """Get scan area for a specific page.

        Args:
            page_num: Page number (0-indexed)

        Returns:
            ManualScanArea or None if not set
        """
        return self.areas.get(page_num)

    def set(self, page_num: int, area: ManualScanArea) -> None:
        """Set scan area for a specific page.

        Args:
            page_num: Page number (0-indexed)
            area: ManualScanArea for this page
        """
        self.areas[page_num] = area

    def has_page(self, page_num: int) -> bool:
        """Check if scan area exists for a page.

        Args:
            page_num: Page number (0-indexed)

        Returns:
            True if scan area exists for this page
        """
        return page_num in self.areas


def save_scan_areas(scan_areas: ManualScanAreas, file_path: str | Path) -> None:
    """Save manual scan areas to JSON file.

    Args:
        scan_areas: ManualScanAreas to save
        file_path: Path to JSON file
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert to JSON-serializable format
    data: dict[str, Any] = {}
    for page_num, area in scan_areas.areas.items():
        page_data = {
            "top_left": list(area.top_left),
            "top_right": list(area.top_right),
            "bottom_right": list(area.bottom_right),
            "bottom_left": list(area.bottom_left),
        }
        if area.mask_rects:
            page_data["mask_rects"] = [list(rect) for rect in area.mask_rects]
        if area.line_breaks:
            page_data["line_breaks"] = list(area.line_breaks)
        if area.paragraph_breaks:
            page_data["paragraph_breaks"] = list(area.paragraph_breaks)
        data[str(page_num)] = page_data

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_scan_areas(file_path: str | Path) -> ManualScanAreas:
    """Load manual scan areas from JSON file.

    Args:
        file_path: Path to JSON file

    Returns:
        ManualScanAreas loaded from file

    Raises:
        FileNotFoundError: If file does not exist
        ValueError: If file format is invalid
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Scan areas file not found: {file_path}")

    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)

    areas: dict[int, ManualScanArea] = {}
    for page_str, corners_dict in data.items():
        try:
            page_num = int(page_str)
            mask_rects = None
            if "mask_rects" in corners_dict:
                mask_rects = [tuple(rect) for rect in corners_dict["mask_rects"]]
            line_breaks = None
            if "line_breaks" in corners_dict:
                line_breaks = list(corners_dict["line_breaks"])
            paragraph_breaks = None
            if "paragraph_breaks" in corners_dict:
                paragraph_breaks = list(corners_dict["paragraph_breaks"])
            area = ManualScanArea(
                top_left=tuple(corners_dict["top_left"]),
                top_right=tuple(corners_dict["top_right"]),
                bottom_right=tuple(corners_dict["bottom_right"]),
                bottom_left=tuple(corners_dict["bottom_left"]),
                mask_rects=mask_rects,
                line_breaks=line_breaks,
                paragraph_breaks=paragraph_breaks,
            )
            areas[page_num] = area
        except (KeyError, ValueError, TypeError) as e:
            raise ValueError(
                f"Invalid scan area format for page {page_str}: {e}"
            ) from e

    return ManualScanAreas(areas=areas)
