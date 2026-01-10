#!/usr/bin/env python3
"""
Batch processing test for OJD OCR Processor.
This script tests the batch processing functionality with sample PDF files.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from PyQt6.QtCore import QObject, pyqtSignal

    from src.philocr.workers.processing_worker import ProcessingWorker
except ImportError:
    print(
        "PyQt6 not installed or processing_worker.py not found. Tests will be skipped."
    )
    PYQT_AVAILABLE = False
else:
    PYQT_AVAILABLE = True


def create_dummy_pdf_file() -> str:
    """
    Create a dummy PDF file for testing.

    Returns:
        Path to the created file
    """
    # For a real test, we would create an actual PDF file
    # But for this test script, we'll just create a placeholder
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
        pdf_content = (
            b"%PDF-1.7\n"
            b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
            b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
            b"3 0 obj\n<< /Type /Page /Parent 2 0 R "
            b"/MediaBox [0 0 612 792] /Contents 4 0 R >>\nendobj\n"
            b"4 0 obj\n<< /Length 44 >>\nstream\n"
            b"BT\n/F1 12 Tf\n100 700 Td\n(Test PDF) Tj\nET\n"
            b"endstream\nendobj\n"
            b"xref\n0 5\n"
            b"0000000000 65535 f\n"
            b"0000000010 00000 n\n"
            b"0000000060 00000 n\n"
            b"0000000119 00000 n\n"
            b"0000000209 00000 n\n"
            b"trailer\n<< /Size 5 /Root 1 0 R >>\n"
            b"startxref\n304\n%%EOF"
        )
        f.write(pdf_content)
        return f.name


def create_dummy_pdf_files(count: int = 3) -> list[str]:
    """
    Create multiple dummy PDF files for batch testing.

    Args:
        count: Number of files to create

    Returns:
        List of paths to the created files
    """
    return [create_dummy_pdf_file() for _ in range(count)]


if PYQT_AVAILABLE:

    class TestSignalReceiver(QObject):
        """Signal receiver for testing the ProcessingWorker."""

        test_complete = pyqtSignal(bool)

        def __init__(self):
            super().__init__()
            self.received_text = ""
            self.received_status = []
            self.progress_values = []
            self.error_messages = []
            self.finished_called = False
            self.json_data = None

        def on_text_update(self, text: str):
            """Handle text updates from the worker."""
            self.received_text = text

        def on_status_update(self, status: str):
            """Handle status updates from the worker."""
            self.received_status.append(status)

        def on_progress_update(self, progress: int):
            """Handle progress updates from the worker."""
            self.progress_values.append(progress)

        def on_error(self, error: str):
            """Handle error messages from the worker."""
            self.error_messages.append(error)

        def on_finished(self, success: bool):
            """Handle worker completion."""
            self.finished_called = True
            self.test_complete.emit(success)

        def on_json_ready(self, json_data: dict):
            """Handle JSON data from the worker."""
            self.json_data = json_data


def test_batch_processing_setup():
    """Test setting up batch processing."""
    import pytest

    if not PYQT_AVAILABLE:
        pytest.skip("PyQt6 not available")

    print("Testing batch processing setup...")

    test_files = []
    try:
        # Create test files
        test_files = create_dummy_pdf_files(3)

        # Create a processing worker
        worker = ProcessingWorker(test_files[0])

        # Set up batch mode
        worker.set_batch_mode(test_files)

        # Check if batch mode was set correctly
        assert worker.batch_mode is True
        assert worker.batch_files == test_files

        print("Batch processing setup test passed.")
    finally:
        # Clean up test files
        for file_path in test_files:
            if os.path.exists(file_path):
                os.unlink(file_path)


def test_metadata_handling():
    """Test handling metadata in the processing worker."""
    import pytest

    if not PYQT_AVAILABLE:
        pytest.skip("PyQt6 not available")

    print("Testing metadata handling...")

    test_file = None
    try:
        # Create a test file
        test_file = create_dummy_pdf_file()

        # Create a processing worker
        worker = ProcessingWorker(test_file)

        # Set metadata
        test_metadata = {
            "document_type": "test",
            "processor": "unit_test",
            "timestamp": "2023-01-01T00:00:00",
        }
        worker.set_metadata(test_metadata)

        # Check if metadata was set correctly
        assert worker.metadata == test_metadata

        print("Metadata handling test passed.")
    finally:
        # Clean up test file
        if test_file and os.path.exists(test_file):
            os.unlink(test_file)


def run_batch_processing_tests():
    """Run all batch processing tests and report results."""
    print("=" * 50)
    print("OJD OCR Processor - Batch Processing Tests")
    print("=" * 50)

    if not PYQT_AVAILABLE:
        print("\nWARNING: PyQt6 not available. Most tests will be skipped.")

    tests = {
        "Batch Processing Setup": test_batch_processing_setup,
        "Metadata Handling": test_metadata_handling,
    }

    results = {}
    all_passed = True

    for name, test_func in tests.items():
        print(f"\nRunning test: {name}")
        try:
            result = test_func()
            results[name] = result
            if not result:
                all_passed = False
        except Exception as e:
            print(f"Test failed with exception: {e}")
            results[name] = False
            all_passed = False

    print("\n" + "=" * 50)
    print("Test Results:")
    for name, result in results.items():
        status = "PASSED" if result else "FAILED"
        print(f"{name}: {status}")

    print("\nOverall result:", "PASSED" if all_passed else "FAILED")

    if not PYQT_AVAILABLE:
        print("\nNote: Some tests were skipped because PyQt6 is not available.")

    return all_passed


if __name__ == "__main__":
    success = run_batch_processing_tests()
    sys.exit(0 if success else 1)
