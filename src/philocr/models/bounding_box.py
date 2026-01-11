"""Bounding box data structure for text regions."""

from dataclasses import dataclass


@dataclass
class BoundingBox:
    """Bounding box for text regions.

    Attributes:
        x1: Left coordinate
        y1: Top coordinate
        x2: Right coordinate
        y2: Bottom coordinate
    """

    x1: int
    y1: int
    x2: int
    y2: int

    @property
    def width(self) -> int:
        """Width of the bounding box."""
        return self.x2 - self.x1

    @property
    def height(self) -> int:
        """Height of the bounding box."""
        return self.y2 - self.y1
