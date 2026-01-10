"""Pytest configuration and shared fixtures for the test suite."""

# Add src to Python path
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture()
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture()
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    env_vars = {
        "GOOGLE_APPLICATION_CREDENTIALS": "/fake/path/credentials.json",
        "DOCUMENT_AI_PROJECT_ID": "test-project-id",
        "DOCUMENT_AI_PROCESSOR_ID": "test-processor-id",
        "DOCUMENT_AI_LOCATION": "us",
        "GOOGLE_CLOUD_PROJECT_ID": "test-project-id",
    }

    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

    return env_vars


@pytest.fixture()
def mock_env_file(temp_dir):
    """Create a mock environment file."""
    env_file = temp_dir / "test.env"
    env_content = """# Test environment file
GOOGLE_APPLICATION_CREDENTIALS=/test/path/credentials.json
DOCUMENT_AI_PROJECT_ID=test-project-id
DOCUMENT_AI_PROCESSOR_ID=test-processor-id
DOCUMENT_AI_LOCATION=us
GOOGLE_CLOUD_PROJECT_ID=test-project-id
"""
    env_file.write_text(env_content)
    return env_file


@pytest.fixture()
def mock_credentials_file(temp_dir):
    """Create a mock Google credentials JSON file."""
    creds_file = temp_dir / "credentials.json"
    creds_content = {
        "type": "service_account",
        "project_id": "test-project-id",
        "private_key_id": "test-key-id",
        "private_key": "-----BEGIN PRIVATE KEY-----\ntest-key\n-----END PRIVATE KEY-----\n",
        "client_email": "test@test-project-id.iam.gserviceaccount.com",
        "client_id": "123456789",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/test%40test-project-id.iam.gserviceaccount.com",
    }

    import json

    creds_file.write_text(json.dumps(creds_content, indent=2))
    return creds_file


@pytest.fixture()
def mock_document_ai_client():
    """Mock Google Document AI client."""
    with patch("google.cloud.documentai.DocumentProcessorServiceClient") as mock_client:
        # Create mock response
        mock_response = Mock()
        mock_response.document.text = "Sample extracted text"
        mock_response.document.pages = []

        # Configure mock client
        mock_instance = Mock()
        mock_instance.process_document.return_value = mock_response
        mock_client.return_value = mock_instance

        yield mock_instance


@pytest.fixture()
def sample_pdf_file(temp_dir):
    """Create a sample PDF file for testing."""
    pdf_file = temp_dir / "sample.pdf"
    # Create a minimal valid PDF
    pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> >> >> /MediaBox [0 0 612 792] /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 44 >>
stream
BT
/F1 12 Tf
100 700 Td
(Hello World) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000308 00000 n 
trailer
<< /Size 5 /Root 1 0 R >>
startxref
402
%%EOF"""
    pdf_file.write_bytes(pdf_content)
    return pdf_file


@pytest.fixture()
def sample_json_response():
    """Create a sample Document AI JSON response."""
    return {
        "document": {
            "text": "Sample Document Text\nPage 1 content\nPage 2 content",
            "pages": [
                {
                    "pageNumber": 1,
                    "dimension": {"width": 8.5, "height": 11, "unit": "INCH"},
                    "layout": {
                        "textAnchor": {
                            "textSegments": [{"startIndex": 0, "endIndex": 20}]
                        },
                        "confidence": 0.99,
                        "boundingPoly": {
                            "vertices": [
                                {"x": 0, "y": 0},
                                {"x": 100, "y": 0},
                                {"x": 100, "y": 100},
                                {"x": 0, "y": 100},
                            ]
                        },
                    },
                    "blocks": [],
                    "paragraphs": [],
                    "lines": [],
                    "tokens": [],
                }
            ],
            "entities": [],
            "textStyles": [],
        }
    }


@pytest.fixture()
def mock_pyqt_app():
    """Mock PyQt application for UI testing."""
    with patch("PyQt6.QtWidgets.QApplication") as mock_app:
        mock_instance = Mock()
        mock_app.return_value = mock_instance
        yield mock_instance


@pytest.fixture(autouse=True)
def reset_environment(monkeypatch):
    """Reset environment variables before each test."""
    # Clear Document AI related variables
    env_vars_to_clear = [
        "GOOGLE_APPLICATION_CREDENTIALS",
        "DOCUMENT_AI_PROJECT_ID",
        "DOCUMENT_AI_PROCESSOR_ID",
        "DOCUMENT_AI_LOCATION",
        "GOOGLE_CLOUD_PROJECT_ID",
    ]

    for var in env_vars_to_clear:
        monkeypatch.delenv(var, raising=False)

    # Restore is handled automatically by monkeypatch


@pytest.fixture()
def mock_file_operations():
    """Mock common file operations."""
    with patch("builtins.open", mock_open()) as mock_file:
        with patch("os.path.exists", return_value=True):
            with patch("os.path.isfile", return_value=True):
                with patch("os.path.isdir", return_value=False):
                    yield mock_file


# Markers for different test types
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line(
        "markers", "requires_credentials: Tests that require Google Cloud credentials"
    )
