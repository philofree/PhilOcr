# UI Transformation Plan: PhilOCR v2 → v3

## Overview

Transform the current tabbed interface into a two-panel layout with left sidebar controls and right content area.

---

## Current Structure

```
┌─────────────────────────────────────────────────────────────────┐
│ Header: PhilOcr v2.0.0                    [Settings] [About]    │
├─────────────────────────────────────────────────────────────────┤
│ Processing Mode: ○ Standard OCR  ● Advanced Pipeline  [Config]  │
├─────────────────────────────────────────────────────────────────┤
│ [Select PDF] [Batch] [Load JSON] [Save Text] [Save MD] ... etc  │
├─────────────────────────────────────────────────────────────────┤
│ Status: Ready                                                   │
├─────────────────────────────────────────────────────────────────┤
│ [Text] [Markdown] [HTML] [JSON] [Scan Area Selection]  ← TABS   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│                     Tab Content Area                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Target Structure

```
┌──────────────────┬──────────────────────────────────────────────┐
│ Phil OCR         │                                              │
│ [Settings][Clear]│                                              │
├──────────────────┤         Main Content Area                    │
│ [Select ][Process│         (Page preview with scan regions)     │
│  Scan   ] Scan   │                                              │
│  Area   ] Area   │    ┌─────────────────────────────────┐       │
├──────────────────┤    │  Slide-over panel (when viewing │       │
│ ○ Standard OCR   │    │  Text/Markdown/HTML/JSON)       │       │
│ ● Manual Scan    │    └─────────────────────────────────┘       │
├──────────────────┤                                              │
│ INPUT            ├──────────────────────────────────────────────┤
│ [Single PDF    ] │  Instructions Bar (Manual mode only)         │
│ [Batch Process ] │  [● Body] [● Footnotes] [Copy to Next →]     │
│ [Load JSON     ] ├──────────────────────────────────────────────┤
├──────────────────┤  Page Scroll List                            │
│ OUTPUT           │  (scrollable list of page thumbnails)        │
│ [View ][Save   ] ├──────────────────────────────────────────────┤
│ [Text ][Text   ] │  [████████████░░░░░░░░] 45%  Page 23/50      │
│ [View ][Save   ] │  Status: Manual Scan Area mode               │
│ [MD   ][MD     ] └──────────────────────────────────────────────┘
│ [View ][Save   ] 
│ [HTML ][HTML   ] 
│ [View ][Save   ] 
│ [JSON ][JSON   ] 
└──────────────────┘
```

---

## Behavior Specifications

### View Buttons (Slide-Over Panel)

The View buttons (View Text, View Markdown, View HTML, View JSON) trigger a **slide-over panel** that covers the page preview temporarily:

1. **First click** on "View Text" → Panel slides in from the right, showing text content
2. **Second click** on same button (or click elsewhere) → Panel slides back out
3. The PDF preview **stays loaded underneath** — the overlay just temporarily covers it
4. Only one overlay can be visible at a time (clicking "View HTML" while "View Text" is open switches content)

```python
class ContentAreaWidget(QWidget):
    """Main content area with slide-over capability."""
    
    def __init__(self):
        self.page_view = PagePreviewWidget()      # Always present underneath
        self.overlay_view = TextOverlayWidget()   # Slides over when viewing output
        self.overlay_visible = False
        self.current_view = None  # "text", "markdown", "html", "json"
        
    def show_overlay(self, view_type: str, content: str):
        """Slide overlay in with specified content."""
        self.overlay_view.set_content(content, view_type)
        if not self.overlay_visible:
            self.overlay_view.slide_in()  # Animate from right
            self.overlay_visible = True
        self.current_view = view_type
        
    def hide_overlay(self):
        """Slide overlay back out, revealing page preview."""
        self.overlay_view.slide_out()
        self.overlay_visible = False
        self.current_view = None
        
    def toggle_overlay(self, view_type: str, content: str):
        """Toggle overlay - hide if same type, show if different."""
        if self.overlay_visible and self.current_view == view_type:
            self.hide_overlay()
        else:
            self.show_overlay(view_type, content)
```

### Standard OCR Mode

When "Standard OCR" is selected:

- **Right panel shows**: Scrollable view of all PDF pages (no crop rectangles)
- **Purpose**: User can scroll through to verify they selected the correct document
- **Instructions bar**: Hidden (no regions to configure)
- **Page scroll list**: Still visible for navigation
- **Processing**: Sends full pages to Document AI without cropping

### Manual Scan Area Mode

When "Manual Scan Area" is selected:

- **Right panel shows**: Large page preview with Body (green) and Footnotes (blue) regions
- **Instructions bar**: Visible with region toggles and "Copy to Next Page" button
- **Page scroll list**: Visible, showing thumbnails with region indicators
- **Processing**: Crops to defined regions before sending to Document AI

### Progress Bar Location

Progress bar is at the **bottom of the right panel**, as part of the status area:

```
├──────────────────────────────────────────────────────────────┤
│  [████████████████░░░░░░░░░░░░░░] 45%    Processing page 23  │
│  Status: Manual Scan Area mode — 50 pages total              │
└──────────────────────────────────────────────────────────────┘
```

- Below the page scroll list
- Shows percentage, current operation, and page count
- Text status line below the progress bar

---

## Phase 1: Create New Layout Structure

### 1.1 Create `LeftPanelWidget` class

**New file: `src/philocr/ui/widgets/left_panel.py`**

```python
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QPushButton, QRadioButton, QButtonGroup, QLabel
)

class LeftPanelWidget(QWidget):
    """Left sidebar containing all controls."""
    
    # Signals for primary actions
    select_scan_area_clicked = pyqtSignal()
    process_scan_area_clicked = pyqtSignal()
    
    # Signals for mode change
    mode_changed = pyqtSignal(str)  # "standard" or "manual"
    
    # Signals for input actions
    single_pdf_clicked = pyqtSignal()
    batch_process_clicked = pyqtSignal()
    load_json_clicked = pyqtSignal()
    
    # Signals for view actions (toggle slide-over)
    view_text_clicked = pyqtSignal()
    view_markdown_clicked = pyqtSignal()
    view_html_clicked = pyqtSignal()
    view_json_clicked = pyqtSignal()
    
    # Signals for save actions
    save_text_clicked = pyqtSignal()
    save_markdown_clicked = pyqtSignal()
    save_html_clicked = pyqtSignal()
    save_json_clicked = pyqtSignal()
    
    # Signals for header actions
    settings_clicked = pyqtSignal()
    clear_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(210)
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Header
        layout.addWidget(self._create_header())
        
        # Primary actions
        layout.addWidget(self._create_primary_actions())
        
        # Mode selector
        layout.addWidget(self._create_mode_selector())
        
        # Input section
        layout.addWidget(self._create_input_section())
        
        # Output section
        layout.addWidget(self._create_output_section())
        
        # Stretch at bottom
        layout.addStretch()
        
    def _create_header(self) -> QFrame:
        """Create header with title and Settings/Clear buttons."""
        # ... implementation
        
    def _create_primary_actions(self) -> QFrame:
        """Create Select Scan Area / Process Scan Area buttons."""
        # ... implementation
        
    def _create_mode_selector(self) -> QFrame:
        """Create Standard OCR / Manual Scan Area radio buttons."""
        # ... implementation
        
    def _create_input_section(self) -> QFrame:
        """Create Single PDF, Batch Process, Load JSON buttons."""
        # ... implementation
        
    def _create_output_section(self) -> QFrame:
        """Create View/Save button pairs."""
        # ... implementation
        
    def set_save_buttons_enabled(self, enabled: bool):
        """Enable/disable save buttons based on content availability."""
        # ... implementation
        
    def set_processing_state(self, processing: bool):
        """Update UI state during processing."""
        # ... implementation
```

### 1.2 Create `RightPanelWidget` class

**New file: `src/philocr/ui/widgets/right_panel.py`**

```python
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget

class RightPanelWidget(QWidget):
    """Right panel containing content area, instructions, page list, and status."""
    
    # Signals
    page_selected = pyqtSignal(int)  # page_num
    copy_to_next_clicked = pyqtSignal()
    region_toggled = pyqtSignal(str, bool)  # region_type, enabled
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Main content area (page preview + slide-over)
        self.content_area = ContentAreaWidget()
        layout.addWidget(self.content_area, 1)  # Expanding
        
        # Instructions bar (Manual mode only)
        self.instructions_bar = InstructionsBarWidget()
        layout.addWidget(self.instructions_bar)
        
        # Page scroll list
        self.page_list = PageScrollListWidget()
        layout.addWidget(self.page_list)
        
        # Status bar with progress
        self.status_bar = StatusBarWidget()
        layout.addWidget(self.status_bar)
        
    def set_mode(self, mode: str):
        """Switch between 'standard' and 'manual' mode."""
        self.instructions_bar.setVisible(mode == "manual")
        self.content_area.set_regions_visible(mode == "manual")
        
    def load_pdf(self, pdf_path: str):
        """Load PDF and display pages."""
        # ... implementation
        
    def show_overlay(self, view_type: str, content: str):
        """Show slide-over panel with content."""
        self.content_area.show_overlay(view_type, content)
        
    def hide_overlay(self):
        """Hide slide-over panel."""
        self.content_area.hide_overlay()
        
    def set_progress(self, percent: int, status_text: str):
        """Update progress bar and status."""
        self.status_bar.set_progress(percent, status_text)
```

### 1.3 Create `ContentAreaWidget` (with slide-over)

**New file: `src/philocr/ui/widgets/content_area.py`**

```python
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve
from PyQt6.QtWidgets import QWidget, QStackedLayout

class ContentAreaWidget(QWidget):
    """Main content area with page preview and slide-over panel."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.overlay_visible = False
        self.current_view = None
        self._setup_ui()
        
    def _setup_ui(self):
        # Use a custom layout that allows overlay
        self.page_preview = PagePreviewWidget()
        self.overlay = SlideOverPanel()
        
        # Position overlay off-screen initially
        # ... implementation
        
    def show_overlay(self, view_type: str, content: str):
        """Slide in overlay with content."""
        self.overlay.set_content(content, view_type)
        if not self.overlay_visible:
            self._animate_overlay_in()
        self.overlay_visible = True
        self.current_view = view_type
        
    def hide_overlay(self):
        """Slide out overlay."""
        self._animate_overlay_out()
        self.overlay_visible = False
        self.current_view = None
        
    def toggle_overlay(self, view_type: str, content: str):
        """Toggle overlay visibility."""
        if self.overlay_visible and self.current_view == view_type:
            self.hide_overlay()
        else:
            self.show_overlay(view_type, content)
            
    def _animate_overlay_in(self):
        """Animate overlay sliding in from right."""
        self.animation = QPropertyAnimation(self.overlay, b"pos")
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        # ... set start/end positions
        self.animation.start()
        
    def _animate_overlay_out(self):
        """Animate overlay sliding out to right."""
        # ... implementation
```

### 1.4 Create `ScanRegionEditor` widget (Two Regions)

**New file: `src/philocr/ui/widgets/scan_region_editor.py`**

```python
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPen, QColor

class ScanRegionEditor(QWidget):
    """
    Page preview with two draggable regions: Body (green) and Footnotes (blue).
    Each region can be moved as a unit, resized via edges, or skewed via corners.
    """
    
    regions_changed = pyqtSignal(int, dict)  # page_num, {"body": region, "footnotes": region}
    
    def __init__(self, page_num: int, page_image, parent=None):
        super().__init__(parent)
        self.page_num = page_num
        self.page_image = page_image
        
        # Region data
        self.body_region = None      # ManualScanArea or None
        self.footnotes_region = None # ManualScanArea or None
        self.body_enabled = True
        self.footnotes_enabled = True
        
        # Interaction state
        self.dragging = False
        self.drag_target = None  # "body", "footnotes"
        self.drag_handle = None  # "tl", "tr", "bl", "br", "top", "bottom", "left", "right", "move"
        
        # Display scaling
        self.scale_x = 1.0
        self.scale_y = 1.0
        
        self.setMouseTracking(True)
        
    def set_body_region(self, region):
        """Set body region coordinates."""
        self.body_region = region
        self.update()
        
    def set_footnotes_region(self, region):
        """Set footnotes region coordinates."""
        self.footnotes_region = region
        self.update()
        
    def set_body_enabled(self, enabled: bool):
        """Enable/disable body region."""
        self.body_enabled = enabled
        self.update()
        
    def set_footnotes_enabled(self, enabled: bool):
        """Enable/disable footnotes region."""
        self.footnotes_enabled = enabled
        self.update()
        
    def paintEvent(self, event):
        """Draw page image and regions."""
        painter = QPainter(self)
        
        # Draw page image
        # ... implementation
        
        # Draw body region (green)
        if self.body_region and self.body_enabled:
            self._draw_region(painter, self.body_region, QColor(46, 204, 113), "Body")
            
        # Draw footnotes region (blue)
        if self.footnotes_region and self.footnotes_enabled:
            self._draw_region(painter, self.footnotes_region, QColor(52, 152, 219), "Footnotes")
            
    def _draw_region(self, painter, region, color, label):
        """Draw a single region with handles and label."""
        # Draw rectangle
        # Draw corner handles
        # Draw edge handles
        # Draw center move handle
        # Draw label
        # ... implementation
        
    def mousePressEvent(self, event):
        """Handle mouse press for starting drag."""
        # Hit test against both regions
        # ... implementation
        
    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging."""
        # Update region based on drag target and handle
        # ... implementation
        
    def mouseReleaseEvent(self, event):
        """Handle mouse release to end drag."""
        # Emit regions_changed signal
        # ... implementation
```

### 1.5 Create Supporting Widgets

**`src/philocr/ui/widgets/instructions_bar.py`**

```python
class InstructionsBarWidget(QWidget):
    """Instructions bar with region toggles and Copy to Next button."""
    
    body_toggled = pyqtSignal(bool)
    footnotes_toggled = pyqtSignal(bool)
    copy_to_next_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        
        # Region toggles
        self.body_checkbox = QCheckBox("● Body")
        self.body_checkbox.setChecked(True)
        self.body_checkbox.setStyleSheet("color: #2ecc71; font-weight: bold;")
        
        self.footnotes_checkbox = QCheckBox("● Footnotes")
        self.footnotes_checkbox.setChecked(True)
        self.footnotes_checkbox.setStyleSheet("color: #3498db; font-weight: bold;")
        
        # Instructions text
        instructions = QLabel("Drag corners to resize • Drag center to move")
        
        # Copy button
        self.copy_btn = QPushButton("Copy to Next Page →")
        
        layout.addWidget(self.body_checkbox)
        layout.addWidget(self.footnotes_checkbox)
        layout.addStretch()
        layout.addWidget(instructions)
        layout.addWidget(self.copy_btn)
```

**`src/philocr/ui/widgets/page_scroll_list.py`**

```python
class PageScrollListWidget(QWidget):
    """Vertical scrollable list of page thumbnails."""
    
    page_selected = pyqtSignal(int)  # page_num
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(130)
        self._setup_ui()
        
    def load_pages(self, pdf_path: str, regions: dict):
        """Load page thumbnails from PDF."""
        # ... implementation
        
    def set_current_page(self, page_num: int):
        """Highlight the current page."""
        # ... implementation
        
    def update_page_regions(self, page_num: int, regions: dict):
        """Update region indicators for a page."""
        # ... implementation
```

**`src/philocr/ui/widgets/status_bar_widget.py`**

```python
class StatusBarWidget(QWidget):
    """Status bar with progress bar and status text."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status text
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        
    def set_progress(self, percent: int, text: str):
        """Update progress bar."""
        self.progress_bar.setVisible(percent > 0 and percent < 100)
        self.progress_bar.setValue(percent)
        self.status_label.setText(text)
        
    def set_status(self, text: str):
        """Update status text only."""
        self.status_label.setText(text)
```

---

## Phase 2: Update Data Model

### 2.1 Update `ManualScanArea` model

**File: `src/philocr/models/scan_area.py`**

```python
from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ManualScanArea:
    """Single scan area defined by 4 corner points."""
    
    top_left: tuple[int, int]
    top_right: tuple[int, int]
    bottom_right: tuple[int, int]
    bottom_left: tuple[int, int]
    
    def to_list(self) -> list[tuple[int, int]]:
        """Convert to list of corners."""
        return [self.top_left, self.top_right, self.bottom_right, self.bottom_left]
    
    def scale_to(self, target_width: int, target_height: int, 
                 source_width: int, source_height: int) -> list[tuple[int, int]]:
        """Scale coordinates to target dimensions."""
        scale_x = target_width / source_width
        scale_y = target_height / source_height
        return [(int(x * scale_x), int(y * scale_y)) for x, y in self.to_list()]
    
    @classmethod
    def from_list(cls, corners: list[tuple[int, int]]) -> ManualScanArea:
        """Create from list of corners."""
        return cls(
            top_left=tuple(corners[0]),
            top_right=tuple(corners[1]),
            bottom_right=tuple(corners[2]),
            bottom_left=tuple(corners[3]),
        )
    
    @classmethod
    def create_default_body(cls, width: int, height: int) -> ManualScanArea:
        """Create default body region (top 70% of page, with margins)."""
        margin_x = int(width * 0.08)
        margin_top = int(height * 0.08)
        margin_bottom = int(height * 0.30)  # Leave room for footnotes
        return cls(
            top_left=(margin_x, margin_top),
            top_right=(width - margin_x, margin_top),
            bottom_right=(width - margin_x, height - margin_bottom),
            bottom_left=(margin_x, height - margin_bottom),
        )
    
    @classmethod
    def create_default_footnotes(cls, width: int, height: int) -> ManualScanArea:
        """Create default footnotes region (bottom 20% of page, with margins)."""
        margin_x = int(width * 0.08)
        top = int(height * 0.75)
        bottom = int(height * 0.95)
        return cls(
            top_left=(margin_x, top),
            top_right=(width - margin_x, top),
            bottom_right=(width - margin_x, bottom),
            bottom_left=(margin_x, bottom),
        )


@dataclass
class PageRegions:
    """Scan regions for a single page."""
    
    body: ManualScanArea | None = None
    footnotes: ManualScanArea | None = None
    source_width: int | None = None
    source_height: int | None = None
    
    def has_body(self) -> bool:
        return self.body is not None
    
    def has_footnotes(self) -> bool:
        return self.footnotes is not None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        data = {}
        if self.body:
            data["body"] = {
                "top_left": list(self.body.top_left),
                "top_right": list(self.body.top_right),
                "bottom_right": list(self.body.bottom_right),
                "bottom_left": list(self.body.bottom_left),
            }
        if self.footnotes:
            data["footnotes"] = {
                "top_left": list(self.footnotes.top_left),
                "top_right": list(self.footnotes.top_right),
                "bottom_right": list(self.footnotes.bottom_right),
                "bottom_left": list(self.footnotes.bottom_left),
            }
        if self.source_width:
            data["source_width"] = self.source_width
        if self.source_height:
            data["source_height"] = self.source_height
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> PageRegions:
        """Create from dictionary."""
        body = None
        footnotes = None
        
        if "body" in data:
            body = ManualScanArea(
                top_left=tuple(data["body"]["top_left"]),
                top_right=tuple(data["body"]["top_right"]),
                bottom_right=tuple(data["body"]["bottom_right"]),
                bottom_left=tuple(data["body"]["bottom_left"]),
            )
        
        if "footnotes" in data:
            footnotes = ManualScanArea(
                top_left=tuple(data["footnotes"]["top_left"]),
                top_right=tuple(data["footnotes"]["top_right"]),
                bottom_right=tuple(data["footnotes"]["bottom_right"]),
                bottom_left=tuple(data["footnotes"]["bottom_left"]),
            )
        
        return cls(
            body=body,
            footnotes=footnotes,
            source_width=data.get("source_width"),
            source_height=data.get("source_height"),
        )


@dataclass
class DocumentRegions:
    """Collection of scan regions for all pages in a document."""
    
    pages: dict[int, PageRegions]  # page_num -> PageRegions
    
    def get(self, page_num: int) -> PageRegions | None:
        return self.pages.get(page_num)
    
    def set(self, page_num: int, regions: PageRegions):
        self.pages[page_num] = regions
    
    def copy_to_page(self, from_page: int, to_page: int):
        """Copy regions from one page to another."""
        if from_page in self.pages:
            # Deep copy the regions
            source = self.pages[from_page]
            self.pages[to_page] = PageRegions(
                body=source.body,
                footnotes=source.footnotes,
                source_width=source.source_width,
                source_height=source.source_height,
            )


def save_document_regions(regions: DocumentRegions, file_path: str | Path) -> None:
    """Save document regions to JSON file."""
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    data = {}
    for page_num, page_regions in regions.pages.items():
        data[str(page_num)] = page_regions.to_dict()
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_document_regions(file_path: str | Path) -> DocumentRegions:
    """Load document regions from JSON file."""
    file_path = Path(file_path)
    
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    pages = {}
    for page_str, page_data in data.items():
        page_num = int(page_str)
        pages[page_num] = PageRegions.from_dict(page_data)
    
    return DocumentRegions(pages=pages)
```

### 2.2 JSON Format

```json
{
  "0": {
    "body": {
      "top_left": [80, 60],
      "top_right": [920, 60],
      "bottom_right": [920, 700],
      "bottom_left": [80, 700]
    },
    "footnotes": {
      "top_left": [80, 750],
      "top_right": [920, 750],
      "bottom_right": [920, 950],
      "bottom_left": [80, 950]
    },
    "source_width": 1000,
    "source_height": 1200
  },
  "1": {
    "body": {
      "top_left": [80, 60],
      "top_right": [920, 60],
      "bottom_right": [920, 720],
      "bottom_left": [80, 720]
    },
    "source_width": 1000,
    "source_height": 1200
  }
}
```

Note: Page 1 has no footnotes region (body only).

---

## Phase 3: Update Pipeline Integration

### 3.1 Update `stage2_mask.py`

**File: `src/philocr/pipeline/stage2_mask.py`**

```python
from philocr.models.scan_area import DocumentRegions, PageRegions

def process_page_regions(
    image: np.ndarray,
    page_regions: PageRegions,
    target_width: int,
    target_height: int,
) -> dict[str, np.ndarray]:
    """
    Extract body and footnotes as separate images.
    
    Args:
        image: Full page image (normalized)
        page_regions: PageRegions with body and/or footnotes
        target_width: Width of the normalized image
        target_height: Height of the normalized image
    
    Returns:
        Dict with "body" and/or "footnotes" keys containing cropped images
    """
    results = {}
    
    source_w = page_regions.source_width or target_width
    source_h = page_regions.source_height or target_height
    
    if page_regions.body:
        scaled_corners = page_regions.body.scale_to(
            target_width, target_height, source_w, source_h
        )
        results["body"] = apply_perspective_transform(image, scaled_corners)
    
    if page_regions.footnotes:
        scaled_corners = page_regions.footnotes.scale_to(
            target_width, target_height, source_w, source_h
        )
        results["footnotes"] = apply_perspective_transform(image, scaled_corners)
    
    return results
```

### 3.2 Output Format

```json
{
  "pages": [
    {
      "page_num": 0,
      "body": {
        "text": "Ὅτι μὲν οὖν ἀρχήν τε καὶ στοιχεῖον...",
        "confidence": 0.95
      },
      "footnotes": {
        "text": "1 αὐξανόμενον M  φερόμενον AFM cf. p. 831,27...",
        "confidence": 0.92
      }
    },
    {
      "page_num": 1,
      "body": {
        "text": "τὸ δὲ ὕδωρ ἀρχὴν εἶναι τῶν ὄντων...",
        "confidence": 0.94
      }
    }
  ],
  "metadata": {
    "processing_mode": "manual_scan_area",
    "total_pages": 2
  }
}
```

---

## Phase 4: Wire Up MainWindow

### 4.1 Update `ui_composer.py`

```python
from PyQt6.QtWidgets import QWidget, QHBoxLayout

from philocr.ui.widgets.left_panel import LeftPanelWidget
from philocr.ui.widgets.right_panel import RightPanelWidget


class MainWindowUIComposer:
    """Composes the two-panel MainWindow layout."""
    
    def compose_ui(self) -> MainWindowUI:
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Left panel (fixed width sidebar)
        left_panel = LeftPanelWidget()
        main_layout.addWidget(left_panel)
        
        # Right panel (expanding content area)
        right_panel = RightPanelWidget()
        main_layout.addWidget(right_panel, 1)
        
        return MainWindowUI(
            main_widget=main_widget,
            left_panel=left_panel,
            right_panel=right_panel,
        )
```

### 4.2 Update Signal Connections in `main_window.py`

```python
def _connect_left_panel_signals(self):
    lp = self.ui.left_panel
    
    # Header
    lp.settings_clicked.connect(self.show_settings_dialog)
    lp.clear_clicked.connect(self.clear_results)
    
    # Primary actions
    lp.select_scan_area_clicked.connect(self._on_select_scan_area)
    lp.process_scan_area_clicked.connect(self._on_process_scan_area)
    
    # Mode
    lp.mode_changed.connect(self._on_mode_changed)
    
    # Input
    lp.single_pdf_clicked.connect(self.select_file)
    lp.batch_process_clicked.connect(self.select_multiple_files)
    lp.load_json_clicked.connect(self.load_json)
    
    # View (toggle slide-over)
    lp.view_text_clicked.connect(lambda: self._toggle_view("text"))
    lp.view_markdown_clicked.connect(lambda: self._toggle_view("markdown"))
    lp.view_html_clicked.connect(lambda: self._toggle_view("html"))
    lp.view_json_clicked.connect(lambda: self._toggle_view("json"))
    
    # Save
    lp.save_text_clicked.connect(self.save_text)
    lp.save_markdown_clicked.connect(self.save_markdown)
    lp.save_html_clicked.connect(self.save_html)
    lp.save_json_clicked.connect(self.save_json)

def _toggle_view(self, view_type: str):
    """Toggle slide-over panel for viewing output."""
    content = self._get_content_for_view(view_type)
    self.ui.right_panel.toggle_overlay(view_type, content)
```

---

## Phase 5: Remove Dead Code

### 5.1 Files to Delete

| File | Reason |
|------|--------|
| `src/philocr/ui/tab_factory.py` | Tabs removed |
| `src/philocr/ui/dialogs/pipeline_config_dialog.py` | Config button removed |
| `src/philocr/detection/zones.py` | Automatic detection removed |
| `src/philocr/detection/profiles.py` | Automatic detection removed |
| `src/philocr/detection/separators.py` | Automatic detection removed |
| `src/philocr/pipeline/stage2_template.py` | Template extraction removed |
| `src/philocr/pipeline/utils/template_visualizer.py` | Template visualization removed |
| `tests/pipeline/test_detection_profiles.py` | Tests for deleted code |
| `tests/pipeline/test_detection_zones.py` | Tests for deleted code |
| `tests/pipeline/test_stage2_template.py` | Tests for deleted code |
| `docs/TWO_PASS_PIPELINE_PLAN.md` | Superseded by manual approach |

### 5.2 Files to Simplify

| File | Changes |
|------|---------|
| `src/philocr/models/config.py` | Remove automatic detection settings |
| `src/philocr/pipeline/orchestrator.py` | Remove template extraction |
| `src/philocr/ui/dialogs/__init__.py` | Remove pipeline config dialog export |

---

## Implementation Order

1. **Phase 1.1**: Create `LeftPanelWidget` 
2. **Phase 1.4**: Create `ScanRegionEditor` (two regions)
3. **Phase 1.5**: Create supporting widgets (InstructionsBar, PageScrollList, StatusBar)
4. **Phase 1.3**: Create `ContentAreaWidget` with slide-over
5. **Phase 1.2**: Create `RightPanelWidget` (assembles content area + supporting widgets)
6. **Phase 2**: Update data model (`PageRegions`, `DocumentRegions`)
7. **Phase 4.1**: Update `ui_composer.py` for new layout
8. **Phase 4.2**: Update `main_window.py` signal connections
9. **Phase 3**: Update pipeline for two regions
10. **Phase 5**: Delete dead code

---

## Testing Checklist

- [ ] Left panel buttons emit correct signals
- [ ] Mode toggle switches between Standard/Manual correctly
- [ ] View buttons toggle slide-over panel
- [ ] Slide-over animation works smoothly
- [ ] Page preview displays PDF correctly
- [ ] Body region (green) is draggable and resizable
- [ ] Footnotes region (blue) is draggable and resizable
- [ ] Region toggles enable/disable regions
- [ ] "Copy to Next Page" copies both regions
- [ ] Page scroll list navigation works
- [ ] Progress bar displays during processing
- [ ] Save buttons export correct formats
- [ ] DPI scaling works correctly (preview → normalized image)
- [ ] JSON save/load preserves both regions
- [ ] Pipeline processes body and footnotes separately
- [ ] Output JSON contains separated body/footnotes text
