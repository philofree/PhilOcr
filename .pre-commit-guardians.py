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
from typing import TYPE_CHECKING, Any

PROJECT_ROOT = Path(__file__).resolve().parent

# Add src directory to sys.path for philocr imports
src_dir = PROJECT_ROOT / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import configure_logging, get_logger
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
    except Exception as e:
        # Get logger here since function may be called before main() configures logging
        if not TYPE_CHECKING:
            from philocr.utils.logging_config import get_logger

            log = get_logger(__name__)
        else:
            log = logger  # type: ignore[used-before-def]
        log.warning(
            "summary_report_load_failed",
            error=str(e),
            error_type=type(e).__name__,
        )
        return None


def main() -> int:
    """Run guardians and check for critical issues."""
    # Configure structured logging FIRST (before any logging calls)
    if not TYPE_CHECKING:
        configure_logging(json_logs=None, log_level="INFO")
        logger = get_logger(__name__)
    else:
        # Type checking only - logger already declared above
        pass

    logger.info("guardian_precommit_started")

    if not GUARDIANS_RUNNER.exists():
        logger.error(
            "guardians_runner_not_found",
            path=str(GUARDIANS_RUNNER),
        )
        return 1

    # Import and run the guardian runner
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

    from guardians.run_all_guardians import (
        clean_old_reports,
        discover_guardians,
        generate_centralized_report,
        load_guardian_class,
        run_guardian,
    )

    # Clean old reports before running guardians
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    clean_old_reports(REPORTS_DIR)

    # Discover guardians
    guardians_dir = PROJECT_ROOT / "guardians"
    all_guardians = discover_guardians(guardians_dir)
    if not all_guardians:
        logger.warning("no_guardians_found")
        return 0

    logger.info(
        "guardian_precommit_check_starting",
        guardian_count=len(all_guardians),
    )

    # Run all guardians
    results = []
    for guardian_name, guardian_path in all_guardians:
        logger.debug("guardian_load_starting", guardian_name=guardian_name)
        guardian_class = load_guardian_class(guardian_path, guardian_name)
        if guardian_class is None:
            logger.warning(
                "guardian_load_failed",
                guardian_name=guardian_name,
            )
            continue

        logger.info("guardian_run_starting", guardian_name=guardian_name)
        result = run_guardian(
            guardian_class,
            guardian_name,
            PROJECT_ROOT,
            write_individual_logs=False,  # Don't clutter with logs in pre-commit
            log_dir=REPORTS_DIR,
        )
        logger.info(
            "guardian_run_completed",
            guardian_name=guardian_name,
            status=result.get("status"),
            issues_found=result.get("issues_found", 0),
            score=result.get("score", 0),
        )
        results.append(result)

    # Generate centralized report
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    generate_centralized_report(results, REPORTS_DIR)
    logger.info("summary_report_generated", reports_dir=str(REPORTS_DIR))

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

    # Calculate summary statistics
    total_issues = sum(r.get("issues_found", 0) for r in results)
    overall_score = (
        sum(r.get("score", 0) for r in results) / len(results) if results else 0
    )

    logger.info(
        "guardian_precommit_summary",
        overall_score=overall_score,
        total_issues=total_issues,
        blocker_issues=blocker_issues,
        critical_issues=critical_issues,
        high_issues=high_issues,
        failed_guardians=failed_guardians,
    )

    # Find the latest summary report
    if REPORTS_DIR.exists():
        summary_reports = sorted(REPORTS_DIR.glob("reports_summary_*.md"), reverse=True)
        if summary_reports:
            report_path = summary_reports[0].relative_to(PROJECT_ROOT)
            logger.info(
                "summary_report_path",
                report_path=str(report_path),
                reports_dir=str(REPORTS_DIR.relative_to(PROJECT_ROOT)),
            )

    # Fail commit if there are blocker or critical issues
    if blocker_issues > 0:
        logger.error(
            "guardian_precommit_blocked",
            reason="blocker_issues",
            blocker_issues=blocker_issues,
            message="Commit blocked: blocker issues found. Review guardian report.",
        )
        return 1

    if critical_issues > 0:
        logger.error(
            "guardian_precommit_blocked",
            reason="critical_issues",
            critical_issues=critical_issues,
            message="Commit blocked: critical issues found. Review guardian report.",
        )
        return 1

    if failed_guardians > 0:
        logger.error(
            "guardian_precommit_blocked",
            reason="failed_guardians",
            failed_guardians=failed_guardians,
            message="Commit blocked: guardians failed to run.",
        )
        return 1

    if total_issues > 0:
        logger.warning(
            "guardian_precommit_issues_found",
            total_issues=total_issues,
            message="Issues found (non-blocking). Review guardian report.",
        )

    logger.info("guardian_precommit_completed", message="All critical checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
