#!/usr/bin/env python3
"""
Test runner script for OCR Fresh project.
Provides convenient commands for running different test suites.
"""

import argparse
import subprocess
import sys


def run_command(cmd: list[str], check: bool = True) -> int:
    """Run a command and return the exit code.

    Args:
        cmd: List of command arguments to execute
        check: If True, raise CalledProcessError on non-zero exit code

    Returns:
        Exit code of the executed command
    """
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=check)
    return result.returncode


def main() -> int:
    """Main entry point for the test runner script.

    Parses command-line arguments and executes the appropriate test suite.

    Returns:
        Exit code: 0 for success, non-zero for failure
    """
    parser = argparse.ArgumentParser(description="Run tests for OCR Fresh")
    parser.add_argument(
        "suite",
        nargs="?",
        default="all",
        choices=["all", "unit", "integration", "coverage", "specific"],
        help="Test suite to run (default: all)",
    )
    parser.add_argument(
        "-f",
        "--file",
        help="Specific test file to run (use with 'specific' suite)",
    )
    parser.add_argument(
        "-k",
        "--keyword",
        help="Run tests matching the given keyword expression",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose output",
    )
    parser.add_argument(
        "--no-cov",
        action="store_true",
        help="Disable coverage reporting",
    )
    parser.add_argument(
        "--html",
        action="store_true",
        help="Generate HTML coverage report",
    )

    args = parser.parse_args()

    # Base pytest command
    cmd = ["pytest"]

    # Add verbosity
    if args.verbose:
        cmd.append("-vv")
    else:
        cmd.append("-v")

    # Handle different test suites
    if args.suite == "unit":
        cmd.extend(["-m", "unit"])
    elif args.suite == "integration":
        cmd.extend(["-m", "integration"])
    elif args.suite == "specific":
        if not args.file:
            print("Error: --file required when using 'specific' suite")
            return 1
        cmd.append(args.file)

    # Add keyword filter if specified
    if args.keyword:
        cmd.extend(["-k", args.keyword])

    # Add coverage options
    if not args.no_cov and args.suite != "specific":
        cmd.extend(
            [
                "--cov=src/philocr",
                "--cov-report=term-missing",
            ]
        )
        if args.html:
            cmd.append("--cov-report=html")

    # Run the tests
    return run_command(cmd, check=False)


if __name__ == "__main__":
    sys.exit(main())
