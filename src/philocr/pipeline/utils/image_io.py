"""Image I/O utilities for pipeline."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


def load_image(path: str | Path) -> np.ndarray:
    """Load an image as a grayscale numpy array.

    Args:
        path: Path to image file

    Returns:
        Grayscale image as numpy array (0-255)

    Raises:
        FileNotFoundError: If image cannot be loaded
    """
    image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise FileNotFoundError(f"Could not load image: {path}")
    return image


def save_image(image: np.ndarray, path: str | Path) -> None:
    """Save a numpy array as an image file.

    Args:
        image: Image as numpy array
        path: Output path
    """
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(path), image)


def load_image_bytes(path: str | Path) -> bytes:
    """Load an image file as bytes (for API calls).

    Args:
        path: Path to image file

    Returns:
        Image file contents as bytes
    """
    with open(path, "rb") as f:
        return f.read()
