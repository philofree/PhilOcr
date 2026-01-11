"""Page-related data structures for pipeline stages."""

from __future__ import annotations

from dataclasses import dataclass

from philocr.models.bounding_box import BoundingBox


@dataclass
class PageImage:
    """Output from Stage 1: normalised page image.

    Attributes:
        page_num: Page number (0-indexed)
        path: Path to normalised image file
        dpi: Resolution of the image
        width: Image width in pixels
        height: Image height in pixels
        skew_corrected: Skew angle that was corrected (in degrees)
    """

    page_num: int
    path: str
    dpi: int
    width: int
    height: int
    skew_corrected: float


@dataclass
class PageZones:
    """Zone boundaries detected on a single page.

    Attributes:
        page_width: Page width in pixels
        page_height: Page height in pixels
        header_bottom: Y-coordinate where header ends
        footer_top: Y-coordinate where footer starts
        left_margin_right: X-coordinate where left margin ends
        right_margin_left: X-coordinate where right margin starts
        footnote_separator_y: Y-coordinate of footnote separator (None if none)
        body_left: Left boundary of body region
        body_right: Right boundary of body region
        body_top: Top boundary of body region
        body_bottom: Bottom boundary of body region
    """

    page_width: int
    page_height: int
    header_bottom: int
    footer_top: int
    left_margin_right: int
    right_margin_left: int
    footnote_separator_y: int | None
    body_left: int
    body_right: int
    body_top: int
    body_bottom: int


@dataclass
class MaskedPage:
    """Output from Stage 2: masked page ready for OCR.

    Attributes:
        page_num: Page number (0-indexed)
        original_path: Path to original normalised image
        masked_path: Path to masked image
        body_bounds: Bounding box of body region
    """

    page_num: int
    original_path: str
    masked_path: str
    body_bounds: BoundingBox


@dataclass
class CroppedPage:
    """Alternative output from Stage 2: cropped page.

    Attributes:
        page_num: Page number (0-indexed)
        original_path: Path to original normalised image
        cropped_path: Path to cropped image
        crop_offset: (x, y) offset of crop region in original image
        crop_size: (width, height) of cropped image
        original_size: (width, height) of original image
    """

    page_num: int
    original_path: str
    cropped_path: str
    crop_offset: tuple[int, int]  # (x, y) offset for coordinate transformation
    crop_size: tuple[int, int]  # (width, height) of cropped image
    original_size: tuple[int, int]  # (width, height) of original image
