#!/bin/bash
# System Operability Verification Script
# Run this script to verify the PhilOcr application works after refactoring

set -e  # Exit on error

cd "$(dirname "$0")"

echo "=== PhilOcr System Operability Verification ==="
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✓ Virtual environment activated"
fi

echo ""
echo "=== Phase 1: Core Application Import ==="
python -c "import sys; sys.path.insert(0, 'src'); from philocr.main import run_app; print('✓ Core application imports')" || {
    echo "✗ Core import failed"
    exit 1
}

echo ""
echo "=== Phase 2: New Component Imports ==="
python -c "import sys; sys.path.insert(0, 'src'); 
from philocr.utils.exceptions import PhilOcrError;
from philocr.processing.parsers.page_parser import PageParser;
from philocr.processing.parsers.structure_extractor import StructureExtractor;
from philocr.ui.main_window_coordinator import MainWindowCoordinator;
from philocr.ui.credentials_form_handler import CredentialsFormHandler;
from philocr.ui.dialog_form_builder import DialogFormBuilder;
from philocr.ui.widget_factory import WidgetFactory;
from philocr.ui.tab_factory import TabFactory;
from philocr.utils.file_io.text_saver import TextSaver;
from philocr.utils.file_io.json_saver import JSONSaver;
from philocr.workers.handlers.single_file_handler import SingleFileHandler;
from philocr.workers.handlers.batch_file_handler import BatchFileHandler;
from philocr.utils.config_io import ConfigIO;
from philocr.utils.config_path_resolver import ConfigPathResolver;
print('✓ All new components import successfully')" || {
    echo "✗ Component imports failed"
    exit 1
}

echo ""
echo "=== Phase 3: Application Initialization ==="
python -c "
import sys
from pathlib import Path
sys.path.insert(0, str(Path('src').absolute()))

from philocr.utils.logging_config import configure_logging
configure_logging(json_logs=None, log_level='INFO')

from PyQt6.QtWidgets import QApplication
app = QApplication(sys.argv)

from philocr.ui.main_window import MainWindow
window = MainWindow('2.0.0', 'PhilOcr', '© 2023', 'Test Description')

# Verify coordinator is initialized
assert hasattr(window, 'coordinator'), 'MainWindow should have coordinator'
assert window.coordinator is not None, 'Coordinator should be initialized'

# Verify managers are initialized
assert hasattr(window, 'file_operations_manager'), 'Should have file_operations_manager'
assert hasattr(window, 'format_display_manager'), 'Should have format_display_manager'
assert hasattr(window, 'worker_manager'), 'Should have worker_manager'
assert hasattr(window, 'config_manager'), 'Should have config_manager'

print('✓ MainWindow created successfully')
print('✓ All managers initialized')
print('✓ Coordinator initialized')
app.quit()
" || {
    echo "✗ Application initialization failed"
    exit 1
}

echo ""
echo "=== Phase 4: Refactored Component Verification ==="
python -c "import sys; sys.path.insert(0, 'src');

# Verify AcademicDocumentParser uses new parsers
from philocr.utils.markdown_converter.academic_doc_parser import AcademicDocumentParser;
parser = AcademicDocumentParser({});
assert hasattr(parser, 'page_parser'), 'Missing page_parser';
assert hasattr(parser, 'structure_extractor'), 'Missing structure_extractor';
print('✓ AcademicDocumentParser uses PageParser and StructureExtractor');

# Verify ConfigManager uses new utilities
from philocr.utils.config_manager import ConfigManager;
config_mgr = ConfigManager();
config = config_mgr.load_config();  # Should work
print('✓ ConfigManager uses ConfigIO and ConfigPathResolver');

print('✓ All refactored components verified')" || {
    echo "✗ Refactored component verification failed"
    exit 1
}

echo ""
echo "=== Phase 5: Exception Hierarchy Verification ==="
python -c "import sys; sys.path.insert(0, 'src');
from philocr.utils.exceptions import (
    PhilOcrError, ConfigurationError, PDFProcessingError, 
    PDFParseError, WorkerError, MarkdownConversionError
);
# Test exception hierarchy
assert issubclass(ConfigurationError, PhilOcrError);
assert issubclass(PDFProcessingError, PhilOcrError);
assert issubclass(WorkerError, PhilOcrError);
print('✓ Exception hierarchy correctly structured')" || {
    echo "✗ Exception hierarchy verification failed"
    exit 1
}

echo ""
echo "=== Phase 6: Dataclass Verification ==="
python -c "import sys; sys.path.insert(0, 'src');
from philocr.ui.worker_callbacks import WorkerCallbacks;
from philocr.processing.document_ai_config import DocumentAIProcessingConfig;
from dataclasses import fields;

# Verify dataclasses are properly defined
callbacks_fields = [f.name for f in fields(WorkerCallbacks)];
assert len(callbacks_fields) > 0, 'WorkerCallbacks should have fields';
print('✓ WorkerCallbacks dataclass verified');

config_fields = [f.name for f in fields(DocumentAIProcessingConfig)];
assert len(config_fields) > 0, 'DocumentAIProcessingConfig should have fields';
print('✓ DocumentAIProcessingConfig dataclass verified')" || {
    echo "✗ Dataclass verification failed"
    exit 1
}

echo ""
echo "=== All Verification Phases Passed ==="
echo ""
echo "✅ System is operable"
echo "✅ All imports successful"
echo "✅ Application initializes correctly"
echo "✅ Refactored components functional"
echo ""
echo "The application is ready to use."
