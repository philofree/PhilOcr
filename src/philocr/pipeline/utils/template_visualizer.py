"""Template visualization utilities for validation and preview."""

from __future__ import annotations

from typing import TYPE_CHECKING

import cv2

if TYPE_CHECKING:
    from philocr.models.template import DocumentTemplate

from philocr.pipeline.utils.image_io import load_image, save_image


def visualise_template(
    image_path: str,
    template: DocumentTemplate,
    output_path: str,
) -> None:
    """Draw template boundaries on image for visual validation.

    Args:
        image_path: Path to original page image
        template: DocumentTemplate with zone boundaries
        output_path: Path to save visualized image
    """
    image = load_image(image_path)

    # Convert to color for drawing
    if len(image.shape) == 2:
        image_color = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    else:
        image_color = image.copy()

    # Draw body region (green rectangle)
    cv2.rectangle(
        image_color,
        (template.body_left, template.body_top),
        (template.body_right, template.body_bottom),
        (0, 255, 0),
        2,
    )

    # Draw header zone (red overlay)
    overlay = image_color.copy()
    cv2.rectangle(
        overlay,
        (0, 0),
        (template.page_width, template.header_bottom),
        (0, 0, 255),
        -1,
    )
    cv2.addWeighted(overlay, 0.3, image_color, 0.7, 0, image_color)

    # Draw footer zone (red overlay)
    overlay = image_color.copy()
    cv2.rectangle(
        overlay,
        (0, template.footer_top),
        (template.page_width, template.page_height),
        (0, 0, 255),
        -1,
    )
    cv2.addWeighted(overlay, 0.3, image_color, 0.7, 0, image_color)

    # Draw left margin (red overlay)
    overlay = image_color.copy()
    cv2.rectangle(
        overlay,
        (0, template.header_bottom),
        (template.left_margin_right, template.footer_top),
        (0, 0, 255),
        -1,
    )
    cv2.addWeighted(overlay, 0.3, image_color, 0.7, 0, image_color)

    # Draw right margin (red overlay)
    overlay = image_color.copy()
    cv2.rectangle(
        overlay,
        (template.right_margin_left, template.header_bottom),
        (template.page_width, template.footer_top),
        (0, 0, 255),
        -1,
    )
    cv2.addWeighted(overlay, 0.3, image_color, 0.7, 0, image_color)

    # Draw footnote zone (orange overlay) if present
    if template.footnote_separator_y:
        overlay = image_color.copy()
        cv2.rectangle(
            overlay,
            (template.body_left, template.footnote_separator_y),
            (template.body_right, template.footer_top),
            (0, 165, 255),
            -1,
        )
        cv2.addWeighted(overlay, 0.3, image_color, 0.7, 0, image_color)

    save_image(image_color, output_path)
