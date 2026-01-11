#!/usr/bin/env python3
"""
Cleanup script for the PhilOcr application.
This script removes redundant files and helps identify dead code.
"""

import argparse
import datetime
import os
import shutil
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)

# List of files that are redundant or should be removed before packaging
REDUNDANT_FILES: list[str] = [
    # Original files that have been refactored
    "main_pyqt.py",
    # Redundant helper scripts
    "env-loader-code.py",
    # Old versions/drafts
    "balanced-with-batching.py",
    # Temporary files
    ".DS_Store",
    # Planning documents that are no longer needed
    "PhilOcr_V.2.1_Refactoring.md",
    "VERSION2_DEVELOPMENT.md",
]

# Project files that should be kept
ESSENTIAL_FILES: list[str] = [
    "main.py",
    "package.py",
    "requirements.txt",
    "ENV.local",
    "README.md",
    "PhilOcr.spec",
    "ui",
    "utils",
    "processing",
    "workers",
    # Add any other essential files here
]


def list_redundant_files() -> list[tuple[str, float]]:
    """List redundant files in the project directory."""
    redundant_present: list[tuple[str, float]] = []

    for file in REDUNDANT_FILES:
        if os.path.exists(file):
            file_size = os.path.getsize(file) / 1024  # KB
            redundant_present.append((file, file_size))

    if redundant_present:
        logger.info(
            "redundant_files_found",
            file_count=len(redundant_present),
            files=[{"file": f, "size_kb": s} for f, s in redundant_present],
        )
    else:
        logger.info("redundant_files_none")

    return redundant_present


def remove_redundant_files(files_to_remove: list[tuple[str, float]]) -> None:
    """Remove the specified redundant files."""
    logger.info("cleanup_removal_started", file_count=len(files_to_remove))

    for file, _ in files_to_remove:
        try:
            if os.path.isdir(file):
                shutil.rmtree(file)
            else:
                os.remove(file)
            logger.info("file_removed", file_path=file)
        except FileNotFoundError:
            logger.warning(
                "file_not_found_removal",
                file_path=file,
                reason="may_have_been_already_removed",
            )
        except PermissionError as e:
            logger.error(
                "file_removal_permission_denied",
                file_path=file,
                error=str(e),
                exc_info=True,
            )
        except Exception as e:
            logger.error(
                "file_removal_failed",
                file_path=file,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            from philocr.utils.logging_config import flush_loggers

            flush_loggers()
            raise RuntimeError(
                f"CRITICAL: File removal failed for {file} - {e}"
            ) from e
    logger.info("cleanup_removal_completed")


def create_backup(files: list[tuple[str, float]]) -> str:
    """Create a backup of files before removing them."""
    backup_dir = "backup_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(backup_dir, exist_ok=True)

    logger.info("cleanup_backup_started", backup_dir=backup_dir, file_count=len(files))

    for file, _ in files:
        try:
            if os.path.isdir(file):
                _ = shutil.copytree(file, os.path.join(backup_dir, file))
            else:
                _ = shutil.copy2(file, backup_dir)
            logger.info("file_backed_up", file_path=file, backup_dir=backup_dir)
        except FileNotFoundError as e:
            logger.error(
                "file_not_found_backup",
                file_path=file,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            from philocr.utils.logging_config import flush_loggers

            flush_loggers()
            raise RuntimeError(
                f"CRITICAL: File not found for backup: {file} - {e}"
            ) from e
        except PermissionError as e:
            logger.error(
                "file_backup_permission_denied",
                file_path=file,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            from philocr.utils.logging_config import flush_loggers

            flush_loggers()
            raise RuntimeError(
                f"CRITICAL: Permission denied backing up file: {file} - {e}"
            ) from e
        except Exception as e:
            logger.error(
                "file_backup_failed",
                file_path=file,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            from philocr.utils.logging_config import flush_loggers

            flush_loggers()
            raise RuntimeError(f"CRITICAL: File backup failed for {file} - {e}") from e

    logger.info("cleanup_backup_completed", backup_dir=backup_dir)
    return backup_dir


def main() -> None:
    """Main cleanup function."""
    parser = argparse.ArgumentParser(
        description="Clean up redundant files in the project."
    )
    _ = parser.add_argument(
        "--remove",
        action="store_true",
        help="Remove redundant files (otherwise just list them)",
    )
    _ = parser.add_argument(
        "--backup", action="store_true", help="Create a backup before removing files"
    )
    args = parser.parse_args()

    # List redundant files
    redundant_files = list_redundant_files()

    if not redundant_files:
        return

    if args.remove:
        if args.backup:
            backup_dir = create_backup(redundant_files)
            logger.info("cleanup_backup_finished", backup_dir=backup_dir)

        remove_redundant_files(redundant_files)
        logger.info("cleanup_completed")
    else:
        logger.info("cleanup_dry_run", file_count=len(redundant_files))


if __name__ == "__main__":
    main()
