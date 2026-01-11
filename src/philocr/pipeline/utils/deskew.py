"""Deskewing utilities for document images."""

import cv2
import numpy as np


def detect_skew(image: np.ndarray) -> float:
    """Detect skew angle of a document image.

    Args:
        image: Grayscale image

    Returns:
        Skew angle in degrees (positive = clockwise)
    """
    # Threshold to binary
    _, binary = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Find coordinates of all black pixels
    coords = np.column_stack(np.where(binary > 0))

    if len(coords) < 100:
        return 0.0

    # Fit a minimum area rectangle
    rect = cv2.minAreaRect(coords)
    angle = float(rect[-1])

    # Adjust angle
    if angle < -45:
        angle = 90 + angle
    elif angle > 45:
        angle = angle - 90

    return angle


def rotate_image(image: np.ndarray, angle: float) -> np.ndarray:
    """Rotate an image by a given angle.

    Args:
        image: Input image
        angle: Rotation angle in degrees (positive = counterclockwise)

    Returns:
        Rotated image
    """
    height, width = image.shape[:2]
    center = (width // 2, height // 2)

    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(
        image,
        matrix,
        (width, height),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )

    return rotated
