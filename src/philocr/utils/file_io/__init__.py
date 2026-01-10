"""File I/O utilities for saving and loading various file formats.

This module provides pure file I/O operations without UI dependencies,
allowing for better separation of concerns and testability.
"""

from __future__ import annotations

from philocr.utils.file_io.html_saver import HTMLSaver
from philocr.utils.file_io.json_loader import JSONLoader
from philocr.utils.file_io.json_saver import JSONSaver
from philocr.utils.file_io.markdown_saver import MarkdownSaver
from philocr.utils.file_io.text_saver import TextSaver

__all__ = [
    "TextSaver",
    "JSONSaver",
    "JSONLoader",
    "HTMLSaver",
    "MarkdownSaver",
]
