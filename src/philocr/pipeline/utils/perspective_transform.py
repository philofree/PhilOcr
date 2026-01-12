"""Perspective transformation utilities for straightening non-rectangular scan areas."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

# Number of corners required for a perspective transform
NUM_CORNERS = 4

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)


def is_rectangular(corners: list[tuple[int, int]], tolerance: float = 0.01) -> bool:
    """Check if corners form a rectangle (within tolerance).

    Args:
        corners: List of 4 (x, y) corner points
        tolerance: Tolerance for angle deviation (as fraction of 90 degrees)

    Returns:
        True if corners form a rectangle
    """
    if len(corners) != NUM_CORNERS:
        return False

    # Calculate angles at each corner
    angles = []
    for i in range(4):
        p1 = np.array(corners[i])
        p2 = np.array(corners[(i + 1) % 4])
        p3 = np.array(corners[(i + 2) % 4])

        v1 = p2 - p1
        v2 = p3 - p2

        # Calculate angle between vectors
        cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-10)
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        angle = np.arccos(cos_angle)
        angles.append(angle)

    # Check if all angles are approximately 90 degrees
    target_angle = np.pi / 2  # 90 degrees in radians
    tolerance_rad = target_angle * tolerance

    return all(abs(angle - target_angle) < tolerance_rad for angle in angles)


def calculate_destination_size(
    corners: list[tuple[int, int]],
) -> tuple[int, int]:
    """Calculate destination size for perspective transform.

    Uses the average width and height of opposite sides.

    Args:
        corners: List of 4 (x, y) corner points

    Returns:
        (width, height) for destination rectangle
    """
    if len(corners) != NUM_CORNERS:
        raise ValueError(f"Must provide exactly {NUM_CORNERS} corner points")

    # Calculate width (average of top and bottom edges)
    top_width = np.linalg.norm(np.array(corners[1]) - np.array(corners[0]))
    bottom_width = np.linalg.norm(np.array(corners[2]) - np.array(corners[3]))
    width = int((top_width + bottom_width) / 2)

    # Calculate height (average of left and right edges)
    left_height = np.linalg.norm(np.array(corners[3]) - np.array(corners[0]))
    right_height = np.linalg.norm(np.array(corners[2]) - np.array(corners[1]))
    height = int((left_height + right_height) / 2)

    return (width, height)


def apply_perspective_transform(
    image: np.ndarray,
    corners: list[tuple[int, int]],
    mask_rects: list[tuple[int, int, int, int]] | None = None,
) -> np.ndarray:
    """Crop image to the region defined by 4 corner points.

    Uses a mask to extract only the pixels within the quadrilateral defined
    by the corners, then crops to the bounding box.

    Args:
        image: Input image (grayscale or color)
        corners: List of 4 (x, y) corner points in order:
                [top_left, top_right, bottom_right, bottom_left]
        mask_rects: Optional list of rectangles to mask out (fill with white)
                   Each rectangle is (x, y, width, height)

    Returns:
        Cropped image with only pixels inside the quadrilateral
    """
    if len(corners) != NUM_CORNERS:
        raise ValueError(f"Must provide exactly {NUM_CORNERS} corner points")

    # Make a copy to avoid modifying the original
    image = image.copy()

    # Apply mask rectangles BEFORE cropping (they're in original image coordinates)
    if mask_rects:
        for rect in mask_rects:
            x, y, width, height = rect
            # Clamp to image bounds
            x1 = max(0, x)
            y1 = max(0, y)
            x2 = min(image.shape[1], x + width)
            y2 = min(image.shape[0], y + height)
            
            # Fill with white
            if len(image.shape) == 2:
                # Grayscale
                image[y1:y2, x1:x2] = 255
            else:
                # Color
                image[y1:y2, x1:x2] = 255

        logger.info("masks_applied", num_masks=len(mask_rects))

    original_height, original_width = image.shape[:2]

    # Create a mask for the quadrilateral
    import cv2

    mask = np.zeros(image.shape[:2], dtype=np.uint8)
    pts = np.array(corners, dtype=np.int32)
    cv2.fillPoly(mask, [pts], 255)

    # Apply mask - set pixels outside quadrilateral to white
    if len(image.shape) == 2:
        # Grayscale
        image[mask == 0] = 255
    else:
        # Color
        image[mask == 0] = 255

    # Get bounding box for cropping
    x_coords = [c[0] for c in corners]
    y_coords = [c[1] for c in corners]
    x1, x2 = min(x_coords), max(x_coords)
    y1, y2 = min(y_coords), max(y_coords)

    # Clamp to image bounds
    x1 = max(0, min(x1, image.shape[1]))
    x2 = max(0, min(x2, image.shape[1]))
    y1 = max(0, min(y1, image.shape[0]))
    y2 = max(0, min(y2, image.shape[0]))

    logger.info(
        "crop_image",
        original_size=(original_width, original_height),
        corners=corners,
        crop_bounds=(x1, y1, x2, y2),
    )

    # Crop to bounding box (but only pixels inside quadrilateral are preserved)
    cropped = image[y1:y2, x1:x2]

    logger.info(
        "crop_complete",
        original_size=(original_width, original_height),
        cropped_size=(cropped.shape[1], cropped.shape[0]),
    )

    return cropped
