#!/usr/bin/env python3
"""
Environment configuration test for OJD OCR Processor.
This script tests the environment loading functionality with different scenarios.
"""

import json
import os

import pytest

from philocr.utils.env_loader import get_embedded_env, load_embedded_env
from philocr.utils.env_utils import get_google_credentials, load_env_file


class TestEnvironmentLoading:
    """Test suite for environment configuration and loading."""

    @pytest.mark.unit()
    def test_valid_env_file_loading(self, mock_env_file, monkeypatch):
        """Test loading a valid environment file."""
        # Clear any existing env vars
        for key in [
            "GOOGLE_APPLICATION_CREDENTIALS",
            "DOCUMENT_AI_PROJECT_ID",
            "DOCUMENT_AI_PROCESSOR_ID",
            "DOCUMENT_AI_LOCATION",
        ]:
            monkeypatch.delenv(key, raising=False)

        # Load the mock environment file
        env_vars = load_env_file(str(mock_env_file))

        # Verify environment variables were loaded correctly
        assert (
            os.getenv("GOOGLE_APPLICATION_CREDENTIALS") == "/test/path/credentials.json"
        )
        assert os.getenv("DOCUMENT_AI_PROJECT_ID") == "test-project-id"
        assert os.getenv("DOCUMENT_AI_PROCESSOR_ID") == "test-processor-id"
        assert os.getenv("DOCUMENT_AI_LOCATION") == "us"

        # Verify the returned dictionary
        assert (
            env_vars.get("GOOGLE_APPLICATION_CREDENTIALS")
            == "/test/path/credentials.json"
        )
        assert env_vars.get("DOCUMENT_AI_PROJECT_ID") == "test-project-id"

    @pytest.mark.unit()
    def test_invalid_env_file_handling(self, temp_dir, monkeypatch):
        """Test handling of invalid environment file."""
        # Create an invalid env file
        invalid_env_file = temp_dir / "invalid.env"
        invalid_env_file.write_text(
            "# Invalid test environment file\nINVALID_VAR=value\n"
        )

        # Clear any existing env vars
        for key in [
            "GOOGLE_APPLICATION_CREDENTIALS",
            "DOCUMENT_AI_PROJECT_ID",
            "DOCUMENT_AI_PROCESSOR_ID",
        ]:
            monkeypatch.delenv(key, raising=False)

        # Load the invalid environment file
        load_env_file(str(invalid_env_file))

        # Verify critical variables are not set
        assert os.getenv("GOOGLE_APPLICATION_CREDENTIALS") is None
        assert os.getenv("DOCUMENT_AI_PROJECT_ID") is None
        assert os.getenv("DOCUMENT_AI_PROCESSOR_ID") is None

        # But the invalid var should be loaded
        assert os.getenv("INVALID_VAR") == "value"

    @pytest.mark.unit()
    def test_nonexistent_env_file(self, monkeypatch):
        """Test handling of non-existent environment file."""
        # Try to load a non-existent file
        result = load_env_file("/path/to/nonexistent/file.env")

        # Should return empty dict and not raise exception
        assert result == {}

    @pytest.mark.unit()
    def test_embedded_env_loading(self, monkeypatch):
        """Test the embedded environment functionality."""
        # Clear any existing env vars
        for key in [
            "GOOGLE_APPLICATION_CREDENTIALS",
            "DOCUMENT_AI_PROJECT_ID",
            "DOCUMENT_AI_PROCESSOR_ID",
        ]:
            monkeypatch.delenv(key, raising=False)

        # Test embedded environment loading
        load_embedded_env()

        # Get embedded environment
        embedded_env = get_embedded_env()

        # Should be empty or None since we removed hardcoded credentials
        assert embedded_env is None or len(embedded_env) == 0

    @pytest.mark.unit()
    def test_google_credentials_retrieval(self, mock_env_vars):
        """Test retrieving Google credentials from environment."""
        # Test retrieving Google credentials
        creds = get_google_credentials()

        # Verify credentials were retrieved correctly
        assert creds["credentials_path"] == "/fake/path/credentials.json"
        assert creds["project_id"] == "test-project-id"
        assert creds["processor_id"] == "test-processor-id"
        assert creds.get("location", "us") == "us"

    @pytest.mark.unit()
    def test_google_credentials_missing(self, monkeypatch):
        """Test behavior when Google credentials are missing."""
        # Clear all environment variables
        for key in [
            "GOOGLE_APPLICATION_CREDENTIALS",
            "DOCUMENT_AI_PROJECT_ID",
            "DOCUMENT_AI_PROCESSOR_ID",
            "DOCUMENT_AI_LOCATION",
        ]:
            monkeypatch.delenv(key, raising=False)

        # Get credentials
        creds = get_google_credentials()

        # Should return dict with None values or raise exception
        assert creds.get("credentials_path") is None or creds["credentials_path"] == ""
        assert creds.get("project_id") is None or creds["project_id"] == ""
        assert creds.get("processor_id") is None or creds["processor_id"] == ""

    @pytest.mark.unit()
    def test_env_file_with_comments_and_empty_lines(self, temp_dir):
        """Test loading env file with comments and empty lines."""
        env_file = temp_dir / "test_comments.env"
        env_content = """# This is a comment
# Another comment

GOOGLE_APPLICATION_CREDENTIALS=/path/to/creds.json
# Mid-file comment
DOCUMENT_AI_PROJECT_ID=test-project

# Empty line above
DOCUMENT_AI_PROCESSOR_ID=test-processor
"""
        env_file.write_text(env_content)

        env_vars = load_env_file(str(env_file))

        # Verify only actual variables are loaded
        assert env_vars.get("GOOGLE_APPLICATION_CREDENTIALS") == "/path/to/creds.json"
        assert env_vars.get("DOCUMENT_AI_PROJECT_ID") == "test-project"
        assert env_vars.get("DOCUMENT_AI_PROCESSOR_ID") == "test-processor"

        # Comments should not be loaded
        assert "# This is a comment" not in env_vars

    @pytest.mark.unit()
    def test_env_file_with_quotes(self, temp_dir):
        """Test loading env file with quoted values."""
        env_file = temp_dir / "test_quotes.env"
        env_content = """SINGLE_QUOTED='value with spaces'
DOUBLE_QUOTED="another value"
NO_QUOTES=simple_value
MIXED_QUOTES="value with 'single' quotes"
"""
        env_file.write_text(env_content)

        env_vars = load_env_file(str(env_file))

        # python-dotenv should handle quotes properly
        assert env_vars.get("SINGLE_QUOTED") == "value with spaces"
        assert env_vars.get("DOUBLE_QUOTED") == "another value"
        assert env_vars.get("NO_QUOTES") == "simple_value"
        assert env_vars.get("MIXED_QUOTES") == "value with 'single' quotes"

    @pytest.mark.unit()
    def test_env_variable_override(self, mock_env_vars, temp_dir):
        """Test that loading env file overrides existing environment variables."""
        # Set initial value
        assert os.getenv("DOCUMENT_AI_PROJECT_ID") == "test-project-id"

        # Create env file with different value
        env_file = temp_dir / "override.env"
        env_file.write_text("DOCUMENT_AI_PROJECT_ID=overridden-project-id\n")

        # Load the file
        load_env_file(str(env_file))

        # Verify the value was overridden
        assert os.getenv("DOCUMENT_AI_PROJECT_ID") == "overridden-project-id"

    @pytest.mark.integration()
    @pytest.mark.requires_credentials()
    def test_real_credentials_file_loading(self, mock_credentials_file):
        """Test loading actual credentials JSON file format."""
        # Mock the credentials file path in environment
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(mock_credentials_file)

        # Verify the file exists and is valid JSON
        assert mock_credentials_file.exists()

        with open(mock_credentials_file) as f:
            creds_data = json.load(f)

        # Verify required fields
        assert creds_data["type"] == "service_account"
        assert creds_data["project_id"] == "test-project-id"
        assert "private_key" in creds_data
        assert "client_email" in creds_data
