# UI Changes Summary for Pipeline Architecture v1.4

**Quick Reference**: Required UI modifications for integrating the new 4-stage pipeline architecture.

---

## Critical UI Changes

### 1. **Multi-Stage Progress Display** ⚠️ HIGH PRIORITY

**Current State**:
- Single progress bar (0-100%)
- Simple text status: "Processing document: filename.pdf"

**Required Change**:
```
┌─────────────────────────────────────────────────────────┐
│ Overall Progress: [████████████████░░░░░░] 80%         │
├─────────────────────────────────────────────────────────┤
│ Stage 1: Image Normalisation                            │
│ [████████████░░░░░░] 80% - "Normalising pages (80/100)"│
│                                                         │
│ Stage 2: Template Extraction                            │
│ [████████████████████] 100% - "Template ready (0.92)"  │
│                                                         │
│ Stage 3: OCR Processing                                 │
│ [░░░░░░░░░░░░░░░░░░░░] 0% - "Waiting..."               │
│                                                         │
│ Stage 4: Text Assembly                                  │
│ [░░░░░░░░░░░░░░░░░░░░] 0% - "Waiting..."               │
└─────────────────────────────────────────────────────────┘
```

**Implementation**:
- New widget: `StageProgressWidget` in `src/philocr/ui/widgets/stage_progress.py`
- Replace single `QProgressBar` in `MainWindowUI`
- Update `ProcessingWorker` to emit stage-specific progress signals

**Signals Required**:
```python
# New signals for ProcessingWorker
stage_signal = pyqtSignal(str, int, str)  # (stage_name, progress, status_text)
overall_progress_signal = pyqtSignal(int)  # Overall 0-100%
```

---

### 2. **Pipeline Configuration Dialog** ⚠️ HIGH PRIORITY

**Current State**:
- Settings dialog only for Google Cloud credentials
- No pipeline-specific configuration

**Required Change**:
- New menu item: "Pipeline Settings" (separate from credentials)
- Tabbed dialog with 4+ tabs (one per stage, plus presets)

**Dialog Structure**:
```
┌──────────────────────────────────────────────────────┐
│ Pipeline Configuration                               │
├──────────────────────────────────────────────────────┤
│ [Presets ▼] [Stage 1] [Stage 2] [Stage 3] [Stage 4] │
├──────────────────────────────────────────────────────┤
│ Stage 1: Image Normalisation                         │
│                                                      │
│ Target DPI:          [300        ]                   │
│ Deskew Threshold:    [0.1        ] degrees          │
│                                                      │
│ Stage 2a: Zone Detection                            │
│ Header Search:       [15         ] % of page height │
│ Footer Search:       [15         ] % of page height │
│ Margin Search:       [20         ] % of page width  │
│ Content Threshold:   [0.05       ]                  │
│                                                      │
│ Stage 2b: Template Extraction                       │
│ Sample Size:         [20         ] pages            │
│ Min Pages:           [5          ]                  │
│ Outlier Threshold:   [2.0        ] MAD multiplier   │
│                                                      │
│ [Reset to Defaults]  [Save]  [Cancel]               │
└──────────────────────────────────────────────────────┘
```

**Preset Options**:
- "Standard Greek Prose Edition" (default)
- "Fragment Edition" (Diels-Kranz style)
- "Verse Edition" (Homer, tragedy)
- "Custom" (user-modified settings)

**Implementation**:
- `PipelineConfigDialog` in `src/philocr/ui/dialogs/pipeline_config_dialog.py`
- Extend `ConfigManager` to handle pipeline config section
- Load/save to YAML config file

---

### 3. **Template Preview Tab** ⚠️ MEDIUM PRIORITY

**Current State**:
- Results tabs: Text, Markdown, HTML, JSON
- No template visualization

**Required Change**:
- Add new tab: "Template Preview"
- Show sample page with template boundaries overlaid
- Display template statistics

**Preview Content**:
```
┌────────────────────────────────────────────────────┐
│ [Sample Page Image with Overlays]                 │
│                                                    │
│ ┌──────────────────────────────────────────────┐  │
│ │ [Green: Body region]                         │  │
│ │ [Red: Excluded zones (header, footer,        │  │
│ │      margins, footnotes)]                     │  │
│ └──────────────────────────────────────────────┘  │
│                                                    │
│ Template Statistics:                               │
│ • Confidence: 0.92                                │
│ • Pages Analysed: 20                              │
│ • Body Region: (350, 200) to (2200, 2850)        │
│ • Has Line Numbers: Yes (left margin)             │
│ • Has Footnotes: Yes                              │
│                                                    │
│ [Export Template JSON]  [Re-extract Template]     │
└────────────────────────────────────────────────────┘
```

**Implementation**:
- New tab in `MainWindowUI.tab_widget`
- `TemplatePreviewGenerator` in `src/philocr/ui/preview_generators/template_preview.py`
- Render using QLabel with QPixmap or custom QWidget

---

### 4. **Processing Mode Selector** ⚠️ HIGH PRIORITY

**Current State**:
- Single processing path (direct Document AI)

**Required Change**:
- Add mode selector before file selection
- Radio buttons or dropdown

**UI Element**:
```
Processing Mode:
○ Standard OCR (Direct Document AI)
● Advanced Pipeline (Template-based masking)

[Info] The advanced pipeline analyzes page layout to detect text
      blocks and generate templates for contamination exclusion.
```

**Location**: Main window header, above file selection buttons

**Implementation**:
- Add to `MainWindowUIComposer._setup_header()` or separate section
- Store preference in config: `processing.processing_mode`
- Route to appropriate workflow in `ProcessingWorker`

**Key Difference from Current System**:
- **Current (Standard OCR)**: PDF → Document AI OCR → Extract blocks/layout from OCR results → Structure post-processing
- **Advanced Pipeline**: PDF → Image processing → Detect block map/layout from page images → Generate template → Mask non-body regions → OCR only body regions → Assemble text

**Template Extraction**: The image processor analyzes normalised page images to detect the block map/layout of text regions using projection profiles and zone detection algorithms. This layout analysis (Stage 2a) identifies where body text, headers, footers, margins, and footnotes appear, then generates a statistical template from multiple sample pages. This template is used to mask non-body regions before OCR, preventing contamination from line numbers, page numbers, etc.

---

### 5. **Enhanced Status Messages** ⚠️ LOW PRIORITY

**Current Status Messages**:
- "Processing document: filename.pdf"
- "Processing 1 of 5: file.pdf (100 pages)"
- "Completed. Processed 100 pages."

**New Stage-Specific Messages**:
```
Stage 1: "Normalising pages (80/100)..."
Stage 2a: "Detecting zones on sample pages (12/20)..."
Stage 2b: "Extracting template... (confidence: 0.92)"
Stage 2c: "Applying template mask (45/100 pages)..."
Stage 3: "Running OCR (45/100 pages, ~6min remaining)..."
Stage 4: "Assembling text (45/100 pages)..."
```

**Implementation**:
- Update `ProcessingWorker.status_signal.emit()` calls
- Format: `f"Stage {n}: {stage_name} ({details})"`

---

### 6. **Results Metadata Display** ⚠️ LOW PRIORITY

**Current State**:
- JSON tab shows full document JSON
- No structured metadata summary

**Required Change**:
- Add metadata section to JSON preview (or separate metadata tab)
- Display pipeline processing information

**Metadata Display**:
```
Pipeline Metadata:
──────────────────
Processing Mode: Advanced Pipeline
Pipeline Version: 1.4

Template:
  Confidence: 0.92
  Body Bounds: (350, 200) to (2200, 2850)
  Has Line Numbers: Yes (left margin)
  Has Footnotes: Yes

Processing Times:
  Stage 1: 50.2s
  Stage 2: 41.5s
  Stage 3: 420.0s
  Stage 4: 5.0s
  Total: 516.7s

Genre Hints:
  Primary: prose
  Confidence: 0.7
```

**Implementation**:
- Extend `ResultProcessor.finalize_single_result()` to include pipeline metadata
- Update JSON structure (backward compatible)

---

## UI Component Checklist

### New Components Needed

- [ ] `StageProgressWidget` - Multi-stage progress display
- [ ] `PipelineConfigDialog` - Configuration dialog
- [ ] `TemplatePreviewWidget` - Template visualization
- [ ] `ProcessingModeSelector` - Mode selection (simple radio buttons)
- [ ] `PipelineMetadataDisplay` - Metadata summary (optional)

### Modified Components

- [ ] `MainWindowUI` - Add template preview tab, mode selector
- [ ] `MainWindowUIComposer` - Compose new UI elements
- [ ] `ProcessingWorker` - Add stage progress signals, mode routing
- [ ] `WorkerManager` - Handle new signals
- [ ] `ConfigManager` - Load/save pipeline config
- [ ] `ResultProcessor` - Include pipeline metadata

### Configuration Files

- [ ] `config.yaml.template` - Add pipeline section
- [ ] `ConfigManager.get_default_config()` - Default pipeline settings
- [ ] Migration script for existing config files

---

## Implementation Priority

### Phase 1: Essential (Week 1-2)
1. **Multi-stage progress widget** - Need feedback during long processing
2. **Processing mode selector** - UI selector for Standard vs Advanced Pipeline
3. **Basic pipeline config** - Configuration dialog with sensible defaults

### Phase 2: Important (Week 2-3)
4. **Full pipeline config dialog** - All tunable parameters
5. **Enhanced status messages** - Better user feedback
6. **Template preview tab** - User trust and validation

### Phase 3: Polish (Week 3-4)
7. **Metadata display** - Rich information in results
8. **Template export/import** - Reuse templates
9. **Visual refinements** - UX improvements

---

## Backward Compatibility

### Preserve Existing Behavior

1. **Same Output Formats**: Text/Markdown/HTML/JSON unchanged
2. **Same Signals**: `ProcessingWorker` interface remains compatible
3. **Config Migration**: Existing config files load without errors

### Migration Path (Single User Context)

Since there's only one user, you can:
- Start with advanced pipeline as default once ready (or keep both modes for testing)
- Directly configure pipeline settings without worrying about multiple user preferences
- Skip mode selector entirely if you always want to use the new pipeline
- Test both modes side-by-side during development, then switch default when satisfied

---

## Testing Checklist

### UI Tests

- [ ] Multi-stage progress updates correctly
- [ ] Pipeline config dialog saves/loads settings
- [ ] Template preview renders correctly
- [ ] Processing mode selector persists choice
- [ ] Status messages update per stage
- [ ] Cancel button works between stages

### Integration Tests

- [ ] Standard mode still works (backward compatibility)
- [ ] Advanced mode completes full pipeline
- [ ] Progress signals emit correctly
- [ ] Configuration persists across restarts
- [ ] Template visualization matches actual template

---

## Quick Implementation Notes

### Signal Updates for ProcessingWorker

```python
class ProcessingWorker(QThread):
    # Existing signals
    update_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)  # Keep for backward compat
    error_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool)
    json_ready_signal = pyqtSignal(dict)
    
    # New signals for pipeline
    stage_progress_signal = pyqtSignal(str, int, str)  # stage, progress, status
    overall_progress_signal = pyqtSignal(int)  # 0-100 overall
    template_ready_signal = pyqtSignal(dict)  # Template metadata for preview
```

### Config Structure Addition

```yaml
# Add to config.yaml
processing:
  processing_mode: "standard"  # or "advanced_pipeline"
  
pipeline:  # New section
  stage1: {...}
  stage2a: {...}
  stage2b: {...}
  stage2c: {...}
  stage3: {...}
  stage4: {...}
  validation: {...}
  performance: {...}
```

---

## Summary

**Minimum Viable Integration**: Multi-stage progress + processing mode selector + pipeline config dialog  
**Full Integration**: All UI changes above  
**Estimated Effort**: 2-4 weeks depending on polish level

**Key Implementation Notes**:
- **Template Extraction**: The image processor detects the block map/layout of text regions from uploaded pages using projection profiles and zone detection. This layout analysis generates a statistical template that identifies where body text typically appears.
- **Processing Mode**: UI selector allows switching between Standard OCR (direct Document AI) and Advanced Pipeline (layout-based template masking)
- **Configuration**: Full pipeline config dialog with all tunable parameters accessible
- **Template Visualization**: Critical for validating that layout detection correctly identifies body regions

The architecture is sound, and UI changes are essential. The plan remains the same - no need to hide complexity since there's only one user, but the core implementation approach is unchanged.
