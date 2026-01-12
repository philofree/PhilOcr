# MainWindow Class Analysis

## Current State

- **Lines of Code**: 642 (limit: 300) - **2.14× over limit**
- **Methods**: 29 (limit: 10) - **2.9× over limit**
- **Cohesion**: 0.26 (minimum: 0.8) - **Very low cohesion**
- **Status**: CRITICAL - All three metrics severely violated

## Responsibility Analysis

The MainWindow class has **too many responsibilities**, violating the Single Responsibility Principle. Here's a breakdown of what it does:

### 1. Core Window Management (~30 lines)
- Window initialization and configuration
- UI composition setup
- Manager initialization (factory pattern)

### 2. UI State Management (~10 methods)
- `update_status()` - Status message updates
- `update_text()` - Text content updates
- `show_error()` - Error dialog display
- `clear_results()` - UI state reset
- `processing_finished()` - Processing completion handling

### 3. Dialog Management (~2 methods)
- `show_settings_dialog()` - Settings dialog
- `show_about_dialog()` - About dialog

### 4. File Operations (~7 methods)
- `select_file()` - Single file selection
- `select_multiple_files()` - Batch file selection
- `load_json()` - JSON file loading
- `save_text()` - Text file saving
- `save_json()` - JSON file saving
- `save_html()` - HTML file saving
- `save_markdown()` - Markdown file saving

### 5. Template Visualization (~5 methods, ~200 lines)
- `_handle_template_ready()` - Template ready handler
- `_show_template_image_menu()` - Context menu for template images
- `_save_template_image()` - Save template visualization
- `_open_template_image_window()` - Open template in separate window
- `_format_template_preview()` - Format template preview text

**This is a MAJOR violation** - Template visualization should be a separate handler class.

### 6. Scan Area Management (~3 methods, ~90 lines)
- `_show_scan_area_viewer()` - Display scan area viewer
- `_on_scan_areas_saved()` - Handle scan areas saved signal
- `_on_process_requested()` - Handle process requested signal

**This could be extracted** into a ScanAreaManager.

### 7. Progress Handling (~2 methods)
- `_handle_stage_progress()` - Stage progress updates
- `_handle_overall_progress()` - Overall progress updates

### 8. Processing Coordination (~3 methods)
- `json_data_ready()` - JSON data ready handler
- `_get_processing_mode()` - Get processing mode
- `debug_markdown()` - Debug markdown conversion

### 9. Lifecycle Management (~1 method)
- `closeEvent()` - Window close handling

## Refactoring Recommendations

### Priority 1: Extract Template Visualization Handler (Largest Blob)

**Extract to**: `src/philocr/ui/template_preview_handler.py`

**Methods to extract**:
- `_handle_template_ready()` (60 lines)
- `_show_template_image_menu()` (21 lines)
- `_save_template_image()` (37 lines)
- `_open_template_image_window()` (54 lines)
- `_format_template_preview()` (19 lines)

**Estimated reduction**: ~190 lines, 5 methods

**New class structure**:
```python
class TemplatePreviewHandler:
    """Handles template visualization and preview operations."""
    
    def __init__(
        self,
        template_preview_text: QTextEdit,
        template_preview_image: QLabel,
        parent_widget: QWidget,
        on_status_update: Callable[[str], None],
        on_error: Callable[[str], None],
    ) -> None:
        ...
    
    def handle_template_ready(self, template_dict: dict[str, Any]) -> None:
        ...
    
    def _show_image_menu(self, pos: QPoint, image_label: QLabel) -> None:
        ...
    
    def _save_image(self, image_path: str) -> None:
        ...
    
    def _open_image_window(self, image_path: str) -> None:
        ...
    
    def _format_preview_text(self, template_dict: dict[str, Any]) -> str:
        ...
```

### Priority 2: Extract Scan Area Manager

**Extract to**: `src/philocr/ui/scan_area_manager.py`

**Methods to extract**:
- `_show_scan_area_viewer()` (44 lines)
- `_on_scan_areas_saved()` (11 lines)
- `_on_process_requested()` (30 lines)

**Estimated reduction**: ~85 lines, 3 methods

**New class structure**:
```python
class ScanAreaManager:
    """Manages scan area viewer and processing coordination."""
    
    def __init__(
        self,
        scan_area_tab: QWidget,
        tab_widget: QTabWidget,
        worker_manager: WorkerManager,
        on_status_update: Callable[[str], None],
        on_error: Callable[[str], None],
    ) -> None:
        ...
    
    def show_scan_area_viewer(self, pdf_path: str) -> None:
        ...
    
    def on_scan_areas_saved(self, scan_areas: ManualScanAreas) -> None:
        ...
    
    def on_process_requested(self, scan_areas: ManualScanAreas, pdf_path: str) -> None:
        ...
```

### Priority 3: Consolidate File Operation Delegates

The MainWindow already delegates file operations to `file_operations_manager`, but the methods are still thin wrappers. These are fine to keep, but we can verify they're truly just delegation.

**Current methods** (all < 5 lines):
- `select_file()` - delegates to file_operations_manager
- `select_multiple_files()` - delegates to file_operations_manager
- `load_json()` - delegates to file_operations_manager
- `save_text()` - delegates to file_operations_manager
- `save_json()` - delegates to file_operations_manager
- `save_html()` - delegates to file_operations_manager
- `save_markdown()` - delegates to file_operations_manager

**Status**: These are acceptable thin delegation methods. They maintain UI layer purity.

### Priority 4: Extract Progress Handler

**Extract to**: Integrate with MainWindowCoordinator or create ProgressHandler

**Methods to extract**:
- `_handle_stage_progress()` (12 lines)
- `_handle_overall_progress()` (12 lines)

**Estimated reduction**: ~24 lines, 2 methods

## After Refactoring Projections

### Size Reduction

| Component | Lines Removed | Methods Removed |
|-----------|---------------|-----------------|
| Template Preview Handler | ~190 | 5 |
| Scan Area Manager | ~85 | 3 |
| Progress Handler | ~24 | 2 |
| **Total Reduction** | **~299** | **10** |

### Projected Final State

- **Lines of Code**: ~343 (target: <300) - **Still over limit, but much better**
- **Methods**: ~19 (target: ≤10) - **Still over limit**
- **Cohesion**: Should improve significantly (target: ≥0.8)

### Additional Refactoring Needed

After Priority 1-4, we still need to:

1. **Further reduce methods** (target: ≤10):
   - Consider if some file operation methods can be consolidated
   - Consider if dialog methods can be consolidated
   - Verify all methods are truly necessary

2. **Further reduce size** (target: ≤300 lines):
   - Review `__init__` method (145 lines) - could this be split?
   - Look for other extraction opportunities

3. **Improve cohesion**:
   - With extracted handlers, cohesion should improve
   - Verify that remaining methods share a cohesive purpose

## Implementation Strategy

### Phase 1: Extract Template Preview Handler
1. Create `src/philocr/ui/template_preview_handler.py`
2. Move template-related methods
3. Update MainWindow to use handler
4. Test template visualization functionality

### Phase 2: Extract Scan Area Manager
1. Create `src/philocr/ui/scan_area_manager.py`
2. Move scan area-related methods
3. Update MainWindow to use manager
4. Test scan area functionality

### Phase 3: Extract Progress Handler
1. Integrate with MainWindowCoordinator or create new handler
2. Move progress-related methods
3. Update MainWindow
4. Test progress updates

### Phase 4: Review and Optimize
1. Re-run God Class guardian
2. Identify remaining issues
3. Additional refactoring if needed

## Notes

- The MainWindow already uses many manager classes (good separation), but still has too much logic
- Template visualization is the biggest single responsibility (190 lines)
- Scan area management is the second biggest (85 lines)
- Most file operations are already delegated (good), just thin wrappers remain
- The `__init__` method is large (145 lines) but mostly manager initialization (acceptable)
