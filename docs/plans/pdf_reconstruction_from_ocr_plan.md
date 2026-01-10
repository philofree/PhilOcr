# PDF Reconstruction from Google Document AI OCR Output

## Document Purpose

This document outlines the plan for implementing PDF reconstruction functionality using output from Google Document AI OCR. The goal is to reconstruct PDF documents from OCR data while preserving layout, text positioning, and basic formatting.

**Core Principle**: Use bounding polygon coordinates and text content from Document AI to recreate PDFs with accurate text positioning.

**Key Capability**: Generate searchable PDFs from OCR output that maintain the original document's spatial layout.

**Document Status**: Implementation specification
**Version**: 1.1
**Date**: 2026-01-10

---

## Relationship to PhilOcr Pipeline

This document describes an **auxiliary capability**, not part of the core PhilOcr pipeline.

See: `philocr_pipeline_architecture_v1_4.md` for the primary pipeline specification.

### Primary vs Secondary Goals

| Goal | Responsibility | Document |
|------|---------------|----------|
| **Primary**: Clean body text extraction | PhilOcr Pipeline v1.4 | `philocr_pipeline_architecture_v1_4.md` |
| **Secondary**: Reference preservation | Alignment + Positional Oracle | This document |

### Why PDF Reconstruction is Secondary

The PhilOcr pipeline's primary goal is extracting clean, flowing Greek text for alignment to reference scaffolds (Stephanus, Bekker, Diels-Kranz, etc.).

PDF reconstruction serves a **different purpose**: preserving spatial layout for reference lookup. It does not help with clean text extraction—in fact, it preserves the very contamination (line numbers, headers, footnotes) that the pipeline removes.

### The Positional Oracle Role

PDF reconstruction becomes valuable as a **positional oracle** for reference recovery:

1. **Reference numbers in margins are unreliable to OCR** — "15" becomes "I5" or "1S"
2. **But their positions are reliable** — we know *where* they appear on the page
3. **The reconstructed PDF preserves these positions** — enabling manual or geometric lookup
4. **References are recovered via alignment**, not OCR — the reference text already has the numbers

See [Section 1.3: Positional Oracle Use Case](#13-positional-oracle-use-case) for details.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Feasibility Analysis](#2-feasibility-analysis)
3. [Technical Approach](#3-technical-approach)
4. [Data Structure Analysis](#4-data-structure-analysis)
5. [Implementation Architecture](#5-implementation-architecture)
6. [Detailed Implementation Plan](#6-detailed-implementation-plan)
7. [Limitations and Constraints](#7-limitations-and-constraints)
8. [Future Enhancements](#8-future-enhancements)
9. [Testing Strategy](#9-testing-strategy)
10. [Performance Considerations](#10-performance-considerations)

---

## 1. Executive Summary

### 1.1 Overview

Google Document AI OCR provides rich structured output including:
- Text content with precise bounding polygons (coordinates)
- Page dimensions
- Hierarchical layout information (blocks, paragraphs, lines, tokens)
- Confidence scores

This data contains sufficient information to reconstruct PDF documents with accurate text positioning.

### 1.2 Use Cases

1. **Searchable PDF Generation**: Convert OCR output to searchable PDFs
2. **Layout Preservation**: Maintain original document structure in reconstructed PDFs
3. **Document Recovery**: Reconstruct PDFs when originals are unavailable
4. **Format Conversion**: Transform OCR JSON output into standard PDF format
5. **Archive Enhancement**: Add OCR text layer to scanned documents
6. **Positional Oracle**: Reference lookup for alignment verification (see 1.3)

### 1.3 Positional Oracle Use Case

**Problem**: Scholarly reference numbers (Stephanus, Bekker, line numbers) appear in margins and are unreliable to OCR. Short isolated numbers lack linguistic context, leading to errors like "15" → "I5" or "1S".

**Solution**: Don't OCR the references. Instead:

1. **PhilOcr pipeline** extracts clean body text (masking margins)
2. **Alignment** matches body text to reference scaffolds (TLG, Perseus, etc.)
3. **Reference numbers are recovered from the scaffold**, not from OCR
4. **Positional oracle** (this PDF) enables manual verification and edge-case recovery

**How it works**:

```
┌─────────────────────────────────────────────────────────────┐
│  Reconstructed PDF with Grid Overlay                        │
│                                                             │
│  ┌─────┐                                                    │
│  │ [?] │  ἄνδρα μοι ἔννεπε, μοῦσα, πολύτροπον...          │
│  │     │  πλάγχθη, ἐπεὶ Τροίης ἱερὸν πτολίεθρον           │
│  │     │  ἔπερσεν· πολλῶν δ' ἀνθρώπων ἴδεν ἄστεα          │
│  │     │                                                    │
│  │ [?] │  καὶ νόον ἔγνω· πολλὰ δ' ὅ γ' ἐν πόντῳ           │
│  │     │  πάθεν ἄλγεα ὃν κατὰ θυμόν...                     │
│  └─────┘                                                    │
│   ↑                                                         │
│   Margin zone: positions recorded, text NOT trusted         │
└─────────────────────────────────────────────────────────────┘
```

**Grid overlay records**:
- Margin element detected at Y=350 (content unknown or unreliable)
- Body line at Y=355 correlates with margin element
- After alignment: "Body line at Y=355 = Odyssey 1.15"

**Use cases for positional oracle**:
- Manual verification when alignment confidence is low
- Debugging "where did line 15 go?"
- Recovering references for passages that failed alignment
- Visual inspection of complex editions (von Arnim SVF, Diels-Kranz)

### 1.4 Complex Editions

For multilingual fragment collections (e.g., von Arnim's SVF, Diels-Kranz):
- Multiple languages (Greek, Latin, German commentary)
- Editorial insertions and apparatus
- Discontinuous fragment text
- Complex footnote structures

The positional oracle is especially valuable here because:
1. Alignment is harder (fragments may not match reference texts exactly)
2. Manual verification is more often needed
3. The spatial relationship between fragment numbers and text is critical

### 1.3 Current State

- ✅ Document AI processing is implemented (`src/philocr/processing/document_ai.py`)
- ✅ JSON serialization captures full layout data (`_document_to_dict` function)
- ✅ PyMuPDF library available for PDF creation (`requirements.txt`)
- ❌ PDF reconstruction functionality not yet implemented

---

## 2. Feasibility Analysis

### 2.1 Available Data

From Document AI output, we have:

#### 2.1.1 Page-Level Information
- Page dimensions (width, height in points)
- Page number/index

#### 2.1.2 Layout Elements
- **Blocks**: Large text regions with bounding polygons
- **Paragraphs**: Paragraph boundaries with coordinates
- **Lines**: Line-level positioning
- **Tokens**: Individual text elements with precise coordinates

#### 2.1.3 Spatial Data
Each layout element contains:
- `bounding_poly.vertices`: Array of (x, y) coordinates defining bounding box
- Confidence scores for quality assessment

#### 2.1.4 Text Content
- Full document text (concatenated)
- Text segments with start/end indices
- Normalized Unicode text (NFC normalized)

### 2.2 Data Sufficiency Assessment

| Requirement | Available | Notes |
|------------|-----------|-------|
| Text content | ✅ Yes | Full text available |
| Text positioning | ✅ Yes | Bounding polygons provide coordinates |
| Page dimensions | ✅ Yes | Width/height for each page |
| Page order | ✅ Yes | Pages array maintains order |
| Font size estimation | ⚠️ Partial | Can infer from bounding box height |
| Font family | ❌ No | Not in OCR output |
| Font style (bold/italic) | ❌ No | Not reliably detected |
| Text color | ❌ No | OCR extracts grayscale/black text |
| Images | ❌ No | Only text extraction, not images |
| Complex layouts | ⚠️ Partial | Depends on bounding polygon accuracy |

### 2.3 Feasibility Conclusion

**✅ Feasible** - The available data is sufficient for basic PDF reconstruction with:
- Accurate text positioning
- Proper page structure
- Reasonable font size approximation
- Searchable text layers

**⚠️ Limitations** - Some original formatting cannot be preserved:
- Original fonts replaced with standard fonts
- Color information not available
- Images excluded from reconstruction
- Complex formatting may require additional processing

---

## 3. Technical Approach

### 3.1 Technology Stack

#### 3.1.1 Primary Library: PyMuPDF (fitz)

**Rationale**:
- Already in project dependencies (`requirements.txt`)
- Excellent PDF creation capabilities
- Supports precise text positioning
- Good Unicode support
- Active maintenance and documentation

**Key Capabilities**:
- Create new PDF documents
- Set page dimensions
- Insert text at specific coordinates
- Set font sizes and styles
- Create searchable PDFs

#### 3.1.2 Data Source

- Document AI JSON output (from `_document_to_dict` function)
- Format: `Dict[str, Any]` with structure defined in `document_ai.py`

### 3.2 Reconstruction Strategy

#### 3.2.1 Hierarchical Text Placement

```
Document
  └── Pages (ordered)
       └── Elements (sorted by position)
            ├── Blocks (largest regions)
            ├── Paragraphs (within blocks)
            ├── Lines (within paragraphs)
            └── Tokens (finest granularity)
```

**Placement Priority**: Use tokens for most accurate positioning, fall back to lines/paragraphs if tokens unavailable.

#### 3.2.2 Coordinate System

- Document AI uses pixel coordinates (0-based, origin at top-left)
- PyMuPDF uses points (1/72 inch, origin at bottom-left)
- **Requirement**: Coordinate transformation function

**Transformation**:
```
pdf_y = page_height - ocr_y
pdf_x = ocr_x (same)
```

#### 3.2.3 Font Size Estimation

From bounding polygon height:
```python
# Bounding box height in OCR coordinates
bbox_height = max(vertices.y) - min(vertices.y)

# Convert to points (assuming OCR coords are pixels)
# Typical conversion: points = pixels * (72 / DPI)
# For most documents: DPI ≈ 72-300

# Heuristic: Use median token height per page
font_size = calculate_median_font_size(page_tokens)
```

---

## 4. Data Structure Analysis

### 4.1 Document AI JSON Structure

From `_document_to_dict` function (lines 312-432 in `document_ai.py`):

```python
{
    "text": "Full document text (NFC normalized)",
    "pages": [
        {
            "page_number": 1,
            "dimension": {
                "width": 612.0,    # points
                "height": 792.0    # points
            },
            "blocks": [
                {
                    "layout": {
                        "confidence": 0.95,
                        "bounding_poly": {
                            "vertices": [
                                {"x": 100.0, "y": 200.0},
                                {"x": 400.0, "y": 200.0},
                                {"x": 400.0, "y": 250.0},
                                {"x": 100.0, "y": 250.0}
                            ]
                        },
                        "text": "Block text content"
                    },
                    "text": "Block text content"
                }
            ],
            "paragraphs": [...],  # Similar structure
            "lines": [...],       # Similar structure
            "tokens": [...],      # Similar structure
            "text": "Page-level text"
        }
    ]
}
```

### 4.2 Bounding Polygon Format

Each bounding polygon has 4 vertices defining a rectangle:
- Top-left: `vertices[0]` or `min(x), min(y)`
- Top-right: `max(x), min(y)`
- Bottom-right: `max(x), max(y)`
- Bottom-left: `min(x), max(y)`

**Note**: Vertices may not be in consistent order, so calculate:
```python
min_x = min(v["x"] for v in vertices)
max_x = max(v["x"] for v in vertices)
min_y = min(v["y"] for v in vertices)
max_y = max(v["y"] for v in vertices)
```

### 4.3 Text Extraction Points

Text can be extracted from multiple levels:
1. **Token level** (most precise): Individual words/characters
2. **Line level** (balanced): Full lines of text
3. **Paragraph level** (larger blocks): Paragraph chunks
4. **Block level** (fallback): Large text regions

**Strategy**: Prefer tokens > lines > paragraphs > blocks

---

## 5. Implementation Architecture

### 5.1 Module Structure

```
src/philocr/utils/pdf_reconstructor.py
    ├── PDFReconstructor (main class)
    │   ├── reconstruct_pdf() - Main entry point
    │   ├── _create_document() - Initialize PDF document
    │   ├── _process_page() - Process single page
    │   ├── _place_text_elements() - Place text on page
    │   ├── _calculate_font_size() - Estimate font size
    │   └── _transform_coordinates() - OCR → PDF coords
    │
    ├── CoordinateTransformer (utility)
    │   └── ocr_to_pdf_coords() - Coordinate conversion
    │
    └── FontSizeEstimator (utility)
        └── estimate_font_size() - Calculate font sizes
```

### 5.2 Class Design

#### 5.2.1 PDFReconstructor

```python
class PDFReconstructor:
    """Reconstruct PDF from Document AI JSON output."""
    
    def __init__(
        self,
        default_font: str = "helv",  # Helvetica
        default_dpi: float = 72.0,
        use_tokens: bool = True,
        fallback_to_lines: bool = True
    ):
        """
        Initialize PDF reconstructor.
        
        Args:
            default_font: Font family to use (helv, cour, times)
            default_dpi: DPI assumption for coordinate conversion
            use_tokens: Prefer token-level positioning
            fallback_to_lines: Fall back to lines if tokens unavailable
        """
    
    def reconstruct_pdf(
        self,
        document_json: Dict[str, Any],
        output_path: str
    ) -> str:
        """
        Reconstruct PDF from Document AI JSON.
        
        Args:
            document_json: Document AI JSON output
            output_path: Path for output PDF file
            
        Returns:
            Path to created PDF file
        """
```

### 5.3 Processing Flow

```
1. Load Document AI JSON
   ↓
2. Initialize PyMuPDF document
   ↓
3. For each page in JSON:
   ├── Create page with correct dimensions
   ├── Extract text elements (tokens/lines/blocks)
   ├── Sort elements by position (top-to-bottom, left-to-right)
   ├── Estimate font sizes
   ├── Transform coordinates (OCR → PDF)
   └── Place text elements on page
   ↓
4. Save PDF file
   ↓
5. Return output path
```

---

## 6. Detailed Implementation Plan

### 6.1 Phase 1: Core Functionality

#### 6.1.1 Create Module Structure

**File**: `src/philocr/utils/pdf_reconstructor.py`

**Components**:
1. `PDFReconstructor` class (main)
2. `CoordinateTransformer` helper class
3. `FontSizeEstimator` helper class
4. Error handling and logging

#### 6.1.2 Coordinate Transformation

**Implementation**:
```python
def transform_coordinates(
    x: float,
    y: float,
    page_height: float,
    ocr_dpi: float = 72.0,
    pdf_dpi: float = 72.0
) -> Tuple[float, float]:
    """
    Transform OCR coordinates to PDF coordinates.
    
    OCR: Top-left origin, pixels
    PDF: Bottom-left origin, points (1/72 inch)
    
    Args:
        x: OCR x coordinate
        y: OCR y coordinate
        page_height: Page height in points
        ocr_dpi: OCR coordinate system DPI
        pdf_dpi: PDF coordinate system DPI (usually 72)
        
    Returns:
        (pdf_x, pdf_y) tuple
    """
    # Scale if DPI differs
    scale = pdf_dpi / ocr_dpi
    pdf_x = x * scale
    
    # Flip Y coordinate (OCR: top=0, PDF: bottom=0)
    pdf_y = page_height - (y * scale)
    
    return (pdf_x, pdf_y)
```

#### 6.1.3 Font Size Estimation

**Strategy**: Use token bounding box heights

```python
def estimate_font_size(
    tokens: List[Dict[str, Any]],
    page_height: float,
    ocr_dpi: float = 72.0
) -> float:
    """
    Estimate font size from token bounding boxes.
    
    Args:
        tokens: List of token dictionaries
        page_height: Page height for normalization
        ocr_dpi: OCR coordinate system DPI
        
    Returns:
        Estimated font size in points
    """
    heights = []
    for token in tokens:
        if "layout" in token and "bounding_poly" in token["layout"]:
            vertices = token["layout"]["bounding_poly"]["vertices"]
            if len(vertices) >= 2:
                y_coords = [v["y"] for v in vertices]
                height = max(y_coords) - min(y_coords)
                heights.append(height * (72.0 / ocr_dpi))
    
    if heights:
        # Use median to avoid outliers
        heights.sort()
        median_idx = len(heights) // 2
        return heights[median_idx]
    
    # Default fallback
    return 12.0
```

#### 6.1.4 Text Element Extraction

**Priority order**:
1. Tokens (if `use_tokens=True`)
2. Lines (if tokens unavailable)
3. Paragraphs (if lines unavailable)
4. Blocks (fallback)

```python
def _extract_text_elements(
    self,
    page_data: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Extract text elements in priority order.
    
    Returns:
        List of elements with text and bounding polygons
    """
    elements = []
    
    # Try tokens first (most precise)
    if self.use_tokens and "tokens" in page_data:
        for token in page_data["tokens"]:
            if self._has_valid_layout(token):
                elements.append({
                    "text": token.get("text", ""),
                    "bounding_poly": token["layout"]["bounding_poly"],
                    "level": "token"
                })
    
    # Fall back to lines
    if not elements and self.fallback_to_lines and "lines" in page_data:
        for line in page_data["lines"]:
            if self._has_valid_layout(line):
                elements.append({
                    "text": line.get("text", ""),
                    "bounding_poly": line["layout"]["bounding_poly"],
                    "level": "line"
                })
    
    # ... (paragraphs and blocks as fallback)
    
    # Sort by position (top to bottom, left to right)
    return self._sort_elements(elements)
```

#### 6.1.5 Text Placement

```python
def _place_text_on_page(
    self,
    page: fitz.Page,
    elements: List[Dict[str, Any]],
    page_height: float
) -> None:
    """
    Place text elements on PDF page.
    
    Args:
        page: PyMuPDF page object
        elements: List of text elements to place
        page_height: Page height for coordinate transformation
    """
    for element in elements:
        vertices = element["bounding_poly"]["vertices"]
        
        # Calculate bounding box
        min_x = min(v["x"] for v in vertices)
        max_y = max(v["y"] for v in vertices)  # Top in OCR coords
        
        # Transform coordinates
        pdf_x, pdf_y = self._transform_coordinates(
            min_x, max_y, page_height
        )
        
        # Estimate font size
        font_size = self._estimate_element_font_size(element)
        
        # Insert text
        page.insert_text(
            (pdf_x, pdf_y),
            element["text"],
            fontname=self.default_font,
            fontsize=font_size,
            render_mode=0  # Fill text (visible)
        )
```

### 6.2 Phase 2: Enhancement Features

#### 6.2.1 Text Layering

- Ensure text is placed in reading order
- Handle overlapping elements
- Preserve text visibility

#### 6.2.2 Font Size Refinement

- Calculate font sizes per line/paragraph
- Handle varying font sizes within page
- Detect headers/footers by size

#### 6.2.3 Quality Metrics

- Report confidence scores
- Flag low-confidence regions
- Log reconstruction statistics

### 6.3 Phase 3: Integration

#### 6.3.1 Integration Points

1. **Worker Integration**: Add to `processing_worker.py`
   - New output format option: "PDF (Reconstructed)"
   
2. **UI Integration**: Add to `main_window.py`
   - Export option: "Save as Reconstructed PDF"
   
3. **CLI Integration**: Command-line option
   ```bash
   python -m philocr.reconstruct --input ocr_output.json --output reconstructed.pdf
   ```

#### 6.3.2 Configuration

Add to `config.yaml`:
```yaml
pdf_reconstruction:
  default_font: "helv"  # helv, cour, times
  default_dpi: 72.0
  use_tokens: true
  fallback_to_lines: true
  min_confidence: 0.5  # Minimum confidence for text placement
```

---

## 7. Limitations and Constraints

### 7.1 Technical Limitations

#### 7.1.1 Font Information

**Issue**: Original fonts not preserved

**Impact**: 
- All text uses default font (Helvetica)
- Font styles (bold/italic) not preserved
- Character spacing may differ

**Mitigation**:
- Use standard fonts for maximum compatibility
- Document limitation in user interface

#### 7.1.2 Color Information

**Issue**: OCR extracts text only (grayscale/black)

**Impact**:
- All text appears black
- Highlighted text loses highlighting
- Colored text becomes standard black

**Mitigation**:
- Accept as limitation (OCR output limitation)
- Consider future enhancement with image overlay

#### 7.1.3 Images and Graphics

**Issue**: Only text is extracted, not images

**Impact**:
- Diagrams, charts, illustrations missing
- Photos excluded
- Decorative elements lost

**Mitigation**:
- Document limitation clearly
- Consider hybrid approach: text from OCR + images from original PDF

#### 7.1.4 Complex Layouts

**Issue**: Tables, multi-column layouts may not reconstruct perfectly

**Impact**:
- Column structure may be flattened
- Table alignment may be approximate
- Complex formatting requires manual correction

**Mitigation**:
- Use bounding polygons for positioning
- Prioritize accuracy over perfect formatting
- Provide post-processing tools if needed

### 7.2 Coordinate System Challenges

#### 7.2.1 DPI Assumptions

**Issue**: OCR coordinates may not match assumed DPI

**Impact**:
- Text may be slightly mispositioned
- Font sizes may be inaccurate

**Mitigation**:
- Use configurable DPI setting
- Calculate DPI from page dimensions if available
- Test with various document types

#### 7.2.2 Coordinate Precision

**Issue**: Rounding errors in coordinate transformation

**Impact**:
- Minor positioning errors
- Overlapping text elements

**Mitigation**:
- Use appropriate precision (2 decimal places for points)
- Test with sample documents

### 7.3 Performance Constraints

#### 7.3.1 Large Documents

**Issue**: Processing time increases with page count

**Impact**:
- Slow reconstruction for large documents (100+ pages)

**Mitigation**:
- Batch processing
- Progress indicators
- Background processing

#### 7.3.2 Memory Usage

**Issue**: Full document JSON loaded into memory

**Impact**:
- High memory usage for large documents

**Mitigation**:
- Stream processing (page-by-page)
- Memory-efficient JSON parsing
- Clear resources after processing

---

## 8. Future Enhancements

### 8.1 Short-Term Enhancements

1. **Font Style Detection**
   - Detect bold/italic from bounding box characteristics
   - Use different fonts for headers
   - Preserve emphasis where possible

2. **Image Integration**
   - Extract images from original PDF
   - Overlay images at correct positions
   - Hybrid reconstruction (text + images)

3. **Table Detection**
   - Identify table structures
   - Reconstruct tables with proper alignment
   - Preserve table formatting

4. **Quality Indicators**
   - Highlight low-confidence regions
   - Add confidence scores as annotations
   - Report reconstruction metrics

### 8.2 Long-Term Enhancements

1. **Advanced Layout Analysis**
   - Multi-column detection
   - Header/footer identification
   - Footnote reconstruction

2. **Font Matching**
   - Match fonts by characteristics
   - Use similar fonts from system
   - Embed custom fonts if available

3. **Color Preservation**
   - Extract color from original images
   - Apply color to reconstructed text
   - Preserve highlighting

4. **Interactive Editing**
   - Allow manual position adjustments
   - Font size correction tools
   - Layout refinement interface

### 8.3 Research Areas

1. **ML-Based Font Estimation**
   - Train model to predict font sizes
   - Improve font family matching
   - Style detection improvements

2. **Layout Optimization**
   - Automatic layout refinement
   - Column detection algorithms
   - Alignment optimization

3. **Hybrid Reconstruction**
   - Combine OCR text with original PDF structure
   - Preserve formatting metadata
   - Best-of-both-worlds approach

---

## 9. Testing Strategy

### 9.1 Unit Tests

#### 9.1.1 Coordinate Transformation

```python
def test_coordinate_transformation():
    """Test OCR to PDF coordinate conversion."""
    transformer = CoordinateTransformer()
    
    # Top-left OCR (0, 0) → Bottom-left PDF (0, page_height)
    pdf_x, pdf_y = transformer.transform(0, 0, page_height=792)
    assert pdf_y == 792.0
    
    # Center OCR → Center PDF (with Y flip)
    pdf_x, pdf_y = transformer.transform(306, 396, page_height=792)
    assert pdf_y == 396.0
```

#### 9.1.2 Font Size Estimation

```python
def test_font_size_estimation():
    """Test font size calculation from tokens."""
    tokens = [
        {"layout": {"bounding_poly": {"vertices": [
            {"x": 0, "y": 0}, {"x": 100, "y": 0},
            {"x": 100, "y": 12}, {"x": 0, "y": 12}
        ]}}}
    ]
    size = estimate_font_size(tokens, page_height=792)
    assert 10.0 <= size <= 14.0  # Approximate 12pt
```

#### 9.1.3 Text Element Extraction

```python
def test_text_element_extraction():
    """Test extraction and sorting of text elements."""
    page_data = {
        "tokens": [
            {"layout": {...}, "text": "Hello"},
            {"layout": {...}, "text": "World"}
        ]
    }
    elements = extract_text_elements(page_data)
    assert len(elements) == 2
    assert elements[0]["text"] in ["Hello", "World"]
```

### 9.2 Integration Tests

#### 9.2.1 End-to-End Reconstruction

```python
def test_full_pdf_reconstruction():
    """Test complete PDF reconstruction from Document AI JSON."""
    # Load sample Document AI JSON
    json_data = load_sample_ocr_json()
    
    # Reconstruct PDF
    reconstructor = PDFReconstructor()
    output_path = reconstructor.reconstruct_pdf(json_data, "test_output.pdf")
    
    # Verify PDF created
    assert os.path.exists(output_path)
    
    # Verify PDF is valid
    doc = fitz.open(output_path)
    assert doc.page_count > 0
    assert len(doc[0].get_text()) > 0
    doc.close()
```

#### 9.2.2 Multi-Page Documents

```python
def test_multipage_reconstruction():
    """Test reconstruction of multi-page document."""
    json_data = create_multipage_ocr_data()
    reconstructor = PDFReconstructor()
    output_path = reconstructor.reconstruct_pdf(json_data, "multipage.pdf")
    
    doc = fitz.open(output_path)
    assert doc.page_count == len(json_data["pages"])
    doc.close()
```

### 9.3 Validation Tests

#### 9.3.1 Text Accuracy

- Compare reconstructed text with original OCR text
- Verify no text loss or corruption
- Check Unicode handling

#### 9.3.2 Positioning Accuracy

- Measure text position accuracy
- Compare with original document
- Verify coordinate transformation correctness

#### 9.3.3 Page Structure

- Verify correct page count
- Check page dimensions match
- Validate page ordering

### 9.4 Sample Test Documents

1. **Simple Text Document**
   - Single column, standard formatting
   - Baseline test case

2. **Multi-Column Document**
   - Test column handling
   - Layout preservation

3. **Academic Document**
   - Greek text with footnotes
   - Complex scholarly formatting

4. **Table-Heavy Document**
   - Multiple tables
   - Complex layouts

5. **Large Document**
   - 50+ pages
   - Performance testing

---

## 10. Performance Considerations

### 10.1 Processing Time Estimates

**Per-page processing time**:
- Coordinate transformation: < 1ms per element
- Font size calculation: < 5ms per page
- Text placement: < 10ms per element
- **Total**: ~100-500ms per page (depending on text density)

**Full document**:
- 10-page document: ~1-5 seconds
- 100-page document: ~10-50 seconds
- 1000-page document: ~2-8 minutes

### 10.2 Memory Usage

**Per-page memory**:
- Page data: ~10-100 KB
- Text elements: ~5-50 KB
- **Total per page**: ~15-150 KB

**Full document**:
- 100-page document: ~1.5-15 MB
- Acceptable for most systems

### 10.3 Optimization Strategies

1. **Streaming Processing**
   - Process pages sequentially
   - Clear page data after processing
   - Reduce peak memory usage

2. **Batch Text Placement**
   - Group nearby text elements
   - Reduce individual placement calls
   - Improve PyMuPDF efficiency

3. **Caching**
   - Cache font size calculations
   - Reuse coordinate transformations
   - Minimize redundant calculations

4. **Parallel Processing** (future)
   - Process multiple pages concurrently
   - Use multiprocessing for large documents
   - Balance CPU and I/O

---

## 11. Implementation Checklist

### 11.1 Phase 1: Core Implementation

- [ ] Create `pdf_reconstructor.py` module
- [ ] Implement `CoordinateTransformer` class
- [ ] Implement `FontSizeEstimator` class
- [ ] Implement `PDFReconstructor` class
- [ ] Add coordinate transformation logic
- [ ] Add font size estimation
- [ ] Add text element extraction
- [ ] Add text placement logic
- [ ] Add error handling
- [ ] Add logging

### 11.2 Phase 2: Testing

- [ ] Write unit tests for coordinate transformation
- [ ] Write unit tests for font size estimation
- [ ] Write unit tests for text extraction
- [ ] Write integration tests
- [ ] Create test fixtures (sample OCR JSON)
- [ ] Test with various document types
- [ ] Performance testing

### 11.3 Phase 3: Integration

- [ ] Integrate with processing worker
- [ ] Add UI export option
- [ ] Add CLI support
- [ ] Add configuration options
- [ ] Update documentation
- [ ] Create user guide

### 11.4 Phase 4: Enhancement

- [ ] Improve font size accuracy
- [ ] Add quality metrics
- [ ] Add confidence indicators
- [ ] Optimize performance
- [ ] Add advanced layout handling

---

## 12. Success Criteria

### 12.1 Functional Requirements

1. ✅ Successfully reconstruct PDF from Document AI JSON
2. ✅ Maintain accurate text positioning (±2 points)
3. ✅ Preserve page structure and order
4. ✅ Create searchable PDFs
5. ✅ Handle multi-page documents
6. ✅ Process documents up to 1000 pages

### 12.2 Quality Requirements

1. ✅ Text accuracy: 100% (no text loss)
2. ✅ Positioning accuracy: > 95% within 5 points
3. ✅ Page structure: 100% correct
4. ✅ Processing time: < 1 second per page (average)

### 12.3 User Experience Requirements

1. ✅ Simple API: Single function call
2. ✅ Clear error messages
3. ✅ Progress indicators for large documents
4. ✅ Comprehensive documentation

---

## 13. Risk Assessment

### 13.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Coordinate transformation errors | Medium | High | Extensive testing, validation |
| Font size inaccuracy | High | Medium | Multiple estimation methods |
| Memory issues with large docs | Low | Medium | Streaming processing |
| Performance problems | Medium | Low | Optimization, profiling |

### 13.2 User Experience Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| User expectations too high | High | Medium | Clear documentation of limitations |
| Formatting differences | High | Medium | Explain acceptable variance |
| Processing time complaints | Low | Low | Progress indicators |

---

## 14. Conclusion

PDF reconstruction from Google Document AI OCR output is **feasible and valuable**. The available data provides sufficient information to create accurate, searchable PDFs that preserve document layout and text positioning.

**Key Strengths**:
- Rich spatial data from bounding polygons
- Complete text content
- PyMuPDF library available and capable
- Clear implementation path

**Key Challenges**:
- Font and styling information limitations
- Coordinate system transformation
- Performance optimization for large documents

**Recommended Approach**:
1. Start with core functionality (Phase 1)
2. Validate with test documents
3. Iterate based on feedback
4. Add enhancements incrementally

**Estimated Effort**:
- Phase 1 (Core): 2-3 days
- Phase 2 (Testing): 1-2 days
- Phase 3 (Integration): 1 day
- Phase 4 (Enhancement): Ongoing

**Total Initial Implementation**: ~1 week

---

## Appendix A: Example Code Structure

### A.1 Module Header

```python
"""
PDF Reconstruction from Google Document AI OCR Output

This module provides functionality to reconstruct PDF documents
from Google Document AI JSON output, preserving text positioning
and basic layout structure.
"""

import os
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

import fitz  # PyMuPDF

from philocr.utils.unicode_normalizer import normalize_to_nfc

if TYPE_CHECKING:
    import structlog

    logger: structlog.BoundLogger
else:
    from philocr.utils.logging_config import get_logger

    logger = get_logger(__name__)
```

### A.2 Main Class Skeleton

```python
class PDFReconstructor:
    """Reconstruct PDF from Document AI JSON output."""
    
    def __init__(
        self,
        default_font: str = "helv",
        default_dpi: float = 72.0,
        use_tokens: bool = True,
        fallback_to_lines: bool = True,
        min_confidence: float = 0.5,
    ) -> None:
        """Initialize PDF reconstructor."""
        self.default_font = default_font
        self.default_dpi = default_dpi
        self.use_tokens = use_tokens
        self.fallback_to_lines = fallback_to_lines
        self.min_confidence = min_confidence
    
    def reconstruct_pdf(
        self,
        document_json: Dict[str, Any],
        output_path: str,
    ) -> str:
        """
        Reconstruct PDF from Document AI JSON.
        
        Args:
            document_json: Document AI JSON output
            output_path: Path for output PDF file
            
        Returns:
            Path to created PDF file
            
        Raises:
            ValueError: If document_json is invalid
            IOError: If output_path cannot be written
        """
        # Implementation here
        pass
```

---

## Appendix B: References

### B.1 Documentation

- [PyMuPDF Documentation](https://pymupdf.readthedocs.io/)
- [Google Document AI Documentation](https://cloud.google.com/document-ai/docs)
- [PDF Coordinate Systems](https://www.adobe.com/content/dam/acom/en/devnet/pdf/pdfs/PDF32000_2008.pdf)

### B.2 Related Code

- `src/philocr/processing/document_ai.py` - Document AI processing
- `src/philocr/processing/pdf_utils.py` - PDF utilities
- `src/philocr/utils/document_ai_formatter.py` - JSON formatting

### B.3 Dependencies

- `PyMuPDF>=1.21.0` - PDF creation library
- `google-cloud-documentai>=2.13.0` - Document AI client

---

**Document Version**: 1.0  
**Last Updated**: 2026-01-10  
**Status**: Ready for Implementation