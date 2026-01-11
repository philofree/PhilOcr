"""Stage 2c: Apply template masking/cropping to pages."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from philocr.models.bounding_box import BoundingBox
from philocr.models.config import PipelineConfig
from philocr.models.page import CroppedPage, MaskedPage, PageImage
from philocr.models.template import DocumentTemplate
from philocr.pipeline.utils.docai_helpers import extract_page_num
from philocr.pipeline.utils.image_io import load_image, save_image

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)


def mask_page(
    image_path: str,
    template: DocumentTemplate,
    output_path: str,
    config: PipelineConfig,
) -> MaskedPage:
    """Apply template to mask non-body regions (CANONICAL approach).

    Masking whites-out non-body regions while preserving image dimensions
    and coordinate system. This allows direct coordinate mapping between
    OCR output and original page positions.

    Args:
        image_path: Path to normalised image
        template: Document template with zone boundaries
        output_path: Where to save masked image
        config: Configuration (determines mask vs crop)

    Returns:
        MaskedPage with metadata
    """
    image = load_image(image_path)
    masked = image.copy()

    # Mask header (white out)
    masked[0 : template.header_bottom, :] = 255

    # Mask footer
    masked[template.footer_top :, :] = 255

    # Mask left margin (line numbers)
    masked[
        template.header_bottom : template.footer_top,
        0 : template.left_margin_right,
    ] = 255

    # Mask right margin
    masked[
        template.header_bottom : template.footer_top,
        template.right_margin_left :,
    ] = 255

    # Mask footnotes (if detected)
    if template.footnote_separator_y:
        masked[
            template.footnote_separator_y : template.footer_top,
            template.left_margin_right : template.right_margin_left,
        ] = 255

    save_image(masked, output_path)

    return MaskedPage(
        page_num=extract_page_num(image_path),
        original_path=image_path,
        masked_path=output_path,
        body_bounds=BoundingBox(
            x1=template.body_left,
            y1=template.body_top,
            x2=template.body_right,
            y2=template.body_bottom,
        ),
    )


def crop_to_body(
    image_path: str,
    template: DocumentTemplate,
    config: PipelineConfig,
    output_path: str,
) -> CroppedPage:
    """Alternative: Crop to body region only.

    Pros: Smaller image, faster OCR
    Cons: Lose coordinate consistency with original (requires transformation)

    Args:
        image_path: Path to original normalised image
        template: Document template with body bounds
        config: Configuration (may include crop_padding)
        output_path: Where to save cropped image

    Returns:
        CroppedPage with offset information for coordinate transformation
    """
    image = load_image(image_path)

    # Apply padding if configured
    padding = config.crop_padding

    # Crop to body bounds with padding
    top = max(0, template.body_top - padding)
    bottom = min(image.shape[0], template.body_bottom + padding)
    left = max(0, template.body_left - padding)
    right = min(image.shape[1], template.body_right + padding)

    body_image = image[top:bottom, left:right]

    save_image(body_image, output_path)

    return CroppedPage(
        page_num=extract_page_num(image_path),
        original_path=image_path,
        cropped_path=output_path,
        crop_offset=(left, top),
        crop_size=(body_image.shape[1], body_image.shape[0]),
        original_size=(image.shape[1], image.shape[0]),
    )


def transform_ocr_coordinates(
    ocr_bbox: BoundingBox,
    crop_offset: tuple[int, int],
) -> BoundingBox:
    """Transform OCR coordinates from cropped space to original page space.

    This is required when using cropping instead of masking.

    Args:
        ocr_bbox: Bounding box from OCR (in cropped image coordinates)
        crop_offset: (x, y) offset of crop region in original image

    Returns:
        Bounding box in original page coordinates
    """
    offset_x, offset_y = crop_offset

    return BoundingBox(
        x1=ocr_bbox.x1 + offset_x,
        y1=ocr_bbox.y1 + offset_y,
        x2=ocr_bbox.x2 + offset_x,
        y2=ocr_bbox.y2 + offset_y,
    )


def choose_masking_strategy(config: PipelineConfig) -> str:
    """Determine whether to use masking or cropping.

    Args:
        config: Pipeline configuration

    Returns:
        'mask' or 'crop'
    """
    if config.use_cropping:
        return "crop"
    return "mask"


def apply_template_to_pages(
    normalised_images: list[PageImage],
    template: DocumentTemplate,
    output_dir: str,
    config: PipelineConfig,
) -> list[MaskedPage] | list[CroppedPage]:
    """Apply template to all normalised pages.

    Args:
        normalised_images: List of normalised page images
        template: Document template
        output_dir: Directory for masked/cropped images
        config: Pipeline configuration

    Returns:
        List of MaskedPage or CroppedPage objects
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    strategy = choose_masking_strategy(config)

    results: list[MaskedPage] | list[CroppedPage] = []

    for page_image in normalised_images:
        if strategy == "mask":
            output_path = (
                Path(output_dir) / f"page_{page_image.page_num:04d}_masked.png"
            )
            masked = mask_page(page_image.path, template, str(output_path), config)
            results.append(masked)
        else:
            output_path = (
                Path(output_dir) / f"page_{page_image.page_num:04d}_cropped.png"
            )
            cropped = crop_to_body(page_image.path, template, config, str(output_path))
            results.append(cropped)

        logger.debug(
            "template_applied",
            page_num=page_image.page_num,
            strategy=strategy,
            output_path=str(output_path),
        )

    return results
