---
name: Pipeline Architecture v1.4 Integration
overview: Integrate the 4-stage pipeline architecture (image normalization, template extraction, masked OCR, text assembly) into PhilOcr with full UI support including multi-stage progress tracking, pipeline configuration, and template visualization.
todos:
  - id: models
    content: Create models module with PipelineConfig, DocumentTemplate, PageImage, MaskedPage, OCRResult, PageOutput, Document dataclasses
    status: completed
  - id: detection
    content: Create detection module with projection profiles, zone detection (header/footer/margins), and footnote separator detection
    status: completed
  - id: utils
    content: "Create pipeline utilities: image_io.py, pdf_render.py, deskew.py, docai_helpers.py"
    status: completed
  - id: stage1
    content: "Implement Stage 1: Image normalization (PDF to PNG, deskew, grayscale) with parallel processing"
    status: completed
  - id: stage2_zones
    content: "Implement Stage 2a: Zone detection on sample pages with parallel processing"
    status: completed
  - id: stage2_template
    content: "Implement Stage 2b: Template extraction using ZoneMeasurements, robust statistics (MAD), and confidence calculation"
    status: completed
  - id: stage2_mask
    content: "Implement Stage 2c: Masking/cropping pages based on template with coordinate transformation support"
    status: completed
  - id: stage3
    content: "Implement Stage 3: OCR on masked images with rate limiting, retry logic, and structure extraction (advisory)"
    status: completed
  - id: stage4
    content: "Implement Stage 4: Text assembly with Unicode normalization, optional genre detection, and document assembly"
    status: completed
  - id: orchestrator
    content: Create PipelineOrchestrator to coordinate all stages with progress tracking and error handling
    status: completed
  - id: config
    content: Extend ConfigManager to support pipeline configuration section and processing mode selection
    status: completed
  - id: progress_widget
    content: Create StageProgressWidget UI component showing multi-stage progress with labels and status text
    status: completed
  - id: config_dialog
    content: Create PipelineConfigDialog with tabbed interface, presets, and parameter configuration
    status: completed
  - id: mode_selector
    content: Add processing mode selector (Standard OCR vs Advanced Pipeline) to main UI
    status: completed
  - id: template_preview
    content: Create template preview tab showing template boundaries overlaid on sample pages with statistics
    status: completed
  - id: worker_integration
    content: Update ProcessingWorker to route to PipelineOrchestrator based on mode, emit stage-specific signals
    status: completed
  - id: pipeline_handler
    content: Create PipelineHandler to wrap orchestrator and emit appropriate worker signals
    status: completed
  - id: result_metadata
    content: Extend ResultProcessor to include pipeline metadata (template, stage times, genre hints) in JSON output
    status: completed
  - id: tests
    content: Create comprehensive unit tests for all stages, integration tests for full pipeline, and UI tests
    status: pending
  - id: documentation
    content: Update configuration docs, create migration guide, and update user guide with pipeline information
    status: pending
---

# Pipeline Architecture v1.4 Integration Plan

## Overview

This plan integrates the v1.4 pipeline architecture which adds pre-processing stages before OCR to exclude contamination (line numbers, headers, footers, footnotes) by analyzing page layouts and generating statistical templates. The system will support both "Standard OCR" (current direct Document AI) and "Advanced Pipeline" (new 4-stage architecture) modes.

## Architecture Flow

```
Standard Mode: PDF → Document AI → Text (existing)
Advanced Mode: PDF → Stage 1 (Normalize) → Stage 2 (Template+Mask) → Stage 3 (OCR) → Stage 4 (Assemble) → Text
```

## Phase 1: Foundation - Data Models & Core Infrastructure

### 1.1 Create Pipeline Models Module

**New directory**: `src/philocr/models/`

**Files to create**:

- **`src/philocr/models/__init__.py`**: Export all model classes
- **`src/philocr/models/config.py`**: `PipelineConfig` dataclass with all tunable parameters (30+ fields from architecture doc Section 2.1)
- **`src/philocr/models/template.py`**: `DocumentTemplate` dataclass with JSON serialization/deserialization (Section 4.3)
- **`src/philocr/models/page.py`**: `PageImage`, `MaskedPage`, `CroppedPage`, `PageZones`, `BoundingBox` dataclasses (Sections 7.1-7.3)
- **`src/philocr/models/document.py`**: `OCRResult`, `TextBlock`, `TextParagraph`, `TextLine`, `PageOutput`, `Document`, `DocumentMetadata`, `DocumentStatistics` dataclasses (Sections 7.4-7.5)

**Implementation notes**:

- Use `@dataclass` with type hints (pyright strict compliance)
- Add `to_json()` and `from_json()` methods where needed
- Include validation methods (e.g., template confidence checks)

### 1.2 Create Detection Modules

**New directory**: `src/philocr/detection/`

**Files to create**:

- **`src/philocr/detection/__init__.py`**: Export detection functions
- **`src/philocr/detection/profiles.py`**: Projection profile utilities (horizontal/vertical profiles, normalization, gap detection)
- **`src/philocr/detection/zones.py`**: Zone detection functions:
  - `detect_page_zones()` - Main zone detection (Section 4.5)
  - `detect_header_boundary()` - Header detection (Section 4.6)
  - `detect_footer_boundary()` - Footer detection (Section 4.6)
  - `detect_left_margin()` - Left margin/line numbers (Section 4.7)
  - `detect_right_margin()` - Right margin detection (Section 4.7)
  - `gaussian_smooth()`, `find_significant_transitions()` - Helper functions
- **`src/philocr/detection/separators.py`**: Footnote separator detection:
  - `detect_footnote_separator()` - Main function (Section 4.8)
  - `detect_horizontal_rule()` - Rule detection helper

**Dependencies**: Add `scipy>=1.11.0` to `requirements.txt` for `gaussian_filter1d`

### 1.3 Create Pipeline Utilities

**New directory**: `src/philocr/pipeline/utils/`

**Files to create**:

- **`src/philocr/pipeline/utils/__init__.py`**: Export utilities
- **`src/philocr/pipeline/utils/image_io.py`**: `load_image()`, `save_image()`, `load_image_bytes()` (Section 8.1)
- **`src/philocr/pipeline/utils/pdf_render.py`**: 
  - `render_pdf_page()` - PDF to numpy array (Section 8.2)
  - `convert_to_grayscale()` - Image conversion
- **`src/philocr/pipeline/utils/docai_helpers.py`**: Document AI response parsing:
  - `extract_text_from_layout()` - Text extraction from layout elements (Section 8.4)
  - `layout_to_bbox()` - Bounding polygon to BoundingBox conversion
  - `calculate_average_confidence()` - Confidence calculation
  - `extract_blocks()`, `extract_paragraphs()`, `extract_lines()` - Structure extraction

**Dependencies**: Ensure `PyMuPDF>=1.23.0`, `opencv-python>=4.8.0`, `numpy>=1.24.0` in `requirements.txt`

### 1.4 Create Image Processing Utilities

**New file**: `src/philocr/pipeline/utils/deskew.py`

- **`detect_skew()`** - Skew angle detection (Section 8.3)
- **`rotate_image()`** - Image rotation for deskewing

**Dependencies**: Uses OpenCV (`cv2`)

## Phase 2: Pipeline Stages Implementation

### 2.1 Stage 1: Image Normalisation

**New file**: `src/philocr/pipeline/stage1_normalise.py`

**Functions**:

- `normalise_page()` - Convert PDF page to normalized PNG (Section 3.2)
- `normalise_all_pages()` - Parallel processing wrapper (Section 9.1)

**Implementation**:

- Use existing `pdf_utils.py` if available, otherwise create new PDF rendering
- Parallel processing with `ThreadPoolExecutor` (configurable workers)
- Output: Directory of normalized PNG images + manifest.json with PageImage metadata

### 2.2 Stage 2a: Zone Detection

**New file**: `src/philocr/pipeline/stage2_zones.py`

**Functions**:

- `detect_zones_for_template()` - Parallel zone detection on sample pages (Section 9.1)
- Uses functions from `detection/zones.py`

**Output**: List of `PageZones` objects

### 2.3 Stage 2b: Template Extraction

**New file**: `src/philocr/pipeline/stage2_template.py`

**Classes/Functions**:

- **`ZoneMeasurements`** - Collector class for template statistics (Section 4.3)
  - `add()` - Add page measurements
  - `calculate_confidence()` - Calculate template confidence (CV-based)
  - `detected()` - Feature detection (line numbers, footnotes)
- **`extract_template()`** - Main template extraction (Section 4.4)
  - Uses `select_sample_pages()` for page sampling
  - Uses `robust_median_with_outliers()` for statistics (MAD-based outlier detection)
  - Returns `DocumentTemplate` with confidence score

**Helper functions**:

- `select_sample_pages()` - Page sampling strategy (Section 4.4)
- `robust_median_with_outliers()` - MAD-based outlier detection (Section 4.4)

**Output**: `DocumentTemplate` with JSON serialization support

### 2.4 Stage 2c: Masking/Cropping

**New file**: `src/philocr/pipeline/stage2_mask.py`

**Functions**:

- `mask_page()` - Canonical masking approach (Section 4.9)
- `crop_to_body()` - Alternative cropping approach (Section 4.10)
- `choose_masking_strategy()` - Strategy selection based on config
- `transform_ocr_coordinates()` - Coordinate transformation for cropped images

**Implementation**:

- Masking preserves coordinate consistency (canonical)
- Cropping requires coordinate transformation (optional, lossy)

**Output**: List of `MaskedPage` or `CroppedPage` objects

### 2.5 Stage 3: OCR on Masked Images

**New file**: `src/philocr/pipeline/stage3_ocr.py`

**Functions**:

- `ocr_masked_page()` - Async OCR function (Section 5.2)
- `ocr_all_pages()` - Batch OCR with rate limiting (Section 9.1)
- `ocr_with_retry()` - Retry logic with exponential backoff (Section 12.2)

**Implementation**:

- Integrate with existing `document_ai.py` client
- Use existing `RateLimiter` class
- One request per page (not per line)
- Extract structure (blocks, paragraphs, lines) but treat as advisory

**Output**: List of `OCRResult` objects

### 2.6 Stage 4: Text Assembly

**New file**: `src/philocr/pipeline/stage4_assemble.py`

**Functions**:

- `assemble_page()` - Page-level assembly (Section 6.4)
- `normalise_text()` - Unicode NFC normalization, whitespace cleaning (Section 6.4)
- `assemble_document()` - Full document assembly (Section 6.4)
- **Optional**: `detect_genre_hint()` - Genre detection heuristics (Section 6.5)
  - `analyse_line_lengths()` - Verse detection
  - `detect_speaker_patterns()` - Dialogue detection
  - `detect_fragment_patterns()` - Fragment edition detection

**Output**: `PageOutput` objects, assembled into `Document`

### 2.7 Pipeline Orchestrator

**New file**: `src/philocr/pipeline/orchestrator.py`

**Class**: `PipelineOrchestrator`

**Methods**:

- `process_document()` - Main entry point, coordinates all stages
- `_stage1_normalise()` - Stage 1 execution
- `_stage2_extract_template()` - Stage 2a+2b execution
- `_stage2_apply_masking()` - Stage 2c execution
- `_stage3_ocr()` - Stage 3 execution
- `_stage4_assemble()` - Stage 4 execution

**Progress tracking**:

- Emit stage-specific progress signals
- Calculate overall progress (weighted by stage time estimates)

**Error handling**:

- Template extraction fallbacks (Section 12.1)
- OCR retry logic (Section 12.2)
- Stage-specific error recovery

**New file**: `src/philocr/pipeline/__init__.py`

- Export `PipelineOrchestrator`, `process_document()` convenience function

## Phase 3: Configuration System Updates

### 3.1 Extend ConfigManager

**Modify**: `src/philocr/utils/config_manager.py`

**Changes**:

- Update `get_default_config()` to include `pipeline` section with all default values (Section 2.1)
- Add `processing.processing_mode` field (default: "standard")
- Ensure backward compatibility with existing config files

### 3.2 Create Pipeline Config Loader

**New file**: `src/philocr/models/config_loader.py`

**Functions**:

- `load_pipeline_config()` - Load `PipelineConfig` from config dict
- `pipeline_config_to_dict()` - Convert `PipelineConfig` to dict for saving
- Validation: Ensure all required fields present, validate ranges

### 3.3 Update Config Template

**Modify**: `config.yaml.template`

**Add**:

```yaml
processing:
  processing_mode: "standard"  # "standard" | "advanced_pipeline"

pipeline:
  stage1:
    target_dpi: 300
    deskew_threshold: 0.1
  # ... (full pipeline section with all parameters)
```

## Phase 4: UI Components

### 4.1 Multi-Stage Progress Widget

**New file**: `src/philocr/ui/widgets/stage_progress.py`

**Class**: `StageProgressWidget(QWidget)`

**Features**:

- Overall progress bar (0-100%)
- Four stage progress bars with labels
- Status text per stage
- Time estimates (optional)

**Layout**:

```
┌─────────────────────────────────────────┐
│ Overall: [████████░░] 80%              │
│ Stage 1: [████████░░] 80% - "Normalising..." │
│ Stage 2: [████████████] 100% - "Complete" │
│ Stage 3: [░░░░░░░░░░] 0% - "Waiting..." │
│ Stage 4: [░░░░░░░░░░] 0% - "Waiting..." │
└─────────────────────────────────────────┘
```

**Methods**:

- `update_stage(stage_name, progress, status_text)` - Update individual stage
- `update_overall(progress)` - Update overall progress
- `reset()` - Reset all stages

### 4.2 Pipeline Configuration Dialog

**New file**: `src/philocr/ui/dialogs/pipeline_config_dialog.py`

**Class**: `PipelineConfigDialog(QDialog)`

**Features**:

- Tabbed interface (Presets, Stage 1, Stage 2a, Stage 2b, Stage 2c, Stage 3, Stage 4)
- Preset dropdown: "Standard Greek Prose", "Fragment Edition", "Verse Edition", "Custom"
- Parameter inputs with tooltips
- Load/save functionality
- Validation on save

**Integration**: Add to `src/philocr/ui/dialog_manager.py` - new method `show_pipeline_config()`

### 4.3 Processing Mode Selector

**Modify**: `src/philocr/ui/ui_composer.py`

**Changes**:

- Add processing mode selector in `_setup_header()` or new section
- Radio buttons: "Standard OCR" vs "Advanced Pipeline"
- Store selection in config: `processing.processing_mode`

**New UI component**: Add to `MainWindowUI` dataclass:

- `mode_selector: QWidget` (radio button group)

### 4.4 Template Preview Tab

**New file**: `src/philocr/ui/preview_generators/template_preview.py`

**Class**: `TemplatePreviewGenerator`

**Functions**:

- `generate_template_preview(template, sample_image_path)` - Generate preview with overlays
- `visualise_template()` - Draw template boundaries on image (Section 11.4)

**Modify**: `src/philocr/ui/tab_factory.py`

**Changes**:

- Add "Template Preview" tab to tab widget
- Render template visualization using QLabel with QPixmap or custom QWidget

### 4.5 Enhanced Status Messages

**Modify**: `src/philocr/workers/processing_worker.py`

**New signals** (add to `ProcessingWorker`):

- `stage_progress_signal = pyqtSignal(str, int, str)` - (stage_name, progress, status_text)
- `overall_progress_signal = pyqtSignal(int)` - Overall 0-100%
- `template_ready_signal = pyqtSignal(dict)` - Template metadata for preview

**Update**: Status message format to include stage names and details

### 4.6 Update MainWindow UI

**Modify**: `src/philocr/ui/main_window.py`

**Changes**:

- Replace single progress bar with `StageProgressWidget`
- Connect new pipeline signals
- Add template preview tab to tab widget
- Handle template ready signal to populate preview

**Modify**: `src/philocr/ui/ui_composer.py`

**Changes**:

- Update `MainWindowUI` dataclass to include mode selector
- Replace `progress_bar: QProgressBar` with `stage_progress: StageProgressWidget`

## Phase 5: Integration with Existing System

### 5.1 Update ProcessingWorker

**Modify**: `src/philocr/workers/processing_worker.py`

**Changes**:

- Add `processing_mode` parameter (from config)
- Route to appropriate handler:
  - "standard" → Existing `SingleFileHandler` / `BatchFileHandler`
  - "advanced_pipeline" → New `PipelineOrchestrator`
- Emit stage-specific progress signals for pipeline mode
- Maintain backward compatibility (existing signals still work)

### 5.2 Create Pipeline Handler

**New file**: `src/philocr/workers/handlers/pipeline_handler.py`

**Class**: `PipelineHandler`

**Methods**:

- `process_single_file()` - Single file pipeline processing
- `process_batch_files()` - Batch pipeline processing
- `_emit_progress()` - Convert pipeline progress to worker signals

**Integration**: Called from `ProcessingWorker` when mode is "advanced_pipeline"

### 5.3 Update Result Processor

**Modify**: `src/philocr/workers/handlers/result_processor.py`

**Changes**:

- Extend `finalize_single_result()` to include pipeline metadata if available
- Add template information to JSON output
- Add stage timing information
- Maintain backward compatibility (standard mode JSON unchanged)

### 5.4 Update Worker Manager

**Modify**: `src/philocr/ui/worker_manager.py`

**Changes**:

- Connect new pipeline signals (`stage_progress_signal`, `template_ready_signal`)
- Update `StageProgressWidget` on stage updates
- Handle template ready signal to show preview

## Phase 6: Testing & Validation

### 6.1 Unit Tests

**New directory**: `tests/pipeline/`

**Files**:

- `test_stage1_normalise.py` - Image normalization tests
- `test_stage2_zones.py` - Zone detection tests
- `test_stage2_template.py` - Template extraction tests
- `test_stage2_mask.py` - Masking/cropping tests
- `test_stage3_ocr.py` - OCR integration tests
- `test_stage4_assemble.py` - Text assembly tests
- `test_detection_profiles.py` - Projection profile tests
- `test_detection_zones.py` - Zone detection algorithm tests
- `test_models.py` - Data model serialization tests

### 6.2 Integration Tests

**New file**: `tests/integration/test_pipeline_integration.py`

**Tests**:

- Full pipeline end-to-end
- Template extraction validation (Section 11.1)
- Masking validation (Section 11.2)
- OCR comparison (Section 11.3)
- Progress signal emissions
- Error recovery between stages

### 6.3 UI Tests

**Files**:

- `tests/ui/test_stage_progress_widget.py` - Progress widget updates
- `tests/ui/test_pipeline_config_dialog.py` - Config dialog load/save
- `tests/ui/test_mode_selector.py` - Mode switching

### 6.4 Visual Validation Tool

**New file**: `src/philocr/pipeline/utils/template_visualizer.py`

**Function**: `visualise_template()` - Generate template overlay images (Section 11.4)

**Usage**: Command-line tool or integrated into UI template preview

## Phase 7: Documentation & Migration

### 7.1 Update Configuration Documentation

**Modify**: `docs/CONFIG_SYSTEM.md`

**Add**: Pipeline configuration section with parameter explanations

### 7.2 Update User Guide

**Modify**: `docs/OJD_OCR_User_Guide.md` (or create new guide)

**Add**:

- Pipeline architecture explanation
- When to use Standard vs Advanced Pipeline
- Template configuration guide
- Troubleshooting template extraction

### 7.3 Create Migration Guide

**New file**: `docs/PIPELINE_MIGRATION.md`

**Content**:

- Config file migration (backward compatibility)
- Feature comparison (Standard vs Advanced)
- Performance implications
- Template reuse strategies

## Implementation Order

### Week 1: Foundation

- Create models module (Phase 1.1)
- Create detection modules (Phase 1.2)
- Create pipeline utilities (Phase 1.3-1.4)
- Unit tests for models and detection

### Week 2: Core Pipeline

- Implement Stage 1 (Phase 2.1)
- Implement Stage 2a, 2b, 2c (Phase 2.2-2.4)
- Template extraction validation
- Unit tests for stages

### Week 3: OCR & Assembly

- Implement Stage 3 (Phase 2.5)
- Implement Stage 4 (Phase 2.6)
- Create orchestrator (Phase 2.7)
- Integration tests

### Week 4: Configuration & UI Foundation

- Extend ConfigManager (Phase 3)
- Create pipeline config dialog (Phase 4.2)
- Create stage progress widget (Phase 4.1)
- Processing mode selector (Phase 4.3)

### Week 5: UI Integration & Polish

- Template preview tab (Phase 4.4)
- Integrate with ProcessingWorker (Phase 5)
- Enhanced status messages (Phase 4.5)
- UI tests

### Week 6: Testing & Documentation

- Comprehensive testing (Phase 6)
- Documentation updates (Phase 7)
- Visual validation tools
- Performance optimization

## Dependencies to Add

**Update `requirements.txt`**:

- `scipy>=1.11.0` (for gaussian smoothing)
- Ensure `opencv-python>=4.8.0` (already likely present)
- Ensure `numpy>=1.24.0` (already likely present)
- Ensure `PyMuPDF>=1.23.0` (already likely present)

## Backward Compatibility

- Existing "Standard OCR" mode remains unchanged
- Config files without pipeline section use defaults
- Existing JSON output format preserved (pipeline metadata is additive)
- All existing signals maintained (new signals are additional)
- ProcessingWorker interface compatible (routing based on mode)

## Success Criteria

1. Both processing modes functional (Standard and Advanced Pipeline)
2. Template extraction works on diverse document types
3. Masking effectively excludes line numbers, headers, footers
4. Multi-stage progress tracking visible in UI
5. Pipeline configuration accessible and functional
6. Template preview validates extraction quality
7. All tests passing
8. Documentation complete