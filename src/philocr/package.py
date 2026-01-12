#!/usr/bin/env python3
"""
Packaging script for the PhilOcr application.
This script prepares the application for packaging with PyInstaller.
"""

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)


def clean_project() -> None:
    """Clean up temporary and build files before packaging."""
    logger.info("package_cleanup_started")

    # Directories to clean
    clean_dirs = ["__pycache__", "build", "dist", ".pytest_cache"]

    # Files to clean
    clean_files = ["*.pyc", "*.pyo"]

    # Clean directories
    for dir_name in clean_dirs:
        for path in Path(".").rglob(dir_name):
            if path.is_dir():
                logger.debug("package_cleanup_removing_dir", path=str(path))
                shutil.rmtree(path, ignore_errors=True)

    # Clean files
    for pattern in clean_files:
        for path in Path(".").rglob(pattern):
            if path.is_file():
                logger.debug("package_cleanup_removing_file", path=str(path))
                path.unlink()
    logger.info("package_cleanup_completed")


def check_requirements() -> bool:
    """
    Check if all requirements are installed.

    Returns:
        bool: True if requirements check/installation succeeded, False otherwise
    """
    logger.info("package_requirements_check_started")
    try:
        # Use a more direct approach to install requirements
        import subprocess
        import sys

        # Install each requirement individually to avoid pip module issues
        with open("requirements.txt") as f:
            requirements = [
                line.strip() for line in f if line.strip() and not line.startswith("#")
            ]

        failed_requirements = []
        for req in requirements:
            logger.info("package_requirement_installing", requirement=req)
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", req],
                check=False,  # Don't fail if one requirement has issues
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                failed_requirements.append(req)
                logger.warning(
                    "requirement_install_failed",
                    requirement=req,
                    error=result.stderr,
                )

        if failed_requirements:
            logger.error(
                "requirements_install_multiple_failed",
                failed_count=len(failed_requirements),
                failed_requirements=failed_requirements,
            )
            logger.warning(
                "requirements_install_warning",
                failed_count=len(failed_requirements),
            )
            return False

        logger.info("requirements_check_completed", success=True)
        logger.info("requirements_check_completed", success=True)
        return True
    except FileNotFoundError:
        error_msg = "requirements.txt file not found"
        logger.error(
            "requirements_file_not_found",
            error=error_msg,
        )
        return False
    except Exception as e:
        logger.error(
            "requirements_check_failed",
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True,
        )
        from philocr.utils.logging_config import flush_loggers

        flush_loggers()
        raise RuntimeError(f"CRITICAL: Requirements check failed - {e}") from e


def build_executable() -> bool:
    """Build the executable using PyInstaller."""
    logger.info("package_build_started")

    # First verify that all files exist
    env_file = Path("ENV.local")
    if not env_file.exists():
        logger.error("package_build_env_file_missing", env_file=str(env_file))
        return False

    creds_file = Path(os.getenv("GOOGLE_APPLICATION_CREDENTIALS", ""))
    if not creds_file.exists():
        logger.error(
            "package_build_creds_file_missing",
            creds_file=str(creds_file),
        )
        return False

    # Make sure we have the spec file
    spec_file = Path("PhilOcr.spec")
    if not spec_file.exists():
        logger.info("package_spec_file_creating")
        _ = create_pyinstaller_spec()

    # Run PyInstaller
    logger.info("package_pyinstaller_running")

    cmd = [sys.executable, "-m", "PyInstaller", "PhilOcr.spec"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)

    if result.returncode != 0:
        logger.error(
            "package_pyinstaller_failed",
            exit_code=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
        )
        return False

    logger.info("package_pyinstaller_completed")

    # Verify the output
    if platform.system() == "Darwin":  # macOS
        app_path = Path("dist/PhilOcr.app")
        if not app_path.exists():
            logger.error("package_bundle_not_found", app_path=str(app_path))
            return False
        logger.info("package_bundle_created", app_path=str(app_path))
    else:  # Windows or Linux
        exe_suffix = ".exe" if platform.system() == "Windows" else ""
        exe_path = Path(f"dist/PhilOcr/PhilOcr{exe_suffix}")
        if not exe_path.exists():
            logger.error("package_exe_not_found", exe_path=str(exe_path))
            return False
        logger.info("package_exe_created", exe_path=str(exe_path))

    return True


def create_pyinstaller_spec() -> bool:
    """Create a PyInstaller spec file for the application."""
    logger.info("package_spec_file_creating")

    # Find credentials path
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")

    # Find an appropriate icon file
    # For macOS .app bundles, we need .icns files, but SVG can be used for QIcon
    icon_path = ""
    if os.path.exists("philocr_icons"):
        for icon_file in os.listdir("philocr_icons"):
            # For macOS, prefer .icns files if they exist
            if (
                platform.system() == "Darwin"
                and icon_file.endswith(".icns")
                or platform.system() == "Windows"
                and icon_file.endswith(".ico")
            ):
                icon_path = os.path.join("philocr_icons", icon_file)
                break

        # If no .icns/.ico found, try SVG files (for QIcon, not bundle icon)
        if not icon_path and os.listdir("philocr_icons"):
            for icon_file in os.listdir("philocr_icons"):
                if icon_file.endswith((".svg", ".png")):
                    # Use app-icon-512.svg as default if available
                    if icon_file == "app-icon-512.svg":
                        icon_path = os.path.join("philocr_icons", icon_file)
                        break
                    if not icon_path:
                        icon_path = os.path.join("philocr_icons", icon_file)

    # Create the spec file content
    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-
import platform

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('ENV.local', '.'),
        ('{credentials_path}', '.'),
        ('philocr_icons', 'philocr_icons'),
        ('README.md', '.'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=['balanced-with-batching.py', 'env-loader-code.py', 'test_document_ai.py', 'test_icon_loading.py'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PhilOcr',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="{icon_path}",
)

if platform.system() == "Darwin":
    app = BUNDLE(
        exe,
        name='PhilOcr.app',
        icon="{icon_path}",
        bundle_identifier=None,
        info_plist={{
            'NSHighResolutionCapable': 'True',
            'CFBundleName': 'PhilOcr',
            'CFBundleDisplayName': 'PhilOcr',
            'CFBundleGetInfoString': 'Extract text from PDFs using Google Document AI',
            'CFBundleVersion': '1.0.0',
            'CFBundleShortVersionString': '1.0.0',
            'NSHumanReadableCopyright': 'Copyright © 2025'
        }},
    )
"""

    spec_file_path = "PhilOcr.spec"
    with open(spec_file_path, "w") as f:
        _ = f.write(spec_content)

    logger.info("package_spec_file_created", spec_file=spec_file_path)
    return True


def create_readme() -> bool:
    """Create a README file for the packaged application."""
    logger.info("package_readme_creating")

    readme_content = """# PhilOcr

## Overview
PhilOcr is a desktop application that processes scanned PDFs of ancient Greek texts using Google's Document AI service.

## Features
- Process individual PDF files or batch process multiple files
- Extracts text using advanced OCR technology
- Handles multi-page documents automatically
- Export extracted text to files

## Installation
No installation is required. Simply double-click the application to run it.

## Usage
1. Launch the application
2. Click "Select File" to choose a single PDF or "Batch Process" for multiple PDFs
3. Wait for processing to complete
4. Review the extracted text
5. Optionally save the text to a file

## Known Limitations
- Large PDFs (over 15 pages) are split into smaller chunks for processing
- Processing is limited by Google Cloud API rate limits

## Troubleshooting
If you encounter issues with Google Cloud authentication:
1. Click the "About" button in the application
2. Check that your credentials are valid
3. If needed, use the credentials dialog to update your settings

## Version History
- 1.0.0: Initial release
"""

    readme_path = "packaged_README.md"
    with open(readme_path, "w") as f:
        _ = f.write(readme_content)

    logger.info("package_readme_created", readme_file=readme_path)
    return True


def main() -> None:
    """Main packaging function."""
    logger.info("package_main_started")

    # Clean the project
    clean_project()

    # Check requirements
    if not check_requirements():
        logger.warning("package_requirements_check_failed_continuing")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != "y":
            logger.info("package_build_cancelled")
            sys.exit(1)

    # Create a packaged README
    _ = create_readme()

    # Build the executable
    if build_executable():
        logger.info("package_build_completed")

        # Determine the path to the packaged application
        if platform.system() == "Darwin":  # macOS
            app_path = "dist/PhilOcr.app"
            logger.info(
                "package_build_success_macos",
                app_path=os.path.abspath(app_path),
            )
        else:  # Windows or Linux
            exe_suffix = ".exe" if platform.system() == "Windows" else ""
            exe_path = f"dist/PhilOcr/PhilOcr{exe_suffix}"
            logger.info(
                "package_build_success_other",
                exe_path=os.path.abspath(exe_path),
                platform=platform.system(),
            )
    else:
        logger.error("package_build_failed")


if __name__ == "__main__":
    main()
