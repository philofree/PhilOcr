#!/usr/bin/env python3
"""
Run all tests for the OJD OCR Processor.
This script discovers and runs all test scripts in the tests directory.
"""

import os
import subprocess
import sys
from pathlib import Path

# Set working directory to the project root
os.chdir(Path(__file__).parent.parent)


def discover_test_scripts() -> list[str]:
    """
    Discover all test scripts in the tests directory.

    Returns:
        List of paths to test scripts
    """
    tests_dir = Path("tests")
    test_scripts = []

    for file in tests_dir.glob("test_*.py"):
        if file.name != os.path.basename(__file__):
            test_scripts.append(str(file))

    # Add the smoke test
    smoke_test = tests_dir / "smoke_test.py"
    if smoke_test.exists() and str(smoke_test) not in test_scripts:
        test_scripts.append(str(smoke_test))

    return sorted(test_scripts)


def run_test_script(script_path: str) -> bool:
    """
    Run a test script and return whether it passed.

    Args:
        script_path: Path to the test script

    Returns:
        True if the test passed, False otherwise
    """
    print(f"\n{'=' * 60}")
    print(f"Running {os.path.basename(script_path)}")
    print(f"{'=' * 60}")

    try:
        result = subprocess.run(
            [sys.executable, script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )

        # Print the output
        print(result.stdout)

        return result.returncode == 0
    except Exception as e:
        print(f"Error running {script_path}: {e}")
        return False


def run_all_tests() -> bool:
    """
    Run all test scripts and return whether they all passed.

    Returns:
        True if all tests passed, False otherwise
    """
    print("=" * 60)
    print("OJD OCR Processor - Running All Tests")
    print("=" * 60)

    test_scripts = discover_test_scripts()

    if not test_scripts:
        print("No test scripts found.")
        return False

    print(f"Found {len(test_scripts)} test scripts:")
    for script in test_scripts:
        print(f"  - {os.path.basename(script)}")

    # Run the tests
    results = {}
    all_passed = True

    for script in test_scripts:
        script_name = os.path.basename(script)
        passed = run_test_script(script)
        results[script_name] = passed

        if not passed:
            all_passed = False

    # Print the summary
    print("\n" + "=" * 60)
    print("Test Summary:")
    for script_name, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        print(f"{script_name}: {status}")

    print("\nOverall result:", "PASSED" if all_passed else "FAILED")

    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
