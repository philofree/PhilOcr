"""Basic tests to verify test infrastructure is working correctly."""

import pytest


class TestBasicSetup:
    """Basic tests to ensure pytest is configured correctly."""

    @pytest.mark.unit()
    def test_pytest_is_working(self):
        """Verify that pytest can run a simple test."""
        assert True

    @pytest.mark.unit()
    def test_fixtures_are_available(self, temp_dir):
        """Verify that fixtures from conftest.py are available."""
        assert temp_dir.exists()
        assert temp_dir.is_dir()

    @pytest.mark.unit()
    def test_mock_env_vars(self, mock_env_vars):
        """Verify that environment variable mocking works."""
        assert mock_env_vars["DOCUMENT_AI_PROJECT_ID"] == "test-project-id"
        assert mock_env_vars["DOCUMENT_AI_PROCESSOR_ID"] == "test-processor-id"

    @pytest.mark.unit()
    def test_imports_work(self):
        """Verify that we can import from the philocr package."""
        try:
            from philocr.utils.env_utils import load_env_file

            assert load_env_file is not None
        except ImportError as e:
            pytest.fail(f"Failed to import philocr modules: {e}")

    @pytest.mark.unit()
    def test_sample_pdf_fixture(self, sample_pdf_file):
        """Verify that the sample PDF fixture creates a valid file."""
        assert sample_pdf_file.exists()
        assert sample_pdf_file.suffix == ".pdf"
        assert sample_pdf_file.stat().st_size > 0

    @pytest.mark.unit()
    def test_json_response_fixture(self, sample_json_response):
        """Verify that the sample JSON response fixture is valid."""
        assert "document" in sample_json_response
        assert "text" in sample_json_response["document"]
        assert "pages" in sample_json_response["document"]
        assert len(sample_json_response["document"]["pages"]) > 0
