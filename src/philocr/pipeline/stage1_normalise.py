"""Stage 1: Image normalization - PDF to normalized PNG images."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import TYPE_CHECKING

from philocr.models.config import PipelineConfig
from philocr.models.page import PageImage
from philocr.pipeline.utils.deskew import detect_skew, rotate_image
from philocr.pipeline.utils.image_io import save_image
from philocr.pipeline.utils.pdf_render import convert_to_grayscale, render_pdf_page

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)


def normalise_page(
    pdf_path: str,
    page_num: int,
    output_dir: str,
    config: PipelineConfig,
) -> PageImage:
    """Convert PDF page to normalised raster image.

    Args:
        pdf_path: Path to source PDF
        page_num: Page number (0-indexed)
        output_dir: Directory for output images
        config: Pipeline configuration

    Returns:
        PageImage with metadata about the normalised image
    """
    # Render PDF page
    image = render_pdf_page(pdf_path, page_num, dpi=config.target_dpi)

    # Convert to grayscale
    image = convert_to_grayscale(image)

    # Deskew if needed
    skew_angle = detect_skew(image)
    if abs(skew_angle) > config.deskew_threshold:
        image = rotate_image(image, -skew_angle)
        skew_corrected = skew_angle
    else:
        skew_corrected = 0.0

    # Save
    output_path = Path(output_dir) / f"page_{page_num:04d}.png"
    save_image(image, str(output_path))

    return PageImage(
        page_num=page_num,
        path=str(output_path),
        dpi=config.target_dpi,
        width=image.shape[1],
        height=image.shape[0],
        skew_corrected=skew_corrected,
    )


def normalise_all_pages(
    pdf_path: str,
    page_range: range,
    output_dir: str,
    config: PipelineConfig,
) -> list[PageImage]:
    """Normalise multiple pages in parallel.

    Args:
        pdf_path: Path to source PDF
        page_range: Range of page numbers to process (0-indexed)
        output_dir: Directory for output images
        config: Pipeline configuration

    Returns:
        List of PageImage objects
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    images: list[PageImage] = []
    max_workers = config.stage1_parallel_workers

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                normalise_page, pdf_path, page_num, output_dir, config
            ): page_num
            for page_num in page_range
        }

        for future in as_completed(futures):
            page_num = futures[future]
            try:
                page_image = future.result()
                images.append(page_image)
                logger.debug(
                    "page_normalised",
                    page_num=page_num,
                    path=page_image.path,
                    width=page_image.width,
                    height=page_image.height,
                )
            except Exception as e:
                logger.error(
                    "page_normalisation_failed",
                    page_num=page_num,
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True,
                )
                raise

    # Sort by page number
    images.sort(key=lambda x: x.page_num)

    # Save manifest
    manifest_path = Path(output_dir) / "manifest.json"
    manifest_data = {
        "total_pages": len(images),
        "pages": [
            {
                "page_num": img.page_num,
                "path": img.path,
                "dpi": img.dpi,
                "width": img.width,
                "height": img.height,
                "skew_corrected": img.skew_corrected,
            }
            for img in images
        ],
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    return images
