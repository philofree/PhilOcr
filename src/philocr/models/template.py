"""Document template model for statistical mask."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass
class DocumentTemplate:
    """Statistical mask for body region detection.

    Represents the principle that zone detection can be applied to pages
    in this document. Stores aggregated zone measurements from sample pages.

    Attributes:
        page_width: Page width in pixels (median from sample pages)
        page_height: Page height in pixels (median from sample pages)
        body_left: Left boundary of body region (median from sample pages)
        body_right: Right boundary of body region (median from sample pages)
        body_top: Top boundary of body region (median from sample pages)
        body_bottom: Bottom boundary of body region (median from sample pages)
        header_bottom: Y-coordinate where header ends (median from sample
            pages)
        footer_top: Y-coordinate where footer starts (median from sample
            pages)
        left_margin_right: X-coordinate where left margin ends (median from
            sample pages)
        right_margin_left: X-coordinate where right margin starts (median
            from sample pages)
        footnote_separator_y: Y-coordinate of footnote separator (median,
            None if no footnotes)
        pages_analysed: Number of pages used for validation
        confidence: Confidence that the layout principle applies consistently
            (0.0 to 1.0)
        has_line_numbers_left: True if line numbers detected on left side
        has_line_numbers_right: True if line numbers detected on right side
        has_footnotes: True if footnotes detected
    """

    page_width: int
    page_height: int
    body_left: int
    body_right: int
    body_top: int
    body_bottom: int
    header_bottom: int
    footer_top: int
    left_margin_right: int
    right_margin_left: int
    footnote_separator_y: int | None
    pages_analysed: int
    confidence: float
    has_line_numbers_left: bool
    has_line_numbers_right: bool
    has_footnotes: bool

    def to_json(self, path: str) -> None:
        """Save template to JSON file.

        Args:
            path: Path to save JSON file
        """
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.__dict__, f, indent=2, ensure_ascii=False)

    @classmethod
    def from_json(cls, path: str) -> DocumentTemplate:
        """Load template from JSON file.

        Args:
            path: Path to JSON file

        Returns:
            DocumentTemplate instance
        """
        with open(path, encoding="utf-8") as f:
            data: dict[str, Any] = json.load(f)
        return cls(**data)
