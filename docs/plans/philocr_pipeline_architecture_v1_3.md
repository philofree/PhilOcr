# PhilOcr Pipeline Architecture v1.3

## Document Purpose

This document defines the OCR pipeline for PhilOcr, designed to extract clean Greek text from scanned scholarly editions while excluding contaminating elements (line numbers, page numbers, footnotes, headers).

**Core Principle**: Use cross-page template extraction to identify and mask non-body zones, then let Document AI process the clean body region.

**Key Simplification (v1.2)**: OCR operates on masked/cropped body regions, not individual lines. The template is a pre-processing filter, not a structural scaffold.

**Improvements in v1.3**: Added configuration parameters, fully specified algorithms, coordinate transformation utilities, outlier detection, poetry/prose detection, and performance optimization strategies.

**Document Status**: Implementation specification
**Version**: 1.3
**Date**: 2026-01-10

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Configuration Parameters](#2-configuration-parameters)
3. [Stage 1: Image Normalisation](#3-stage-1-image-normalisation)
4. [Stage 2: Template Extraction & Zone Masking](#4-stage-2-template-extraction--zone-masking)
5. [Stage 3: OCR on Masked Body Region](#5-stage-3-ocr-on-masked-body-region)
6. [Stage 4: Geometry-Informed Assembly](#6-stage-4-geometry-informed-assembly)
7. [Data Structures](#7-data-structures)
8. [Performance Optimization](#8-performance-optimization)
9. [Implementation Plan](#9-implementation-plan)
10. [Testing Strategy](#10-testing-strategy)
11. [Error Handling](#11-error-handling)
12. [Cost Analysis](#12-cost-analysis)

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
│              STAGE 4: GEOMETRY-INFORMED ASSEMBLY                 │
│                                                                  │
│  OCR output + Template → Structured text with paragraphs        │
│                                                                  │
│  Template informs: paragraph breaks, indent interpretation      │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 What Changed from v1.1

| Aspect | v1.1 (Over-engineered) | v1.2 (Practical) |
|--------|------------------------|------------------|
| OCR granularity | One crop per line | One masked image per page |
| API calls per page | ~30-50 | 1 |
| Line detection | Custom, pre-OCR | Document AI handles it |
| Template role | Structural scaffold | Pre-processing filter |
| Complexity | High | Moderate |

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
    poetry_avg_line_length_threshold: int = 50  # Chars; below = poetry
    poetry_line_length_cv_threshold: float = 0.3  # Coefficient of variation
    indent_ratio_threshold_1: float = 0.02  # < 2% = flush left
    indent_ratio_threshold_2: float = 0.06  # < 6% = standard indent
    
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
```

---

## 3. Stage 1: Image Normalisation

### 2.1 Purpose

Convert PDF pages to stable raster images with consistent geometry.

### 2.2 Processing

```python
def normalise_page(pdf_path: str, page_num: int, output_dir: str) -> PageImage:
    """
    Convert PDF page to normalised raster image.
    """
    TARGET_DPI = 300
    
    # Render PDF page
    image = render_pdf_page(pdf_path, page_num, dpi=TARGET_DPI)
    
    # Convert to grayscale
    image = convert_to_grayscale(image)
    
    # Deskew if needed
    skew_angle = detect_skew(image)
    if abs(skew_angle) > 0.1:
        image = rotate_image(image, -skew_angle)
    
    # Save
    output_path = f"{output_dir}/page_{page_num:04d}.png"
    save_image(image, output_path)
    
    return PageImage(
        page_num=page_num,
        path=output_path,
        dpi=TARGET_DPI,
        width=image.width,
        height=image.height,
        skew_corrected=skew_angle
    )
```

### 2.3 Output

- Directory of normalised PNG images
- Manifest with page metadata

---

## 4. Stage 2: Template Extraction & Zone Masking

### 3.1 Purpose

Analyse multiple pages to establish document-wide zone boundaries, then mask each page to expose only the body region.

### 3.2 The Template Model

```python
@dataclass
class DocumentTemplate:
    """
    Canonical layout parameters for the document.
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
    footnote_separator_y: int   # Footnotes below this line
    
    # Detection metadata
    pages_analysed: int
    confidence: float
    has_line_numbers_left: bool
    has_line_numbers_right: bool
    has_footnotes: bool
```

### 3.3 Template Extraction Algorithm

```python
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
    
    def add(self, zones: PageZones):
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
        if zones.footnote_separator_y:
            self.footnote_separators.append(zones.footnote_separator_y)
        # TODO: These would need to be detected during zone detection
        self.has_line_numbers_left.append(False)  # Placeholder
        self.has_line_numbers_right.append(False)  # Placeholder
        self.has_footnotes.append(zones.footnote_separator_y is not None)
    
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


def extract_template(
    normalised_images: List[PageImage],
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
    if len(values) < 3:
        return int(np.median(values)) if values else 0, []
    
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

### 3.4 Zone Detection (Per Page)

```python
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
    h_profile_norm = h_profile / np.max(h_profile) if np.max(h_profile) > 0 else h_profile
    v_profile_norm = v_profile / np.max(v_profile) if np.max(v_profile) > 0 else v_profile
    
    # Find content boundaries using threshold
    content_threshold = config.content_threshold
    content_rows = np.where(h_profile_norm > content_threshold)[0]
    content_cols = np.where(v_profile_norm > content_threshold)[0]
    
    content_top = content_rows[0] if len(content_rows) > 0 else 0
    content_bottom = content_rows[-1] if len(content_rows) > 0 else height
    content_left = content_cols[0] if len(content_cols) > 0 else 0
    content_right = content_cols[-1] if len(content_cols) > 0 else width
    
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

### 3.5 Header/Footer Detection

```python
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


@dataclass
class Gap:
    """Represents a gap in a profile."""
    start: int
    end: int
```

### 3.6 Margin Detection (Line Numbers)

```python
def detect_left_margin(
    v_profile: np.ndarray,
    content_left: int,
    width: int,
    config: PipelineConfig
) -> int:
    """
    Detect left margin boundary (where line numbers end, body begins).
    
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

### 3.7 Footnote Separator Detection

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

### 3.8 Applying the Template: Masking

```python
def mask_page(image_path: str, template: DocumentTemplate, output_path: str) -> MaskedPage:
    """
    Apply template to mask non-body regions.
    
    Two approaches:
    1. Crop: Extract only the body region (smaller image)
    2. Mask: White-out non-body regions (same size image)
    
    We use masking to preserve coordinate consistency.
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

### 3.9 Masking vs Cropping Decision

**Default Approach: Masking (recommended)**
- Preserves coordinate consistency with original page
- Allows Document AI coordinates to map directly to original
- Easier to debug and visualize
- Slightly larger file size, but negligible performance impact

**Alternative Approach: Cropping**
- Smaller image files, slightly faster OCR
- Requires coordinate transformation in Stage 4
- More complex but can be beneficial for very large documents

**Decision Criteria:**

```python
def choose_masking_strategy(
    template: DocumentTemplate,
    config: PipelineConfig
) -> str:
    """
    Determine whether to use masking or cropping.
    
    Returns:
        'mask' or 'crop'
    """
    # Use config setting if explicitly set
    if config.use_cropping:
        return 'crop'
    
    # Default to masking for coordinate preservation
    return 'mask'
```

### 3.10 Alternative: Cropping Instead of Masking

```python
def crop_to_body(
    image_path: str,
    template: DocumentTemplate,
    config: PipelineConfig,
    output_path: str
) -> CroppedPage:
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
    ocr_bbox: BoundingBox,
    crop_offset: Tuple[int, int]
) -> BoundingBox:
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
```

---

## 5. Stage 3: OCR on Masked Body Region

### 4.1 Purpose

Send the masked/cropped image to Document AI. One request per page.

### 4.2 Processing

```python
async def ocr_masked_page(
    masked_page: MaskedPage,
    rate_limiter: RateLimiter
) -> OCRResult:
    """
    Send masked page to Document AI for OCR.
    
    Document AI handles:
    - Line detection
    - Word detection
    - Character recognition
    
    We just send the image and receive text.
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


def extract_blocks(response) -> List[TextBlock]:
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


def extract_paragraphs(response) -> List[TextParagraph]:
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
```

### 4.3 What Document AI Returns

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

## 6. Stage 4: Geometry-Informed Assembly

### 5.1 Purpose

Combine OCR output with template knowledge to produce final structured text.

### 5.2 What the Template Adds

Document AI detects paragraphs, but doesn't understand:
- Scholarly indent conventions
- Poetry vs prose distinction
- Chapter/section breaks

The template provides geometric context to interpret OCR output.

### 5.3 Assembly Logic

```python
def assemble_page(
    ocr_result: OCRResult,
    template: DocumentTemplate,
    config: PipelineConfig,
    content_type: Optional[str] = None
) -> PageOutput:
    """
    Assemble final output using OCR text and template context.
    
    Args:
        ocr_result: OCR result from Document AI
        template: Document template for coordinate context
        config: Configuration with indent thresholds
        content_type: 'prose', 'poetry', or None (auto-detect)
    
    Returns:
        PageOutput with structured paragraphs and text
    """
    
    if not ocr_result.text:
        return PageOutput(
            page_num=ocr_result.page_num,
            paragraphs=[],
            full_text="",
            confidence=0.0
        )
    
    # Auto-detect content type if not provided
    if content_type is None:
        content_type = detect_content_type(ocr_result, config)
    
    # Use Document AI's paragraph structure as base
    paragraphs = []
    
    for para in ocr_result.paragraphs:
        # Determine indent class from bbox position
        indent_class = classify_indent(
            para.bbox.x1,
            template.body_left,
            template.body_right,
            config
        )
        
        paragraphs.append(Paragraph(
            text=normalise_text(para.text),
            indent_class=indent_class,
            confidence=para.confidence,
            bbox=para.bbox
        ))
    
    # For prose: join paragraphs with double newlines
    # For poetry: preserve line breaks within paragraphs
    if content_type == 'prose':
        full_text = '\n\n'.join(p.text for p in paragraphs)
    else:
        full_text = ocr_result.text  # Preserve all line breaks for poetry
    
    return PageOutput(
        page_num=ocr_result.page_num,
        paragraphs=paragraphs,
        full_text=normalise_text(full_text),
        confidence=ocr_result.confidence,
        content_type=content_type
    )


def detect_content_type(
    ocr_result: OCRResult,
    config: PipelineConfig
) -> str:
    """
    Detect if content is poetry or prose.
    
    Poetry indicators:
    - Consistent short line lengths
    - Low coefficient of variation in line lengths
    - Many lines start at same indent level
    
    Prose indicators:
    - Variable line lengths
    - Higher variation in line lengths
    - Fewer explicit line breaks
    
    Args:
        ocr_result: OCR result with lines extracted
        config: Configuration with detection thresholds
    
    Returns:
        'poetry' or 'prose'
    """
    if not ocr_result.lines or len(ocr_result.lines) < 3:
        return 'prose'
    
    line_lengths = [len(line.text.strip()) for line in ocr_result.lines if line.text.strip()]
    
    if len(line_lengths) < 3:
        return 'prose'
    
    avg_length = np.mean(line_lengths)
    std_length = np.std(line_lengths)
    
    # Calculate coefficient of variation (CV)
    cv = std_length / avg_length if avg_length > 0 else float('inf')
    
    # Poetry has consistent short lines
    if (avg_length < config.poetry_avg_line_length_threshold and
            cv < config.poetry_line_length_cv_threshold):
        return 'poetry'
    
    return 'prose'


def classify_indent(
    x_position: int,
    body_left: int,
    body_right: int,
    config: PipelineConfig
) -> int:
    """
    Classify indent level based on x-position.
    
    0 = flush left
    1 = standard indent (new paragraph)
    2 = deep indent (quotation, poetry)
    
    Args:
        x_position: X-coordinate of line start
        body_left: Left boundary of body region
        body_right: Right boundary of body region
        config: Configuration with indent threshold ratios
    
    Returns:
        Indent class (0, 1, or 2)
    """
    body_width = body_right - body_left
    
    if body_width <= 0:
        return 0
    
    relative_x = x_position - body_left
    indent_ratio = relative_x / body_width
    
    if indent_ratio < config.indent_ratio_threshold_1:
        return 0  # Flush left
    elif indent_ratio < config.indent_ratio_threshold_2:
        return 1  # Standard indent
    else:
        return 2  # Deep indent


def normalise_text(text: str) -> str:
    """
    Normalise OCR output text.
    """
    import unicodedata
    
    # Unicode NFC normalisation (critical for Greek)
    text = unicodedata.normalize('NFC', text)
    
    # Normalise whitespace
    text = ' '.join(text.split())
    
    return text
```

### 5.4 Document Assembly

```python
def assemble_document(
    page_outputs: List[PageOutput],
    template: DocumentTemplate,
    metadata: DocumentMetadata
) -> Document:
    """
    Assemble all pages into final document.
    """
    
    return Document(
        metadata=metadata,
        template=template,
        pages=page_outputs,
        full_text='\n\n'.join(p.full_text for p in page_outputs),
        statistics=DocumentStatistics(
            total_pages=len(page_outputs),
            total_paragraphs=sum(len(p.paragraphs) for p in page_outputs),
            average_confidence=mean(p.confidence for p in page_outputs),
            pages_with_errors=[p.page_num for p in page_outputs if p.confidence == 0]
        )
    )
```

---

## 7. Data Structures

### 6.1 Stage 1 Output

```python
@dataclass
class PageImage:
    page_num: int
    path: str
    dpi: int
    width: int
    height: int
    skew_corrected: float
```

### 6.2 Stage 2 Output

```python
@dataclass
class DocumentTemplate:
    page_width: int
    page_height: int
    body_left: int
    body_right: int
    body_top: int
    body_bottom: int
    header_bottom: int
    footer_top: int
    left_margin_right: int
    right_margin_left: int
    footnote_separator_y: Optional[int]
    pages_analysed: int
    confidence: float
    has_line_numbers_left: bool
    has_line_numbers_right: bool
    has_footnotes: bool

@dataclass
class MaskedPage:
    page_num: int
    original_path: str
    masked_path: str
    body_bounds: BoundingBox
```

### 6.3 Stage 3 Output

```python
@dataclass
class TextBlock:
    text: str
    confidence: float
    bbox: BoundingBox

@dataclass
class TextParagraph:
    text: str
    confidence: float
    bbox: BoundingBox

@dataclass
class OCRResult:
    page_num: int
    text: str
    blocks: List[TextBlock]
    paragraphs: List[TextParagraph]
    lines: List[TextLine]
    confidence: float
    error: Optional[str] = None
    raw_response: Optional[Any] = None
```

### 6.4 Stage 4 Output

```python
@dataclass
class Paragraph:
    text: str
    indent_class: int
    confidence: float
    bbox: BoundingBox

@dataclass
class PageOutput:
    page_num: int
    paragraphs: List[Paragraph]
    full_text: str
    confidence: float

@dataclass
class Document:
    metadata: DocumentMetadata
    template: DocumentTemplate
    pages: List[PageOutput]
    full_text: str
    statistics: DocumentStatistics
```

### 6.5 Template JSON Example

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

### 6.6 Directory Structure

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

## 7. Performance Optimization

### 7.1 Parallelization Strategy

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
            executor.submit(detect_page_zones, load_image(images[i].path), config)
            for i in sample_indices
        ]
        return [f.result() for f in futures]
```

**Rationale**: Zone detection is CPU-intensive image processing that can run concurrently.

#### Stage 3: OCR Processing

```python
import asyncio

async def ocr_all_pages(
    masked_pages: List[MaskedPage],
    rate_limiter: RateLimiter,
    config: PipelineConfig
) -> List[OCRResult]:
    """
    Process OCR for multiple pages with rate limiting.
    
    Note: Rate limiting prevents true parallelization, but async allows
    efficient waiting and concurrent request preparation.
    """
    semaphore = asyncio.Semaphore(config.ocr_rate_limit_per_minute)
    
    async def ocr_with_semaphore(page):
        async with semaphore:
            return await ocr_with_retry(page, rate_limiter, config)
    
    tasks = [ocr_with_semaphore(page) for page in masked_pages]
    return await asyncio.gather(*tasks)
```

**Rationale**: Rate limiting prevents parallel API calls, but async allows efficient I/O waiting.

### 7.2 Caching Strategy

```python
from functools import lru_cache
import hashlib
import json

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
    cache_path = f"{cache_dir}/template_{cache_key}.json"
    
    if os.path.exists(cache_path):
        logger.info(f"Loading template from cache: {cache_key}")
        return DocumentTemplate.from_json(cache_path)
    
    template = extract_template(normalised_images, config)
    template.save_json(cache_path)
    logger.info(f"Cached template: {cache_key}")
    
    return template
```

### 7.3 Memory Management

For large documents (1000+ pages), consider streaming:

```python
def process_large_document(
    pdf_path: str,
    config: PipelineConfig,
    batch_size: int = 50
) -> Iterator[PageOutput]:
    """
    Process document in batches to manage memory.
    
    Yields PageOutput objects as batches complete.
    """
    # Stage 1: Normalise all pages (necessary for template)
    # For very large docs, might need to sample first
    all_images = normalise_all_pages(pdf_path, range(total_pages), config)
    
    # Stage 2: Extract template from sample
    template = extract_template(all_images[:config.template_sample_size], config)
    
    # Stage 3-4: Process in batches
    for batch_start in range(0, len(all_images), batch_size):
        batch_end = min(batch_start + batch_size, len(all_images))
        batch_images = all_images[batch_start:batch_end]
        
        # Mask, OCR, assemble batch
        masked = [mask_page(img.path, template, config) for img in batch_images]
        ocr_results = await ocr_all_pages(masked, rate_limiter, config)
        outputs = [assemble_page(ocr, template, config) for ocr in ocr_results]
        
        yield from outputs
```

### 7.4 Expected Performance

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

## 9. Implementation Plan

### 9.1 Module Structure

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
└── models/
    ├── __init__.py
    ├── template.py
    ├── page.py
    └── document.py
```

### 9.2 Implementation Order

**Week 1: Stage 1 + Basic Stage 2**
- Image normalisation (builds on existing PDF handling)
- Basic zone detection using projection profiles
- Manual validation on 10 test pages

**Week 2: Template Extraction**
- Multi-page analysis
- Robust statistics (median, IQR)
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

### 9.3 Dependencies

```
# Core
opencv-python>=4.8.0    # Image processing
numpy>=1.24.0           # Array operations
scipy>=1.11.0           # Signal processing (smoothing, peak detection)

# Existing
PyMuPDF>=1.23.0         # PDF rendering
google-cloud-documentai # OCR
Pillow>=10.0.0          # Image I/O
```

---

## 10. Testing Strategy

### 10.1 Template Extraction Validation

```python
def test_template_extraction():
    """Validate template extraction on known document."""
    
    # Process a document with known layout
    template = extract_template(test_images)
    
    # Verify template matches expected values (±tolerance)
    assert abs(template.body_left - EXPECTED_BODY_LEFT) < 20
    assert abs(template.left_margin_right - EXPECTED_MARGIN) < 20
    assert template.has_line_numbers_left == True
```

### 10.2 Masking Validation

```python
def test_masking_excludes_line_numbers():
    """Verify line numbers are masked out."""
    
    masked = mask_page(test_image, template, output_path)
    masked_img = load_image(masked.masked_path)
    
    # Left margin should be white
    left_margin = masked_img[:, 0:template.left_margin_right]
    assert np.mean(left_margin) > 250  # Nearly all white
```

### 10.3 OCR Comparison Test

```python
def test_ocr_without_contamination():
    """Compare OCR results: masked vs unmasked."""
    
    # OCR on original (unmasked) image
    original_result = ocr_page(original_image)
    
    # OCR on masked image
    masked_result = ocr_page(masked_image)
    
    # Masked result should NOT contain line numbers
    assert not re.search(r'^\d{1,3}\s+', masked_result.text, re.MULTILINE)
    
    # Masked result should contain body text
    assert 'ἄνδρα μοι ἔννεπε' in masked_result.text
```

### 10.4 Visual Validation Tool

```python
def visualise_template(image_path: str, template: DocumentTemplate, output_path: str):
    """
    Draw template boundaries on image for visual validation.
    """
    image = load_image(image_path)
    
    # Draw body region (green)
    draw_rectangle(image, 
        (template.body_left, template.body_top),
        (template.body_right, template.body_bottom),
        color=(0, 255, 0), thickness=2)
    
    # Draw excluded zones (red)
    # Header
    draw_filled_rectangle(image,
        (0, 0), (template.page_width, template.header_bottom),
        color=(255, 0, 0), alpha=0.3)
    
    # Footer
    draw_filled_rectangle(image,
        (0, template.footer_top), (template.page_width, template.page_height),
        color=(255, 0, 0), alpha=0.3)
    
    # Left margin
    draw_filled_rectangle(image,
        (0, template.header_bottom), (template.left_margin_right, template.footer_top),
        color=(255, 0, 0), alpha=0.3)
    
    # Footnote zone
    if template.footnote_separator_y:
        draw_filled_rectangle(image,
            (template.body_left, template.footnote_separator_y),
            (template.body_right, template.footer_top),
            color=(255, 165, 0), alpha=0.3)  # Orange for footnotes
    
    save_image(image, output_path)
```

### 10.5 10-Page Validation Protocol

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

## 11. Error Handling

### 11.1 Template Extraction Failures

```python
def extract_template_with_fallback(images: List[PageImage]) -> DocumentTemplate:
    """
    Extract template with fallback for edge cases.
    """
    
    try:
        template = extract_template(images)
        
        if template.confidence < 0.5:
            logger.warning("Low confidence template; using conservative defaults")
            template = apply_conservative_defaults(template)
        
        return template
        
    except Exception as e:
        logger.error(f"Template extraction failed: {e}")
        return get_default_template()


def get_default_template() -> DocumentTemplate:
    """
    Conservative default template for when extraction fails.
    
    Assumes:
    - 10% margins on each side
    - 5% header, 5% footer
    - No footnotes
    """
    return DocumentTemplate(
        page_width=2550,  # Assumes 300 DPI, 8.5" wide
        page_height=3300,  # Assumes 300 DPI, 11" tall
        body_left=255,     # 10% margin
        body_right=2295,
        body_top=165,      # 5% header
        body_bottom=3135,  # 5% footer
        header_bottom=165,
        footer_top=3135,
        left_margin_right=255,
        right_margin_left=2295,
        footnote_separator_y=None,
        pages_analysed=0,
        confidence=0.0,
        has_line_numbers_left=False,
        has_line_numbers_right=False,
        has_footnotes=False
    )
```

### 11.2 OCR Failures

```python
async def ocr_with_retry(
    masked_page: MaskedPage,
    rate_limiter: RateLimiter,
    max_retries: int = 3
) -> OCRResult:
    """
    OCR with retry logic for transient failures.
    """
    
    for attempt in range(max_retries):
        try:
            result = await ocr_masked_page(masked_page, rate_limiter)
            
            if result.error is None:
                return result
            
            logger.warning(f"OCR attempt {attempt + 1} failed: {result.error}")
            
        except Exception as e:
            logger.warning(f"OCR attempt {attempt + 1} exception: {e}")
        
        # Exponential backoff
        await asyncio.sleep(2 ** attempt)
    
    # All retries failed
    return OCRResult(
        page_num=masked_page.page_num,
        text="",
        blocks=[],
        paragraphs=[],
        lines=[],
        confidence=0.0,
        error=f"Failed after {max_retries} attempts"
    )
```

---

## 12. Cost Analysis

### 12.1 API Calls

| Approach | Calls per Page | Calls for 500-page Book |
|----------|---------------|------------------------|
| v1.1 (line-level) | ~40 | ~20,000 |
| v1.2 (page-level) | 1 | 500 |

### 12.2 Document AI Pricing

At current pricing (~$1.50 per 1000 pages for OCR):
- v1.1: ~$30 per book (treating each line crop as a "page")
- v1.2: ~$0.75 per book

**v1.2 is ~40x cheaper.**

---

## Summary

### What This Architecture Does

1. **Extracts a template** from multiple pages to establish where body text lives
2. **Masks excluded zones** (margins, headers, footers, footnotes) before OCR
3. **Sends clean body images** to Document AI (one per page)
4. **Uses template context** to interpret paragraph structure

### What It Doesn't Do

- Line-by-line OCR (unnecessary complexity)
- Custom line detection (Document AI handles this)
- Complex OCR-to-geometry mapping (solved by pre-masking)

### The Core Insight

**Mask the contaminants before OCR, not after.**

Document AI is good at reading clean pages. It's bad at knowing what to exclude. The template tells us what to exclude; Document AI does the reading.

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-10 | Initial specification |
| 1.1 | 2026-01-10 | Added cross-page template extraction |
| 1.2 | 2026-01-10 | Simplified to page-level OCR with pre-masking |
| 1.3 | 2026-01-10 | Added configuration parameters, fully specified algorithms (select_sample_pages, robust_median_with_outliers, find_gaps, gaussian_smooth, find_significant_transitions), coordinate transformation utilities, poetry/prose detection, performance optimization strategies, masking vs cropping decision criteria, and enhanced error handling |
