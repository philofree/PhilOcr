#!/usr/bin/env python3
"""
Smoke test for OJD OCR Processor.
This script verifies that the application can start and initialize correctly.
"""

import importlib.util
import os
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.philocr.utils.env_loader import load_embedded_env
from src.philocr.utils.env_utils import load_env_file


def test_environment_loading():
    """Test that environment variables can be loaded."""
    print("Testing environment loading...")

    # Load environment variables
    _ = load_env_file("ENV.local")
    load_embedded_env()

    # Check if critical environment variables are set
    critical_vars = [
        "GOOGLE_APPLICATION_CREDENTIALS",
        "DOCUMENT_AI_PROJECT_ID",
        "DOCUMENT_AI_PROCESSOR_ID",
    ]

    missing_vars = []
    for var in critical_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print(
            f"WARNING: The following critical environment variables are not set: {', '.join(missing_vars)}"
        )
        print("The application may not function correctly without these variables.")
    else:
        print("Environment variables loaded successfully.")

    return len(missing_vars) == 0


def test_import_structure():
    """Test that key modules can be imported."""
    print("Testing import structure...")

    try:
        # Check for module availability using importlib
        modules = [
            "src.philocr.main.run_app",
            "src.philocr.processing.document_ai.process_pdf",
            "src.philocr.ui.main_window.MainWindow",
            "src.philocr.utils.markdown_converter.AcademicDocumentParser",
            "src.philocr.utils.markdown_converter.MarkdownHandler",
        ]

        missing_modules = []
        for module_path in modules:
            module_name, attribute = module_path.rsplit(".", 1)
            if importlib.util.find_spec(module_name) is None:
                missing_modules.append(module_path)
                continue

            # Try importing the specific attribute
            try:
                module = __import__(module_name, fromlist=[attribute])
                getattr(module, attribute)
            except (ImportError, AttributeError):
                missing_modules.append(module_path)

        if missing_modules:
            print(f"Missing modules: {', '.join(missing_modules)}")
            return False

        print("All modules imported successfully.")
        return True
    except ImportError as e:
        print(f"Import error: {e}")
        return False


def test_icon_loading():
    """Test that icon loading functions work."""
    print("Testing icon loading...")

    try:
        from src.philocr.ui.icon_loader import get_splash_image_path

        splash_path = get_splash_image_path()
        if splash_path:
            print(f"Splash screen found at: {splash_path}")
        else:
            print("Splash screen not found, but fallback should work.")

        return True
    except (FileNotFoundError, OSError, ImportError) as e:
        print(f"Icon loading error: {e}")
        return False
    except Exception as e:
        # Catch unexpected errors but don't fail smoke test for them
        print(f"Unexpected icon loading error: {e}")
        return False


def run_smoke_tests():
    """Run all smoke tests and report results."""
    print("=" * 50)
    print("OJD OCR Processor - Smoke Tests")
    print("=" * 50)

    tests = {
        "Environment Loading": test_environment_loading,
        "Import Structure": test_import_structure,
        "Icon Loading": test_icon_loading,
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
        except (
            FileNotFoundError,
            OSError,
            ImportError,
            ValueError,
            AttributeError,
        ) as e:
            print(f"Test failed with expected exception: {type(e).__name__}: {e}")
            results[name] = False
            all_passed = False
        except Exception as e:
            # Catch unexpected errors - log but continue
            print(f"Test failed with unexpected exception: {type(e).__name__}: {e}")
            results[name] = False
            all_passed = False

    print("\n" + "=" * 50)
    print("Test Results:")
    for name, result in results.items():
        status = "PASSED" if result else "FAILED"
        print(f"{name}: {status}")

    print("\nOverall result:", "PASSED" if all_passed else "FAILED")

    return all_passed


if __name__ == "__main__":
    success = run_smoke_tests()
    sys.exit(0 if success else 1)
