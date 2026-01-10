#!/usr/bin/env python3
"""
Pyright wrapper that separates errors and warnings into distinct sections.
This script runs pyright and formats output to clearly distinguish errors from warnings.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def run_pyright(files: list[str] | None = None) -> tuple[int, dict]:
    """Run pyright and return exit code and parsed JSON output."""
    cmd = ["pyright", "--outputjson"]
    # If files provided, add them; otherwise pyright will analyze the whole project
    if files:
        cmd.extend(files)
    else:
        # Run on src/ directory if no files specified
        cmd.append("src/")

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=False, cwd=Path.cwd()
        )
        output = json.loads(result.stdout) if result.stdout else {}
        return result.returncode, output
    except json.JSONDecodeError:
        # Fallback if output isn't valid JSON
        result = subprocess.run(
            ["pyright"] + (files or []),
            capture_output=True,
            text=True,
            check=False,
            cwd=Path.cwd(),
        )
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        return result.returncode, {}


def format_diagnostics(
    diagnostics: list[dict], severity: str
) -> tuple[list[str], dict[str, list[dict]]]:
    """Format diagnostics by severity, grouped by rule type.

    Returns:
        tuple: (formatted_lines, grouped_by_rule_dict)
    """
    filtered = [d for d in diagnostics if d.get("severity") == severity]
    if not filtered:
        return [], {}

    # Group by rule type
    grouped_by_rule: dict[str, list[dict]] = {}
    for diag in filtered:
        rule = diag.get("rule", "unknown")
        if rule not in grouped_by_rule:
            grouped_by_rule[rule] = []
        grouped_by_rule[rule].append(diag)

    # Format grouped diagnostics
    lines = []
    for rule in sorted(grouped_by_rule.keys()):
        rule_diagnostics = grouped_by_rule[rule]
        rule_count = len(rule_diagnostics)

        # Add header for this rule type (first one has no leading newline)
        if lines:
            lines.append("")
        lines.append(
            f"  [{rule}] ({rule_count} {'item' if rule_count == 1 else 'items'}):"
        )

        for diag in sorted(
            rule_diagnostics,
            key=lambda d: (
                d.get("file", ""),
                d.get("range", {}).get("start", {}).get("line", 0),
            ),
        ):
            file_path = diag.get("file", "unknown")
            range_info = diag.get("range", {})
            start = range_info.get("start", {})
            line = start.get("line", 0) + 1  # 0-based to 1-based
            col = start.get("character", 0) + 1  # 0-based to 1-based
            message = diag.get("message", "")

            lines.append(f"    {file_path}:{line}:{col} - {message}")

    return lines, grouped_by_rule


def main() -> int:
    """Main entry point."""
    # Get files from command line if provided
    # Pre-commit passes filenames as arguments
    files = sys.argv[1:] if len(sys.argv) > 1 else None

    # Filter out non-Python files if any were passed
    if files:
        files = [f for f in files if f.endswith(".py") or "/" in f or "\\" in f]
        if not files:
            # No Python files to check
            return 0

    exit_code, output = run_pyright(files)

    # Extract summary
    summary = output.get("summary", {})
    error_count = summary.get("errorCount", 0)
    warning_count = summary.get("warningCount", 0)
    info_count = summary.get("informationCount", 0)

    # Extract all diagnostics
    all_diagnostics = []
    for diag in output.get("generalDiagnostics", []):
        all_diagnostics.append(diag)

    # Separate and group errors and warnings by rule type
    error_lines, error_groups = format_diagnostics(all_diagnostics, "error")
    warning_lines, warning_groups = format_diagnostics(all_diagnostics, "warning")
    info_lines, info_groups = format_diagnostics(all_diagnostics, "information")

    # Print summary header
    print("\n" + "=" * 80)
    print("PYRIGHT TYPE CHECKING RESULTS")
    print("=" * 80)

    # Print ERRORS section - all errors grouped by kind
    if error_lines:
        print(f"\n❌ ERRORS ({error_count}):")
        print("-" * 80)
        for error_line in error_lines:
            print(error_line)
        print()
    else:
        print(f"\n✅ ERRORS: {error_count} (none)")

    # Print WARNINGS section - all warnings grouped by kind
    if warning_lines:
        print(f"\n⚠️  WARNINGS ({warning_count}):")
        print("-" * 80)
        for warning_line in warning_lines:
            print(warning_line)
        print()
    else:
        print(f"\n✅ WARNINGS: {warning_count} (none)")

    # Print INFO section (if any) - grouped by kind
    if info_lines:
        print(f"\nℹ️  INFORMATION ({info_count}):")
        print("-" * 80)
        for info_line in info_lines:
            print(info_line)
        print()

    # Print summary footer
    print("=" * 80)
    print(
        f"Summary: {error_count} errors, {warning_count} warnings, "
        f"{info_count} informations"
    )
    print("=" * 80 + "\n")

    # Exit with non-zero if there are errors
    # Warnings don't cause failure, only errors do
    return 1 if error_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
