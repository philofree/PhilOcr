"""Stage 2a: Zone detection on sample pages."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import TYPE_CHECKING

from philocr.detection.zones import detect_page_zones
from philocr.models.config import PipelineConfig
from philocr.models.page import PageImage, PageZones
from philocr.pipeline.utils.image_io import load_image

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)


def detect_zones_for_template(
    normalised_images: list[PageImage],
    sample_indices: list[int],
    config: PipelineConfig,
) -> list[PageZones]:
    """Detect zones on multiple pages in parallel for template extraction.

    Args:
        normalised_images: List of normalised page images
        sample_indices: List of indices into normalised_images to sample
        config: Pipeline configuration

    Returns:
        List of PageZones objects for sampled pages
    """
    zones_list: list[PageZones] = []
    max_workers = config.stage2a_parallel_workers

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                detect_page_zones,
                load_image(normalised_images[i].path),
                config,
            ): i
            for i in sample_indices
        }

        for future in as_completed(futures):
            idx = futures[future]
            try:
                zones = future.result()
                zones_list.append(zones)
                logger.debug(
                    "zones_detected",
                    page_index=idx,
                    page_num=normalised_images[idx].page_num,
                    body_left=zones.body_left,
                    body_right=zones.body_right,
                    body_top=zones.body_top,
                    body_bottom=zones.body_bottom,
                )
            except Exception as e:
                logger.error(
                    "zone_detection_failed",
                    page_index=idx,
                    page_num=normalised_images[idx].page_num,
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True,
                )
                raise

    return zones_list
