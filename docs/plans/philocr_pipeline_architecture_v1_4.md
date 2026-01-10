# PhilOcr Pipeline Architecture v1.4

## Document Purpose

This document defines the OCR pipeline for PhilOcr, designed to extract clean Greek text from scanned scholarly editions while excluding contaminating elements (line numbers, page numbers, footnotes, headers).

**Document Status**: Implementation specification
**Version**: 1.4
**Date**: 2026-01-10

---

## Design Goal

The aim of PhilOcr is **not** to produce a typographically faithful digital edition, and it is **not** to preserve page layout, marginalia, or scholarly apparatus through OCR.

The aim is to recover a **clean, contiguous stream of Greek body text**, in correct reading order, with minimal contamination, such that it can be reliably aligned back to an existing reference scaffold (Stephanus, Bekker, etc.) and used for downstream linguistic, philosophical, and translational work.

### The Three Essential Requirements

To achieve that, the system must do only three things, and no more:

1. **Prevent non-body material from ever reaching OCR.** Headers, page numbers, line numbers, footnotes, and marginalia are not "errors" to be corrected later. They are noise to be geometrically excluded upstream. If they reach OCR, the system has already failed.

2. **Treat geometry as authoritative and OCR as advisory.** Geometry decides what text exists and where. OCR merely supplies candidate strings for already-defined body regions. No attempt is made to preserve or infer references, layout semantics, or scholarly structure during OCR itself.

3. **Support deterministic reattachment of references after the fact.** References are not preserved through the pipeline. They are recovered later by matching clean text against known reference texts or positional oracles (e.g., Foxit), using ordered, sequential alignment.

### What Is Explicitly Out of Scope

- Character-level OCR correction
- Guessing editorial intent
- Merging apparatus with body text
- Perfect page-by-page accuracy
- Preserving layout through OCR

### Success Criterion

The success criterion is **not** "how accurate is the OCR output on its own", but:

> **Can the extracted body text be aligned monotonically to an authoritative reference text with high confidence and low manual intervention?**

If the answer is yes, the system has succeeded—even if the OCR text is messy, even if accents are wrong, even if occasional words are dropped.

This framing keeps the design from over-engineering itself. Anything that does not directly serve **clean body extraction + reliable alignment** is a liability, not a feature.

---

## Core Principles

**Principle 1: Geometry is authoritative. OCR is advisory.**

The template determines structure. OCR merely fills in characters. When geometry and OCR disagree, geometry wins.

**Principle 2: Contamination is the problem, not OCR accuracy.**

The system succeeds by preventing noise from reaching OCR, not by correcting it afterward.

**Principle 3: The template is a statistical mask, not a semantic model.**

The template encodes "where body text typically appears" based on robust statistics. It does not encode meaning, intent, or scholarly structure.

**Principle 4: Masking is canonical. Cropping is optional and lossy.**

Masking preserves coordinate continuity and allows later lookup or overlay without extra transforms. Cropping is permitted but loses global coordinate consistency.

**Principle 5: Heuristics are labeled as heuristics.**

Soft rules (margin detection, poetry detection, indent classification) are explicitly flagged as heuristic, not structural truth. They may fail on edge cases.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Configuration Parameters](#2-configuration-parameters)
3. [Stage 1: Image Normalisation](#3-stage-1-image-normalisation)
4. [Stage 2: Template Extraction & Zone Masking](#4-stage-2-template-extraction--zone-masking)
5. [Stage 3: OCR on Masked Body Region](#5-stage-3-ocr-on-masked-body-region)
6. [Stage 4: Text Assembly](#6-stage-4-text-assembly)
7. [Data Structures](#7-data-structures)
8. [Utility Functions](#8-utility-functions)
9. [Performance Optimization](#9-performance-optimization)
10. [Implementation Plan](#10-implementation-plan)
11. [Testing Strategy](#11-testing-strategy)
12. [Error Handling](#12-error-handling)
13. [Cost Analysis](#13-cost-analysis)

---

## 1. Architecture Overview

### 1.1 The Problem

Scholarly Greek editions contain elements that contaminate OCR output:
- Line numbers in margins (e.g., "5", "10", "15")
- Page numbers in headers or footers
- Running heads (section/chapter titles)
- Footnotes and apparatus criticus
- Marginal annotations

When OCR processes the full page, these elements get merged into body text.

### 1.2 The Solution

**Mask the contaminants before OCR, not after.**

```
┌─────────────────────────────────────────────────────────────────┐
│                    STAGE 1: IMAGE NORMALISATION                  │
│                                                                  │
│  PDF Page → Raster (PNG) → Deskew → Stable Geometry             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│            STAGE 2: TEMPLATE EXTRACTION & ZONE MASKING           │
│                                                                  │
│  2a: Analyse multiple pages → Extract DocumentTemplate          │
│  2b: Apply template → Mask/crop to body region only             │
│                                                                  │
│  Output: Masked images with only body text visible              │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│              STAGE 3: OCR ON MASKED BODY REGION                  │
│                                                                  │
│  Masked image → Document AI → Full OCR response                 │
│                                                                  │
│  ONE request per page (not per line)                            │
│  Document AI handles line detection within body region          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    STAGE 4: TEXT ASSEMBLY                        │
│                                                                  │
│  OCR text → Reading order concatenation → Clean body stream     │
│                                                                  │
│  Geometry is authoritative. OCR structure is advisory.          │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 What Changed from v1.1

| Aspect | v1.1 (Over-engineered) | v1.2+ (Practical) |
|--------|------------------------|-------------------|
| OCR granularity | One crop per line | One masked image per page |
| API calls per page | ~30-50 | 1 |
| Line detection | Custom, pre-OCR | Document AI handles it |
| Template role | Structural scaffold | Statistical mask |
| Stage 4 role | Layout reconstruction | Simple text assembly |
| Complexity | High | Low |

### 1.4 Why This Works

The actual problem is **contamination**, not **structure detection**. Document AI is good at detecting lines and paragraphs within a clean region. It's bad at knowing what to exclude.

By masking the page before OCR:
- Line numbers never reach the OCR engine
- Page headers/footers are invisible
- Footnotes are excluded from body
- Document AI sees only what matters

---

## 2. Configuration Parameters

### 2.1 Tunable Thresholds

All detection algorithms use configurable thresholds that can be adjusted for different document types or scan quality:

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class PipelineConfig:
    """Configuration parameters for the OCR pipeline."""
    
    # === STAGE 1: Image Normalisation ===
    target_dpi: int = 300
    output_format: str = "PNG"
    deskew_threshold: float = 0.1  # Degrees; only correct if > this
    
    # === STAGE 2a: Zone Detection ===
    header_search_percent: float = 0.15  # Search top 15% for header
    footer_search_percent: float = 0.15  # Search bottom 15% for footer
    margin_search_percent: float = 0.20  # Search outer 20% for margins
    content_threshold: float = 0.05  # Min % of row/column that must be ink
    min_gap_size: int = 20  # Pixels; minimum gap to consider significant
    
    # === STAGE 2a: Margin Detection ===
    margin_smooth_sigma: float = 5.0  # Gaussian smoothing sigma for profiles
    transition_threshold: float = 0.5  # Gradient threshold for margin boundary
    margin_default_percent: float = 0.05  # Default margin if detection fails
    
    # === STAGE 2a: Footnote Detection ===
    footnote_search_percent: float = 0.40  # Search lower 40% of body
    horizontal_rule_min_width: float = 0.2  # Min 20% of width for rule
    footnote_gap_min_size: int = 30  # Pixels; minimum gap for footnote separator
    
    # === STAGE 2b: Template Extraction ===
    template_sample_size: int = 20  # Pages to sample for template
    template_min_pages: int = 5  # Minimum pages required
    template_skip_first: int = 2  # Skip first N pages (often title/contents)
    template_skip_last: int = 2  # Skip last N pages (often index/blank)
    outlier_threshold: float = 2.0  # MAD multiplier for outlier detection
    
    # === STAGE 2c: Masking Strategy ===
    use_cropping: bool = False  # True = crop, False = mask (default)
    crop_padding: int = 0  # Extra pixels around body when cropping
    
    # === STAGE 3: OCR ===
    ocr_max_retries: int = 3
    ocr_retry_backoff_base: float = 2.0  # Exponential backoff multiplier
    ocr_rate_limit_per_minute: int = 15
    
    # === STAGE 4: Assembly ===
    indent_ratio_threshold_1: float = 0.02  # < 2% = flush left
    indent_ratio_threshold_2: float = 0.06  # < 6% = standard indent
    
    # === STAGE 4: Genre Detection (Heuristic) ===
    verse_avg_line_threshold: int = 60  # Chars; below suggests verse
    verse_cv_threshold: float = 0.3  # Coefficient of variation; below suggests verse
    speaker_ratio_threshold: float = 0.15  # Ratio of lines with speaker markers
    fragment_ratio_threshold: float = 0.2  # Ratio of fragment markers to paragraphs
    
    # === Validation ===
    min_template_confidence: float = 0.5  # Below this, use defaults
    min_ocr_confidence: float = 0.3  # Below this, flag for review
    min_genre_confidence: float = 0.5  # Below this, default to prose
    
    # === Performance ===
    stage1_parallel_workers: int = 4
    stage2a_parallel_workers: int = 4
    stage3_batch_size: int = 1  # For future batch API support
```

### 2.2 Configuration File Format

Configuration can be provided as YAML or JSON:

```yaml
# config.yaml
stage1:
  target_dpi: 300
  deskew_threshold: 0.1

stage2a:
  header_search_percent: 0.15
  footer_search_percent: 0.15
  margin_search_percent: 0.20
  content_threshold: 0.05
  min_gap_size: 20

stage2b:
  template_sample_size: 20
  template_min_pages: 5
  outlier_threshold: 2.0

stage2c:
  use_cropping: false

stage3:
  ocr_max_retries: 3
  ocr_rate_limit_per_minute: 15

stage4:
  poetry_avg_line_length_threshold: 50
  poetry_line_length_cv_threshold: 0.3

validation:
  min_template_confidence: 0.5
  min_ocr_confidence: 0.3
```

---

## 3. Stage 1: Image Normalisation

### 3.1 Purpose

Convert PDF pages to stable raster images with consistent geometry.

### 3.2 Processing

```python
import numpy as np
from pathlib import Path

def normalise_page(
    pdf_path: str, 
    page_num: int, 
    output_dir: str,
    config: PipelineConfig
) -> 'PageImage':
    """
    Convert PDF page to normalised raster image.
    
    Args:
        pdf_path: Path to source PDF
        page_num: Page number (0-indexed)
        output_dir: Directory for output images
        config: Pipeline configuration
    
    Returns:
        PageImage with metadata about the normalised image
    """
    # Render PDF page
    image = render_pdf_page(pdf_path, page_num, dpi=config.target_dpi)
    
    # Convert to grayscale
    image = convert_to_grayscale(image)
    
    # Deskew if needed
    skew_angle = detect_skew(image)
    if abs(skew_angle) > config.deskew_threshold:
        image = rotate_image(image, -skew_angle)
    
    # Save
    output_path = Path(output_dir) / f"page_{page_num:04d}.png"
    save_image(image, str(output_path))
    
    return PageImage(
        page_num=page_num,
        path=str(output_path),
        dpi=config.target_dpi,
        width=image.shape[1],
        height=image.shape[0],
        skew_corrected=skew_angle
    )
```

### 3.3 Output

- Directory of normalised PNG images
- Manifest with page metadata

---

## 4. Stage 2: Template Extraction & Zone Masking

### 4.1 Purpose

Analyse multiple pages to establish document-wide zone boundaries, then mask each page to expose only the body region.

### 4.2 Critical Concept: The Template is a Statistical Mask

The template is **not** "canonical layout parameters for the document" in a semantic sense. It is a **statistical mask** that encodes "where body text typically appears" based on robust statistics across multiple pages.

This distinction matters because it changes how aggressively we trust the template:

**Hard Rule**: Below `min_template_confidence` (default 0.5), the system **must** fall back to conservative defaults. It must **not** attempt clever inference or heuristic recovery.

**Rationale**: A low-confidence template means the document has unusual or inconsistent layout. Aggressive masking based on unreliable statistics will cause data loss. Conservative defaults (wide body region, no footnote detection) are safer.

### 4.3 The Template Model

```python
from dataclasses import dataclass
from typing import Optional, List
import json

@dataclass
class DocumentTemplate:
    """
    Statistical mask for body region detection.
    
    NOT a semantic model of document structure.
    All measurements in pixels at 300 DPI.
    """
    
    # Page dimensions
    page_width: int
    page_height: int
    
    # Body region (the text we want)
    body_left: int
    body_right: int
    body_top: int
    body_bottom: int
    
    # Excluded zones
    header_bottom: int          # Everything above this is header
    footer_top: int             # Everything below this is footer
    left_margin_right: int      # Left margin ends here (line numbers)
    right_margin_left: int      # Right margin starts here
    footnote_separator_y: Optional[int]  # Footnotes below this line (None if no footnotes)
    
    # Detection metadata
    pages_analysed: int
    confidence: float
    has_line_numbers_left: bool
    has_line_numbers_right: bool
    has_footnotes: bool
    
    def to_json(self, path: str) -> None:
        """Save template to JSON file."""
        with open(path, 'w') as f:
            json.dump(self.__dict__, f, indent=2)
    
    @classmethod
    def from_json(cls, path: str) -> 'DocumentTemplate':
        """Load template from JSON file."""
        with open(path, 'r') as f:
            data = json.load(f)
        return cls(**data)
```

### 4.3 Zone Measurements Collector

```python
from typing import List, Tuple
import numpy as np

@dataclass
class PageZones:
    """Zone boundaries detected on a single page."""
    page_width: int
    page_height: int
    header_bottom: int
    footer_top: int
    left_margin_right: int
    right_margin_left: int
    footnote_separator_y: Optional[int]
    body_left: int
    body_right: int
    body_top: int
    body_bottom: int


class ZoneMeasurements:
    """
    Collects zone measurements from multiple pages for template extraction.
    """
    
    def __init__(self):
        self.page_widths: List[int] = []
        self.page_heights: List[int] = []
        self.body_lefts: List[int] = []
        self.body_rights: List[int] = []
        self.body_tops: List[int] = []
        self.body_bottoms: List[int] = []
        self.header_bottoms: List[int] = []
        self.footer_tops: List[int] = []
        self.left_margin_rights: List[int] = []
        self.right_margin_lefts: List[int] = []
        self.footnote_separators: List[int] = []
        self.has_line_numbers_left: List[bool] = []
        self.has_line_numbers_right: List[bool] = []
        self.has_footnotes: List[bool] = []
    
    def add(self, zones: PageZones) -> None:
        """Add measurements from a single page."""
        self.page_widths.append(zones.page_width)
        self.page_heights.append(zones.page_height)
        self.body_lefts.append(zones.body_left)
        self.body_rights.append(zones.body_right)
        self.body_tops.append(zones.body_top)
        self.body_bottoms.append(zones.body_bottom)
        self.header_bottoms.append(zones.header_bottom)
        self.footer_tops.append(zones.footer_top)
        self.left_margin_rights.append(zones.left_margin_right)
        self.right_margin_lefts.append(zones.right_margin_left)
        if zones.footnote_separator_y is not None:
            self.footnote_separators.append(zones.footnote_separator_y)
        self.has_footnotes.append(zones.footnote_separator_y is not None)
        
        # Line number detection would be added here
        # For now, use heuristic: if left margin > 5% of page width, likely has line numbers
        margin_ratio = zones.left_margin_right / zones.page_width if zones.page_width > 0 else 0
        self.has_line_numbers_left.append(margin_ratio > 0.08)
        self.has_line_numbers_right.append(False)  # Less common
    
    def calculate_confidence(self) -> float:
        """
        Calculate template confidence based on measurement consistency.
        
        Uses coefficient of variation (CV) across measurements.
        Lower CV = higher confidence.
        """
        if len(self.page_widths) < 3:
            return 0.5
        
        # Calculate CV for key measurements
        cvs = []
        for measurements in [
            self.page_widths, self.page_heights,
            self.body_lefts, self.body_rights,
            self.header_bottoms, self.footer_tops
        ]:
            if len(measurements) > 1:
                mean_val = np.mean(measurements)
                std_val = np.std(measurements)
                cv = std_val / mean_val if mean_val > 0 else 1.0
                cvs.append(cv)
        
        # Confidence is inverse of average CV, capped at 1.0
        avg_cv = np.mean(cvs) if cvs else 1.0
        confidence = max(0.0, min(1.0, 1.0 - avg_cv))
        
        return float(confidence)
    
    def detected(self, feature: str) -> bool:
        """
        Check if a feature was detected on majority of pages.
        
        Args:
            feature: 'line_numbers_left', 'line_numbers_right', or 'footnotes'
        
        Returns:
            True if detected on >50% of pages
        """
        if feature == 'line_numbers_left':
            values = self.has_line_numbers_left
        elif feature == 'line_numbers_right':
            values = self.has_line_numbers_right
        elif feature == 'footnotes':
            values = self.has_footnotes
        else:
            return False
        
        if not values:
            return False
        
        return sum(values) / len(values) > 0.5
```

### 4.4 Template Extraction Algorithm

```python
def extract_template(
    normalised_images: List['PageImage'],
    config: PipelineConfig
) -> DocumentTemplate:
    """
    Analyse multiple pages to establish consistent zone boundaries.
    
    Strategy:
    1. Sample pages from throughout document (avoiding title/index pages)
    2. Detect zones on each page
    3. Use robust median with outlier detection
    4. Calculate confidence based on consistency
    """
    
    # Sample pages evenly across document
    sample_indices = select_sample_pages(
        len(normalised_images),
        config.template_sample_size,
        config.template_skip_first,
        config.template_skip_last,
        config.template_min_pages
    )
    
    measurements = ZoneMeasurements()
    
    for idx in sample_indices:
        image = load_image(normalised_images[idx].path)
        zones = detect_page_zones(image, config)
        measurements.add(zones)
    
    # Extract template using robust statistics with outlier detection
    template = DocumentTemplate(
        page_width=robust_median_with_outliers(
            measurements.page_widths, config.outlier_threshold
        )[0],
        page_height=robust_median_with_outliers(
            measurements.page_heights, config.outlier_threshold
        )[0],
        body_left=robust_median_with_outliers(
            measurements.body_lefts, config.outlier_threshold
        )[0],
        body_right=robust_median_with_outliers(
            measurements.body_rights, config.outlier_threshold
        )[0],
        body_top=robust_median_with_outliers(
            measurements.body_tops, config.outlier_threshold
        )[0],
        body_bottom=robust_median_with_outliers(
            measurements.body_bottoms, config.outlier_threshold
        )[0],
        header_bottom=robust_median_with_outliers(
            measurements.header_bottoms, config.outlier_threshold
        )[0],
        footer_top=robust_median_with_outliers(
            measurements.footer_tops, config.outlier_threshold
        )[0],
        left_margin_right=robust_median_with_outliers(
            measurements.left_margin_rights, config.outlier_threshold
        )[0],
        right_margin_left=robust_median_with_outliers(
            measurements.right_margin_lefts, config.outlier_threshold
        )[0],
        footnote_separator_y=robust_median_with_outliers(
            measurements.footnote_separators, config.outlier_threshold
        )[0] if measurements.footnote_separators else None,
        pages_analysed=len(sample_indices),
        confidence=measurements.calculate_confidence(),
        has_line_numbers_left=measurements.detected('line_numbers_left'),
        has_line_numbers_right=measurements.detected('line_numbers_right'),
        has_footnotes=measurements.detected('footnotes')
    )
    
    return template


def select_sample_pages(
    total_pages: int,
    sample_size: int,
    skip_first: int = 2,
    skip_last: int = 2,
    min_pages: int = 5
) -> List[int]:
    """
    Select representative pages for template extraction.
    
    Strategy:
    - Skip first N pages (often title/contents)
    - Skip last N pages (often index/blank)
    - Distribute evenly across remaining pages
    - If document is too short, use all available pages
    
    Args:
        total_pages: Total number of pages in document
        sample_size: Desired number of pages to sample
        skip_first: Number of pages to skip at start
        skip_last: Number of pages to skip at end
        min_pages: Minimum pages required for sampling
    
    Returns:
        List of page indices (0-based) to use for template extraction
    """
    if total_pages <= min_pages:
        # Use all pages if document is short
        return list(range(total_pages))
    
    available = total_pages - skip_first - skip_last
    
    if available <= 0:
        # Fallback: skip less
        skip_first = min(skip_first, total_pages // 4)
        skip_last = min(skip_last, total_pages // 4)
        available = total_pages - skip_first - skip_last
    
    if available <= sample_size:
        # Not enough pages to sample; use all available
        return list(range(skip_first, total_pages - skip_last))
    
    # Distribute evenly across available pages
    step = available / sample_size
    indices = [
        skip_first + int(i * step)
        for i in range(sample_size)
    ]
    
    return indices


def robust_median_with_outliers(
    values: List[int],
    outlier_threshold: float = 2.0
) -> Tuple[int, List[int]]:
    """
    Calculate median while identifying and excluding outliers.
    
    Uses Median Absolute Deviation (MAD) for robust outlier detection.
    
    Args:
        values: List of integer measurements
        outlier_threshold: Number of MADs to consider outlier (default 2.0)
    
    Returns:
        Tuple of (median_value, outlier_indices)
    """
    if not values:
        return 0, []
    
    if len(values) < 3:
        return int(np.median(values)), []
    
    # Calculate median and MAD
    med = np.median(values)
    deviations = [abs(v - med) for v in values]
    mad = np.median(deviations) if deviations else 0
    
    # If MAD is zero or very small, no outliers possible
    if mad < 1.0:
        return int(med), []
    
    # Identify outliers
    outliers = [
        i for i, v in enumerate(values)
        if abs(v - med) > outlier_threshold * mad
    ]
    
    # Recalculate median excluding outliers if found
    if outliers and len(outliers) < len(values) / 2:
        clean_values = [v for i, v in enumerate(values) if i not in outliers]
        med = np.median(clean_values)
    
    return int(med), outliers
```

### 4.5 Zone Detection (Per Page)

```python
def detect_page_zones(image: np.ndarray, config: PipelineConfig) -> PageZones:
    """
    Detect zones on a single page using projection profiles.
    
    Args:
        image: Grayscale image (numpy array, 0-255)
        config: Pipeline configuration with detection thresholds
    
    Returns:
        PageZones dataclass with detected boundaries
    """
    height, width = image.shape[:2]
    
    # Horizontal projection (sum across rows) → find vertical boundaries
    h_profile = np.sum(255 - image, axis=1).astype(float)
    
    # Vertical projection (sum across columns) → find horizontal boundaries
    v_profile = np.sum(255 - image, axis=0).astype(float)
    
    # Normalize profiles to [0, 1] for threshold comparison
    h_max = np.max(h_profile)
    v_max = np.max(v_profile)
    h_profile_norm = h_profile / h_max if h_max > 0 else h_profile
    v_profile_norm = v_profile / v_max if v_max > 0 else v_profile
    
    # Find content boundaries using threshold
    content_threshold = config.content_threshold
    content_rows = np.where(h_profile_norm > content_threshold)[0]
    content_cols = np.where(v_profile_norm > content_threshold)[0]
    
    content_top = int(content_rows[0]) if len(content_rows) > 0 else 0
    content_bottom = int(content_rows[-1]) if len(content_rows) > 0 else height
    content_left = int(content_cols[0]) if len(content_cols) > 0 else 0
    content_right = int(content_cols[-1]) if len(content_cols) > 0 else width
    
    # Detect header zone (isolated content at top)
    header_bottom = detect_header_boundary(
        h_profile, content_top, height, config
    )
    
    # Detect footer zone (isolated content at bottom)
    footer_top = detect_footer_boundary(
        h_profile, content_bottom, height, config
    )
    
    # Detect left margin (narrow column of content, typically line numbers)
    left_margin_right = detect_left_margin(
        v_profile, content_left, width, config
    )
    
    # Detect right margin
    right_margin_left = detect_right_margin(
        v_profile, content_right, width, config
    )
    
    # Detect footnote separator (horizontal gap or rule in lower body)
    footnote_sep = detect_footnote_separator(
        image, header_bottom, footer_top, config
    )
    
    return PageZones(
        page_width=width,
        page_height=height,
        header_bottom=header_bottom,
        footer_top=footer_top,
        left_margin_right=left_margin_right,
        right_margin_left=right_margin_left,
        footnote_separator_y=footnote_sep,
        body_left=left_margin_right,
        body_right=right_margin_left,
        body_top=header_bottom,
        body_bottom=footnote_sep if footnote_sep else footer_top
    )
```

### 4.6 Header/Footer Detection

```python
@dataclass
class Gap:
    """Represents a gap in a profile."""
    start: int
    end: int


def detect_header_boundary(
    h_profile: np.ndarray,
    content_top: int,
    height: int,
    config: PipelineConfig
) -> int:
    """
    Find where header ends and body begins.
    
    Strategy: Look for a significant gap in the horizontal profile
    within the top N% of the page (configurable).
    
    Args:
        h_profile: Horizontal projection profile (sum of pixels per row)
        content_top: First row with content
        height: Total page height
        config: Configuration with search percentage and gap threshold
    
    Returns:
        Y-coordinate where header zone ends
    """
    search_limit = int(height * config.header_search_percent)
    search_limit = min(search_limit, content_top + search_limit)
    
    if search_limit <= content_top:
        return content_top
    
    # Find gaps (runs of low values) in the profile
    search_region = h_profile[content_top:search_limit]
    gaps = find_gaps(search_region, config.min_gap_size)
    
    if gaps:
        # Header ends at the first significant gap
        return content_top + gaps[0].end
    else:
        # No clear header; use top of content
        return content_top


def detect_footer_boundary(
    h_profile: np.ndarray,
    content_bottom: int,
    height: int,
    config: PipelineConfig
) -> int:
    """
    Find where body ends and footer begins.
    
    Strategy: Look for a significant gap in the horizontal profile
    within the bottom N% of the page (configurable).
    
    Args:
        h_profile: Horizontal projection profile
        content_bottom: Last row with content
        height: Total page height
        config: Configuration with search percentage and gap threshold
    
    Returns:
        Y-coordinate where footer zone starts
    """
    search_start = int(height * (1 - config.footer_search_percent))
    search_start = max(search_start, content_bottom - int(height * config.footer_search_percent))
    
    if search_start >= content_bottom:
        return content_bottom
    
    # Find gaps in the profile (searching backwards from bottom)
    search_region = h_profile[search_start:content_bottom]
    gaps = find_gaps(search_region, config.min_gap_size)
    
    if gaps:
        # Footer starts at the last significant gap
        return search_start + gaps[-1].start
    else:
        # No clear footer; use bottom of content
        return content_bottom


def find_gaps(
    profile: np.ndarray,
    min_gap_size: int,
    threshold_percentile: float = 0.1
) -> List[Gap]:
    """
    Find gaps (runs of low values) in a projection profile.
    
    Args:
        profile: 1D array of profile values
        min_gap_size: Minimum gap size in pixels to consider
        threshold_percentile: Percentile to use as "low" threshold (default 0.1)
    
    Returns:
        List of Gap objects (start, end positions)
    """
    if len(profile) == 0:
        return []
    
    # Determine threshold: values below this percentile are considered gaps
    threshold = np.percentile(profile, threshold_percentile * 100)
    
    # Find runs of values below threshold
    below_threshold = profile < threshold
    
    gaps = []
    in_gap = False
    gap_start = 0
    
    for i, is_low in enumerate(below_threshold):
        if is_low and not in_gap:
            # Start of new gap
            gap_start = i
            in_gap = True
        elif not is_low and in_gap:
            # End of gap
            gap_size = i - gap_start
            if gap_size >= min_gap_size:
                gaps.append(Gap(start=gap_start, end=i))
            in_gap = False
    
    # Handle gap at end of profile
    if in_gap:
        gap_size = len(profile) - gap_start
        if gap_size >= min_gap_size:
            gaps.append(Gap(start=gap_start, end=len(profile)))
    
    return gaps
```

### 4.7 Margin Detection (Line Numbers)

**WARNING: This is a heuristic, not structural truth.**

The margin detection logic assumes line numbers form a sparse column distinct from dense body text. This works well for typical scholarly editions but may produce false positives on:
- Editions with wide margins but no line numbers
- Documents with marginal annotations that resemble body text
- Unusual page layouts

The current threshold (`margin_ratio > 0.08`) is acceptable for v1 but should be flagged as tunable.

```python
def detect_left_margin(
    v_profile: np.ndarray,
    content_left: int,
    width: int,
    config: PipelineConfig
) -> int:
    """
    HEURISTIC: Detect left margin boundary (where line numbers end, body begins).
    
    Strategy: 
    1. Line numbers form a narrow column of sparse content
    2. Body text forms a dense column
    3. Find the transition point using gradient analysis
    
    Args:
        v_profile: Vertical projection profile (sum of pixels per column)
        content_left: Leftmost column with content
        width: Total page width
        config: Configuration with search percentage and thresholds
    
    Returns:
        X-coordinate where left margin ends (body begins)
    """
    search_limit = int(width * config.margin_search_percent)
    search_limit = min(search_limit, content_left + search_limit)
    
    if search_limit <= content_left:
        return content_left + int(width * config.margin_default_percent)
    
    # Smooth the profile to reduce noise
    search_region = v_profile[:search_limit]
    smoothed = gaussian_smooth(search_region, config.margin_smooth_sigma)
    
    # Find the column where density increases significantly (body starts)
    # This is typically a step change in the profile
    gradient = np.gradient(smoothed)
    
    # Find largest positive gradient (transition from sparse to dense)
    transition_points = find_significant_transitions(
        gradient, config.transition_threshold
    )
    
    if transition_points:
        return content_left + transition_points[0]
    else:
        # No clear margin; use default percentage
        return content_left + int(width * config.margin_default_percent)


def detect_right_margin(
    v_profile: np.ndarray,
    content_right: int,
    width: int,
    config: PipelineConfig
) -> int:
    """
    Detect right margin boundary.
    
    Similar to left margin but searching from the right.
    
    Args:
        v_profile: Vertical projection profile
        content_right: Rightmost column with content
        width: Total page width
        config: Configuration with search percentage and thresholds
    
    Returns:
        X-coordinate where right margin starts (body ends)
    """
    search_start = int(width * (1 - config.margin_search_percent))
    search_start = max(search_start, content_right - int(width * config.margin_search_percent))
    
    if search_start >= content_right:
        return content_right - int(width * config.margin_default_percent)
    
    # Search region is from search_start to end
    search_region = v_profile[search_start:]
    smoothed = gaussian_smooth(search_region, config.margin_smooth_sigma)
    gradient = np.gradient(smoothed)
    
    # Find largest negative gradient (transition from dense to sparse)
    # Negate gradient to find where it drops (transition from body to margin)
    transition_points = find_significant_transitions(
        -gradient, config.transition_threshold
    )
    
    if transition_points:
        return search_start + transition_points[-1]
    else:
        return content_right - int(width * config.margin_default_percent)


def gaussian_smooth(
    signal: np.ndarray,
    sigma: float
) -> np.ndarray:
    """
    Apply Gaussian smoothing to a 1D signal.
    
    Uses scipy.ndimage.gaussian_filter1d for efficient smoothing.
    
    Args:
        signal: 1D array to smooth
        sigma: Standard deviation of Gaussian kernel
    
    Returns:
        Smoothed signal (same length as input)
    """
    from scipy.ndimage import gaussian_filter1d
    return gaussian_filter1d(signal.astype(float), sigma=sigma)


def find_significant_transitions(
    gradient: np.ndarray,
    threshold: float
) -> List[int]:
    """
    Find significant transition points in a gradient signal.
    
    Args:
        gradient: 1D array of gradient values
        threshold: Minimum gradient magnitude to consider significant
    
    Returns:
        List of indices where significant transitions occur
    """
    if len(gradient) == 0:
        return []
    
    # Normalize gradient to [0, 1] for threshold comparison
    abs_gradient = np.abs(gradient)
    max_grad = np.max(abs_gradient)
    
    if max_grad == 0:
        return []
    
    normalized = abs_gradient / max_grad
    
    # Find peaks above threshold
    above_threshold = normalized > threshold
    
    # Find indices where gradient crosses threshold
    transitions = []
    for i in range(1, len(above_threshold)):
        if above_threshold[i] and not above_threshold[i-1]:
            # Rising edge
            transitions.append(i)
        elif not above_threshold[i] and above_threshold[i-1]:
            # Falling edge
            transitions.append(i-1)
    
    return sorted(set(transitions))
```

### 4.8 Footnote Separator Detection

```python
def detect_footnote_separator(
    image: np.ndarray,
    body_top: int,
    body_bottom: int,
    config: PipelineConfig
) -> Optional[int]:
    """
    Detect footnote separator within the body region.
    
    Types of separators:
    1. Horizontal rule (thin line)
    2. Large whitespace gap
    3. Row of markers (*, †, etc.)
    
    Args:
        image: Full page image
        body_top: Top of body region
        body_bottom: Bottom of body region
        config: Configuration with search percentage and gap thresholds
    
    Returns:
        Y-coordinate of footnote separator, or None if not found
    """
    body_height = body_bottom - body_top
    if body_height <= 0:
        return None
    
    # Search in lower N% of body region (configurable)
    search_start_percent = 1.0 - config.footnote_search_percent
    search_top = body_top + int(body_height * search_start_percent)
    search_region = image[search_top:body_bottom, :]
    
    if search_region.size == 0:
        return None
    
    # Method 1: Detect horizontal rule
    rule_y = detect_horizontal_rule(search_region, config)
    if rule_y is not None:
        return search_top + rule_y
    
    # Method 2: Detect large gap
    h_profile = np.sum(255 - search_region, axis=1)
    gaps = find_gaps(h_profile, config.footnote_gap_min_size)
    
    if gaps:
        # Use the first large gap as separator
        return search_top + gaps[0].start
    
    # No footnote separator detected
    return None


def detect_horizontal_rule(
    region: np.ndarray,
    config: PipelineConfig
) -> Optional[int]:
    """
    Detect a horizontal line (footnote separator rule).
    
    A horizontal rule is identified by:
    - A row with significant dark pixels (configurable minimum width)
    - Surrounded by mostly white space (above and below)
    - Thin (not multiple rows of text)
    
    Args:
        region: Image region to search (body lower portion)
        config: Configuration with minimum rule width threshold
    
    Returns:
        Y-coordinate of rule (relative to region top), or None
    """
    height, width = region.shape[:2]
    
    if height < 5 or width == 0:
        return None
    
    min_rule_width = int(width * config.horizontal_rule_min_width)
    
    for y in range(1, height - 3):
        row = region[y, :]
        
        # Check if row has a continuous dark segment
        dark_pixels = np.where(row < 128)[0]
        
        if len(dark_pixels) >= min_rule_width:
            # Check if it's a thin line (not text)
            # Rule should have white space above and below
            above_mean = np.mean(region[max(0, y-2):y, :])
            below_mean = np.mean(region[y+1:min(height, y+4), :])
            
            # Both above and below should be mostly white
            if above_mean > 200 and below_mean > 200:
                return y
    
    return None
```

### 4.9 Applying the Template: Masking (Canonical)

**Masking is the canonical approach.** It preserves coordinate continuity with the original page, allowing later Foxit-style lookup or overlay without extra transforms.

Cropping is permitted as an alternative (see 4.10) but is **optional and lossy** with respect to global coordinates.

```python
def mask_page(
    image_path: str, 
    template: DocumentTemplate, 
    output_path: str,
    config: PipelineConfig
) -> 'MaskedPage':
    """
    Apply template to mask non-body regions (CANONICAL approach).
    
    Masking whites-out non-body regions while preserving image dimensions
    and coordinate system. This allows direct coordinate mapping between
    OCR output and original page positions.
    
    Args:
        image_path: Path to normalised image
        template: Document template with zone boundaries
        output_path: Where to save masked image
        config: Configuration (determines mask vs crop)
    
    Returns:
        MaskedPage with metadata
    """
    image = load_image(image_path)
    masked = image.copy()
    
    # Mask header (white out)
    masked[0:template.header_bottom, :] = 255
    
    # Mask footer
    masked[template.footer_top:, :] = 255
    
    # Mask left margin (line numbers)
    masked[template.header_bottom:template.footer_top, 0:template.left_margin_right] = 255
    
    # Mask right margin
    masked[template.header_bottom:template.footer_top, template.right_margin_left:] = 255
    
    # Mask footnotes (if detected)
    if template.footnote_separator_y:
        masked[template.footnote_separator_y:template.footer_top, 
               template.left_margin_right:template.right_margin_left] = 255
    
    save_image(masked, output_path)
    
    return MaskedPage(
        page_num=extract_page_num(image_path),
        original_path=image_path,
        masked_path=output_path,
        body_bounds=BoundingBox(
            x1=template.body_left,
            y1=template.body_top,
            x2=template.body_right,
            y2=template.body_bottom
        )
    )
```

### 4.10 Alternative: Cropping Instead of Masking

```python
def crop_to_body(
    image_path: str,
    template: DocumentTemplate,
    config: PipelineConfig,
    output_path: str
) -> 'CroppedPage':
    """
    Alternative: Crop to body region only.
    
    Pros: Smaller image, faster OCR
    Cons: Lose coordinate consistency with original (requires transformation)
    
    Args:
        image_path: Path to original normalised image
        template: Document template with body bounds
        config: Configuration (may include crop_padding)
        output_path: Where to save cropped image
    
    Returns:
        CroppedPage with offset information for coordinate transformation
    """
    image = load_image(image_path)
    
    # Apply padding if configured
    padding = config.crop_padding
    
    # Crop to body bounds with padding
    top = max(0, template.body_top - padding)
    bottom = min(image.shape[0], template.body_bottom + padding)
    left = max(0, template.body_left - padding)
    right = min(image.shape[1], template.body_right + padding)
    
    body_image = image[top:bottom, left:right]
    
    save_image(body_image, output_path)
    
    return CroppedPage(
        page_num=extract_page_num(image_path),
        original_path=image_path,
        cropped_path=output_path,
        crop_offset=(left, top),
        crop_size=(body_image.shape[1], body_image.shape[0]),
        original_size=(image.shape[1], image.shape[0])
    )


def transform_ocr_coordinates(
    ocr_bbox: 'BoundingBox',
    crop_offset: Tuple[int, int]
) -> 'BoundingBox':
    """
    Transform OCR coordinates from cropped space to original page space.
    
    This is required when using cropping instead of masking.
    
    Args:
        ocr_bbox: Bounding box from OCR (in cropped image coordinates)
        crop_offset: (x, y) offset of crop region in original image
    
    Returns:
        Bounding box in original page coordinates
    """
    offset_x, offset_y = crop_offset
    
    return BoundingBox(
        x1=ocr_bbox.x1 + offset_x,
        y1=ocr_bbox.y1 + offset_y,
        x2=ocr_bbox.x2 + offset_x,
        y2=ocr_bbox.y2 + offset_y
    )


def choose_masking_strategy(config: PipelineConfig) -> str:
    """
    Determine whether to use masking or cropping.
    
    Args:
        config: Pipeline configuration
    
    Returns:
        'mask' or 'crop'
    """
    if config.use_cropping:
        return 'crop'
    return 'mask'
```

---

## 5. Stage 3: OCR on Masked Body Region

### 5.1 Purpose

Send the masked/cropped image to Document AI. One request per page.

### 5.2 Critical Constraint: OCR Structure is Advisory

Document AI returns paragraph and line segmentation along with text. This structure is **advisory, not authoritative**.

- **Authoritative**: The raw text string (`response.document.text`)
- **Advisory**: Paragraph boundaries, line boundaries, block structure

Document AI provides candidate segmentation. Geometry-derived constraints (from Stage 2) may override it if needed. In practice, for clean body extraction, we primarily use the raw text and treat structural metadata as optional hints.

**Why this matters**: Document AI may merge or split paragraphs in ways that violate indent geometry. If we treat OCR structure as ground truth, we reintroduce layout dependence that Stage 2 was designed to eliminate.

### 5.2 Processing

```python
import asyncio
from typing import Any

async def ocr_masked_page(
    masked_page: 'MaskedPage',
    rate_limiter: 'RateLimiter',
    document_ai_client: Any
) -> 'OCRResult':
    """
    Send masked page to Document AI for OCR.
    
    Document AI handles:
    - Line detection
    - Word detection
    - Character recognition
    
    We just send the image and receive text.
    
    Args:
        masked_page: MaskedPage object with path to masked image
        rate_limiter: Rate limiter for API calls
        document_ai_client: Document AI client instance
    
    Returns:
        OCRResult with extracted text and structure
    """
    await rate_limiter.acquire()
    
    image_bytes = load_image_bytes(masked_page.masked_path)
    
    try:
        response = await document_ai_client.process_document(
            content=image_bytes,
            mime_type='image/png'
        )
        
        return OCRResult(
            page_num=masked_page.page_num,
            text=response.document.text,
            blocks=extract_blocks(response),
            paragraphs=extract_paragraphs(response),
            lines=extract_lines(response),
            confidence=calculate_average_confidence(response),
            raw_response=response
        )
        
    except Exception as e:
        return OCRResult(
            page_num=masked_page.page_num,
            text="",
            blocks=[],
            paragraphs=[],
            lines=[],
            confidence=0.0,
            error=str(e)
        )


def extract_blocks(response: Any) -> List['TextBlock']:
    """Extract block-level structure from Document AI response."""
    blocks = []
    
    for page in response.document.pages:
        for block in page.blocks:
            text = extract_text_from_layout(response.document.text, block.layout)
            blocks.append(TextBlock(
                text=text,
                confidence=block.layout.confidence,
                bbox=layout_to_bbox(block.layout.bounding_poly)
            ))
    
    return blocks


def extract_paragraphs(response: Any) -> List['TextParagraph']:
    """Extract paragraph-level structure from Document AI response."""
    paragraphs = []
    
    for page in response.document.pages:
        for para in page.paragraphs:
            text = extract_text_from_layout(response.document.text, para.layout)
            paragraphs.append(TextParagraph(
                text=text,
                confidence=para.layout.confidence,
                bbox=layout_to_bbox(para.layout.bounding_poly)
            ))
    
    return paragraphs


def extract_lines(response: Any) -> List['TextLine']:
    """Extract line-level structure from Document AI response."""
    lines = []
    
    for page in response.document.pages:
        for line in page.lines:
            text = extract_text_from_layout(response.document.text, line.layout)
            lines.append(TextLine(
                text=text,
                confidence=line.layout.confidence,
                bbox=layout_to_bbox(line.layout.bounding_poly)
            ))
    
    return lines
```

### 5.3 What Document AI Returns

Document AI provides rich structure that we can use:

```json
{
  "text": "Full extracted text...",
  "pages": [
    {
      "blocks": [
        {
          "layout": {
            "textAnchor": {"textSegments": [{"startIndex": 0, "endIndex": 100}]},
            "confidence": 0.98,
            "boundingPoly": {"vertices": [...]}
          }
        }
      ],
      "paragraphs": [...],
      "lines": [...],
      "tokens": [...]
    }
  ]
}
```

We use Document AI's paragraph detection as a starting point, then refine with template knowledge in Stage 4.

---

## 6. Stage 4: Text Assembly

### 6.1 Purpose

Concatenate OCR text in reading order to produce a clean body stream.

**Critical constraint**: Stage 4 interprets; it does not rediscover structure. Geometry was authoritative in Stage 2. OCR provided candidate strings in Stage 3. Stage 4 simply assembles the result.

### 6.2 What Stage 4 Does

1. Takes OCR text from Stage 3
2. Normalises Unicode (NFC)
3. Cleans whitespace
4. Concatenates pages in order
5. Outputs a clean text stream

### 6.3 What Stage 4 Does NOT Do

- Reconstruct layout from OCR structure
- Override geometry with OCR paragraph detection
- Infer scholarly semantics
- Correct OCR errors

**Document AI's paragraph and line structure is advisory, not authoritative.** If we use it at all, it is as a convenience for initial segmentation, not as ground truth.

### 6.4 Assembly Logic

```python
def assemble_page(ocr_result: 'OCRResult') -> 'PageOutput':
    """
    Assemble page output from OCR result.
    
    This is intentionally simple. The goal is clean text extraction,
    not layout reconstruction.
    
    Args:
        ocr_result: OCR result from Document AI
    
    Returns:
        PageOutput with normalised text
    """
    if not ocr_result.text:
        return PageOutput(
            page_num=ocr_result.page_num,
            full_text="",
            confidence=0.0
        )
    
    # Normalise and clean the text
    clean_text = normalise_text(ocr_result.text)
    
    return PageOutput(
        page_num=ocr_result.page_num,
        full_text=clean_text,
        confidence=ocr_result.confidence
    )


def normalise_text(text: str) -> str:
    """
    Normalise OCR output text.
    
    This is intentionally conservative. We are not trying to "fix" Greek,
    only to produce consistent Unicode that can be aligned later.
    
    Args:
        text: Raw text from OCR
    
    Returns:
        Normalised text (NFC Unicode, cleaned whitespace)
    """
    import unicodedata
    
    # Unicode NFC normalisation (critical for Greek)
    text = unicodedata.normalize('NFC', text)
    
    # Collapse multiple spaces to single space
    # Preserve paragraph breaks (double newlines)
    lines = text.split('\n')
    lines = [' '.join(line.split()) for line in lines]
    text = '\n'.join(lines)
    
    return text.strip()
```

### 6.5 Optional: Genre Detection Hints (Heuristic)

Genre detection provides **triangulation metadata** for later reconstruction. Even approximate classification is valuable because it constrains downstream formatting decisions.

**WARNING**: These are soft heuristics. They may misclassify edge cases. The hints are advisory, not authoritative.

#### 6.5.1 Genre Types

| Genre | CSS Class | Characteristics | Examples |
|-------|-----------|-----------------|----------|
| `prose` | `format-prose` | Continuous paragraphs, variable line lengths, justified text | Plato's dialogues (narrative), Aristotle's treatises |
| `verse` | `format-verse` | Line-by-line display, consistent short lines, significant line breaks | Homer, Hesiod, tragedy choruses |
| `speakers` | `format-speakers` | Speaker-attributed turns, speaker names at line starts | Plato's dialogues (dramatic portions) |
| `verse_speakers` | `format-verse-speakers` | Line-by-line with speaker attributions | Tragedy/comedy dialogue |
| `fragments` | `format-fragments` | Numbered fragment units, discontinuous text | Pre-Socratic fragments, papyrus editions |

#### 6.5.2 Detection Heuristics

```python
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum
import re


class GenreHint(Enum):
    """Genre classification for downstream formatting."""
    PROSE = "prose"
    VERSE = "verse"
    SPEAKERS = "speakers"
    VERSE_SPEAKERS = "verse_speakers"
    FRAGMENTS = "fragments"
    UNKNOWN = "unknown"


@dataclass
class GenreDetectionResult:
    """Result of genre detection with confidence scores."""
    primary_genre: GenreHint
    confidence: float  # 0.0 to 1.0
    signals: dict  # Evidence that led to classification
    

def detect_genre_hint(
    ocr_result: 'OCRResult',
    config: 'PipelineConfig'
) -> GenreDetectionResult:
    """
    HEURISTIC: Detect likely genre of text content.
    
    This is triangulation metadata for later reconstruction.
    Even approximate classification constrains formatting decisions.
    
    Strategy:
    1. Analyse line length distribution (verse vs prose)
    2. Detect speaker patterns (dialogue detection)
    3. Detect fragment markers (fragment detection)
    4. Combine signals with confidence weighting
    
    Args:
        ocr_result: OCR result with text and line structure
        config: Configuration with detection thresholds
    
    Returns:
        GenreDetectionResult with genre hint and confidence
    """
    if not ocr_result.text or len(ocr_result.text.strip()) < 50:
        return GenreDetectionResult(
            primary_genre=GenreHint.UNKNOWN,
            confidence=0.0,
            signals={"reason": "insufficient_text"}
        )
    
    signals = {}
    
    # === SIGNAL 1: Line length distribution (verse indicator) ===
    line_stats = analyse_line_lengths(ocr_result)
    signals["line_stats"] = line_stats
    is_verse_like = (
        line_stats["avg_length"] < config.verse_avg_line_threshold and
        line_stats["cv"] < config.verse_cv_threshold
    )
    
    # === SIGNAL 2: Speaker patterns (dialogue indicator) ===
    speaker_stats = detect_speaker_patterns(ocr_result.text)
    signals["speaker_stats"] = speaker_stats
    has_speakers = speaker_stats["speaker_ratio"] > config.speaker_ratio_threshold
    
    # === SIGNAL 3: Fragment markers (fragment indicator) ===
    fragment_stats = detect_fragment_patterns(ocr_result.text)
    signals["fragment_stats"] = fragment_stats
    has_fragments = fragment_stats["fragment_ratio"] > config.fragment_ratio_threshold
    
    # === COMBINE SIGNALS ===
    
    # Priority: fragments > verse_speakers > speakers > verse > prose
    if has_fragments:
        return GenreDetectionResult(
            primary_genre=GenreHint.FRAGMENTS,
            confidence=fragment_stats["confidence"],
            signals=signals
        )
    
    if is_verse_like and has_speakers:
        return GenreDetectionResult(
            primary_genre=GenreHint.VERSE_SPEAKERS,
            confidence=min(line_stats["confidence"], speaker_stats["confidence"]),
            signals=signals
        )
    
    if has_speakers:
        return GenreDetectionResult(
            primary_genre=GenreHint.SPEAKERS,
            confidence=speaker_stats["confidence"],
            signals=signals
        )
    
    if is_verse_like:
        return GenreDetectionResult(
            primary_genre=GenreHint.VERSE,
            confidence=line_stats["confidence"],
            signals=signals
        )
    
    # Default to prose
    return GenreDetectionResult(
        primary_genre=GenreHint.PROSE,
        confidence=0.7,  # Prose is the default assumption
        signals=signals
    )


def analyse_line_lengths(ocr_result: 'OCRResult') -> dict:
    """
    Analyse line length distribution for verse detection.
    
    Verse characteristics:
    - Short, consistent line lengths
    - Low coefficient of variation
    - Lines often end mid-sentence
    
    Prose characteristics:
    - Variable line lengths (justified to margins)
    - Higher coefficient of variation
    - Lines break at word boundaries, not semantic units
    """
    import numpy as np
    
    lines = ocr_result.text.split('\n')
    line_lengths = [len(line.strip()) for line in lines if line.strip()]
    
    if len(line_lengths) < 5:
        return {
            "avg_length": 0,
            "std_length": 0,
            "cv": float('inf'),
            "confidence": 0.0
        }
    
    avg_length = np.mean(line_lengths)
    std_length = np.std(line_lengths)
    cv = std_length / avg_length if avg_length > 0 else float('inf')
    
    # Confidence based on how clearly verse-like or prose-like
    if cv < 0.2 and avg_length < 60:
        confidence = 0.9  # Very clearly verse
    elif cv < 0.3 and avg_length < 80:
        confidence = 0.7  # Probably verse
    elif cv > 0.5:
        confidence = 0.8  # Probably prose
    else:
        confidence = 0.5  # Ambiguous
    
    return {
        "avg_length": float(avg_length),
        "std_length": float(std_length),
        "cv": float(cv),
        "line_count": len(line_lengths),
        "confidence": confidence
    }


def detect_speaker_patterns(text: str) -> dict:
    """
    Detect speaker attribution patterns for dialogue detection.
    
    Common patterns in Greek editions:
    - "ΣΩ." or "ΣΩΚ." (Socrates)
    - "ΠΡΩ." (Protagoras)
    - All-caps names followed by period/colon
    - Names at start of lines/paragraphs
    
    Also detects Latin speaker markers in bilingual editions:
    - "SO." or "SOC."
    - Names in small caps
    """
    # Greek speaker patterns (all caps, 2-4 letters, followed by period)
    greek_speaker_pattern = r'^[\s]*([Α-Ω]{2,4})\.\s'
    
    # Latin/transliterated speaker patterns
    latin_speaker_pattern = r'^[\s]*([A-Z]{2,4})\.\s'
    
    # Extended name patterns (e.g., "ΣΩΚΡΑΤΗΣ" or "SOCRATES")
    full_name_pattern = r'^[\s]*([Α-Ω]{4,12}|[A-Z]{4,12})[\.\:]\s'
    
    lines = text.split('\n')
    total_lines = len([l for l in lines if l.strip()])
    
    if total_lines == 0:
        return {"speaker_ratio": 0.0, "confidence": 0.0, "patterns_found": []}
    
    speaker_lines = 0
    patterns_found = []
    
    for line in lines:
        if not line.strip():
            continue
        
        # Check each pattern
        for pattern in [greek_speaker_pattern, latin_speaker_pattern, full_name_pattern]:
            match = re.match(pattern, line)
            if match:
                speaker_lines += 1
                patterns_found.append(match.group(1))
                break
    
    speaker_ratio = speaker_lines / total_lines
    
    # Confidence based on consistency of patterns
    unique_speakers = len(set(patterns_found))
    if speaker_ratio > 0.3 and 2 <= unique_speakers <= 10:
        confidence = 0.9  # Clear dialogue with multiple speakers
    elif speaker_ratio > 0.2 and unique_speakers >= 2:
        confidence = 0.7  # Probably dialogue
    elif speaker_ratio > 0.1:
        confidence = 0.5  # Possible dialogue
    else:
        confidence = 0.3  # Unlikely dialogue
    
    return {
        "speaker_ratio": speaker_ratio,
        "speaker_lines": speaker_lines,
        "total_lines": total_lines,
        "unique_speakers": unique_speakers,
        "patterns_found": list(set(patterns_found))[:10],  # Sample
        "confidence": confidence
    }


def detect_fragment_patterns(text: str) -> dict:
    """
    Detect fragment numbering patterns.
    
    Common patterns in fragment editions:
    - "Fr. 1", "Fr. 12", "Frag. 1"
    - "B1", "B12" (Diels-Kranz numbering)
    - "1.", "12." at start of sections
    - "[1]", "[12]" bracketed numbers
    - "§1", "§12" section markers
    
    Fragment editions typically have:
    - Discontinuous text
    - Frequent numbering
    - Short isolated passages
    """
    # Fragment number patterns
    patterns = [
        r'Fr(?:ag)?\.?\s*\d+',  # Fr. 1, Frag. 12
        r'\b[AB]\d+\b',  # B1, A12 (Diels-Kranz)
        r'^\s*\d{1,3}\.\s',  # 1. at line start
        r'\[\d{1,3}\]',  # [1], [12]
        r'§\s*\d+',  # §1, § 12
    ]
    
    fragment_markers = 0
    total_paragraphs = len([p for p in text.split('\n\n') if p.strip()])
    
    if total_paragraphs == 0:
        return {"fragment_ratio": 0.0, "confidence": 0.0}
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.MULTILINE)
        fragment_markers += len(matches)
    
    # Ratio of fragment markers to paragraphs
    fragment_ratio = fragment_markers / total_paragraphs if total_paragraphs > 0 else 0
    
    # High ratio suggests fragment edition
    if fragment_ratio > 0.5:
        confidence = 0.9
    elif fragment_ratio > 0.3:
        confidence = 0.7
    elif fragment_ratio > 0.1:
        confidence = 0.5
    else:
        confidence = 0.2
    
    return {
        "fragment_ratio": fragment_ratio,
        "fragment_markers": fragment_markers,
        "total_paragraphs": total_paragraphs,
        "confidence": confidence
    }
```

#### 6.5.3 Configuration Parameters

Add these to `PipelineConfig`:

```python
# === GENRE DETECTION (Heuristic) ===
verse_avg_line_threshold: int = 60  # Chars; below suggests verse
verse_cv_threshold: float = 0.3  # Coefficient of variation; below suggests verse
speaker_ratio_threshold: float = 0.15  # Ratio of lines with speaker markers
fragment_ratio_threshold: float = 0.2  # Ratio of fragment markers to paragraphs
```

#### 6.5.4 Usage in PageOutput

```python
@dataclass
class PageOutput:
    """Final processed output for a single page."""
    page_num: int
    full_text: str
    confidence: float
    genre_hint: Optional[GenreHint] = None  # Advisory, not authoritative
    genre_confidence: float = 0.0
    genre_signals: Optional[dict] = None  # For debugging/inspection
```

#### 6.5.5 Important Caveats

1. **Mixed genres**: A single document may contain multiple genres (e.g., Plato's dialogues have prose narrative + speaker-attributed dialogue + occasional verse quotations). The hint applies to the **dominant** genre of a page or section.

2. **Edition variation**: The same text may appear differently in different editions. A critical edition of Homer looks different from a school text.

3. **OCR artifacts**: Speaker detection may false-positive on OCR errors that look like abbreviations.

4. **Confidence thresholds**: Downstream systems should check `genre_confidence` and fall back to safe defaults (usually `prose`) when confidence is low.

### 6.6 Optional: Indent Hints (Heuristic)

If downstream processing benefits from paragraph hints, indent classification can be provided **as metadata, not as authoritative structure**.

**WARNING**: This is a soft heuristic. It may fail on editions with unusual formatting.

```python
def classify_indent_hint(
    x_position: int,
    body_left: int,
    body_right: int
) -> int:
    """
    HEURISTIC: Classify indent level based on x-position.
    
    This is advisory metadata, not structural truth.
    
    0 = flush left (likely continuation)
    1 = standard indent (likely new paragraph)
    2 = deep indent (likely quotation)
    
    Args:
        x_position: X-coordinate of line start
        body_left: Left boundary of body region
        body_right: Right boundary of body region
    
    Returns:
        Indent hint (0, 1, or 2)
    """
    body_width = body_right - body_left
    
    if body_width <= 0:
        return 0
    
    relative_x = x_position - body_left
    indent_ratio = relative_x / body_width
    
    if indent_ratio < 0.02:
        return 0  # Flush left
    elif indent_ratio < 0.06:
        return 1  # Standard indent
    else:
        return 2  # Deep indent
```

### 6.4 Document Assembly

```python
from statistics import mean

def assemble_document(
    page_outputs: List['PageOutput'],
    template: DocumentTemplate,
    metadata: 'DocumentMetadata'
) -> 'Document':
    """
    Assemble all pages into final document.
    
    Args:
        page_outputs: List of PageOutput objects
        template: Document template used for processing
        metadata: Document metadata (title, source, etc.)
    
    Returns:
        Complete Document object
    """
    confidences = [p.confidence for p in page_outputs if p.confidence > 0]
    
    return Document(
        metadata=metadata,
        template=template,
        pages=page_outputs,
        full_text='\n\n'.join(p.full_text for p in page_outputs),
        statistics=DocumentStatistics(
            total_pages=len(page_outputs),
            total_paragraphs=sum(len(p.paragraphs) for p in page_outputs),
            average_confidence=mean(confidences) if confidences else 0.0,
            pages_with_errors=[p.page_num for p in page_outputs if p.confidence == 0]
        )
    )
```

---

## 7. Data Structures

### 7.1 Core Data Types

```python
from dataclasses import dataclass, field
from typing import List, Optional, Any, Tuple
import json


@dataclass
class BoundingBox:
    """Bounding box for text regions."""
    x1: int  # Left
    y1: int  # Top
    x2: int  # Right
    y2: int  # Bottom
    
    @property
    def width(self) -> int:
        return self.x2 - self.x1
    
    @property
    def height(self) -> int:
        return self.y2 - self.y1
```

### 7.2 Stage 1 Output

```python
@dataclass
class PageImage:
    """Output from Stage 1: normalised page image."""
    page_num: int
    path: str
    dpi: int
    width: int
    height: int
    skew_corrected: float
```

### 7.3 Stage 2 Output

```python
@dataclass
class MaskedPage:
    """Output from Stage 2: masked page ready for OCR."""
    page_num: int
    original_path: str
    masked_path: str
    body_bounds: BoundingBox


@dataclass
class CroppedPage:
    """Alternative output from Stage 2: cropped page."""
    page_num: int
    original_path: str
    cropped_path: str
    crop_offset: Tuple[int, int]  # (x, y) offset for coordinate transformation
    crop_size: Tuple[int, int]    # (width, height) of cropped image
    original_size: Tuple[int, int]  # (width, height) of original image
```

### 7.4 Stage 3 Output

```python
@dataclass
class TextBlock:
    """Block-level text structure from OCR."""
    text: str
    confidence: float
    bbox: BoundingBox


@dataclass
class TextParagraph:
    """Paragraph-level text structure from OCR."""
    text: str
    confidence: float
    bbox: BoundingBox


@dataclass
class TextLine:
    """Line-level text structure from OCR."""
    text: str
    confidence: float
    bbox: BoundingBox


@dataclass
class OCRResult:
    """Complete OCR result for a single page."""
    page_num: int
    text: str
    blocks: List[TextBlock]
    paragraphs: List[TextParagraph]
    lines: List[TextLine]
    confidence: float
    error: Optional[str] = None
    raw_response: Optional[Any] = None
```

### 7.5 Stage 4 Output

```python
@dataclass
class Paragraph:
    """Processed paragraph with indent classification."""
    text: str
    indent_class: int  # 0=flush, 1=standard, 2=deep
    confidence: float
    bbox: BoundingBox


@dataclass
class PageOutput:
    """Final processed output for a single page."""
    page_num: int
    paragraphs: List[Paragraph]
    full_text: str
    confidence: float
    content_type: str = 'prose'  # 'prose' or 'poetry'


@dataclass
class DocumentMetadata:
    """Metadata about the source document."""
    title: str
    source_path: str
    author: Optional[str] = None
    edition: Optional[str] = None
    year: Optional[int] = None


@dataclass
class DocumentStatistics:
    """Statistics about the processed document."""
    total_pages: int
    total_paragraphs: int
    average_confidence: float
    pages_with_errors: List[int]


@dataclass
class Document:
    """Complete processed document."""
    metadata: DocumentMetadata
    template: DocumentTemplate
    pages: List[PageOutput]
    full_text: str
    statistics: DocumentStatistics
    
    def to_json(self, path: str) -> None:
        """Save document to JSON file."""
        # Convert dataclasses to dicts for JSON serialization
        data = {
            'metadata': self.metadata.__dict__,
            'template': self.template.__dict__,
            'pages': [
                {
                    'page_num': p.page_num,
                    'paragraphs': [
                        {
                            'text': para.text,
                            'indent_class': para.indent_class,
                            'confidence': para.confidence,
                            'bbox': para.bbox.__dict__
                        }
                        for para in p.paragraphs
                    ],
                    'full_text': p.full_text,
                    'confidence': p.confidence,
                    'content_type': p.content_type
                }
                for p in self.pages
            ],
            'full_text': self.full_text,
            'statistics': self.statistics.__dict__
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
```

### 7.6 Template JSON Example

```json
{
  "page_width": 2550,
  "page_height": 3300,
  "body_left": 350,
  "body_right": 2200,
  "body_top": 200,
  "body_bottom": 2850,
  "header_bottom": 180,
  "footer_top": 3100,
  "left_margin_right": 350,
  "right_margin_left": 2200,
  "footnote_separator_y": 2850,
  "pages_analysed": 20,
  "confidence": 0.92,
  "has_line_numbers_left": true,
  "has_line_numbers_right": false,
  "has_footnotes": true
}
```

### 7.7 Directory Structure

```
project/
├── input/
│   └── plato_republic_1903.pdf
│
├── stage1_normalised/
│   ├── manifest.json
│   ├── page_0001.png
│   └── ...
│
├── stage2_masked/
│   ├── template.json
│   ├── page_0001_masked.png
│   └── ...
│
├── stage3_ocr/
│   ├── page_0001_ocr.json
│   └── ...
│
└── stage4_output/
    ├── page_0001.json
    ├── document.json
    └── document.txt
```

---

## 8. Utility Functions

### 8.1 Image I/O

```python
import numpy as np
from pathlib import Path
from typing import Union
import cv2


def load_image(path: Union[str, Path]) -> np.ndarray:
    """
    Load an image as a grayscale numpy array.
    
    Args:
        path: Path to image file
    
    Returns:
        Grayscale image as numpy array (0-255)
    """
    image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise FileNotFoundError(f"Could not load image: {path}")
    return image


def save_image(image: np.ndarray, path: Union[str, Path]) -> None:
    """
    Save a numpy array as an image file.
    
    Args:
        image: Image as numpy array
        path: Output path
    """
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(path), image)


def load_image_bytes(path: Union[str, Path]) -> bytes:
    """
    Load an image file as bytes (for API calls).
    
    Args:
        path: Path to image file
    
    Returns:
        Image file contents as bytes
    """
    with open(path, 'rb') as f:
        return f.read()
```

### 8.2 PDF Rendering

```python
import fitz  # PyMuPDF


def render_pdf_page(
    pdf_path: str, 
    page_num: int, 
    dpi: int = 300
) -> np.ndarray:
    """
    Render a PDF page to a numpy array.
    
    Args:
        pdf_path: Path to PDF file
        page_num: Page number (0-indexed)
        dpi: Resolution for rendering
    
    Returns:
        Page image as numpy array
    """
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_num)
    
    # Calculate zoom factor for desired DPI
    zoom = dpi / 72  # PDF default is 72 DPI
    matrix = fitz.Matrix(zoom, zoom)
    
    # Render to pixmap
    pixmap = page.get_pixmap(matrix=matrix)
    
    # Convert to numpy array
    image = np.frombuffer(pixmap.samples, dtype=np.uint8)
    image = image.reshape(pixmap.height, pixmap.width, pixmap.n)
    
    doc.close()
    return image


def convert_to_grayscale(image: np.ndarray) -> np.ndarray:
    """
    Convert image to grayscale.
    
    Args:
        image: Input image (may be color or grayscale)
    
    Returns:
        Grayscale image
    """
    if len(image.shape) == 2:
        return image  # Already grayscale
    elif image.shape[2] == 4:
        return cv2.cvtColor(image, cv2.COLOR_RGBA2GRAY)
    else:
        return cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
```

### 8.3 Deskewing

```python
def detect_skew(image: np.ndarray) -> float:
    """
    Detect skew angle of a document image.
    
    Args:
        image: Grayscale image
    
    Returns:
        Skew angle in degrees (positive = clockwise)
    """
    # Threshold to binary
    _, binary = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # Find coordinates of all black pixels
    coords = np.column_stack(np.where(binary > 0))
    
    if len(coords) < 100:
        return 0.0
    
    # Fit a minimum area rectangle
    rect = cv2.minAreaRect(coords)
    angle = rect[-1]
    
    # Adjust angle
    if angle < -45:
        angle = 90 + angle
    elif angle > 45:
        angle = angle - 90
    
    return angle


def rotate_image(image: np.ndarray, angle: float) -> np.ndarray:
    """
    Rotate an image by a given angle.
    
    Args:
        image: Input image
        angle: Rotation angle in degrees (positive = counterclockwise)
    
    Returns:
        Rotated image
    """
    height, width = image.shape[:2]
    center = (width // 2, height // 2)
    
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(
        image, matrix, (width, height),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE
    )
    
    return rotated
```

### 8.4 Document AI Helpers

```python
from typing import Any


def extract_text_from_layout(full_text: str, layout: Any) -> str:
    """
    Extract text for a layout element using text anchors.
    
    Args:
        full_text: Complete document text
        layout: Layout object with textAnchor
    
    Returns:
        Text content for this layout element
    """
    if not layout.text_anchor or not layout.text_anchor.text_segments:
        return ""
    
    text_parts = []
    for segment in layout.text_anchor.text_segments:
        start = int(segment.start_index) if segment.start_index else 0
        end = int(segment.end_index) if segment.end_index else len(full_text)
        text_parts.append(full_text[start:end])
    
    return ''.join(text_parts)


def layout_to_bbox(bounding_poly: Any) -> BoundingBox:
    """
    Convert Document AI bounding polygon to BoundingBox.
    
    Args:
        bounding_poly: Document AI BoundingPoly object
    
    Returns:
        BoundingBox with integer coordinates
    """
    if not bounding_poly.vertices:
        return BoundingBox(x1=0, y1=0, x2=0, y2=0)
    
    vertices = bounding_poly.vertices
    x_coords = [v.x for v in vertices if v.x is not None]
    y_coords = [v.y for v in vertices if v.y is not None]
    
    if not x_coords or not y_coords:
        return BoundingBox(x1=0, y1=0, x2=0, y2=0)
    
    return BoundingBox(
        x1=int(min(x_coords)),
        y1=int(min(y_coords)),
        x2=int(max(x_coords)),
        y2=int(max(y_coords))
    )


def calculate_average_confidence(response: Any) -> float:
    """
    Calculate average confidence across all text blocks.
    
    Args:
        response: Document AI response
    
    Returns:
        Average confidence (0.0-1.0)
    """
    confidences = []
    
    for page in response.document.pages:
        for block in page.blocks:
            if block.layout.confidence:
                confidences.append(block.layout.confidence)
    
    return sum(confidences) / len(confidences) if confidences else 0.0


def extract_page_num(image_path: str) -> int:
    """
    Extract page number from image filename.
    
    Expects format: page_XXXX.png
    
    Args:
        image_path: Path to image file
    
    Returns:
        Page number (0-indexed)
    """
    import re
    match = re.search(r'page_(\d+)', image_path)
    if match:
        return int(match.group(1))
    return 0
```

---

## 9. Performance Optimization

### 9.1 Parallelization Strategy

The pipeline can be significantly accelerated by parallelizing independent operations:

#### Stage 1: Image Normalisation

```python
from concurrent.futures import ThreadPoolExecutor

def normalise_all_pages(
    pdf_path: str,
    page_range: range,
    output_dir: str,
    config: PipelineConfig
) -> List[PageImage]:
    """
    Normalise multiple pages in parallel.
    """
    with ThreadPoolExecutor(max_workers=config.stage1_parallel_workers) as executor:
        futures = [
            executor.submit(normalise_page, pdf_path, p, output_dir, config)
            for p in page_range
        ]
        return [f.result() for f in futures]
```

**Rationale**: PDF rendering and image processing are I/O and CPU intensive but independent per page.

#### Stage 2a: Zone Detection

```python
def detect_zones_for_template(
    normalised_images: List[PageImage],
    sample_indices: List[int],
    config: PipelineConfig
) -> List[PageZones]:
    """
    Detect zones on multiple pages in parallel for template extraction.
    """
    with ThreadPoolExecutor(max_workers=config.stage2a_parallel_workers) as executor:
        futures = [
            executor.submit(
                detect_page_zones, 
                load_image(normalised_images[i].path), 
                config
            )
            for i in sample_indices
        ]
        return [f.result() for f in futures]
```

**Rationale**: Zone detection is CPU-intensive image processing that can run concurrently.

#### Stage 3: OCR Processing

```python
async def ocr_all_pages(
    masked_pages: List[MaskedPage],
    rate_limiter: 'RateLimiter',
    document_ai_client: Any,
    config: PipelineConfig
) -> List[OCRResult]:
    """
    Process OCR for multiple pages with rate limiting.
    
    Note: Rate limiting prevents true parallelization, but async allows
    efficient waiting and concurrent request preparation.
    """
    semaphore = asyncio.Semaphore(config.ocr_rate_limit_per_minute)
    
    async def ocr_with_semaphore(page: MaskedPage) -> OCRResult:
        async with semaphore:
            return await ocr_with_retry(page, rate_limiter, document_ai_client, config)
    
    tasks = [ocr_with_semaphore(page) for page in masked_pages]
    return await asyncio.gather(*tasks)
```

**Rationale**: Rate limiting prevents parallel API calls, but async allows efficient I/O waiting.

### 9.2 Caching Strategy

```python
import hashlib
import os

def get_template_cache_key(normalised_images: List[PageImage]) -> str:
    """
    Generate cache key from image metadata.
    
    Uses page dimensions and file sizes to detect if template needs recalculation.
    """
    metadata = {
        'count': len(normalised_images),
        'pages': [
            {'width': img.width, 'height': img.height, 'dpi': img.dpi}
            for img in normalised_images[:10]  # Sample first 10
        ]
    }
    return hashlib.sha256(json.dumps(metadata, sort_keys=True).encode()).hexdigest()


def load_or_extract_template(
    normalised_images: List[PageImage],
    cache_dir: str,
    config: PipelineConfig
) -> DocumentTemplate:
    """
    Load template from cache if available, otherwise extract and cache.
    """
    cache_key = get_template_cache_key(normalised_images)
    cache_path = os.path.join(cache_dir, f"template_{cache_key}.json")
    
    if os.path.exists(cache_path):
        return DocumentTemplate.from_json(cache_path)
    
    template = extract_template(normalised_images, config)
    template.to_json(cache_path)
    
    return template
```

### 9.3 Memory Management

For large documents (1000+ pages), consider streaming:

```python
from typing import Iterator

def process_large_document(
    pdf_path: str,
    output_dir: str,
    config: PipelineConfig,
    batch_size: int = 50
) -> Iterator[PageOutput]:
    """
    Process document in batches to manage memory.
    
    Yields PageOutput objects as batches complete.
    """
    import fitz
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    doc.close()
    
    # Stage 1: Normalise all pages (necessary for template)
    all_images = normalise_all_pages(pdf_path, range(total_pages), output_dir, config)
    
    # Stage 2: Extract template from sample
    template = extract_template(all_images[:config.template_sample_size], config)
    
    # Stage 3-4: Process in batches
    for batch_start in range(0, len(all_images), batch_size):
        batch_end = min(batch_start + batch_size, len(all_images))
        batch_images = all_images[batch_start:batch_end]
        
        # Mask batch
        masked_dir = os.path.join(output_dir, 'stage2_masked')
        masked = [
            mask_page(
                img.path, 
                template, 
                os.path.join(masked_dir, f"page_{img.page_num:04d}_masked.png"),
                config
            )
            for img in batch_images
        ]
        
        # OCR batch (would need async context in practice)
        # ocr_results = await ocr_all_pages(masked, rate_limiter, client, config)
        
        # Assemble batch
        # outputs = [assemble_page(ocr, template, config) for ocr in ocr_results]
        
        # yield from outputs
        pass  # Placeholder for actual implementation
```

### 9.4 Expected Performance

| Stage | Operation | Time per Page | 100 Pages | 1000 Pages |
|-------|-----------|---------------|-----------|------------|
| Stage 1 | PDF render + deskew | 0.5s | 50s (parallel) | 8min (parallel) |
| Stage 2a | Zone detection (sample 20) | 2s | 40s (parallel) | 40s (parallel) |
| Stage 2b | Template extraction | - | 1s | 1s |
| Stage 2c | Masking | 0.1s | 10s (parallel) | 2min (parallel) |
| Stage 3 | OCR (rate limited) | 4s | 7min | 67min |
| Stage 4 | Assembly | 0.05s | 5s | 50s |
| **Total** | | | **~8min** | **~78min** |

**Note**: Stage 3 is the bottleneck due to API rate limits. Consider batch API if available.

---

## 10. Implementation Plan

### 10.1 Module Structure

```
src/philocr/
├── pipeline/
│   ├── __init__.py
│   ├── orchestrator.py       # Coordinates all stages
│   ├── stage1_normalise.py   # PDF → normalised images
│   ├── stage2_template.py    # Template extraction
│   ├── stage2_mask.py        # Apply template masking
│   ├── stage3_ocr.py         # Document AI calls
│   └── stage4_assemble.py    # Final assembly
├── detection/
│   ├── __init__.py
│   ├── profiles.py           # Projection profile analysis
│   ├── zones.py              # Zone boundary detection
│   └── separators.py         # Footnote separator detection
├── processing/
│   ├── document_ai.py        # Existing Document AI client
│   └── pdf_utils.py          # Existing PDF utilities
├── models/
│   ├── __init__.py
│   ├── config.py             # PipelineConfig
│   ├── template.py           # DocumentTemplate
│   ├── page.py               # Page-related dataclasses
│   └── document.py           # Document dataclasses
└── utils/
    ├── __init__.py
    ├── image_io.py           # load_image, save_image
    ├── pdf_render.py         # render_pdf_page
    └── docai_helpers.py      # Document AI utilities
```

### 10.2 Implementation Order

**Week 1: Stage 1 + Basic Stage 2**
- Image normalisation (builds on existing PDF handling)
- Basic zone detection using projection profiles
- Manual validation on 10 test pages

**Week 2: Template Extraction**
- Multi-page analysis
- Robust statistics (median, MAD)
- Template JSON output
- Validation visualisation tool

**Week 3: Masking + Stage 3**
- Template application (masking)
- Integration with existing Document AI code
- OCR on masked images
- Compare results with full-page OCR

**Week 4: Stage 4 + Integration**
- Assembly logic
- Full pipeline orchestration
- End-to-end testing
- Documentation

### 10.3 Dependencies

```
# Core
opencv-python>=4.8.0    # Image processing
numpy>=1.24.0           # Array operations
scipy>=1.11.0           # Signal processing (smoothing, peak detection)

# Existing
PyMuPDF>=1.23.0         # PDF rendering
google-cloud-documentai # OCR
Pillow>=10.0.0          # Image I/O

# Optional
pyyaml>=6.0             # YAML config support
```

---

## 11. Testing Strategy

### 11.1 Template Extraction Validation

```python
def test_template_extraction():
    """Validate template extraction on known document."""
    
    # Process a document with known layout
    template = extract_template(test_images, config)
    
    # Verify template matches expected values (±tolerance)
    assert abs(template.body_left - EXPECTED_BODY_LEFT) < 20
    assert abs(template.left_margin_right - EXPECTED_MARGIN) < 20
    assert template.has_line_numbers_left == True
    assert template.confidence > 0.7
```

### 11.2 Masking Validation

```python
def test_masking_excludes_line_numbers():
    """Verify line numbers are masked out."""
    
    masked = mask_page(test_image_path, template, output_path, config)
    masked_img = load_image(masked.masked_path)
    
    # Left margin should be white
    left_margin = masked_img[:, 0:template.left_margin_right]
    assert np.mean(left_margin) > 250  # Nearly all white
```

### 11.3 OCR Comparison Test

```python
def test_ocr_without_contamination():
    """Compare OCR results: masked vs unmasked."""
    import re
    
    # OCR on original (unmasked) image
    original_result = await ocr_page(original_image)
    
    # OCR on masked image
    masked_result = await ocr_page(masked_image)
    
    # Masked result should NOT contain line numbers at line starts
    assert not re.search(r'^\d{1,3}\s+', masked_result.text, re.MULTILINE)
    
    # Masked result should contain body text
    assert 'ἄνδρα μοι ἔννεπε' in masked_result.text
```

### 11.4 Visual Validation Tool

```python
def visualise_template(
    image_path: str, 
    template: DocumentTemplate, 
    output_path: str
) -> None:
    """
    Draw template boundaries on image for visual validation.
    """
    import cv2
    
    image = cv2.imread(image_path)
    if len(image.shape) == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    
    # Draw body region (green)
    cv2.rectangle(
        image,
        (template.body_left, template.body_top),
        (template.body_right, template.body_bottom),
        (0, 255, 0), 2
    )
    
    # Draw header zone (red overlay)
    overlay = image.copy()
    cv2.rectangle(
        overlay,
        (0, 0),
        (template.page_width, template.header_bottom),
        (0, 0, 255), -1
    )
    cv2.addWeighted(overlay, 0.3, image, 0.7, 0, image)
    
    # Draw footer zone (red overlay)
    overlay = image.copy()
    cv2.rectangle(
        overlay,
        (0, template.footer_top),
        (template.page_width, template.page_height),
        (0, 0, 255), -1
    )
    cv2.addWeighted(overlay, 0.3, image, 0.7, 0, image)
    
    # Draw left margin (red overlay)
    overlay = image.copy()
    cv2.rectangle(
        overlay,
        (0, template.header_bottom),
        (template.left_margin_right, template.footer_top),
        (0, 0, 255), -1
    )
    cv2.addWeighted(overlay, 0.3, image, 0.7, 0, image)
    
    # Draw footnote zone (orange overlay)
    if template.footnote_separator_y:
        overlay = image.copy()
        cv2.rectangle(
            overlay,
            (template.body_left, template.footnote_separator_y),
            (template.body_right, template.footer_top),
            (0, 165, 255), -1
        )
        cv2.addWeighted(overlay, 0.3, image, 0.7, 0, image)
    
    cv2.imwrite(output_path, image)
```

### 11.5 10-Page Validation Protocol

1. Select 10 pages with variety:
   - Regular body text
   - Pages with footnotes
   - Pages with line numbers
   - Chapter opening (if present)

2. Run pipeline on all 10 pages

3. For each page:
   - Visual check: template overlay correct?
   - OCR check: line numbers absent from text?
   - OCR check: body text present and accurate?
   - Footnote check: separated correctly?

4. Document any failures and adjust thresholds

---

## 12. Error Handling

### 12.1 Template Extraction Failures

```python
def extract_template_with_fallback(
    images: List[PageImage],
    config: PipelineConfig
) -> DocumentTemplate:
    """
    Extract template with fallback for edge cases.
    """
    try:
        template = extract_template(images, config)
        
        if template.confidence < config.min_template_confidence:
            template = apply_conservative_defaults(template, images[0])
        
        return template
        
    except Exception as e:
        return get_default_template(images[0] if images else None)


def get_default_template(sample_image: Optional[PageImage] = None) -> DocumentTemplate:
    """
    Conservative default template for when extraction fails.
    
    Assumes:
    - 10% margins on each side
    - 5% header, 5% footer
    - No footnotes
    """
    if sample_image:
        width = sample_image.width
        height = sample_image.height
    else:
        # Assume 300 DPI, 8.5x11 inch page
        width = 2550
        height = 3300
    
    return DocumentTemplate(
        page_width=width,
        page_height=height,
        body_left=int(width * 0.10),
        body_right=int(width * 0.90),
        body_top=int(height * 0.05),
        body_bottom=int(height * 0.95),
        header_bottom=int(height * 0.05),
        footer_top=int(height * 0.95),
        left_margin_right=int(width * 0.10),
        right_margin_left=int(width * 0.90),
        footnote_separator_y=None,
        pages_analysed=0,
        confidence=0.0,
        has_line_numbers_left=False,
        has_line_numbers_right=False,
        has_footnotes=False
    )


def apply_conservative_defaults(
    template: DocumentTemplate,
    sample_image: PageImage
) -> DocumentTemplate:
    """
    Apply conservative defaults to a low-confidence template.
    """
    # Expand margins slightly to be safe
    margin_expansion = int(sample_image.width * 0.02)
    
    template.body_left = max(template.body_left, template.left_margin_right + margin_expansion)
    template.body_right = min(template.body_right, template.right_margin_left - margin_expansion)
    
    return template
```

### 12.2 OCR Failures

```python
async def ocr_with_retry(
    masked_page: MaskedPage,
    rate_limiter: 'RateLimiter',
    document_ai_client: Any,
    config: PipelineConfig
) -> OCRResult:
    """
    OCR with retry logic for transient failures.
    """
    for attempt in range(config.ocr_max_retries):
        try:
            result = await ocr_masked_page(masked_page, rate_limiter, document_ai_client)
            
            if result.error is None:
                return result
            
        except Exception as e:
            pass
        
        # Exponential backoff
        await asyncio.sleep(config.ocr_retry_backoff_base ** attempt)
    
    # All retries failed
    return OCRResult(
        page_num=masked_page.page_num,
        text="",
        blocks=[],
        paragraphs=[],
        lines=[],
        confidence=0.0,
        error=f"Failed after {config.ocr_max_retries} attempts"
    )
```

---

## 13. Cost Analysis

### 13.1 API Calls

| Approach | Calls per Page | Calls for 500-page Book |
|----------|---------------|------------------------|
| v1.1 (line-level) | ~40 | ~20,000 |
| v1.2+ (page-level) | 1 | 500 |

### 13.2 Document AI Pricing

At current pricing (~$1.50 per 1000 pages for OCR):
- v1.1: ~$30 per book (treating each line crop as a "page")
- v1.2+: ~$0.75 per book

**v1.2+ is ~40x cheaper.**

---

## 14. Quick Start Example

```python
from philocr.pipeline import process_document
from philocr.models import PipelineConfig

# Load configuration (optional - uses defaults if not provided)
config = PipelineConfig()

# Or load from YAML
# config = PipelineConfig.from_yaml("config.yaml")

# Process a document
result = await process_document(
    pdf_path="plato_republic_1903.pdf",
    output_dir="./output",
    config=config
)

# Access results
print(f"Processed {result.statistics.total_pages} pages")
print(f"Average confidence: {result.statistics.average_confidence:.2f}")
print(f"Full text length: {len(result.full_text)} characters")

# Save to JSON
result.to_json("./output/document.json")

# Save plain text
with open("./output/document.txt", "w", encoding="utf-8") as f:
    f.write(result.full_text)
```

---

## Related Documents

### Reference Recovery and Positional Oracle

This pipeline produces **clean body text** but intentionally excludes scholarly reference numbers (Stephanus, Bekker, line numbers, fragment numbers) which live in the margins.

**Reference recovery strategy**:
1. **Primary method**: Align clean body text to reference scaffolds (TLG, Perseus, etc.) — references are recovered from the scaffold, not from OCR
2. **Fallback method**: Use positional oracle for manual lookup when alignment fails

**Positional oracle**: A reconstructed PDF with grid overlay that preserves spatial positions of margin elements. Useful for:
- Manual verification of alignment
- Debugging reference attachment
- Complex editions (von Arnim SVF, Diels-Kranz) where alignment is difficult

See: `pdf_reconstruction_from_ocr_plan.md` Section 1.3 for the positional oracle specification.

**Why not OCR the references?** Reference numbers in margins are unreliable to OCR ("15" → "I5" or "1S") because they are short, isolated, and lack linguistic context. Geometric position is reliable; OCR text is not.

---

## Summary

### What This Architecture Does

1. **Extracts a template** from multiple pages to establish where body text lives
2. **Masks excluded zones** (margins, headers, footers, footnotes) before OCR
3. **Sends clean body images** to Document AI (one per page)
4. **Assembles clean text** in reading order with genre hints

### What It Doesn't Do

- Line-by-line OCR (unnecessary complexity)
- Custom line detection (Document AI handles this)
- Complex OCR-to-geometry mapping (solved by pre-masking)
- OCR reference numbers (recovered via alignment instead)
- Preserve layout through OCR (that's the positional oracle's job)

### The Core Insight

**Mask the contaminants before OCR, not after.**

Document AI is good at reading clean pages. It's bad at knowing what to exclude. The template tells us what to exclude; Document AI does the reading.

**References are recovered via alignment, not OCR.** The reference text already has the numbers; we just need to match our clean text to it.

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-10 | Initial specification |
| 1.1 | 2026-01-10 | Added cross-page template extraction |
| 1.2 | 2026-01-10 | Simplified to page-level OCR with pre-masking |
| 1.3 | 2026-01-10 | Added configuration, algorithms, coordinate transforms, poetry detection, performance optimization |
| 1.3.1 | 2026-01-10 | Fixed section numbering, added missing type definitions, utility functions, quick start example |
| 1.4 | 2026-01-10 | Added explicit design goal and success criterion. Committed fully to "geometry is authoritative, OCR is advisory". Simplified Stage 4 to text assembly (not layout reconstruction). Labeled heuristics explicitly. Added hard rule for template confidence fallback. Stated masking as canonical, cropping as optional/lossy. Added comprehensive genre detection heuristics (prose, verse, speakers, verse_speakers, fragments) as triangulation metadata for reconstruction. Added reference recovery strategy section linking to positional oracle (pdf_reconstruction_from_ocr_plan.md). |
