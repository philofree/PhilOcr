"""Document AI response parsing utilities."""

import re
from typing import Any

from google.cloud import documentai

from philocr.models.bounding_box import BoundingBox
from philocr.models.ocr_result import TextBlock, TextLine, TextParagraph


def extract_text_from_layout(full_text: str, layout: Any) -> str:
    """Extract text for a layout element using text anchors.

    Args:
        full_text: Complete document text
        layout: Layout object with textAnchor

    Returns:
        Text content for this layout element
    """
    if not hasattr(layout, "text_anchor") or not layout.text_anchor:
        return ""
    if not hasattr(layout.text_anchor, "text_segments"):
        return ""
    if not layout.text_anchor.text_segments:
        return ""

    text_parts: list[str] = []
    for segment in layout.text_anchor.text_segments:
        start = int(segment.start_index) if segment.start_index else 0
        end = int(segment.end_index) if segment.end_index else len(full_text)
        text_parts.append(full_text[start:end])

    return "".join(text_parts)


def layout_to_bbox(bounding_poly: Any) -> BoundingBox:
    """Convert Document AI bounding polygon to BoundingBox.

    Args:
        bounding_poly: Document AI BoundingPoly object

    Returns:
        BoundingBox with integer coordinates
    """
    if not hasattr(bounding_poly, "vertices") or not bounding_poly.vertices:
        return BoundingBox(x1=0, y1=0, x2=0, y2=0)

    vertices = bounding_poly.vertices
    x_coords = [v.x for v in vertices if v.x is not None]
    y_coords = [v.y for v in vertices if v.y is not None]

    if not x_coords or not y_coords:
        return BoundingBox(x1=0, y1=0, x2=0, y2=0)

    return BoundingBox(
        x1=int(min(x_coords)),
        y1=int(min(y_coords)),
        x2=int(max(x_coords)),
        y2=int(max(y_coords)),
    )


def calculate_average_confidence(response: documentai.Document) -> float:
    """Calculate average confidence across all text blocks.

    Args:
        response: Document AI Document response

    Returns:
        Average confidence (0.0-1.0)
    """
    confidences: list[float] = []

    if not hasattr(response, "pages") or not response.pages:
        return 0.0

    for page in response.pages:
        if not hasattr(page, "blocks") or not page.blocks:
            continue
        for block in page.blocks:
            if (
                hasattr(block, "layout")
                and block.layout
                and hasattr(block.layout, "confidence")
                and block.layout.confidence is not None
            ):
                confidences.append(float(block.layout.confidence))

    if not confidences:
        return 0.0

    return sum(confidences) / len(confidences)


def extract_blocks(response: documentai.Document, full_text: str) -> list[TextBlock]:
    """Extract block-level structure from Document AI response.

    Args:
        response: Document AI Document response
        full_text: Complete document text

    Returns:
        List of TextBlock objects
    """
    blocks: list[TextBlock] = []

    if not hasattr(response, "pages") or not response.pages:
        return blocks

    for page in response.pages:
        if not hasattr(page, "blocks") or not page.blocks:
            continue
        for block in page.blocks:
            if not hasattr(block, "layout") or not block.layout:
                continue

            text = extract_text_from_layout(full_text, block.layout)
            confidence = (
                float(block.layout.confidence)
                if hasattr(block.layout, "confidence")
                and block.layout.confidence is not None
                else 0.0
            )
            bbox = (
                layout_to_bbox(block.layout.bounding_poly)
                if hasattr(block.layout, "bounding_poly") and block.layout.bounding_poly
                else BoundingBox(x1=0, y1=0, x2=0, y2=0)
            )

            blocks.append(TextBlock(text=text, confidence=confidence, bbox=bbox))

    return blocks


def extract_paragraphs(
    response: documentai.Document, full_text: str
) -> list[TextParagraph]:
    """Extract paragraph-level structure from Document AI response.

    Args:
        response: Document AI Document response
        full_text: Complete document text

    Returns:
        List of TextParagraph objects
    """
    paragraphs: list[TextParagraph] = []

    if not hasattr(response, "pages") or not response.pages:
        return paragraphs

    for page in response.pages:
        if not hasattr(page, "paragraphs") or not page.paragraphs:
            continue
        for para in page.paragraphs:
            if not hasattr(para, "layout") or not para.layout:
                continue

            text = extract_text_from_layout(full_text, para.layout)
            confidence = (
                float(para.layout.confidence)
                if hasattr(para.layout, "confidence")
                and para.layout.confidence is not None
                else 0.0
            )
            bbox = (
                layout_to_bbox(para.layout.bounding_poly)
                if hasattr(para.layout, "bounding_poly") and para.layout.bounding_poly
                else BoundingBox(x1=0, y1=0, x2=0, y2=0)
            )

            paragraphs.append(
                TextParagraph(text=text, confidence=confidence, bbox=bbox)
            )

    return paragraphs


def extract_lines(response: documentai.Document, full_text: str) -> list[TextLine]:
    """Extract line-level structure from Document AI response.

    Args:
        response: Document AI Document response
        full_text: Complete document text

    Returns:
        List of TextLine objects
    """
    lines: list[TextLine] = []

    if not hasattr(response, "pages") or not response.pages:
        return lines

    for page in response.pages:
        if not hasattr(page, "lines") or not page.lines:
            continue
        for line in page.lines:
            if not hasattr(line, "layout") or not line.layout:
                continue

            text = extract_text_from_layout(full_text, line.layout)
            confidence = (
                float(line.layout.confidence)
                if hasattr(line.layout, "confidence")
                and line.layout.confidence is not None
                else 0.0
            )
            bbox = (
                layout_to_bbox(line.layout.bounding_poly)
                if hasattr(line.layout, "bounding_poly") and line.layout.bounding_poly
                else BoundingBox(x1=0, y1=0, x2=0, y2=0)
            )

            lines.append(TextLine(text=text, confidence=confidence, bbox=bbox))

    return lines


def extract_page_num(image_path: str) -> int:
    """Extract page number from image filename.

    Expects format: page_XXXX.png

    Args:
        image_path: Path to image file

    Returns:
        Page number (0-indexed)
    """
    match = re.search(r"page_(\d+)", image_path)
    if match:
        return int(match.group(1))
    return 0
