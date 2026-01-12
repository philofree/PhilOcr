# Editorial Markup System - Scholarly Text Annotation

## Vision

Transform PhilOcr from a basic OCR tool into a **scholarly text annotation and structure preservation system** that allows editors to mark up scanned pages with semantic regions that are preserved through the OCR process and made available for post-processing.

## Core Concept

Instead of just extracting raw text, editors can define **semantic regions** on the scanned page that tell the OCR system how to interpret and format different parts of the text:

- **Footnotes** → `[[footnote: ...]]`
- **Marginalia** → `[[margin: ...]]`
- **Headers** → `[[header: ...]]`
- **Line numbers** → `[[linenum: X]]`
- **Paragraph breaks** → `\n\n`
- **Section breaks** → `[[section: ...]]`
- **Editorial notes** → `[[note: ...]]`
- **Apparatus criticus** → `[[apparatus: ...]]`

## User Workflow

### 1. Right-Click Context Menu

```
Right-click on page →
┌─────────────────────────┐
│ Mark as...              │
├─────────────────────────┤
│ ✓ Text (default)        │
│   Footnote              │
│   Marginalia            │
│   Header                │
│   Line Number           │
│   Paragraph Break       │
│   Section Break         │
│   Apparatus             │
│   Editorial Note        │
│   [Mask/Exclude]        │
└─────────────────────────┘
```

### 2. Draw Region

- Select annotation type from menu
- Draw rectangle or click point (depending on type)
- Region is color-coded by type
- Multiple regions of same type can be added

### 3. Visual Feedback

Different annotation types have different visual styles:

| Type | Color | Style |
|------|-------|-------|
| Text (default) | Green | Solid border |
| Footnote | Brown | Dashed border + label |
| Marginalia | Orange | Dotted border |
| Header | Purple | Bold border |
| Line Number | Gray | Thin border |
| Paragraph Break | Blue | Horizontal line (thick) |
| Line Break | Blue | Horizontal line (thin) |
| Section Break | Cyan | Double horizontal line |
| Mask/Exclude | Red | Filled white |

### 4. Region Labels

Each region shows a small label:
```
┌──────────────────┐
│ [F1] Footnote   │
│ Cf. Plato Rep...│
└──────────────────┘
```

## Data Model

### Extended ManualScanArea

```python
@dataclass
class AnnotationRegion:
    """Semantic annotation region."""
    type: AnnotationType  # enum: FOOTNOTE, MARGINALIA, HEADER, etc.
    bounds: tuple[int, int, int, int]  # x, y, width, height
    metadata: dict[str, Any]  # optional: number, label, etc.

@dataclass
class ManualScanArea:
    top_left: tuple[int, int]
    top_right: tuple[int, int]
    bottom_right: tuple[int, int]
    bottom_left: tuple[int, int]
    mask_rects: list[tuple[int, int, int, int]] | None = None
    line_breaks: list[int] | None = None
    annotations: list[AnnotationRegion] | None = None  # NEW
```

### AnnotationType Enum

```python
class AnnotationType(Enum):
    TEXT = "text"  # default - no markup
    FOOTNOTE = "footnote"
    MARGINALIA = "marginalia"
    HEADER = "header"
    LINE_NUMBER = "linenum"
    PARAGRAPH_BREAK = "paragraph_break"
    SECTION_BREAK = "section_break"
    APPARATUS = "apparatus"
    EDITORIAL_NOTE = "note"
    MASK = "mask"  # exclude from OCR
```

## OCR Integration

### Stage 1: Region Detection

During OCR, identify which annotation region each text block falls into:

```python
def classify_text_block(block_bounds: tuple, annotations: list[AnnotationRegion]) -> str:
    """Determine which annotation region contains this text block."""
    for annotation in annotations:
        if block_overlaps_region(block_bounds, annotation.bounds):
            return annotation.type
    return AnnotationType.TEXT
```

### Stage 2: Text Wrapping

Wrap extracted text based on region type:

```python
def wrap_text_block(text: str, annotation_type: AnnotationType) -> str:
    """Wrap text with appropriate markup."""
    if annotation_type == AnnotationType.FOOTNOTE:
        return f"[[footnote: {text}]]"
    elif annotation_type == AnnotationType.MARGINALIA:
        return f"[[margin: {text}]]"
    elif annotation_type == AnnotationType.HEADER:
        return f"[[header: {text}]]"
    # ... etc
    else:
        return text  # plain text
```

### Stage 3: Post-Processing

Output includes semantic markup that can be:
- **Extracted**: Pull all footnotes into a separate file
- **Formatted**: Convert to LaTeX, TEI XML, Markdown with extensions
- **Validated**: Check that line numbers are sequential
- **Analyzed**: Count apparatus entries, cross-references, etc.

## Implementation Phases

### Phase 1: Foundation (Week 1)
- [x] Basic polygon cropping (DONE)
- [x] Mask/whiteout regions (DONE)
- [x] Line break markers (DONE)
- [ ] Add AnnotationType enum
- [ ] Add AnnotationRegion dataclass
- [ ] Extend ManualScanArea with annotations field
- [ ] Update save/load for annotations

### Phase 2: UI Components (Week 2)
- [ ] Right-click context menu
- [ ] Annotation mode selector
- [ ] Color-coded region drawing
- [ ] Region labels/tags
- [ ] Delete individual annotations (double-click)
- [ ] Edit annotation type (right-click existing region)
- [ ] Paragraph break mode (special case - horizontal line like line breaks but double)

### Phase 3: OCR Integration (Week 3)
- [ ] Text block classification by region
- [ ] Text wrapping based on annotation type
- [ ] Handle overlapping regions (priority system)
- [ ] Generate annotated JSON output
- [ ] Preview annotated output in UI

### Phase 4: Post-Processing (Week 4)
- [ ] Extract annotations to separate files
- [ ] Generate TEI XML with semantic markup
- [ ] LaTeX output with proper formatting
- [ ] Markdown with footnote extensions
- [ ] Validation reports (sequential line numbers, etc.)
- [ ] Statistics dashboard (footnote count, apparatus entries, etc.)

### Phase 5: Advanced Features (Future)
- [ ] Auto-detection of common patterns (footnote positioning, line numbers)
- [ ] Templates for common scholarly text layouts
- [ ] Batch annotation across multiple pages
- [ ] Annotation inheritance ("use previous page's layout")
- [ ] Export/import annotation profiles
- [ ] Collaborative annotation (share annotation configs)

## Use Cases

### Critical Edition of Plato

```
Page Layout:
┌────────────────────────────────────┐
│ [HEADER] Plato - Republic Book I  │
├────────────────────────────────────┤
│ 5 [LN] τὸν οὖν δὴ Πολέμαρχον...  │
│ 6 [LN] ἐπειδὴ γὰρ ἦσαν...        │
│ 7 [LN] καὶ μὴν ἔφη ὁ...          │
│                                    │
│ ┌──────────────────────────┐     │
│ │ [FOOTNOTE 1]             │     │
│ │ Cf. Symp. 177d. See      │     │
│ │ Burnet's discussion...    │     │
│ └──────────────────────────┘     │
└────────────────────────────────────┘
```

OCR Output:
```markdown
[[header: Plato - Republic Book I]]

[[linenum: 5]] τὸν οὖν δὴ Πολέμαρχον...

[[linenum: 6]] ἐπειδὴ γὰρ ἦσαν...

[[linenum: 7]] καὶ μὴν ἔφη ὁ...

[[footnote: Cf. Symp. 177d. See Burnet's discussion...]]
```

### Manuscript with Marginalia

```
Page Layout:
┌────────────────────────────────────┐
│ [MARGIN-LEFT]                      │
│ "important!"                       │
│                                    │
│     Main text flows here with     │
│     ancient Greek characters...   │
│                                    │
│               [MARGIN-RIGHT]      │
│               "cf. other MS"      │
└────────────────────────────────────┘
```

OCR Output:
```markdown
[[margin-left: important!]]

Main text flows here with ancient Greek characters...

[[margin-right: cf. other MS]]
```

## Technical Considerations

### 1. Region Overlap Handling

When text blocks fall into multiple regions, use priority:
1. MASK (highest - exclude completely)
2. FOOTNOTE
3. MARGINALIA
4. HEADER
5. LINE_NUMBER
6. APPARATUS
7. TEXT (lowest - default)

### 2. DPI Scaling

All annotation coordinates stored in original image dimensions, scaled during OCR processing (same as mask_rects).

### 3. Serialization

```json
{
  "0": {
    "top_left": [100, 100],
    "top_right": [900, 105],
    "bottom_right": [895, 1200],
    "bottom_left": [105, 1195],
    "annotations": [
      {
        "type": "footnote",
        "bounds": [150, 1050, 400, 120],
        "metadata": {"number": 1}
      },
      {
        "type": "header",
        "bounds": [200, 50, 600, 40],
        "metadata": {"level": 1}
      }
    ],
    "line_breaks": [200, 250, 300, 350],
    "mask_rects": [[850, 100, 50, 30]]
  }
}
```

### 4. Performance

- Annotations cached per page
- Hit testing optimized with spatial indexing for many regions
- Drawing uses efficient QPainter batching

## Future: AI-Assisted Annotation

Once annotation system is established, train models to:
- Auto-detect footnote regions by position/size
- Recognize line number patterns
- Identify headers by font size/formatting
- Suggest apparatus entries
- Detect marginalia by position outside main text block

Editor reviews and corrects AI suggestions, saving time on repetitive pages.

## Benefits

1. **Preserves scholarly structure** - Footnotes, line numbers, apparatus stay connected to text
2. **Enables rich post-processing** - Generate LaTeX, TEI XML, semantic HTML
3. **Validates consistency** - Check sequential line numbers, cross-reference footnotes
4. **Supports collaborative editing** - Share annotation profiles, build templates
5. **Reduces post-OCR cleanup** - Structure captured during OCR, not added later
6. **Publication-ready output** - Direct export to scholarly formats

## Comparison to Current State

### Current (Basic OCR)
```
Text comes out as:
5 τὸν οὖν δὴ Πολέμαρχον 1 Cf. Symp. 177d 6 ἐπειδὴ γὰρ...
```
Editor must manually:
- Separate line numbers
- Extract footnotes
- Identify headers
- Add paragraph breaks
- Format for publication

### With Editorial Markup System
```
Text comes out as:
[[linenum: 5]] τὸν οὖν δὴ Πολέμαρχον

[[linenum: 6]] ἐπειδὴ γὰρ...

[[footnote: Cf. Symp. 177d]]
```
Editor receives:
- Structured, semantic text
- Preservation of scholarly apparatus
- Publication-ready formatting
- Validation reports

**Time savings: Weeks → Hours**

## Next Steps

1. **Proof of concept**: Add paragraph breaks (thick blue line, right-click)
2. **User feedback**: Does the workflow feel natural?
3. **Prioritize annotation types**: Which 3-5 types are most critical?
4. **Design context menu**: Layout, shortcuts, visual design
5. **Prototype OCR integration**: One annotation type end-to-end

---

*This document describes a transformational feature for scholarly OCR that could set PhilOcr apart as the premier tool for digitizing critical editions, manuscripts, and scholarly texts with complex apparatus.*
