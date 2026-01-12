---
name: MainWindow Refactoring Plan
overview: Refactor MainWindow class to extract TemplatePreviewHandler, ScanAreaManager, and ProgressHandler, reducing size from 642 lines to ~350 lines and methods from 29 to ~19, while detecting and removing dead code.
todos:
  - id: extract_template_preview_handler
    content: Create TemplatePreviewHandler class and extract template visualization methods from MainWindow (~190 lines, 5 methods)
    status: completed
  - id: extract_scan_area_manager
    content: Create ScanAreaManager class and extract scan area management methods from MainWindow (~85 lines, 3 methods)
    status: completed
  - id: extract_progress_handler
    content: Extract progress handling methods to MainWindowCoordinator or ProgressHandler (~24 lines, 2 methods)
    status: completed
  - id: dead_code_detection
    content: Detect and document/remove dead code (template preview UI elements, unused imports, unused methods)
    status: completed
  - id: verify_refactoring
    content: Run God Class guardian and verify improvements, run tests to ensure no regressions
    status: completed
---

# MainWindow Refactoring Plan

## Current State Analysis

- **Lines**: 642 (limit: 300) - 2.14× over limit
- **Methods**: 29 (limit: 10) - 2.9× over limit  
- **Cohesion**: 0.26 (minimum: 0.8) - Very low cohesion
- **Status**: CRITICAL violations on all three metrics

## Refactoring Strategy

Extract three major responsibility groups into separate handler classes:

1. Template Preview Handler (~190 lines, 5 methods)
2. Scan Area Manager (~85 lines, 3 methods)
3. Progress Handler (~24 lines, 2 methods)

## Phase 1: Extract Template Preview Handler

### Create New File

- **File**: `src/philocr/ui/template_preview_handler.py`
- **Purpose**: Handle all template visualization and preview operations

### Methods to Extract from MainWindow

1. `_handle_template_ready()` (60 lines) → `handle_template_ready()`
2. `_show_template_image_menu()` (21 lines) → `_show_image_menu()`
3. `_save_template_image()` (37 lines) → `_save_image()`
4. `_open_template_image_window()` (54 lines) → `_open_image_window()`
5. `_format_template_preview()` (19 lines) → `_format_preview_text()`

### TemplatePreviewHandler Class Structure

```python
class TemplatePreviewHandler:
    """Handles template visualization and preview operations."""
    
    def __init__(
        self,
        template_preview_text: QTextEdit | None,
        template_preview_image: QLabel | None,
        parent_widget: QWidget,
        on_status_update: Callable[[str], None],
        on_error: Callable[[str], None],
    ) -> None:
        ...
    
    def handle_template_ready(self, template_dict: dict[str, Any]) -> None:
        """Handle template ready signal."""
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

### Dead Code Detection

- Check if `template_preview_text` and `template_preview_image` exist in UI composer
- If they don't exist, the `hasattr` checks indicate potentially dead code
- Keep the handler structure (template_ready callback is connected), but handler may have no-op paths
- Document findings in code comments

### Integration Changes

1. In `MainWindow.__init__()`, create `TemplatePreviewHandler` instance
2. Replace `on_template_ready=self._handle_template_ready` with handler method
3. Remove extracted methods from MainWindow
4. Update imports in MainWindow

**Estimated Reduction**: ~190 lines, 5 methods

## Phase 2: Extract Scan Area Manager

### ⚠️ CRITICAL PRESERVATION REQUIREMENT

**The scan area viewer preview functionality MUST be preserved exactly as-is. This includes:**

- PDF page image rendering and display (`ScanAreaViewerWidget`, `PageScanAreaWidget`)
- All page preview images displayed in the scan area tab
- All text displayed in the scan area viewer
- All interactive functionality (dragging scan areas, saving, processing)
- All signal connections (`scan_areas_saved`, `process_requested`)
- Tab switching behavior (switching to scan area tab when file selected)

**The extraction to `ScanAreaManager` is a pure refactoring - it moves code but MUST NOT change behavior.**

### Create New File

- **File**: `src/philocr/ui/scan_area_manager.py`
- **Purpose**: Manage scan area viewer display and processing coordination

### Methods to Extract from MainWindow

1. `_show_scan_area_viewer()` (44 lines) → `show_scan_area_viewer()`

   - **PRESERVE**: All PDF page image rendering via `ScanAreaViewerWidget`
   - **PRESERVE**: All page preview images displayed in the viewer
   - **PRESERVE**: Tab switching to scan area tab
   - **PRESERVE**: Layout clearing and widget creation logic

2. `_on_scan_areas_saved()` (11 lines) → `on_scan_areas_saved()`

   - **PRESERVE**: Signal handling for scan areas saved
   - **PRESERVE**: Status message updates

3. `_on_process_requested()` (30 lines) → `on_process_requested()`

   - **PRESERVE**: Signal handling for process requested
   - **PRESERVE**: Processing mode detection
   - **PRESERVE**: Worker manager integration for manual scan areas

### ScanAreaManager Class Structure

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
        on_scan_areas_changed: Callable[[ManualScanAreas], None],
    ) -> None:
        ...
    
    def show_scan_area_viewer(self, pdf_path: str) -> None:
        """Display scan area viewer for PDF."""
        ...
    
    def on_scan_areas_saved(self, scan_areas: ManualScanAreas) -> None:
        """Handle scan areas saved signal."""
        ...
    
    def on_process_requested(self, scan_areas: ManualScanAreas, pdf_path: str) -> None:
        """Handle process requested signal."""
        ...
```

### Integration Changes

1. In `MainWindow.__init__()`, create `ScanAreaManager` instance

   - Pass `scan_area_tab`, `tab_widget`, `worker_manager`, and callbacks
   - **VERIFY**: All widgets and managers passed correctly

2. Update `select_file()` to use `scan_area_manager.show_scan_area_viewer()`

   - **PRESERVE**: Exact behavior - file selection should show scan area viewer
   - **PRESERVE**: PDF page images must still render and display correctly

3. Remove extracted methods from MainWindow

   - **VERIFY**: No functionality lost - methods are moved, not removed

4. Update MainWindow to store current_pdf_path and pass to manager

   - **PRESERVE**: `current_pdf_path` must still be tracked correctly

5. Update imports in MainWindow

   - **VERIFY**: All necessary imports remain or are added to new manager

### Testing Requirements for Phase 2

**Before proceeding to Phase 3, VERIFY:**

1. ✅ Select PDF file → Scan area viewer displays with all page images
2. ✅ Page images render correctly in `ScanAreaViewerWidget`
3. ✅ Text in scan area viewer displays correctly
4. ✅ Dragging scan areas works correctly
5. ✅ Save scan areas button works
6. ✅ Process with scan areas button works
7. ✅ Tab switching to scan area tab works
8. ✅ All signal connections work correctly
9. ✅ No regressions in manual scan area functionality

**Estimated Reduction**: ~85 lines, 3 methods

## Phase 3: Extract Progress Handler

### Option A: Integrate with MainWindowCoordinator (Preferred)

- Add progress handling methods to existing `MainWindowCoordinator` class
- Consolidates coordination logic in one place

### Option B: Create ProgressHandler (If Option A is unsuitable)

- **File**: `src/philocr/ui/progress_handler.py`
- Extract methods to separate handler

### Methods to Extract from MainWindow

1. `_handle_stage_progress()` (12 lines) → Add to coordinator or handler
2. `_handle_overall_progress()` (12 lines) → Add to coordinator or handler

### Integration Changes

1. If Option A: Add methods to `MainWindowCoordinator`, update MainWindow to use coordinator
2. If Option B: Create `ProgressHandler`, integrate in MainWindow
3. Update `worker_manager` callback registration
4. Remove extracted methods from MainWindow

**Estimated Reduction**: ~24 lines, 2 methods

## Phase 4: Dead Code Detection and Cleanup

### Dead Code Detection Checklist

1. **Template Preview UI Elements**

   - Search for `template_preview_text` creation in UI composer/builder
   - Search for `template_preview_image` creation in UI composer/builder
   - If not found, document as dead code path (handler methods check with `hasattr`)
   - Keep handler structure (callback is connected), but methods may have no-op branches

2. **Unused Imports**

   - Check for unused imports in MainWindow after refactoring
   - Remove any imports no longer needed

3. **Unused Methods**

   - Verify all remaining methods in MainWindow are called
   - Check for private methods that are never invoked

4. **Unused Variables**

   - Check for instance variables that are no longer used after extraction

### Dead Code Removal Strategy

- **Dead Code Paths**: Keep structure but document in comments (e.g., template preview UI not created)
- **Unused Code**: Remove completely (unused imports, methods, variables)
- **Partially Used**: Refactor to remove unused parts

## Phase 5: Verification and Testing

### Code Quality Verification

1. Run God Class guardian to verify improvements:
   ```bash
   python3 guardians/run_all_guardians.py --guardians guardian_028_god_class --root .
   ```

2. Expected improvements:

   - MainWindow lines: ~343 (target: <300, improvement from 642)
   - MainWindow methods: ~19 (target: ≤10, improvement from 29)
   - MainWindow cohesion: Should improve significantly (target: ≥0.8)

### Functional Testing

1. Test template visualization (if UI elements exist)
2. **CRITICAL: Test scan area viewer functionality**

   - Verify PDF page images render correctly
   - Verify all page preview images display in scan area viewer
   - Verify text in scan area viewer displays correctly
   - Verify dragging scan areas works
   - Verify save and process buttons work
   - Verify tab switching works

3. Test progress updates (stage and overall)
4. Test all file operations
5. Test batch processing
6. Test single file processing

### Regression Testing

1. Run existing test suite
2. Verify UI still functions correctly
3. Check for any broken signal connections
4. Verify all callbacks still work

## Implementation Order

1. **Phase 1**: Extract TemplatePreviewHandler
2. **Phase 2**: Extract ScanAreaManager  
3. **Phase 3**: Extract ProgressHandler
4. **Phase 4**: Dead code detection and cleanup
5. **Phase 5**: Verification and testing

## Files to Modify

### New Files

- `src/philocr/ui/template_preview_handler.py`
- `src/philocr/ui/scan_area_manager.py`
- `src/philocr/ui/progress_handler.py` (if Option B for Phase 3)

### Modified Files

- `src/philocr/ui/main_window.py` (remove ~299 lines, 10 methods)
- `src/philocr/ui/main_window_coordinator.py` (if Option A for Phase 3)
- `src/philocr/ui/main_window_factory.py` (may need to create handler instances)
- `src/philocr/ui/__init__.py` (export new classes if needed)

## Success Criteria

1. MainWindow size reduced to ~343 lines (still over limit, but significant improvement)
2. MainWindow methods reduced to ~19 (still over limit, but significant improvement)
3. MainWindow cohesion improves to ≥0.5 (target: ≥0.8, but improvement from 0.26)
4. No functional regressions
5. All tests pass
6. Dead code identified and documented/removed
7. Code follows project coding standards (type hints, docstrings, etc.)

## Notes

- MainWindow will still exceed limits after this refactoring, but will be significantly improved
- Further refactoring may be needed in future to meet all limits
- Template preview handler may contain dead code paths (UI elements not created), but structure is valuable for future use
- **CRITICAL**: Scan area viewer preview functionality (PDF page images, text display) MUST be preserved exactly - no functionality loss
- All extracted handlers should follow UI purity rules (thin wrappers, delegate to workers/utils)
- All extracted handlers should have proper type hints and docstrings
- All extracted handlers should follow structured logging standards

## Preservation Guarantees

### Scan Area Viewer Preview Functionality

The following functionality MUST be preserved exactly as-is:

1. **PDF Page Image Rendering**

   - `ScanAreaViewerWidget` must continue to render and display PDF pages
   - `PageScanAreaWidget` must continue to display individual page images
   - All page preview images must display correctly in the scan area tab

2. **Text Display**

   - All text in the scan area viewer must display correctly
   - Status messages and labels must continue to work

3. **Interactive Functionality**

   - Dragging scan area rectangles must continue to work
   - Saving scan areas must continue to work
   - Processing with scan areas must continue to work
   - All button clicks and interactions must continue to work

4. **Signal Connections**

   - `scan_areas_saved` signal must continue to work
   - `process_requested` signal must continue to work
   - All signal connections must remain functional

5. **UI Behavior**

   - Tab switching to scan area tab must continue to work
   - File selection must still show scan area viewer
   - All UI behavior must remain identical