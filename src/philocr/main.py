import os
import sys
import time
from pathlib import Path

# Add src directory to sys.path to allow absolute imports of philocr
# When running as python -m src.philocr.main, Python adds the project root
# to sys.path, but philocr is located at src/philocr/, so we need
# src/ in sys.path for absolute imports to work.
project_root = Path(__file__).resolve().parent.parent.parent
src_dir = project_root / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from PyQt6.QtCore import QCoreApplication, QLibraryInfo, Qt  # noqa: E402
from PyQt6.QtGui import QFont, QPixmap  # noqa: E402
from PyQt6.QtWidgets import (  # noqa: E402
    QApplication,
    QLabel,
    QSplashScreen,
    QVBoxLayout,
    QWidget,
)

# Imports must come after sys.path manipulation (noqa: E402)
from philocr.ui.icon_loader import (  # noqa: E402
    get_splash_image_path,
    load_application_icon,
)
from philocr.ui.main_window import MainWindow  # noqa: E402
from philocr.utils.env_loader import load_embedded_env  # noqa: E402
from philocr.utils.env_utils import load_env_file  # noqa: E402
from philocr.utils.logging_config import configure_logging, get_logger  # noqa: E402

# Application version information
APP_VERSION = "2.0.0"
APP_NAME = "PhilOcr"
APP_COPYRIGHT = "© 2023"
APP_DESCRIPTION = "Processing Ancient Greek Texts - Part of the Philofree Project"


def setup_qt_plugins() -> None:
    """Ensure Qt uses the correct plugin directory for platform plugins."""
    logger = get_logger(__name__)

    # Clear any inherited Qt environment variables to avoid conflicts
    _ = os.environ.pop("QT_PLUGIN_PATH", None)
    _ = os.environ.pop("QT_QPA_PLATFORM_PLUGIN_PATH", None)

    # Determine the plugin directory that PyQt6 expects
    plugin_dir = QLibraryInfo.path(QLibraryInfo.LibraryPath.PluginsPath)
    logger.info(
        "qt_plugin_path_configured",
        plugin_dir=str(plugin_dir),
    )

    # Force Qt to use only this plugin directory
    QCoreApplication.setLibraryPaths([plugin_dir])

    # On macOS, explicitly set the platform to cocoa
    if sys.platform == "darwin":
        logger.info(
            "qt_platform_set_macos",
            platform="cocoa",
        )
        os.environ["QT_QPA_PLATFORM"] = "cocoa"

    # Log the resulting paths for debugging
    library_paths = [str(p) for p in QCoreApplication.libraryPaths()]
    logger.info(
        "qt_library_paths_configured",
        library_paths=library_paths,
    )


def _setup_macos_bundle_properties() -> None:
    """Set macOS bundle properties for proper menu bar display.

    This ensures the menu bar shows the app name instead of "python".
    """
    if sys.platform == "darwin":  # macOS
        # macOS bundle environment variables use specific naming (noqa: SIM112)
        os.environ["CFBundleName"] = APP_NAME  # noqa: SIM112
        os.environ["CFBundleDisplayName"] = APP_NAME  # noqa: SIM112
        os.environ["CFBundleIdentifier"] = (  # noqa: SIM112
            f"com.philofree.{APP_NAME.lower()}"
        )
        os.environ["CFBundleVersion"] = APP_VERSION  # noqa: SIM112
        os.environ["CFBundleShortVersionString"] = APP_VERSION  # noqa: SIM112

        if sys.argv and len(sys.argv) > 0:
            sys.argv[0] = APP_NAME


def _create_splash_screen(_app: QApplication) -> QSplashScreen:
    """Create and configure the application splash screen.

    Args:
        _app: QApplication instance (unused but required by interface)

    Returns:
        Configured splash screen widget
    """
    splash_image_path = get_splash_image_path()

    if not splash_image_path:
        # Create a simple splash screen
        pixmap = QPixmap(400, 300)
        pixmap.fill(Qt.GlobalColor.white)
        splash = QSplashScreen(pixmap)

        # Create a widget to hold the splash content
        splash_widget = QWidget()
        splash_layout = QVBoxLayout(splash_widget)

        splash_title = QLabel(f"{APP_NAME}")
        splash_title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        splash_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        splash_layout.addWidget(splash_title)

        splash_version = QLabel(f"v{APP_VERSION}")
        splash_version.setFont(QFont("Arial", 14))
        splash_version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        splash_layout.addWidget(splash_version)

        splash_loading = QLabel("Loading application...")
        splash_loading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        splash_layout.addWidget(splash_loading)

        # Render the widget to the pixmap
        splash_widget.setFixedSize(400, 300)
        splash_widget.setStyleSheet("background-color: white;")
        splash_widget.render(pixmap)
    else:
        splash = QSplashScreen(QPixmap(splash_image_path))

    return splash


def _initialize_application() -> QApplication:
    """Initialize Qt application with proper configuration.

    Returns:
        Configured QApplication instance
    """
    _setup_macos_bundle_properties()

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName("Philofree")
    app.setOrganizationDomain("philofree.com")

    _ = load_application_icon(app)

    logger = get_logger(__name__)
    logger.info(
        "qt_application_created",
        app_name=app.applicationName(),
        app_version=app.applicationVersion(),
    )

    return app


def run_app() -> None:
    """Main function to run the application."""
    # Configure structured logging FIRST (before any other imports use logging)
    configure_logging(json_logs=None, log_level="INFO")
    logger = get_logger(__name__)

    # Load environment variables
    _ = load_env_file()
    load_embedded_env()

    logger.info(
        "application_starting",
        app_name=APP_NAME,
        app_version=APP_VERSION,
    )

    # Setup Qt plugins
    _setup_qt_plugins()

    # Initialize Qt application
    app = _initialize_application()

    # Create and show splash screen
    splash = _create_splash_screen(app)
    splash.show()
    app.processEvents()

    # Display splash messages
    splash.showMessage(
        "Checking configuration...",
        Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter,
    )
    app.processEvents()
    time.sleep(1)

    splash.showMessage(
        "Initializing UI...",
        Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter,
    )
    app.processEvents()

    # Create main window
    main_window = MainWindow(APP_VERSION, APP_NAME, APP_COPYRIGHT, APP_DESCRIPTION)

    # Finish splash and show main window
    time.sleep(1)
    splash.finish(main_window)
    main_window.show()

    # Run the application
    sys.exit(app.exec())


def _setup_qt_plugins() -> None:
    """Setup Qt plugins with proper error handling."""
    logger = get_logger(__name__)
    logger.info("qt_plugins_setup_starting")

    try:
        setup_qt_plugins()
    except (OSError, ImportError, RuntimeError) as e:
        logger.error(
            "qt_plugins_setup_failed",
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True,
        )
        from philocr.utils.logging_config import flush_loggers

        flush_loggers()
        raise
    except Exception as e:
        logger.error(
            "qt_plugins_setup_unexpected_error",
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True,
        )
        from philocr.utils.logging_config import flush_loggers

        flush_loggers()
        raise RuntimeError(f"CRITICAL: Qt plugins setup failed - {e}") from e


if __name__ == "__main__":
    run_app()
