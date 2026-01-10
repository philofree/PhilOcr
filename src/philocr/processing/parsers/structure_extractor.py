"""Structure detection and extraction utilities for document parsing.

This module provides functionality for detecting document structure elements
such as footnotes, headings, indentation levels, references, and page numbers.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from philocr.utils.unicode_normalizer import normalize_to_nfc

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)


class StructureExtractor:
    """Extracts and identifies structural elements in documents."""

    @staticmethod
    def detect_references(text: str) -> bool:
        """Detect if a line is a reference/citation.

        Args:
            text: Text to analyze

        Returns:
            True if text matches reference pattern
        """
        # Pattern for numerical references like:
        # "10 Strabo XIII p. 614." or "12 ibid. 6, 9 (p. 732b)."
        ref_pattern = r"^\d+\s+(?:[A-Z][a-z]+|[a-z]+\.)\s"
        return bool(re.match(ref_pattern, text.strip()))

    @staticmethod
    def detect_actual_page_number(elements: list[dict[str, Any]]) -> int | None:
        """Detect the actual page number from page content.

        Args:
            elements: List of text elements on the page

        Returns:
            Page number if found, None otherwise
        """
        if not elements:
            return None

        # Check the first few elements for page number patterns
        header_elements = sorted(elements[:10], key=lambda e: e.get("y_position", 0))
        for elem in header_elements:
            text = normalize_to_nfc(elem.get("text", "").strip())

            # Look for patterns like "VITA. 9" or "8 ZENO CITIEUS"
            numbers = re.findall(r"\b\d+\b", text)
            if numbers:
                for num in numbers:
                    if len(num) <= 2 and int(num) > 0:
                        return int(num)

        # Try more general number extraction
        for elem in elements[:5]:
            text = normalize_to_nfc(elem.get("text", "").strip())
            if text.isdigit() and len(text) <= 2 and int(text) > 0:
                return int(text)

        return None

    @staticmethod
    def is_footnote_marker(text: str) -> bool:
        """Detect if text is a footnote marker.

        Args:
            text: Text to analyze

        Returns:
            True if text matches footnote marker pattern
        """
        # Examples: "1 κεχειροτόνηνται Ρ." or "* Συπαλλητεύς ΒΡ."
        footnote_pattern = r"^(\d+|\*)\s+[^\d]"
        return bool(re.match(footnote_pattern, text.strip()))

    @staticmethod
    def identify_footnote_section(elements: list[dict[str, Any]]) -> int:
        """Identify where the footnote section begins on a page.

        Args:
            elements: List of text elements on the page

        Returns:
            Index of first footnote element, or -1 if not found
        """
        if not elements:
            return -1

        # Calculate page height
        page_height = 0
        for element in elements:
            bounding_poly = element.get("bounding_poly", {})
            vertices = bounding_poly.get("vertices", [])
            for vertex in vertices:
                page_height = max(page_height, vertex.get("y", 0))

        # Footnotes typically appear in the bottom 25% of the page
        bottom_threshold = page_height * 0.75

        # Find possible footnote markers in the bottom section
        for i, element in enumerate(elements):
            y_position = element.get("y_position", 0)
            if y_position > bottom_threshold:
                # Check for significant gap (separator)
                if i > 0:
                    prev_vertices = (
                        elements[i - 1].get("bounding_poly", {}).get("vertices", [])
                    )
                    curr_vertices = element.get("bounding_poly", {}).get("vertices", [])

                    if prev_vertices and curr_vertices:
                        prev_y = prev_vertices[-1].get("y", 0)
                        curr_y = curr_vertices[0].get("y", 0)

                        # Significant gap might indicate separator
                        if (curr_y - prev_y) > 20:
                            text = element.get("text", "")
                            if StructureExtractor.is_footnote_marker(text):
                                return i

        return -1

    @staticmethod
    def _cluster_values(
        values: list[float], threshold: float
    ) -> dict[float, list[float]]:
        """Cluster values within threshold distance of each other.

        Args:
            values: List of numeric values to cluster
            threshold: Maximum distance for values in same cluster

        Returns:
            Dictionary mapping cluster centers to lists of values
        """
        if not values:
            return {}

        sorted_values = sorted(values)
        clusters: dict[float, list[float]] = {}
        current_cluster: list[float] = [sorted_values[0]]
        cluster_center: float = sorted_values[0]

        for value in sorted_values[1:]:
            if abs(value - cluster_center) <= threshold:
                current_cluster.append(value)
                cluster_center = sum(current_cluster) / len(current_cluster)
            else:
                clusters[cluster_center] = current_cluster
                current_cluster = [value]
                cluster_center = value

        if current_cluster:
            clusters[cluster_center] = current_cluster

        return clusters

    @staticmethod
    def identify_indent_levels(elements: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Analyze horizontal positions and assign standardized indent levels.

        Args:
            elements: List of text elements with x_position

        Returns:
            Elements with indent_level added
        """
        if not elements:
            return elements

        # Extract x positions
        x_positions = [e.get("x_position", 0) for e in elements if "x_position" in e]
        if not x_positions:
            return elements

        # Identify indentation clusters
        x_positions = sorted(set(x_positions))
        thresholds: list[float] = []
        current_cluster: list[float] = [x_positions[0]]

        for pos in x_positions[1:]:
            cluster_avg = sum(current_cluster) / len(current_cluster)
            if abs(pos - cluster_avg) < 50:  # 50px threshold
                current_cluster.append(pos)
            else:
                thresholds.append(sum(current_cluster) / len(current_cluster))
                current_cluster = [pos]

        if current_cluster:
            thresholds.append(sum(current_cluster) / len(current_cluster))

        # Assign indent levels
        for element in elements:
            x_pos = element.get("x_position", 0)
            if thresholds:
                distances = [abs(x_pos - t) for t in thresholds]
                closest_idx = distances.index(min(distances))
                element["indent_level"] = closest_idx
            else:
                element["indent_level"] = 0

        return elements

    @staticmethod
    def detect_headings(
        elements: list[dict[str, Any]], page_idx: int
    ) -> list[dict[str, Any]]:
        """Detect headers and other structural elements in the document.

        Args:
            elements: List of text elements
            page_idx: Page index (0-based)

        Returns:
            Elements with type annotations added
        """
        # Identify footnote section first
        footnote_start_idx = StructureExtractor.identify_footnote_section(elements)

        # Standardize indentation levels
        elements = StructureExtractor.identify_indent_levels(elements)

        # Classify each element
        for i, element in enumerate(elements):
            if element.get("type") != "line":
                continue

            text = element.get("text", "").strip()

            # Check for page numbers (isolated numbers at the top)
            if i == 0 and re.match(r"^\d+\s*$", text):
                element["type"] = "page_number"
                continue

            # Check for all caps text (likely section headers)
            if text.isupper() and len(text) > 3:
                element["type"] = "header"
                continue

            # Check if this is a reference
            if StructureExtractor.detect_references(text):
                element["type"] = "reference"
                continue

            # Mark elements in footnote section
            if footnote_start_idx >= 0 and i >= footnote_start_idx:
                element["type"] = "footnote"
                continue

        return elements
