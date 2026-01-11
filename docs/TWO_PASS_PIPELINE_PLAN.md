# Two-Pass Pipeline Enhancement Plan

## Executive Summary

Replace the failing pixel-based template detection with a Google-informed two-pass approach:
1. **Pass 1**: Run Standard OCR on full page → get rich layout JSON with word-level bounding boxes
2. **Pass 2**: Use layout intelligence to classify page regions → mask/crop precisely → run Advanced OCR on body only

This leverages Google's superior layout detection instead of fighting it with hand-crafted heuristics.

---

## Problem Statement

### Current Failure Mode

The pixel-based template detection in `stage2_zones.py` fails on scholarly editions:

```
Template Preview Results (Simplicius):
- Header Bottom: 0          ← WRONG: Should be ~100px (page number + running header)
- Body Top: 0               ← WRONG: Includes header
- Body Bottom: 1705         ← WRONG: Truncates 2-3 lines of main text
- Footer Top: 2476          ← Gap of 770px of lost content
- Line Numbers (Right): False ← WRONG: Edition has right-side line numbers
```

**Root Cause**: Algorithm works from page edges inward, looking for gaps. Scholarly editions have minimal gaps - everything is packed tight for print economy.

### What Google Already Knows

Looking at the Standard pipeline JSON output, Google returns:

```json
{
  "pages": [{
    "tokens": [
      {"text": "818", "layout": {"bounding_poly": {"vertices": [{"x": 100, "y": 50}...]}}},
      {"text": "SIMPLICII", "layout": {"bounding_poly": {"vertices": [{"x": 300, "y": 50}...]}}},
      {"text": "αὐξόμενον", "layout": {"bounding_poly": {"vertices": [{"x": 290, "y": 200}...]}}},
      {"text": "10", "layout": {"bounding_poly": {"vertices": [{"x": 80, "y": 400}...]}}},
      {"text": "AC", "layout": {"bounding_poly": {"vertices": [{"x": 200, "y": 1900}...]}}},
      {"text": "om.", "layout": {"bounding_poly": {"vertices": [{"x": 470, "y": 1920}...]}}}
    ]
  }]
}
```

Google already knows:
- "818" is at (100, 50) - top left corner
- "SIMPLICII" is at (300, 50) - top center  
- "αὐξόμενον" is at (290, 200) - body region
- "10" is at (80, 400) - left margin (line number)
- "AC", "om." are at y > 1900 - apparatus region

**We're paying for this intelligence and throwing it away.**

---

## Proposed Architecture

### Two-Pass Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  PASS 1: Layout Discovery                                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  PDF Page Image                                                 │
│       │                                                         │
│       ▼                                                         │
│  Google Document AI (Standard OCR)                              │
│       │                                                         │
│       ▼                                                         │
│  Rich Layout JSON                                               │
│  ├── tokens[] with bounding boxes                               │
│  ├── lines[] with bounding boxes                                │
│  ├── paragraphs[] with bounding boxes                           │
│  └── blocks[] with bounding boxes                               │
│       │                                                         │
│       ▼                                                         │
│  Token Classification Engine                                    │
│  ├── page_number: isolated digits at top                        │
│  ├── header: Latin text at top                                  │
│  ├── line_number_left: isolated digits in left margin           │
│  ├── line_number_right: isolated digits in right margin         │
│  ├── folio_ref: digit+v/r pattern in right margin               │
│  ├── apparatus: bottom region + sigla patterns                  │
│  └── body: everything else (Greek prose)                        │
│       │                                                         │
│       ▼                                                         │
│  Computed Body Bounding Box                                     │
│  {left, right, top, bottom} from body-classified tokens         │
│       │                                                         │
│       ▼                                                         │
│  Store: layout_cache/{document_id}/page_{n}_layout.json         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  PASS 2: Clean OCR (Optional - only if higher quality needed)   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Original Image + Computed Body Bounding Box                    │
│       │                                                         │
│       ▼                                                         │
│  Precise Masking/Cropping                                       │
│  (mask header, margins, apparatus)                              │
│       │                                                         │
│       ▼                                                         │
│  Google Document AI (can use same or different processor)       │
│       │                                                         │
│       ▼                                                         │
│  Clean Body Text                                                │
│  (no page numbers, headers, line numbers, apparatus)            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Key Insight: Pass 2 May Be Optional

For many use cases, **Pass 1 alone may be sufficient**:
- The token classification already separates body from non-body
- Simply concatenating body-classified tokens gives clean text
- Pass 2 only needed if OCR quality improves with isolated body region

---

## Implementation Plan

### Phase 1: Token Classification Engine

**New file**: `src/philocr/detection/token_classifier.py`

```python
"""Token classification for scholarly edition layout detection."""

import re
from dataclasses import dataclass
from typing import Any

@dataclass
class PageBounds:
    width: int
    height: int

@dataclass  
class ClassifiedToken:
    text: str
    x: int
    y: int
    width: int
    height: int
    confidence: float
    classification: str  # page_number, header, line_number_left, etc.

class TokenClassifier:
    """Classifies tokens from Google OCR based on position and content."""
    
    # Configurable thresholds (as ratios of page dimensions)
    TOP_REGION_THRESHOLD = 0.08      # Top 8% of page
    BOTTOM_REGION_THRESHOLD = 0.70   # Bottom 30% of page
    LEFT_MARGIN_THRESHOLD = 0.15     # Left 15% of page
    RIGHT_MARGIN_THRESHOLD = 0.85    # Right 15% of page
    
    # Apparatus detection patterns
    MANUSCRIPT_SIGLA = re.compile(r'^[A-Z]{1,3}[0-9]?$')  # M, AC, AFM, A1
    APPARATUS_ABBREVS = {'om', 'om.', 'cf', 'cf.', 'add', 'add.', 
                         'del', 'del.', 'v.', 'et', 'sic', 'fort.'}
    LOWER_SIGLA = re.compile(r'^a?[A-Z]{1,3}$')  # aFM, aM
    
    def classify_token(self, token: dict, page_bounds: PageBounds) -> ClassifiedToken:
        """Classify a single token based on position and content."""
        
        text = token.get('text', '').strip()
        layout = token.get('layout', {})
        vertices = layout.get('bounding_poly', {}).get('vertices', [])
        confidence = layout.get('confidence', 0.0)
        
        if not vertices or len(vertices) < 4:
            return self._make_token(text, 0, 0, 0, 0, confidence, 'unknown')
        
        # Calculate position
        x = vertices[0].get('x', 0)
        y = vertices[0].get('y', 0)
        width = vertices[1].get('x', x) - x
        height = vertices[2].get('y', y) - y
        
        # Calculate relative positions
        rel_x = x / page_bounds.width if page_bounds.width > 0 else 0
        rel_y = y / page_bounds.height if page_bounds.height > 0 else 0
        
        # Position flags
        is_top = rel_y < self.TOP_REGION_THRESHOLD
        is_bottom = rel_y > self.BOTTOM_REGION_THRESHOLD
        is_left_margin = rel_x < self.LEFT_MARGIN_THRESHOLD
        is_right_margin = rel_x > self.RIGHT_MARGIN_THRESHOLD
        
        # Classification logic
        classification = self._classify(
            text, is_top, is_bottom, is_left_margin, is_right_margin
        )
        
        return self._make_token(text, x, y, width, height, confidence, classification)
    
    def _classify(self, text: str, is_top: bool, is_bottom: bool,
                  is_left_margin: bool, is_right_margin: bool) -> str:
        """Apply classification rules."""
        
        # 1. Page number: isolated digits at top corners
        if is_top and text.isdigit() and len(text) <= 4:
            return 'page_number'
        
        # 2. Running header: Latin text at top (not digits)
        if is_top and self._is_latin_text(text) and not text.isdigit():
            return 'header'
        
        # 3. Line number (left): isolated 1-2 digit number in left margin
        if is_left_margin and text.isdigit() and len(text) <= 2:
            return 'line_number_left'
        
        # 4. Line number (right): isolated 1-2 digit number in right margin
        if is_right_margin and text.isdigit() and len(text) <= 2:
            return 'line_number_right'
        
        # 5. Folio reference: pattern like "193" or "193v" in right margin
        if is_right_margin and re.match(r'^\d+[rv]?$', text):
            return 'folio_ref'
        
        # 6. Apparatus: bottom region + characteristic patterns
        if is_bottom:
            if self.MANUSCRIPT_SIGLA.match(text):
                return 'apparatus'
            if text.lower() in self.APPARATUS_ABBREVS:
                return 'apparatus'
            if self.LOWER_SIGLA.match(text):
                return 'apparatus'
            # Greek words in bottom region with adjacent sigla → likely apparatus
            # (This is refined by context in full classification)
        
        # 7. Default: body text
        return 'body'
    
    def _is_latin_text(self, text: str) -> bool:
        """Check if text is primarily Latin characters."""
        if not text:
            return False
        latin_chars = sum(1 for c in text if 'A' <= c <= 'Z' or 'a' <= c <= 'z')
        return latin_chars > len(text) * 0.5
    
    def _make_token(self, text, x, y, width, height, confidence, classification):
        return ClassifiedToken(
            text=text, x=x, y=y, width=width, height=height,
            confidence=confidence, classification=classification
        )
    
    def compute_body_bounds(self, classified_tokens: list[ClassifiedToken]) -> dict:
        """Compute bounding box containing all body tokens."""
        body_tokens = [t for t in classified_tokens if t.classification == 'body']
        
        if not body_tokens:
            return None
        
        min_x = min(t.x for t in body_tokens)
        max_x = max(t.x + t.width for t in body_tokens)
        min_y = min(t.y for t in body_tokens)
        max_y = max(t.y + t.height for t in body_tokens)
        
        # Add small padding
        padding = 10
        return {
            'left': max(0, min_x - padding),
            'right': max_x + padding,
            'top': max(0, min_y - padding),
            'bottom': max_y + padding
        }
```

### Phase 2: Layout Cache Manager

**New file**: `src/philocr/detection/layout_cache.py`

```python
"""Manages cached layout JSON from Pass 1."""

import json
import os
from pathlib import Path
from typing import Any

class LayoutCacheManager:
    """Manages storage and retrieval of layout analysis results."""
    
    def __init__(self, cache_dir: str):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get_document_cache_dir(self, document_id: str) -> Path:
        """Get cache directory for a specific document."""
        doc_dir = self.cache_dir / document_id
        doc_dir.mkdir(parents=True, exist_ok=True)
        return doc_dir
    
    def save_page_layout(self, document_id: str, page_num: int, 
                         layout_data: dict) -> Path:
        """Save layout analysis for a page."""
        doc_dir = self.get_document_cache_dir(document_id)
        path = doc_dir / f"page_{page_num:04d}_layout.json"
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(layout_data, f, indent=2, ensure_ascii=False)
        
        return path
    
    def load_page_layout(self, document_id: str, page_num: int) -> dict | None:
        """Load cached layout for a page."""
        doc_dir = self.get_document_cache_dir(document_id)
        path = doc_dir / f"page_{page_num:04d}_layout.json"
        
        if not path.exists():
            return None
        
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_document_template(self, document_id: str, template: dict) -> Path:
        """Save computed template for document."""
        doc_dir = self.get_document_cache_dir(document_id)
        path = doc_dir / "computed_template.json"
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(template, f, indent=2)
        
        return path
    
    def clear_document_cache(self, document_id: str) -> None:
        """Clear all cached data for a document."""
        doc_dir = self.get_document_cache_dir(document_id)
        if doc_dir.exists():
            import shutil
            shutil.rmtree(doc_dir)
    
    def clear_all_cache(self) -> None:
        """Clear entire cache directory."""
        if self.cache_dir.exists():
            import shutil
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get_cache_size(self) -> int:
        """Get total cache size in bytes."""
        total = 0
        for path in self.cache_dir.rglob('*'):
            if path.is_file():
                total += path.stat().st_size
        return total
```

### Phase 3: Two-Pass Orchestrator

**New file**: `src/philocr/pipeline/two_pass_orchestrator.py`

```python
"""Two-pass pipeline orchestrator using Google layout intelligence."""

from pathlib import Path
from typing import Any, Callable

from philocr.detection.token_classifier import TokenClassifier, PageBounds
from philocr.detection.layout_cache import LayoutCacheManager
from philocr.processing.document_ai import process_pdf, RateLimiter
from philocr.models.config import PipelineConfig

class TwoPassOrchestrator:
    """Orchestrates two-pass OCR pipeline."""
    
    def __init__(
        self,
        config: PipelineConfig,
        cache_dir: str,
        on_progress: Callable[[str, int, str], None] | None = None,
        on_status: Callable[[str], None] | None = None,
    ):
        self.config = config
        self.cache_manager = LayoutCacheManager(cache_dir)
        self.token_classifier = TokenClassifier()
        self.on_progress = on_progress or (lambda *args: None)
        self.on_status = on_status or (lambda *args: None)
    
    def process_document(
        self,
        pdf_path: str,
        document_id: str,
        rate_limiter: RateLimiter | None = None,
        skip_pass2: bool = False,
    ) -> dict[str, Any]:
        """Process document through two-pass pipeline.
        
        Args:
            pdf_path: Path to PDF file
            document_id: Unique identifier for caching
            rate_limiter: Optional rate limiter for API calls
            skip_pass2: If True, only run Pass 1 and extract body from classification
        
        Returns:
            Dictionary with:
            - 'body_text': Clean body text
            - 'classified_tokens': All tokens with classifications
            - 'body_bounds': Computed body bounding box
            - 'layout_json': Full layout JSON (if cached)
        """
        
        # === PASS 1: Layout Discovery ===
        self.on_status("Pass 1: Running layout discovery OCR...")
        
        layout_result = self._run_pass1(pdf_path, document_id, rate_limiter)
        
        # Classify tokens and compute body bounds
        self.on_status("Pass 1: Classifying page elements...")
        
        all_classified_tokens = []
        page_templates = []
        
        for page_idx, page_data in enumerate(layout_result.get('pages', [])):
            page_bounds = PageBounds(
                width=int(page_data.get('dimension', {}).get('width', 1677)),
                height=int(page_data.get('dimension', {}).get('height', 2737))
            )
            
            # Classify all tokens on this page
            classified = []
            for token in page_data.get('tokens', []):
                classified_token = self.token_classifier.classify_token(token, page_bounds)
                classified.append(classified_token)
            
            all_classified_tokens.append(classified)
            
            # Compute body bounds for this page
            body_bounds = self.token_classifier.compute_body_bounds(classified)
            page_templates.append({
                'page_num': page_idx + 1,
                'body_bounds': body_bounds,
                'page_bounds': {'width': page_bounds.width, 'height': page_bounds.height}
            })
            
            # Cache the classification
            self.cache_manager.save_page_layout(document_id, page_idx + 1, {
                'tokens': [self._token_to_dict(t) for t in classified],
                'body_bounds': body_bounds,
                'page_bounds': {'width': page_bounds.width, 'height': page_bounds.height}
            })
        
        # Compute document-level template (median of page templates)
        document_template = self._compute_document_template(page_templates)
        self.cache_manager.save_document_template(document_id, document_template)
        
        # Extract body text from Pass 1 classification
        body_text = self._extract_body_text(all_classified_tokens)
        
        if skip_pass2:
            self.on_status("Pass 1 complete. Skipping Pass 2.")
            return {
                'body_text': body_text,
                'classified_tokens': all_classified_tokens,
                'template': document_template,
                'pass2_run': False
            }
        
        # === PASS 2: Clean OCR (optional) ===
        self.on_status("Pass 2: Running clean OCR on body regions...")
        
        # TODO: Implement Pass 2 masking and re-OCR
        # For now, return Pass 1 results
        
        return {
            'body_text': body_text,
            'classified_tokens': all_classified_tokens,
            'template': document_template,
            'pass2_run': False
        }
    
    def _run_pass1(self, pdf_path: str, document_id: str, 
                   rate_limiter: RateLimiter | None) -> dict:
        """Run Pass 1: Full-page OCR to get layout."""
        
        _, layout_json = process_pdf(
            pdf_path,
            rate_limiter=rate_limiter,
            include_layout=True  # This is the key - get full layout JSON
        )
        
        return layout_json or {}
    
    def _extract_body_text(self, all_classified_tokens: list) -> str:
        """Extract body text from classified tokens."""
        
        body_lines = []
        
        for page_tokens in all_classified_tokens:
            # Sort by y position, then x position
            sorted_tokens = sorted(page_tokens, key=lambda t: (t.y, t.x))
            
            # Group into lines (tokens with similar y)
            current_line = []
            current_y = -1
            line_threshold = 20  # pixels
            
            for token in sorted_tokens:
                if token.classification != 'body':
                    continue
                
                if current_y < 0 or abs(token.y - current_y) < line_threshold:
                    current_line.append(token.text)
                    current_y = token.y
                else:
                    # New line
                    if current_line:
                        body_lines.append(' '.join(current_line))
                    current_line = [token.text]
                    current_y = token.y
            
            # Don't forget last line
            if current_line:
                body_lines.append(' '.join(current_line))
            
            body_lines.append('')  # Page break
        
        return '\n'.join(body_lines)
    
    def _compute_document_template(self, page_templates: list) -> dict:
        """Compute document-level template from page templates."""
        import numpy as np
        
        # Extract body bounds that exist
        bounds = [p['body_bounds'] for p in page_templates if p['body_bounds']]
        
        if not bounds:
            return {'confidence': 0.0, 'body_bounds': None}
        
        # Compute median for each boundary
        template = {
            'body_left': int(np.median([b['left'] for b in bounds])),
            'body_right': int(np.median([b['right'] for b in bounds])),
            'body_top': int(np.median([b['top'] for b in bounds])),
            'body_bottom': int(np.median([b['bottom'] for b in bounds])),
            'page_width': page_templates[0]['page_bounds']['width'],
            'page_height': page_templates[0]['page_bounds']['height'],
            'confidence': 0.95,  # High confidence since Google-derived
            'pages_analysed': len(page_templates),
            'method': 'google_token_classification'
        }
        
        return template
    
    def _token_to_dict(self, token) -> dict:
        """Convert ClassifiedToken to dict for JSON serialization."""
        return {
            'text': token.text,
            'x': token.x,
            'y': token.y,
            'width': token.width,
            'height': token.height,
            'confidence': token.confidence,
            'classification': token.classification
        }
```

### Phase 4: Integration with Existing UI

**Modify**: `src/philocr/workers/processing_worker.py`

Add new processing mode:

```python
def __init__(
    self,
    file_path: str,
    parent: Any | None = None,
    temp_cleaner: Any | None = None,
    processing_mode: str = "standard",  # Add "two_pass" option
) -> None:
```

Add handler method:

```python
def _process_two_pass(self) -> None:
    """Process using two-pass Google-informed pipeline."""
    from philocr.pipeline.two_pass_orchestrator import TwoPassOrchestrator
    from philocr.models.config_loader import load_pipeline_config
    from philocr.utils.config_manager import get_config_manager
    
    # Load config
    config_manager = get_config_manager()
    config_dict = config_manager.load_config()
    pipeline_config = load_pipeline_config(config_dict)
    
    # Determine cache directory
    cache_dir = os.path.join(
        os.path.dirname(self.file_path), 
        '.philocr_cache'
    )
    
    # Create orchestrator
    orchestrator = TwoPassOrchestrator(
        config=pipeline_config,
        cache_dir=cache_dir,
        on_progress=self.stage_progress_signal.emit,
        on_status=self.status_signal.emit,
    )
    
    # Generate document ID from filename
    document_id = os.path.splitext(os.path.basename(self.file_path))[0]
    
    # Process
    result = orchestrator.process_document(
        pdf_path=self.file_path,
        document_id=document_id,
        skip_pass2=True  # Start with Pass 1 only
    )
    
    # Emit results
    self.update_signal.emit(result['body_text'])
    self.json_ready_signal.emit({
        'text': result['body_text'],
        'template': result['template'],
        'classified_tokens': [[self._token_to_serializable(t) for t in page] 
                              for page in result['classified_tokens']]
    })
    self.status_signal.emit("Two-pass processing complete.")
```

### Phase 5: UI Enhancements

**Add to Settings/UI**:

1. Processing mode dropdown:
   - "Standard" (current)
   - "Advanced Pipeline" (current 4-stage)
   - "Two-Pass (Google-Informed)" ← NEW

2. Cache management:
   - "Clear Layout Cache" button
   - Display cache size
   - Toggle "Keep layout JSON after processing"

3. Template preview enhancement:
   - Show classified tokens overlay (color-coded)
   - Green = body
   - Red = header/page_number
   - Blue = line numbers
   - Orange = apparatus

---

## PDF Generation from Standard Pipeline

### Bonus Feature: Generate PDF from Standard Pipeline

Since Standard pipeline now captures all layout information, we can reconstruct a "clean" PDF:

**New file**: `src/philocr/output/pdf_generator.py`

```python
"""Generate PDF from OCR results with layout preservation."""

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

class CleanPDFGenerator:
    """Generates clean PDF from classified tokens."""
    
    def __init__(self, font_path: str = None):
        # Register Greek-capable font
        if font_path:
            pdfmetrics.registerFont(TTFont('Greek', font_path))
            self.font_name = 'Greek'
        else:
            self.font_name = 'Helvetica'
    
    def generate(self, classified_pages: list, output_path: str,
                 include_body_only: bool = True) -> None:
        """Generate PDF from classified tokens.
        
        Args:
            classified_pages: List of lists of ClassifiedToken
            output_path: Output PDF path
            include_body_only: If True, only include body-classified tokens
        """
        c = canvas.Canvas(output_path, pagesize=A4)
        page_width, page_height = A4
        
        for page_tokens in classified_pages:
            # Filter tokens
            if include_body_only:
                tokens = [t for t in page_tokens if t.classification == 'body']
            else:
                tokens = page_tokens
            
            # Sort by position
            sorted_tokens = sorted(tokens, key=lambda t: (t.y, t.x))
            
            # Draw tokens
            for token in sorted_tokens:
                # Scale coordinates from original to A4
                # (This needs refinement based on actual page dimensions)
                x = (token.x / 1677) * page_width
                y = page_height - (token.y / 2737) * page_height
                
                c.setFont(self.font_name, 10)
                c.drawString(x, y, token.text)
            
            c.showPage()
        
        c.save()
```

---

## Migration Path

### Step 1: Implement Token Classifier (1-2 days)
- Create `token_classifier.py`
- Unit tests with sample Google JSON
- Validate against known scholarly editions

### Step 2: Implement Layout Cache (0.5 days)
- Create `layout_cache.py`
- Integration with temp file cleanup

### Step 3: Implement Two-Pass Orchestrator (1-2 days)
- Create `two_pass_orchestrator.py`
- Pass 1 implementation (complete)
- Pass 2 stub (for future)

### Step 4: UI Integration (1 day)
- Add processing mode option
- Cache management UI
- Template preview with classification overlay

### Step 5: Testing & Refinement (2-3 days)
- Test on Simplicius, Plato, Homer, etc.
- Tune classification thresholds
- Handle edge cases

---

## Configuration Options

Add to `config.yaml`:

```yaml
two_pass:
  # Token classification thresholds (as ratios of page dimensions)
  top_region_threshold: 0.08
  bottom_region_threshold: 0.70
  left_margin_threshold: 0.15
  right_margin_threshold: 0.85
  
  # Cache settings
  cache_enabled: true
  cache_retention_days: 30
  
  # Pass 2 settings
  run_pass2: false  # Start with Pass 1 only
  pass2_processor_id: null  # Can use different processor for Pass 2
```

---

## Success Metrics

After implementation, the same Simplicius page should show:

```
Template Preview (Two-Pass):
- Header Bottom: ~100         ← CORRECT: Below page number and running header
- Body Top: ~120              ← CORRECT: Below header
- Body Bottom: ~1850          ← CORRECT: Includes all main text
- Footer Top: ~1900           ← CORRECT: Where apparatus begins
- Line Numbers (Left): True   ← CORRECT
- Line Numbers (Right): True  ← CORRECT: Detected folio refs
- Confidence: 0.95            ← HIGH: Google-derived
```

---

## Summary

This plan replaces hand-crafted pixel heuristics with Google's layout intelligence:

1. **Pass 1**: Let Google do layout detection (they're better at it)
2. **Token Classification**: Use position + content to classify elements
3. **Body Extraction**: Compute body bounds from classified tokens
4. **Pass 2 (optional)**: Re-OCR masked body region for higher quality

The key insight: **We're already paying for Google's layout intelligence. Use it instead of fighting it.**
