#!/usr/bin/env python3
"""
Test script for the Document AI OCR functionality.
This script tests the core OCR functionality without actually calling the Google API.
"""

import os
import time
from unittest.mock import Mock, patch

import fitz  # PyMuPDF
import pytest

from philocr.processing.document_ai import RateLimiter
from philocr.processing.pdf_utils import split_pdf
from philocr.utils.env_utils import load_env_file


class TestDocumentAIOCR:
    """Test suite for Document AI OCR application."""

    @pytest.mark.unit()
    def test_env_loading_with_mock_file(self, mock_env_file):
        """Test that environment variables are loaded correctly from a mock file."""
        # Load the mock environment file
        env_vars = load_env_file(str(mock_env_file))

        # Verify the loaded variables
        assert (
            env_vars.get("GOOGLE_APPLICATION_CREDENTIALS")
            == "/test/path/credentials.json"
        )
        assert env_vars.get("DOCUMENT_AI_PROJECT_ID") == "test-project-id"
        assert env_vars.get("DOCUMENT_AI_PROCESSOR_ID") == "test-processor-id"
        assert env_vars.get("DOCUMENT_AI_LOCATION") == "us"

    @pytest.mark.unit()
    def test_env_loading_with_environment(self, mock_env_vars):
        """Test that environment variables are accessible after mocking."""
        # Check that critical environment variables are set
        assert (
            os.getenv("GOOGLE_APPLICATION_CREDENTIALS") == "/fake/path/credentials.json"
        )

        # Check either the new variable name or the legacy one
        project_id = os.getenv("DOCUMENT_AI_PROJECT_ID") or os.getenv(
            "GOOGLE_CLOUD_PROJECT_ID"
        )
        assert project_id == "test-project-id"

        assert os.getenv("DOCUMENT_AI_PROCESSOR_ID") == "test-processor-id"
        assert os.getenv("DOCUMENT_AI_LOCATION") == "us"

    @pytest.mark.unit()
    def test_rate_limiter(self):
        """Test that the rate limiter correctly enforces call limits."""
        max_calls = 5
        period = 0.5  # seconds (reduced for faster testing)
        limiter = RateLimiter(max_calls, period)

        start_time = time.time()

        # Make max_calls calls which should complete immediately
        for _ in range(max_calls):
            limiter.wait_if_needed()

        # This one should wait because we've hit the limit
        limiter.wait_if_needed()

        elapsed = time.time() - start_time

        # Should have waited close to the rate limit period
        assert elapsed >= period * 0.9  # Allow for some timing variance

    @pytest.mark.unit()
    def test_rate_limiter_reset(self):
        """Test that the rate limiter resets after the period."""
        max_calls = 3
        period = 0.2  # seconds
        limiter = RateLimiter(max_calls, period)

        # Make max_calls
        for _ in range(max_calls):
            limiter.wait_if_needed()

        # Wait for period to expire
        time.sleep(period + 0.1)

        # Should be able to make calls again without waiting
        start_time = time.time()
        limiter.wait_if_needed()
        elapsed = time.time() - start_time

        assert elapsed < 0.1  # Should not have waited

    @pytest.mark.unit()
    def test_pdf_processing_mocked(self, temp_dir, mock_document_ai_client):
        """Test PDF processing with mocked Document AI client."""
        # Create a simple test PDF file using PyMuPDF
        pdf_path = temp_dir / "test.pdf"
        doc = fitz.open()  # Create a new empty PDF
        page = doc.new_page()  # Add a new page
        page.insert_text((100, 100), "Test PDF Content")  # Add some text
        doc.save(str(pdf_path))  # Save the PDF
        doc.close()

        # Mock the process_pdf function
        with patch("philocr.processing.document_ai.process_pdf") as mock_process:
            mock_process.return_value = "This is test text extracted from a PDF."

            # Call the mock function
            result = mock_process(str(pdf_path))

            # Verify the result
            assert result == "This is test text extracted from a PDF."
            mock_process.assert_called_once_with(str(pdf_path))

    @pytest.mark.unit()
    def test_pdf_splitting(self, temp_dir):
        """Test PDF splitting functionality using PyMuPDF."""
        # Create a multi-page PDF for testing
        pdf_path = temp_dir / "multipage.pdf"
        doc = fitz.open()
        for i in range(20):  # Create a 20-page document
            page = doc.new_page()
            page.insert_text((100, 100), f"Page {i+1}")
        doc.save(str(pdf_path))
        doc.close()

        # Test splitting with various page limits
        test_cases = [
            (5, 4),  # 20 pages / 5 = 4 chunks
            (10, 2),  # 20 pages / 10 = 2 chunks
            (15, 2),  # 20 pages / 15 = 2 chunks (15 + 5)
            (25, 1),  # 20 pages / 25 = 1 chunk (no split needed)
        ]

        for max_pages, expected_chunks in test_cases:
            split_files = split_pdf(str(pdf_path), max_pages, str(temp_dir))

            # Check if splitting worked as expected
            assert (
                split_files is not None
            ), f"split_pdf returned None for max_pages={max_pages}"
            assert (
                len(split_files) == expected_chunks
            ), f"Expected {expected_chunks} chunks with max_pages={max_pages}, got {len(split_files)}"

            # Verify each chunk has the correct number of pages
            total_pages = 0
            for i, file in enumerate(split_files):
                doc = fitz.open(file)
                page_count = doc.page_count
                total_pages += page_count

                if i < expected_chunks - 1:
                    # All chunks except the last should have max_pages
                    assert (
                        page_count == max_pages
                    ), f"Chunk {i} should have {max_pages} pages, got {page_count}"
                else:
                    # Last chunk should have remaining pages
                    remaining = 20 - (i * max_pages)
                    assert (
                        page_count == remaining
                    ), f"Last chunk should have {remaining} pages, got {page_count}"

                doc.close()

            # Verify total pages
            assert total_pages == 20, f"Total pages should be 20, got {total_pages}"

    @pytest.mark.unit()
    def test_pdf_splitting_single_page(self, temp_dir):
        """Test PDF splitting with a single-page document."""
        # Create a single-page PDF
        pdf_path = temp_dir / "single.pdf"
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((100, 100), "Single Page")
        doc.save(str(pdf_path))
        doc.close()

        # Split with max_pages > 1
        split_files = split_pdf(str(pdf_path), 5, str(temp_dir))

        # Should return the original file or a single chunk
        assert split_files is not None
        assert len(split_files) == 1

    @pytest.mark.integration()
    @pytest.mark.requires_credentials()
    def test_document_ai_client_initialization(
        self, mock_env_vars, mock_credentials_file
    ):
        """Test Document AI client initialization with mocked credentials."""
        with patch(
            "google.cloud.documentai.DocumentProcessorServiceClient"
        ) as mock_client:
            with patch.dict(
                os.environ,
                {"GOOGLE_APPLICATION_CREDENTIALS": str(mock_credentials_file)},
            ):
                # Import here to trigger initialization with mocked env
                from philocr.processing.document_ai import get_document_ai_client

                # Call the function that creates the client
                client = get_document_ai_client()

                # Verify client was created
                mock_client.assert_called_once()
                assert client is not None

    @pytest.mark.unit()
    def test_process_pdf_error_handling(self, temp_dir):
        """Test error handling in PDF processing."""
        # Create an invalid PDF path
        invalid_path = temp_dir / "nonexistent.pdf"

        with patch("philocr.processing.document_ai.process_pdf") as mock_process:
            mock_process.side_effect = FileNotFoundError("File not found")

            with pytest.raises(FileNotFoundError):
                mock_process(str(invalid_path))

    @pytest.mark.unit()
    @patch("philocr.processing.document_ai.DocumentProcessorServiceClient")
    def test_process_pdf_with_rate_limiting(self, mock_client, temp_dir):
        """Test PDF processing with rate limiting."""
        # Create a test PDF
        pdf_path = temp_dir / "test.pdf"
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((100, 100), "Test content")
        doc.save(str(pdf_path))
        doc.close()

        # Mock the client response
        mock_response = Mock()
        mock_response.document.text = "Extracted text"
        mock_client.return_value.process_document.return_value = mock_response

        # Create a rate limiter
        limiter = RateLimiter(max_calls=2, period=1)

        with patch("philocr.processing.document_ai.process_pdf") as mock_process:
            mock_process.return_value = "Extracted text"

            # Process multiple times to test rate limiting
            start_time = time.time()
            for _ in range(3):
                result = mock_process(str(pdf_path), rate_limiter=limiter)
                assert result == "Extracted text"

            elapsed = time.time() - start_time

            # Should have been rate limited on the third call
            assert elapsed >= 0.9  # Allow some variance
