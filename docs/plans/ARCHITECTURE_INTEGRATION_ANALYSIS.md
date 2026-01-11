# Architecture v1.4 Integration Analysis

**Date**: 2026-01-10  
**Purpose**: Analyze integration requirements for PhilOcr Pipeline Architecture v1.4 into the current system

---

## Executive Summary

The proposed v1.4 architecture introduces a 4-stage pre-processing pipeline that fundamentally changes how documents are processed. The current system processes PDFs directly through Document AI. The new architecture adds:

1. **Stage 1**: Image normalization (PDF → PNG, deskew)
2. **Stage 2**: Template extraction & zone masking (multi-page analysis)
3. **Stage 3**: OCR on masked images (existing Document AI)
4. **Stage 4**: Text assembly (enhanced from current)

This analysis identifies integration points, required UI changes, and potential challenges.

---

## Current System Overview

### Architecture
- **PyQt6 GUI application** with worker thread model
- **Direct PDF processing**: PDF → Document AI → Text extraction
- **Chunking strategy**: Splits documents >15 pages automatically
- **Progress tracking**: Single progress bar (0-100%) for chunk processing
- **Status updates**: Text-based status messages
- **Output formats**: Text, Markdown, HTML, JSON

### Key Components
- `ProcessingWorker` (QThread): Handles processing in background
- `ProcessingOrchestrator`: Coordinates chunk processing
- `SingleFileHandler` / `BatchFileHandler`: Process files
- `ConfigManager`: Manages application configuration
- `SettingsManager`: Handles Google Cloud credentials

### Current Configuration
- **Limited pipeline config**: Only Document AI credentials + basic processing settings
- **No stage-specific settings**: No template extraction, masking, or normalization config
- **Simple progress**: Single percentage, no stage breakdown

---

## Proposed Architecture (v1.4) Overview

### New Pipeline Stages

```
Stage 1: Image Normalisation
├── PDF → PNG conversion (300 DPI)
├── Grayscale conversion
└── Deskew correction

Stage 2: Template Extraction & Zone Masking
├── 2a: Multi-page zone detection (sample ~20 pages)
├── 2b: Template extraction (robust statistics)
└── 2c: Apply masking/cropping to all pages

Stage 3: OCR on Masked Body Region
└── Document AI processing (one request per page)

Stage 4: Text Assembly
├── Text normalization (Unicode NFC)
├── Genre detection (optional heuristic)
└── Final document assembly
```

### Key Data Structures
- `DocumentTemplate`: Statistical mask with zone boundaries
- `PipelineConfig`: ~30+ tunable parameters
- `PageImage`, `MaskedPage`, `OCRResult`, `PageOutput`: Stage outputs

---

## Integration Challenges

### 1. **Fundamental Workflow Change**

**Current**: PDF → Document AI → Text  
**New**: PDF → Normalize → Template → Mask → OCR → Assemble → Text

**Impact**: Complete rewrite of processing workflow required.

**Solution**: 
- Keep `ProcessingWorker` but replace internal logic
- Create new `PipelineOrchestrator` to coordinate stages
- Maintain same signal interface for UI compatibility

### 2. **Intermediate File Management**

**New Requirement**: Store normalised images, templates, masked images between stages.

**Current**: Only temporary files for PDF splitting.

**Impact**: Need robust temporary file management and optional caching strategy.

**Solution**:
- Extend `TempFileManager` to handle stage outputs
- Use structured directory hierarchy: `stage1_normalised/`, `stage2_masked/`, `stage3_ocr/`
- Implement cleanup strategy per stage

### 3. **Multi-Stage Progress Tracking**

**Current**: Single progress bar (0-100%) for chunks.

**New Requirement**: Track progress across 4 stages with sub-progress.

**Example Progress Structure**:
```
Stage 1: Normalising pages... [████████░░] 80%
Stage 2: Extracting template... [██████████] 100%
Stage 3: Running OCR... [█████░░░░░] 50%
Stage 4: Assembling text... [░░░░░░░░░░] 0%
```

**UI Changes Required**:
- Multi-level progress indicator
- Stage name labels
- Progress percentage per stage
- Overall progress calculation

### 4. **Template Validation & Visualization**

**New Requirement**: Allow users to inspect/validate extracted template before processing.

**Current**: No pre-processing validation. Layout detection happens post-OCR via Document AI's block structure.

**Key Difference**: 
- **Current**: Document AI OCR → Returns blocks/layout → Structure extracted from OCR results
- **New**: Image processing → Detect block map/layout from page images → Generate template → Mask non-body regions → Then OCR

**Impact**: Need new UI dialog/tab for template visualization to validate that image-based layout detection is working correctly.

**Solution**:
- Add "Template Preview" tab in results area
- Show template boundaries overlaid on sample pages
- Display detected block map (body regions, margins, headers, footers, footnotes)
- Allow manual template adjustment (future enhancement)
- Export template JSON for reuse

**Template Extraction Process** (Stage 2a):
- Analyzes normalised page images using projection profiles
- Detects zone boundaries (header, footer, margins, body, footnotes)
- Builds statistical template from multiple pages (typically 20 sample pages)
- Template represents "where body text typically appears" based on layout analysis

### 5. **Extended Configuration Management**

**Current**: Basic config (max_pages, rate limits, formatting).

**New Requirement**: 30+ pipeline-specific parameters across 4 stages.

**Configuration Categories**:
```yaml
stage1:
  target_dpi: 300
  deskew_threshold: 0.1

stage2a:
  header_search_percent: 0.15
  footer_search_percent: 0.15
  margin_search_percent: 0.20
  content_threshold: 0.05
  # ... 10+ more parameters

stage2b:
  template_sample_size: 20
  template_min_pages: 5
  outlier_threshold: 2.0

stage2c:
  use_cropping: false
  crop_padding: 0

stage3:
  ocr_max_retries: 3
  ocr_rate_limit_per_minute: 15

stage4:
  indent_ratio_threshold_1: 0.02
  indent_ratio_threshold_2: 0.06
  # Genre detection thresholds...
```

**UI Changes Required**:
- New "Pipeline Settings" dialog (separate from credentials)
- Tabbed interface for each stage
- Default presets for common document types
- Advanced/custom mode for fine-tuning

### 6. **Processing Time Changes**

**Current**: ~4s per page (Document AI only).

**New**: 
- Stage 1: 0.5s/page (parallel)
- Stage 2a: 2s/page (sample 20 pages, parallel) → ~40s total
- Stage 2b: ~1s (template extraction)
- Stage 2c: 0.1s/page (masking, parallel)
- Stage 3: 4s/page (OCR, rate-limited)
- Stage 4: 0.05s/page

**Total**: ~8min for 100 pages (vs ~7min currently)

**Impact**: Longer processing times, but better quality output.

**UI Changes**: 
- Update status messages to reflect stages
- Show estimated time remaining per stage
- Allow cancellation between stages

### 7. **Error Handling Enhancements**

**New Failure Points**:
- Template extraction failures (low confidence)
- Masking failures (invalid template)
- Zone detection edge cases

**Current**: Basic retry logic for Document AI.

**Required**: 
- Stage-specific error handling
- Fallback strategies (conservative defaults)
- User notification for template confidence issues

---

## Required UI Changes

### 1. **Enhanced Progress Display**

**Location**: Current progress bar area

**New UI Component**: Multi-stage progress widget

```python
class StageProgressWidget(QWidget):
    """Widget showing progress across multiple pipeline stages."""
    
    - Overall progress bar (0-100%)
    - Stage breakdown:
      * Stage 1: [████████░░] 80% - "Normalising pages..."
      * Stage 2: [░░░░░░░░░░] 0% - "Waiting..."
      * Stage 3: [░░░░░░░░░░] 0% - "Waiting..."
      * Stage 4: [░░░░░░░░░░] 0% - "Waiting..."
    - Time estimates per stage
    - Cancel button (between stages only)
```

**Implementation**: New widget in `src/philocr/ui/widgets/stage_progress.py`

### 2. **Pipeline Configuration Dialog**

**Location**: Settings menu (new "Pipeline Settings" option)

**New Dialog**: `PipelineConfigDialog`

**Structure**:
```
┌─────────────────────────────────────────────┐
│ Pipeline Configuration                      │
├─────────────────────────────────────────────┤
│ [Stage 1] [Stage 2] [Stage 3] [Stage 4]    │
├─────────────────────────────────────────────┤
│ Stage 1: Image Normalisation               │
│                                             │
│ Target DPI:        [300    ] v             │
│ Deskew Threshold:  [0.1    ] degrees       │
│                                             │
│ [Preset: Standard Greek Edition ▼]         │
│ [Reset to Defaults] [Save] [Cancel]        │
└─────────────────────────────────────────────┘
```

**Features**:
- Tabbed interface per stage
- Preset dropdown (Standard, Fragments, Verse, Custom)
- Tooltips explaining each parameter
- Validation on save
- Export/import config files

**Implementation**: `src/philocr/ui/dialogs/pipeline_config_dialog.py`

### 3. **Template Preview Tab**

**Location**: Results area (new tab alongside Text/Markdown/HTML/JSON)

**New Tab**: "Template Preview"

**Content**:
- Sample page image with template overlay
- Template boundaries visualized (green = body, red = excluded)
- Template statistics:
  - Confidence: 0.92
  - Pages analysed: 20
  - Body region: (350, 200) to (2200, 2850)
  - Has line numbers: Yes (left margin)
  - Has footnotes: Yes
- Export template JSON button
- "Re-extract Template" button (if confidence low)

**Implementation**: `src/philocr/ui/preview_generators/template_preview.py`

### 4. **Enhanced Status Messages**

**Current**: "Processing document: filename.pdf"

**New Stage-Specific Messages**:
```
Stage 1: "Normalising pages (80/100)..."
Stage 2a: "Detecting zones on sample pages (12/20)..."
Stage 2b: "Extracting template... (confidence: 0.92)"
Stage 2c: "Applying template mask (45/100 pages)..."
Stage 3: "Running OCR (45/100 pages, ~6min remaining)..."
Stage 4: "Assembling text (45/100 pages)..."
```

**Implementation**: Update `ProcessingWorker.status_signal` emissions

### 5. **Processing Mode Selection**

**New UI Element**: Processing mode selector (before file selection)

**Options**:
- "Standard OCR" (current behavior - direct Document AI)
- "Advanced Pipeline" (new v1.4 architecture with layout-based template extraction)

**Rationale**: 
- Allows switching between modes for comparison
- Template extraction uses image processing to detect block map/layout of text regions from uploaded pages
- Advanced pipeline analyzes page layouts to generate statistical templates for contamination exclusion

**Location**: Main window header, near file selection buttons

**Implementation Details**:
- The advanced pipeline works by:
  1. Analyzing uploaded pages to detect text block layout (projection profiles, zone boundaries)
  2. Generating a statistical template from detected layout patterns
  3. Using template to mask non-body regions before OCR
- This layout detection happens in Stage 2a (zone detection) using the algorithms described in the architecture document

### 6. **Results Metadata Enhancement**

**Current JSON Output**: Basic metadata (filename, page_count, etc.)

**New JSON Output**: Include pipeline metadata

```json
{
  "metadata": {
    "filename": "plato_republic.pdf",
    "page_count": 100,
    "pipeline_version": "1.4",
    "processing_mode": "advanced_pipeline",
    "template": {
      "confidence": 0.92,
      "body_bounds": {...},
      "has_line_numbers": true,
      "has_footnotes": true
    },
    "stages": {
      "stage1": {"time_elapsed": 50.2, "pages_normalised": 100},
      "stage2": {"time_elapsed": 41.5, "template_confidence": 0.92},
      "stage3": {"time_elapsed": 420.0, "pages_ocr": 100},
      "stage4": {"time_elapsed": 5.0}
    },
    "genre_hints": {
      "primary_genre": "prose",
      "confidence": 0.7
    }
  }
}
```

---

## Implementation Strategy

### Phase 1: Foundation (Week 1-2)
1. **Create pipeline module structure**
   ```
   src/philocr/pipeline/
   ├── __init__.py
   ├── orchestrator.py
   ├── stage1_normalise.py
   ├── stage2_template.py
   ├── stage2_mask.py
   ├── stage3_ocr.py (adapt existing)
   └── stage4_assemble.py
   ```

2. **Create data models**
   ```
   src/philocr/models/
   ├── config.py (PipelineConfig)
   ├── template.py (DocumentTemplate)
   ├── page.py (PageImage, MaskedPage, etc.)
   └── document.py (PageOutput, Document)
   ```

3. **Create detection modules**
   ```
   src/philocr/detection/
   ├── profiles.py
   ├── zones.py
   └── separators.py
   ```

4. **Update configuration system**
   - Extend `ConfigManager` to load pipeline config
   - Create `PipelineConfig` loader from YAML
   - Add defaults validation

### Phase 2: UI Foundation (Week 2-3)
1. **Create pipeline config dialog**
   - Basic tabbed interface
   - Load/save pipeline config
   - Preset support

2. **Create stage progress widget**
   - Multi-stage progress display
   - Overall progress calculation
   - Stage labels and percentages

3. **Add processing mode selector**
   - Radio buttons or dropdown
   - Store preference in config
   - Conditional workflow routing

### Phase 3: Pipeline Integration (Week 3-4)
1. **Adapt ProcessingWorker**
   - Add pipeline mode branch
   - Integrate `PipelineOrchestrator`
   - Emit stage-specific progress signals

2. **Update status messages**
   - Stage-aware status text
   - Time estimates (optional)
   - Error messages per stage

3. **Extend result processing**
   - Include template metadata
   - Add stage timing information
   - Preserve backward compatibility

### Phase 4: Advanced Features (Week 4-5)
1. **Template preview tab**
   - Visualize template boundaries
   - Show statistics
   - Export/import templates

2. **Enhanced error handling**
   - Template confidence warnings
   - Fallback UI notifications
   - Recovery strategies

3. **Testing & validation**
   - Test on diverse document types
   - Validate template extraction
   - Compare results (standard vs pipeline)

---

## Configuration Migration

### Current Config Structure
```yaml
processing:
  max_pages_per_request: 15
  rate_limit_requests_per_minute: 15

formatting:
  debug_mode: false
  use_simple_formatting: true
```

### Extended Config Structure
```yaml
# Existing sections remain
processing:
  max_pages_per_request: 15
  rate_limit_requests_per_minute: 15
  # NEW: Processing mode selector
  processing_mode: "standard"  # "standard" | "advanced_pipeline"

# NEW: Pipeline configuration
pipeline:
  stage1:
    target_dpi: 300
    deskew_threshold: 0.1
  stage2a:
    header_search_percent: 0.15
    footer_search_percent: 0.15
    margin_search_percent: 0.20
    content_threshold: 0.05
    min_gap_size: 20
    # ... more parameters
  stage2b:
    template_sample_size: 20
    template_min_pages: 5
    template_skip_first: 2
    template_skip_last: 2
    outlier_threshold: 2.0
  stage2c:
    use_cropping: false
    crop_padding: 0
  stage3:
    ocr_max_retries: 3
    ocr_retry_backoff_base: 2.0
    ocr_rate_limit_per_minute: 15
  stage4:
    indent_ratio_threshold_1: 0.02
    indent_ratio_threshold_2: 0.06
    verse_avg_line_threshold: 60
    verse_cv_threshold: 0.3
    speaker_ratio_threshold: 0.15
    fragment_ratio_threshold: 0.2
  validation:
    min_template_confidence: 0.5
    min_ocr_confidence: 0.3
    min_genre_confidence: 0.5
  performance:
    stage1_parallel_workers: 4
    stage2a_parallel_workers: 4
    stage3_batch_size: 1

formatting:
  # Existing remains
  debug_mode: false
  use_simple_formatting: true
```

**Migration Strategy**:
- Load existing config files (backward compatible)
- Default pipeline config if missing
- Warn user to review pipeline settings on first use
- Provide "Reset to Defaults" in pipeline config dialog

---

## Backward Compatibility Considerations

### 1. **Processing Mode Toggle**
- Default to "standard" mode (current behavior)
- Only use pipeline if explicitly selected
- Maintain existing code path for standard mode

### 2. **Output Format Compatibility**
- Existing JSON format remains valid
- New pipeline mode adds optional `pipeline_metadata` field
- Text/Markdown/HTML output unchanged (user-facing)

### 3. **Configuration Files**
- Existing config files load correctly
- Missing pipeline section uses defaults
- No breaking changes to existing settings

### 4. **API Compatibility**
- `ProcessingWorker` interface unchanged (same signals)
- Internal implementation differs by mode
- `ResultProcessor` handles both output formats

---

## Testing Requirements

### Unit Tests
- Stage 1: Image normalization
- Stage 2a: Zone detection algorithms
- Stage 2b: Template extraction (robust statistics)
- Stage 2c: Masking/cropping logic
- Stage 4: Text assembly and normalization

### Integration Tests
- Full pipeline end-to-end
- Template confidence fallbacks
- Error recovery between stages
- Progress signal emissions

### UI Tests
- Pipeline config dialog load/save
- Stage progress widget updates
- Template preview rendering
- Processing mode switching

### Validation Tests
- Template extraction on diverse documents
- Masking effectiveness (line numbers excluded)
- OCR quality comparison (standard vs pipeline)
- Performance benchmarks

---

## Risks & Mitigations

### Risk 1: Template Extraction Failures
**Impact**: Low confidence templates → poor masking → contaminated OCR  
**Mitigation**: 
- Conservative defaults fallback
- User notification + option to adjust
- Manual template override (future)

### Risk 2: Processing Time Increase
**Impact**: Users may prefer faster standard mode  
**Mitigation**: 
- Keep standard mode as default
- Show quality benefits in documentation
- Allow mode selection per document

### Risk 3: Increased Complexity
**Impact**: More configuration options → user confusion  
**Mitigation**: 
- Sensible defaults
- Preset configurations
- Advanced mode hidden by default
- Comprehensive documentation

### Risk 4: Memory Usage (Large Documents)
**Impact**: Normalised images + masked images in memory  
**Mitigation**: 
- Streaming/batch processing
- Clear intermediate files between stages
- Optional disk caching

---

## Recommendations

### 1. **Implementation Strategy**
- Implement both Standard OCR and Advanced Pipeline modes
- Add UI selector for mode selection (Standard vs Advanced)
- Advanced Pipeline: Image processor detects block map/layout of text from uploaded pages → generates template → masks non-body regions
- Template extraction (Stage 2) uses projection profiles and zone detection to analyze page layouts
- Test both modes side-by-side during development
- User can choose mode based on document type and requirements

### 2. **Preset Configurations**
- Pre-configured settings for common document types:
  - Standard Greek prose editions (default)
  - Fragment editions (Diels-Kranz style)
  - Verse editions (Homer, tragedy)
- Fine-tune presets for your specific document types
- Can expose all advanced options directly - no need to hide complexity
- Presets help with initial template extraction parameters for different layout patterns

### 3. **Template Reuse**
- Save templates to file (export/import)
- Reuse templates for similar document types (e.g., all Loeb editions use same template)
- Store in project directory or user config directory
- Critical for batch processing similar documents

### 4. **Visual Feedback Priority**
- Template preview tab is critical for user trust
- Show before/after masking comparison
- Highlight excluded regions clearly

### 5. **Performance Optimization**
- Parallel processing where possible (Stage 1, 2a, 2c)
- Cache templates for batch processing
- Optional: Skip Stage 1 if PDF is already high-quality

---

## Conclusion

The v1.4 architecture represents a significant enhancement to the OCR pipeline, but requires substantial UI changes to integrate smoothly. The key challenges are:

1. **Multi-stage progress tracking** → New progress widget
2. **Configuration complexity** → Pipeline config dialog with presets
3. **Template validation** → Template preview tab
4. **Backward compatibility** → Processing mode selector

**Recommended Approach**: 
- Implement as optional "Advanced Pipeline" mode
- Maintain existing standard mode
- Provide clear UI for configuration and validation
- Gather user feedback before making default

**Estimated Implementation Time**: 4-5 weeks for full integration with UI enhancements.
