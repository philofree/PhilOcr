"""Pipeline models for PhilOcr v1.4 architecture."""

from philocr.models.bounding_box import BoundingBox
from philocr.models.config import PipelineConfig
from philocr.models.document import (
    Document,
    DocumentMetadata,
    DocumentStatistics,
    GenreDetectionResult,
    GenreHint,
    PageOutput,
    Paragraph,
)
from philocr.models.ocr_result import OCRResult, TextBlock, TextLine, TextParagraph
from philocr.models.page import CroppedPage, MaskedPage, PageImage, PageZones
from philocr.models.scan_area import (
    ManualScanArea,
    ManualScanAreas,
    load_scan_areas,
    save_scan_areas,
    scan_areas_path_for_pdf,
    try_load_scan_areas_for_pdf,
)
from philocr.models.template import DocumentTemplate

__all__ = [
    "BoundingBox",
    "PipelineConfig",
    "DocumentTemplate",
    "PageImage",
    "MaskedPage",
    "CroppedPage",
    "PageZones",
    "OCRResult",
    "TextBlock",
    "TextParagraph",
    "TextLine",
    "PageOutput",
    "Paragraph",
    "Document",
    "DocumentMetadata",
    "DocumentStatistics",
    "GenreHint",
    "GenreDetectionResult",
    "ManualScanArea",
    "ManualScanAreas",
    "load_scan_areas",
    "save_scan_areas",
    "scan_areas_path_for_pdf",
    "try_load_scan_areas_for_pdf",
]
