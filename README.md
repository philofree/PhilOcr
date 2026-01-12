# Philofree OCR: Processing Ancient Greek Texts

**Part of the [Philofree Project](https://philofree.com)**

## Overview

This tool processes scanned PDFs of ancient Greek texts using Google Document AI, producing clean digital text ready for the Philofree corpus. It is designed to digitize out-of-copyright print editions and make them available for scholarly use.

The tool handles scanned PDFs of ancient Greek literature and converts them to structured digital formats suitable for text processing and analysis.

## Features

- **PDF processing** with automatic handling of large scholarly editions
- **Polytonic Greek support** — full Unicode coverage for ancient Greek diacritics
- **Multiple output formats** — Text, Markdown, HTML, JSON (ready for Philofree pipeline integration)
- **Document structure identification** — automatically identifies line numbers, footnotes, headers, indentation levels, and references
- **Manual scan area selection** — precise 4-corner polygon selection for cropping text areas, with mask/whiteout for excluding unwanted content
- **Memory-efficient processing** — handles large critical editions efficiently
- **Batch processing** — process entire library collections systematically

## How It Fits the Philofree Pipeline

```
Scanned PDF (print edition)
        ↓
   Philofree OCR (this tool)
        ↓
   Raw Greek text + metadata
        ↓
   Philofree processing pipeline
        ↓
   Canonical JSON → philofree.com
```

The OCR output feeds directly into our text processing pipeline, where it receives:
- Sentence segmentation with Philofree IDs
- Reference system mapping (Stephanus, Bekker, etc.)
- Integration with the searchable corpus

## Setup Instructions

### Prerequisites

- Python 3.12 or higher
- Google Cloud account with Document AI enabled
- Document AI processor configured for OCR

### Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/philofree/ocr.git
   cd ocr
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   
   # Optional: Install ijson for optimal performance with large files
   pip install ijson
   ```

4. Configure credentials:
   - Copy `ENV.template` to `ENV.local`
   - Add your Google Cloud credentials

### Google Document AI Setup

1. Create a project in [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the Document AI API
3. Create a Document AI processor for OCR
4. Create a service account and download the JSON key file
5. Update your `ENV.local` file with the appropriate values

**Note on costs**: Google Document AI offers a free tier sufficient for small projects. For large-scale digitization, costs vary based on usage volume.

## Usage

### Running the Application

```bash
python -m src.philocr.main
```

### Manual Scan Area Selection

The application provides a "Scan Area Selection" tab for precise control over which parts of each page to process:

#### Setting Up Scan Areas

1. **Select a PDF** and navigate to the "Scan Area Selection" tab
2. **Adjust the green rectangle** for each page:
   - **Drag corners** to position precisely (respects exact quadrilateral, not just bounding box)
   - **Drag edges** to resize
   - **Drag in the middle** to move the entire selection area
   - **Mouse wheel** to zoom in/out (50%-300%) for precise positioning

3. **Copy to multiple pages** (for consistent layouts):
   - **"Copy to Next →"** — applies current scan area to the next page
   - **"Copy to All Following →"** — applies to all remaining pages

#### Using Mask/Whiteout Feature

For excluding unwanted content (folio marks, page numbers, marginalia) that falls within your scan area:

1. **Enable Mask Mode**: Check the "Mask Mode (Draw Whiteout)" checkbox for the page
2. **Draw masks**: Click and drag to draw rectangles over content to exclude
   - Red dashed border shows the mask as you draw
   - Completed masks appear as semi-transparent white rectangles with red borders
3. **Delete individual masks**: Double-click on any mask to remove it
4. **Clear all masks**: Click "Clear Masks" button to start over

#### How Polygon Cropping Works

Unlike simple rectangular cropping, PhilOcr respects your exact 4-corner selection:
- Creates a precise polygon mask from your corners
- Whites out everything outside the polygon (even if it's in the bounding box)
- Essential for skewed pages where rectangular cropping would include margins
- Your pixel-perfect corner placement is preserved

#### Saving and Processing

1. **Save Scan Areas**: Click "Save Scan Areas" button (saves to `.scan_areas.json` alongside your PDF)
2. **Process**: Click "Process Scan Areas" to run OCR with your selections
3. Scan areas and masks are automatically loaded next time you open the same PDF

### Processing a Single File

```python
from utils.markdown_converter.markdown_handler import MarkdownHandler

# Convert OCR JSON output to markdown
MarkdownHandler.save_file_as_markdown(
    json_file_path="path/to/ocr_output.json",
    output_file_path="path/to/greek_text.md"
)
```

### Batch Processing (Recommended for Library Digitization)

```bash
# Process all PDFs in a directory
python test_large_file_batch.py --dir /path/to/scanned_editions --output digitized_texts

# Process a specific file
python test_large_file_batch.py --file /path/to/plato_republic_1903.json --output output_dir
```

## Building Standalone Applications

### macOS
```bash
./src/philocr/build_package.sh
```

### Windows
```bash
.\src\philocr\build_package.bat
```

## Technical Details

### Supported Input Formats

The markdown converter handles multiple JSON output formats from Document AI:
- Standard format with `document_data` and `pages`
- Alternative format with `files` array and page markers
- Chunked format for very large documents

### Processing Strategies

The tool automatically selects the optimal processing method based on file size:
- **Direct processing** for small files (< 50MB)
- **Chunked processing** for large files (50-200MB)
- **Streaming processing** with ijson for very large files (> 200MB)

This ensures that a 2000-page critical edition processes just as reliably as a 50-page fragment collection.

### Document Structure Parsing

The academic document parser automatically identifies and categorizes structural elements in scholarly texts:

- **Line numbers** — identified by position (typically in the left margin)
- **Footnotes** — detected at the bottom of pages by position and formatting patterns
- **Headers** — recognized as all caps text (typically section titles)
- **Indentation levels** — calculated from x-coordinate positions to preserve hierarchical structure
- **References** — detected through pattern matching (e.g., fragment references, citations)

These elements are properly categorized and formatted in the output to maintain the scholarly structure of the original document.

### Output Quality

- Full polytonic Greek character preservation (Unicode NFC normalized)
- Page structure maintained for cross-reference with print editions
- Paragraph and line breaks preserved where meaningful
- Document structure elements (line numbers, footnotes, headers) properly identified and formatted
- Metadata extraction for bibliographic tracking

## Project Structure

```
PhilOcr/
├── src/philocr/            # Main application code
│   ├── main.py             # Application entry point
│   ├── config/             # Configuration handling
│   ├── processing/         # OCR processing logic
│   ├── ui/                 # User interface (PyQt6)
│   └── utils/              # Utilities and helpers
├── tests/                  # Test suite
│   ├── markdown_converter/ # Converter tests
│   └── fixtures/           # Test data
├── docs/                   # Documentation
└── utils/                  # Standalone utilities
    └── markdown_converter/ # JSON-to-Markdown converter
```

## Contributing

Contributions are welcome.

**Ways to contribute**:
- Improve OCR accuracy for polytonic Greek
- Add support for additional output formats
- Enhance batch processing capabilities
- Document edge cases in Greek text processing
- Test with diverse print edition formats

### Development Workflow

1. Place source code in `src/philocr/`
2. Place tests in `tests/`
3. Use absolute imports: `from philocr.main import ...`
4. Run `pre-commit run --all-files` before committing
5. Add entries to the Development Log for significant changes

### Code Quality

Pre-commit hooks enforce:
- Ruff linting
- Black formatting
- isort import sorting
- mypy type checking

## License

**CC0 1.0 Universal — Public Domain Dedication**

This tool is dedicated to the public domain. You can copy, modify, distribute, and use it for any purpose, including commercial purposes, without asking permission.

See [LICENSE](LICENSE) for full details.  
More about CC0: https://creativecommons.org/publicdomain/zero/1.0/

## Security Notes

- Never commit `ENV.local` or credential files
- Store Google Cloud credentials securely
- The application uses environment variables, not hardcoded credentials

## Troubleshooting

**Qt plugin issues (macOS)**:
```bash
./src/philocr/reinstall_qt.sh
```

**Large file processing failures**: Install ijson for streaming support:
```bash
pip install ijson
```

**Polytonic character issues**: Ensure your terminal/editor supports Unicode and the output files are UTF-8 encoded.

## Acknowledgments

- **Google Document AI** — OCR engine with excellent Greek character recognition
- **PyQt6** — Cross-platform user interface
- **PyMuPDF** — PDF handling and manipulation
- The **Philofree community** — Testing and feedback

## Related Projects

- **[Philofree](https://philofree.com)** — The main corpus and translation project
- **[Perseus Digital Library](http://www.perseus.tufts.edu/)** — Open Greek and Latin texts
- **[First1KGreek](https://opengreekandlatin.github.io/First1KGreek/)** — Community-sourced Greek texts
- **[Open Greek and Latin](https://github.com/OpenGreekAndLatin)** — TEI XML corpus development

---

## Development Log

This project maintains a detailed Development Log tracking changes, issues, solutions, and lessons learned.

### Log Format

```markdown
## [YYYY-MM-DD] - Brief Title

**Developer:** [Name]
**Time:** [HH:MM]

### Changes Made
...

### Issues Encountered
...

### Solutions Implemented
...

### Lessons Learned
...

### Next Steps
...
```

The development log preserves institutional knowledge and helps future contributors understand why certain technical decisions were made.
