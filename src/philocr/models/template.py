"""Document template model for statistical mask."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass
class DocumentTemplate:
    """Statistical mask for body region detection.

    NOT a semantic model of document structure.
    All measurements in pixels at 300 DPI.

    Attributes:
        page_width: Page width in pixels
        page_height: Page height in pixels
        body_left: Left boundary of body region
        body_right: Right boundary of body region
        body_top: Top boundary of body region
        body_bottom: Bottom boundary of body region
        header_bottom: Y-coordinate where header zone ends
        footer_top: Y-coordinate where footer zone starts
        left_margin_right: X-coordinate where left margin ends (line numbers)
        right_margin_left: X-coordinate where right margin starts
        footnote_separator_y: Y-coordinate of footnote separator (None if no footnotes)
        pages_analysed: Number of pages used for template extraction
        confidence: Template confidence score (0.0 to 1.0)
        has_line_numbers_left: Whether line numbers detected on left margin
        has_line_numbers_right: Whether line numbers detected on right margin
        has_footnotes: Whether footnotes detected
    """

    # Page dimensions
    page_width: int
    page_height: int

    # Body region (the text we want)
    body_left: int
    body_right: int
    body_top: int
    body_bottom: int

    # Excluded zones
    header_bottom: int  # Everything above this is header
    footer_top: int  # Everything below this is footer
    left_margin_right: int  # Left margin ends here (line numbers)
    right_margin_left: int  # Right margin starts here
    footnote_separator_y: int | None  # Footnotes below this line (None if no footnotes)

    # Detection metadata
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
