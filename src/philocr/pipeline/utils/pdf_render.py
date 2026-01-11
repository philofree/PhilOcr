"""PDF rendering utilities for pipeline."""

import cv2
import fitz  # PyMuPDF
import numpy as np


def render_pdf_page(
    pdf_path: str,
    page_num: int,
    dpi: int = 300,
) -> np.ndarray:
    """Render a PDF page to a numpy array.

    Args:
        pdf_path: Path to PDF file
        page_num: Page number (0-indexed)
        dpi: Resolution for rendering

    Returns:
        Page image as numpy array
    """
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_num)

    # Calculate zoom factor for desired DPI
    zoom = dpi / 72.0  # PDF default is 72 DPI
    matrix = fitz.Matrix(zoom, zoom)

    # Render to pixmap
    pixmap = page.get_pixmap(matrix=matrix)

    # Convert to numpy array
    image = np.frombuffer(pixmap.samples, dtype=np.uint8)
    image = image.reshape(pixmap.height, pixmap.width, pixmap.n)

    doc.close()
    return image


def convert_to_grayscale(image: np.ndarray) -> np.ndarray:
    """Convert image to grayscale.

    Args:
        image: Input image (may be color or grayscale)

    Returns:
        Grayscale image
    """
    if len(image.shape) == 2:
        return image  # Already grayscale
    elif image.shape[2] == 4:
        return cv2.cvtColor(image, cv2.COLOR_RGBA2GRAY)
    else:
        return cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
