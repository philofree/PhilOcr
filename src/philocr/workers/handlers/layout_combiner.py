"""Layout combination utilities for merging chunk layouts.

This module handles combining layout data from multiple PDF chunks
without UI dependencies.
"""

from __future__ import annotations

from typing import Any

from philocr.utils.logging_config import get_logger

logger = get_logger(__name__)


class LayoutCombiner:
    """Combines layout data from multiple PDF chunks."""

    @staticmethod
    def combine_chunk_layouts(
        chunk_layout: dict[str, Any] | None,
        combined_layout: dict[str, Any],
        base_page_num: int,
    ) -> None:
        """Combine layout from a chunk into the combined layout.

        Args:
            chunk_layout: Layout data from the chunk
            combined_layout: Combined layout being built (modified in place)
            base_page_num: Base page number for this chunk
        """
        if not chunk_layout or "pages" not in chunk_layout:
            return

        for page_idx, page in enumerate(chunk_layout["pages"]):
            page["page_number"] = base_page_num + page_idx + 1
            if "pages" not in combined_layout:
                combined_layout["pages"] = []
            combined_layout["pages"].append(page)

        logger.debug(
            "chunk_pages_added_to_layout",
            pages_added=len(chunk_layout["pages"]),
        )
