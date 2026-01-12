"""Stage 2: Crop pages to user-defined scan areas."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from philocr.models.config import PipelineConfig
    from philocr.models.scan_area import ManualScanAreas
else:
    from philocr.models.config import PipelineConfig
    from philocr.models.scan_area import ManualScanAreas

from philocr.models.page import CroppedPage, PageImage
from philocr.pipeline.utils.image_io import load_image, save_image
from philocr.pipeline.utils.perspective_transform import apply_perspective_transform

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)


def apply_zones_to_pages(
    normalised_images: list[PageImage],
    output_dir: str,
    config: PipelineConfig,
    manual_scan_areas: ManualScanAreas | None = None,
) -> list[CroppedPage]:
    """Crop all pages to user-defined scan areas.

    Args:
        normalised_images: List of normalised page images
        output_dir: Directory for cropped images
        config: Pipeline configuration
        manual_scan_areas: Manual scan areas for pages (required)

    Returns:
        List of CroppedPage objects

    Raises:
        RuntimeError: If manual_scan_areas is not provided or missing for a page
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    results: list[CroppedPage] = []

    for page_image in normalised_images:
        image = load_image(page_image.path)
        height, width = image.shape[:2]

        # Check if manual scan area exists for this page
        manual_area = (
            manual_scan_areas.get(page_image.page_num) if manual_scan_areas else None
        )

        if manual_area:
            # Scale corners from preview DPI (150) to pipeline DPI (config.target_dpi)
            # The scan area viewer renders at 150 DPI for preview
            preview_dpi = 150
            dpi_scale = config.target_dpi / preview_dpi

            raw_corners = manual_area.to_list()
            corners = [(int(x * dpi_scale), int(y * dpi_scale)) for x, y in raw_corners]

            # Scale mask rectangles if present
            mask_rects = None
            if manual_area.mask_rects:
                mask_rects = [
                    (
                        int(x * dpi_scale),
                        int(y * dpi_scale),
                        int(w * dpi_scale),
                        int(h * dpi_scale),
                    )
                    for x, y, w, h in manual_area.mask_rects
                ]

            logger.info(
                "cropping_to_scan_area",
                page_num=page_image.page_num,
                original_size=(width, height),
                raw_corners=raw_corners,
                scaled_corners=corners,
                dpi_scale=dpi_scale,
                num_masks=len(mask_rects) if mask_rects else 0,
            )

            # Crop to the scan area (with masks applied)
            cropped_image = apply_perspective_transform(image, corners, mask_rects)

            logger.info(
                "crop_complete",
                page_num=page_image.page_num,
                original_size=(width, height),
                cropped_size=(cropped_image.shape[1], cropped_image.shape[0]),
            )

            # Save cropped image
            output_path = (
                Path(output_dir) / f"page_{page_image.page_num:04d}_cropped.png"
            )
            save_image(cropped_image, str(output_path))

            # Create result object
            cropped_height, cropped_width = cropped_image.shape[:2]
            cropped = CroppedPage(
                page_num=page_image.page_num,
                original_path=page_image.path,
                cropped_path=str(output_path),
                crop_offset=(0, 0),  # Cropped image coordinates start at 0,0
                crop_size=(cropped_width, cropped_height),
                original_size=(width, height),
            )
            results.append(cropped)

        else:
            # No manual scan area - fail loudly
            logger.error(
                "no_manual_scan_area",
                page_num=page_image.page_num,
                message="No manual scan area defined for this page",
            )
            from philocr.utils.logging_config import flush_loggers

            flush_loggers()
            raise RuntimeError(
                f"CRITICAL: No manual scan area defined for page "
                f"{page_image.page_num}. All pages must have manual scan "
                "areas defined."
            )

    return results
