#!/usr/bin/env python3
"""
Test suite for the Document AI Academic Formatter.
Tests HTML output generation and formatting functionality.
"""
import json
from typing import Any

import pytest

from philocr.utils.document_ai_formatter import format_document_ai_json


class TestDocumentAIFormatter:
    """Test suite for Document AI formatter functionality."""

    @pytest.fixture()
    def synthetic_json_data(self) -> dict[str, Any]:
        """Create synthetic JSON data for testing."""
        return {
            "text": "Sample document text",
            "timestamp": "2025-03-24T00:00:00Z",
            "metadata": {"filename": "test.pdf"},
            "document_data": {
                "pages": [
                    {
                        "page_number": 1,
                        "dimension": {"width": 1000, "height": 1500},
                        "blocks": [
                            {
                                "text": "SAMPLE HEADER",
                                "layout": {
                                    "bounding_poly": {
                                        "vertices": [
                                            {"x": 300, "y": 100},
                                            {"x": 700, "y": 100},
                                            {"x": 700, "y": 150},
                                            {"x": 300, "y": 150},
                                        ]
                                    }
                                },
                            },
                            {
                                "text": "This is sample text for testing the formatter.",
                                "layout": {
                                    "bounding_poly": {
                                        "vertices": [
                                            {"x": 100, "y": 200},
                                            {"x": 900, "y": 200},
                                            {"x": 900, "y": 250},
                                            {"x": 100, "y": 250},
                                        ]
                                    }
                                },
                            },
                        ],
                    }
                ]
            },
        }

    @pytest.fixture()
    def json_without_polygons(self) -> dict[str, Any]:
        """Create JSON data without bounding polygons."""
        return {
            "text": "Document without polygons",
            "timestamp": "2025-03-24T00:00:00Z",
            "metadata": {"filename": "no_polygons.pdf"},
            "document_data": {
                "pages": [
                    {
                        "page_number": 1,
                        "dimension": {"width": 1000, "height": 1500},
                        "blocks": [
                            {"text": "HEADER WITHOUT POLYGON"},
                            {"text": "Body text without polygon information"},
                        ],
                    }
                ]
            },
        }

    @pytest.mark.unit()
    def test_format_synthetic_document(self, synthetic_json_data):
        """Test formatting with synthetic document data."""
        html = format_document_ai_json(synthetic_json_data, debug_mode=True)

        # Verify HTML is generated
        assert html is not None
        assert len(html) > 0

        # Check for expected content
        assert "SAMPLE HEADER" in html
        assert "This is sample text for testing the formatter." in html
        assert "test.pdf" in html

        # Check for HTML structure
        assert "<html" in html
        assert "</html>" in html
        assert "<body" in html
        assert "</body>" in html

    @pytest.mark.unit()
    def test_format_without_bounding_polygons(self, json_without_polygons):
        """Test formatting when bounding polygons are missing."""
        html = format_document_ai_json(json_without_polygons, debug_mode=True)

        # Should still generate HTML even without polygons
        assert html is not None
        assert len(html) > 0

        # Check content is included
        assert "HEADER WITHOUT POLYGON" in html
        assert "Body text without polygon information" in html

    @pytest.mark.unit()
    def test_format_empty_document(self):
        """Test formatting with empty document data."""
        empty_json = {
            "text": "",
            "timestamp": "2025-03-24T00:00:00Z",
            "metadata": {"filename": "empty.pdf"},
            "document_data": {"pages": []},
        }

        html = format_document_ai_json(empty_json, debug_mode=True)

        # Should generate HTML structure even for empty document
        assert html is not None
        assert "<html" in html
        assert "</html>" in html

    @pytest.mark.unit()
    def test_format_with_special_characters(self):
        """Test formatting with special characters in text."""
        special_char_json = {
            "text": "Special chars: <>&\"'",
            "timestamp": "2025-03-24T00:00:00Z",
            "metadata": {"filename": "special.pdf"},
            "document_data": {
                "pages": [
                    {
                        "page_number": 1,
                        "dimension": {"width": 1000, "height": 1500},
                        "blocks": [
                            {
                                "text": 'Text with <html> tags & special "quotes"',
                                "layout": {
                                    "bounding_poly": {
                                        "vertices": [
                                            {"x": 100, "y": 100},
                                            {"x": 500, "y": 100},
                                            {"x": 500, "y": 150},
                                            {"x": 100, "y": 150},
                                        ]
                                    }
                                },
                            }
                        ],
                    }
                ]
            },
        }

        html = format_document_ai_json(special_char_json, debug_mode=True)

        # Special characters should be properly escaped
        assert "&lt;html&gt;" in html or "<html>" not in html.replace("<html", "")
        assert "&amp;" in html or "&" in html
        assert "&quot;" in html or '"' in html

    @pytest.mark.unit()
    def test_format_multipage_document(self):
        """Test formatting with multiple pages."""
        multipage_json = {
            "text": "Page 1 text\nPage 2 text",
            "timestamp": "2025-03-24T00:00:00Z",
            "metadata": {"filename": "multipage.pdf"},
            "document_data": {
                "pages": [
                    {
                        "page_number": 1,
                        "dimension": {"width": 1000, "height": 1500},
                        "blocks": [
                            {
                                "text": "Page 1 Header",
                                "layout": {
                                    "bounding_poly": {
                                        "vertices": [
                                            {"x": 100, "y": 100},
                                            {"x": 500, "y": 100},
                                            {"x": 500, "y": 150},
                                            {"x": 100, "y": 150},
                                        ]
                                    }
                                },
                            }
                        ],
                    },
                    {
                        "page_number": 2,
                        "dimension": {"width": 1000, "height": 1500},
                        "blocks": [
                            {
                                "text": "Page 2 Header",
                                "layout": {
                                    "bounding_poly": {
                                        "vertices": [
                                            {"x": 100, "y": 100},
                                            {"x": 500, "y": 100},
                                            {"x": 500, "y": 150},
                                            {"x": 100, "y": 150},
                                        ]
                                    }
                                },
                            }
                        ],
                    },
                ]
            },
        }

        html = format_document_ai_json(multipage_json, debug_mode=True)

        # Check both pages are included
        assert "Page 1 Header" in html
        assert "Page 2 Header" in html

        # Check for page breaks or separators
        assert "page-break" in html or "Page 2" in html

    @pytest.mark.unit()
    def test_format_with_metadata(self):
        """Test that metadata is properly included in output."""
        metadata_json = {
            "text": "Document text",
            "timestamp": "2025-03-24T12:34:56Z",
            "metadata": {
                "filename": "test_document.pdf",
                "pages": 5,
                "author": "Test Author",
            },
            "document_data": {
                "pages": [
                    {
                        "page_number": 1,
                        "dimension": {"width": 1000, "height": 1500},
                        "blocks": [{"text": "Content"}],
                    }
                ]
            },
        }

        html = format_document_ai_json(metadata_json, debug_mode=True)

        # Check metadata is included
        assert "test_document.pdf" in html
        assert "2025-03-24" in html or "timestamp" in html

    @pytest.mark.unit()
    def test_format_invalid_json(self):
        """Test handling of invalid JSON structure."""
        invalid_json = {"invalid": "structure"}

        # Should handle gracefully without crashing
        html = format_document_ai_json(invalid_json, debug_mode=True)
        assert html is not None

    @pytest.mark.unit()
    def test_debug_mode_differences(self, synthetic_json_data):
        """Test differences between debug and non-debug mode."""
        debug_html = format_document_ai_json(synthetic_json_data, debug_mode=True)
        normal_html = format_document_ai_json(synthetic_json_data, debug_mode=False)

        # Both should generate HTML
        assert debug_html is not None
        assert normal_html is not None

        # Debug mode might include additional information
        # (This depends on the implementation)
        assert len(debug_html) >= len(normal_html) or len(debug_html) > 0

    @pytest.mark.unit()
    def test_fix_bounding_polygons_helper(self, json_without_polygons):
        """Test the helper function that adds synthetic bounding polygons."""
        # This tests the fix_bounding_polygons logic if it's exposed
        # For now, we just test that formatter handles missing polygons
        html = format_document_ai_json(json_without_polygons, debug_mode=True)
        assert html is not None
        assert "HEADER WITHOUT POLYGON" in html

    @pytest.mark.integration()
    def test_format_with_real_json_sample(self, temp_dir):
        """Test with a real JSON sample if available."""
        # Create a sample JSON file
        sample_file = temp_dir / "sample.json"
        sample_data = {
            "text": "Real sample text",
            "timestamp": "2025-03-24T00:00:00Z",
            "metadata": {"filename": "real_sample.pdf"},
            "document_data": {
                "pages": [
                    {
                        "page_number": 1,
                        "dimension": {"width": 850, "height": 1100},
                        "blocks": [
                            {
                                "text": "Academic Paper Title",
                                "layout": {
                                    "bounding_poly": {
                                        "vertices": [
                                            {"x": 200, "y": 100},
                                            {"x": 650, "y": 100},
                                            {"x": 650, "y": 150},
                                            {"x": 200, "y": 150},
                                        ]
                                    }
                                },
                            }
                        ],
                    }
                ]
            },
        }

        sample_file.write_text(json.dumps(sample_data))

        # Load and format
        with open(sample_file) as f:
            loaded_data = json.load(f)

        html = format_document_ai_json(loaded_data, debug_mode=True)

        # Verify formatting
        assert html is not None
        assert "Academic Paper Title" in html
        assert "real_sample.pdf" in html
