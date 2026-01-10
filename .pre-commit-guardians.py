#!/usr/bin/env python3
"""
Pre-commit hook wrapper for running guardians.

This script runs all guardians and fails the commit if critical issues are found.
Generates well-structured reports in Markdown and JSON formats.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent
GUARDIANS_RUNNER = PROJECT_ROOT / "guardians" / "run_all_guardians.py"
REPORTS_DIR = PROJECT_ROOT / "guardians" / "framework" / "core" / "logs"


def load_latest_summary_report() -> dict[str, Any] | None:
    """Load the most recent summary report JSON.

    Returns:
        Dictionary with report data or None if not found
    """
    if not REPORTS_DIR.exists():
        return None

    summary_reports = sorted(REPORTS_DIR.glob("reports_summary_*.json"), reverse=True)
    if not summary_reports:
        return None

    try:
        with open(summary_reports[0]) as f:
            return json.load(f)
    except Exception:
        return None


def main() -> int:
    """Run guardians and check for critical issues."""
    if not GUARDIANS_RUNNER.exists():
        print(
            f"Error: Guardians runner not found at {GUARDIANS_RUNNER}",
            file=sys.stderr,
        )
        return 1

    # Import and run the guardian runner
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

    from guardians.run_all_guardians import (
        discover_guardians,
        generate_centralized_report,
        load_guardian_class,
        run_guardian,
    )

    # Discover guardians
    guardians_dir = PROJECT_ROOT / "guardians"
    all_guardians = discover_guardians(guardians_dir)
    if not all_guardians:
        print("Warning: No guardians found!", file=sys.stderr)
        return 0

    print(f"\n{'='*70}")
    print(f"Running {len(all_guardians)} guardian(s) for pre-commit check...")
    print(f"{'='*70}")

    # Run all guardians
    results = []
    for guardian_name, guardian_path in all_guardians:
        guardian_class = load_guardian_class(guardian_path, guardian_name)
        if guardian_class is None:
            print(
                f"Warning: Could not load guardian {guardian_name}",
                file=sys.stderr,
            )
            continue

        result = run_guardian(
            guardian_class,
            guardian_name,
            PROJECT_ROOT,
            write_individual_logs=False,  # Don't clutter with logs in pre-commit
            log_dir=REPORTS_DIR,
        )
        results.append(result)

    # Generate centralized report
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    generate_centralized_report(results, REPORTS_DIR)

    # Load the generated summary report
    summary_report = load_latest_summary_report()

    # Check for critical issues
    critical_issues = 0
    blocker_issues = 0
    failed_guardians = 0
    high_issues = 0

    for result in results:
        if result.get("status") == "error":
            failed_guardians += 1
            continue

        issues = result.get("issues", [])
        for issue in issues:
            severity = issue.get("severity", "unknown")
            if severity == "blocker":
                blocker_issues += 1
            elif severity == "critical":
                critical_issues += 1
            elif severity == "high":
                high_issues += 1

    # Print summary
    total_issues = sum(r.get("issues_found", 0) for r in results)
    overall_score = (
        sum(r.get("score", 0) for r in results) / len(results) if results else 0
    )

    print(f"\n{'='*70}")
    print("GUARDIAN PRE-COMMIT CHECK SUMMARY")
    print(f"{'='*70}")
    print(f"Overall Score: {overall_score:.1f}/100")
    print(f"Total Issues: {total_issues}")
    print(f"  - Blocker: {blocker_issues}")
    print(f"  - Critical: {critical_issues}")
    print(f"  - High: {high_issues}")
    print(f"Failed Guardians: {failed_guardians}")
    print(f"{'='*70}")

    # Find the latest summary report
    if REPORTS_DIR.exists():
        summary_reports = sorted(REPORTS_DIR.glob("reports_summary_*.md"), reverse=True)
        if summary_reports:
            report_path = summary_reports[0].relative_to(PROJECT_ROOT)
            print(f"\n📄 Full report: {report_path}")
            print(f"   Report directory: {REPORTS_DIR.relative_to(PROJECT_ROOT)}")

    # Fail commit if there are blocker or critical issues
    if blocker_issues > 0:
        print(
            f"\n❌ Commit blocked: {blocker_issues} blocker issue(s) found!",
            file=sys.stderr,
        )
        print(
            "   Review the guardian report and fix blocker issues before committing.",
            file=sys.stderr,
        )
        return 1

    if critical_issues > 0:
        print(
            f"\n❌ Commit blocked: {critical_issues} critical issue(s) found!",
            file=sys.stderr,
        )
        print(
            "   Review the guardian report and fix critical issues before committing.",
            file=sys.stderr,
        )
        return 1

    if failed_guardians > 0:
        print(
            f"\n❌ Commit blocked: {failed_guardians} guardian(s) failed to run!",
            file=sys.stderr,
        )
        return 1

    if total_issues > 0:
        print(f"\n⚠️  Warning: {total_issues} issue(s) found (non-blocking)")
        print("   Review the guardian report and address issues when possible.")

    print("\n✅ All critical checks passed! Proceeding with commit...")
    return 0


if __name__ == "__main__":
    sys.exit(main())
