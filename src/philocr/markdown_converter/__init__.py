"""
Markdown converter module for Google Document AI JSON.

This module provides functionality to convert Document AI JSON output to Markdown format.
"""

from philocr.utils.markdown_converter.academic_doc_parser import AcademicDocumentParser
from philocr.utils.markdown_converter.markdown_handler import MarkdownHandler
from philocr.utils.markdown_converter.streaming_academic_doc_parser import (
    StreamingAcademicDocumentParser,
)

__all__ = [
    "AcademicDocumentParser",
    "MarkdownHandler",
    "StreamingAcademicDocumentParser",
]
