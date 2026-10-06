# PhilOcr — Rescuing Ancient Greek from the PDF Graveyard

Thousands of critical editions of ancient Greek literature exist only as scanned PDFs: Burnet's Plato, Bekker's Aristotle, the OCT volumes that generations of scholars have annotated and cited. They're out of copyright. They're freely downloadable. And they're almost completely useless to machines.

The text is locked in images. Standard OCR tools fail badly on polytonic Greek — the accents, breathings, and iota subscripts that distinguish one word from another get mangled or dropped entirely. Most digitization efforts have relied on Tesseract with custom Greek classifiers, which works well enough on clean modern typefaces but struggles with the aged, varied typography of 19th- and early 20th-century scholarly editions.

PhilOcr takes a different approach. It uses Google Document AI — a neural OCR engine that significantly outperforms Tesseract on complex historical typography — and wraps it in a purpose-built pipeline that understands how scholarly editions are structured. It doesn't just extract characters; it understands that the number in the left margin is a line reference, that the small text at the bottom is a footnote, that the all-caps header marks a new section.

The output is clean, structured, Unicode-normalized Greek text ready for downstream processing — or for a corpus like [Eulogikon](https://eulogikon.org).

![PhilOcr: scan-area selection on page 1 of von Arnim's SVF. The body text is enclosed in the green selection; the Latin section heading and the critical apparatus are masked out (red); marginal line numbers are retained.](docs/images/scan-area-selection.png)

*Page 1 of von Arnim's* Stoicorum Veterum Fragmenta *(1903). The body text is selected; the Latin heading and critical apparatus are masked out; the marginal line numbers are kept. The result, measured against a hand-checked reference, is a **1.08% character error rate** — see [`samples/`](samples/).*

## Why This Exists

The Perseus Digital Library and First1KGreek have done heroic work digitizing ancient texts. But their coverage has gaps, their sources are sometimes older transcriptions, and the long tail of scholarly editions — the ones with the best critical apparatus, the most reliable text — remains largely undigitized.

The bottleneck isn't access. It's the OCR step.

PhilOcr is designed to close that gap: take any scanned PDF of an out-of-copyright edition, run it through, and get structured text out the other side. One tool, reproducible pipeline, public domain output.

## What It Does That Others Don't

Most Greek OCR tools stop at character recognition. PhilOcr goes further:

**Structure-aware parsing.** The academic document parser identifies structural elements by their position on the page — line numbers sit in the left margin at predictable x-coordinates, footnotes cluster at the bottom with distinct formatting, headers are typically all-caps. These elements are categorized and preserved in the output, not flattened into a stream of characters.

**The scholar guides the page.** This is the core idea, and it's a deliberate departure from fully-automatic OCR. The hardest, most error-prone decisions in any OCR pipeline are not character recognition — modern neural engines are excellent at that — but *segmentation*: what is body text, what is apparatus, where lines and paragraphs begin and end. A merged or mis-split line silently corrupts everything downstream and never shows up in an accuracy score. So PhilOcr hands those decisions back to the person already looking at the page, through three escalating controls:

1. **Quadrilateral selection** — draw an exact 4-corner polygon around the text block (not just a bounding box), so skewed scans don't drag in the margins.
2. **Whiteout masks** — paint out anything inside the selection the OCR must never see: critical apparatus, folio marks, library stamps, running heads.
3. **Line and paragraph definition** — draw the line boundaries directly on the page and set paragraph breaks, supplying the segmentation the engine would otherwise have to guess.

Seconds per page of human judgment, and the engine is left with the one task it now does superbly: reading characters inside a clean, well-defined region. The high accuracy isn't *despite* the manual steps — it's largely *because* of them.

**Non-destructive by design.** Your selections, masks, and line breaks are saved as a JSON sidecar (`.scan_areas.json`) next to the PDF — the scan itself is never modified. A single toggle (Standard OCR / Manual Scan Area) switches the whole layer off and processes the full page instead. So one document yields two products on demand: the clean body text for a corpus, or the complete page with apparatus when you want everything. The apparatus is deferred, never discarded.

**Scale without pain.** A 2,000-page critical edition is a different beast from a 50-page fragment. PhilOcr automatically selects the right processing strategy: direct for small files under 50MB, chunked for 50–200MB, and streaming via `ijson` for anything larger. No manual configuration needed.

**Pipeline-ready output.** The JSON output maps directly to reference systems (Stephanus, Bekker, OCT line numbers) and is ready for sentence segmentation, corpus integration, or your own downstream processing.

**Full polytonic Unicode.** NFC-normalized output with complete coverage of ancient Greek diacritics. No half-measures.

## How It Works

The application is a four-stage pipeline behind a PyQt6 desktop interface:

| Stage | Job |
|-------|-----|
| 1 Normalize | PDF → grayscale, deskewed page images |
| 2 Mask | Apply your scan areas and whiteout masks |
| 3 OCR | Google Document AI → raw structured OCR result |
| 4 Assemble | Raw result → clean Greek text with document structure |

Each stage owns exactly one transformation; typed model objects flow between them. The result is reproducible and debuggable — when output is wrong, you can see which stage broke.

## Accuracy

On a sample page of von Arnim's *SVF* (1903) — running polytonic Greek from a dense 19th-century Teubner — PhilOcr's output scores against a hand-checked reference text as follows:

| Source | Character Error Rate |
|--------|---------------------|
| Legacy / uncorrected text layer | ~13% |
| **PhilOcr (this pipeline)** | **~1%** |

That ~1% puts it in the same tier as purpose-built academic research systems for this script (e.g. published CRNN pipelines report ~1.05–1.18% CER) — but without training a model or preparing ground truth. The benchmark is fully reproducible: see [`samples/`](samples/) for the page, the OCR output, the reference text, and a standalone script (`python cer.py ...`) that recomputes the figure.

A caveat in the spirit of honesty: this is one passage, not a corpus-wide benchmark, and the reference is a different edition, so the true figure is a conservative one. Apparatus lines and more degraded scans will score worse. The point is the order of magnitude — and that roughly half the residual error is a small, systematic, post-correctable class (dropped breathings on sentence-initial capitals), not random character confusion.

## Quickstart

```bash
git clone https://github.com/philofree/PhilOcr.git
cd PhilOcr
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ENV.template ENV.local   # add your Google Cloud credentials
python -m src.philocr.main
```

Requires Python 3.12+ and a Google Cloud account with Document AI enabled.

### Google Document AI Setup

1. Create a project in [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the Document AI API
3. Create a Document AI processor for OCR
4. Create a service account and download the JSON key file
5. Add the values to `ENV.local`

**Costs:** Google's free tier covers small projects. For library-scale digitization, costs scale with volume but remain reasonable.

## Using the Scan Area Editor

The "Scan Area Selection" tab gives you page-by-page control over what gets OCR'd:

1. **Select a PDF** and open the Scan Area Selection tab
2. **Adjust the green quadrilateral** on each page — drag corners to position precisely, drag edges to resize, drag the middle to move, mouse-wheel to zoom (50%–300%)
3. **Copy across pages** with "Copy to Next →" or "Copy to All Following →" for consistent layouts
4. **Mask unwanted content**: enable Mask Mode, then draw whiteout rectangles over folio marks, page numbers, or marginalia inside your scan area. Double-click a mask to delete it.
5. **Save** (stored as `.scan_areas.json` alongside your PDF, auto-loaded next time) and **Process**

Cropping respects your exact polygon: everything outside the four corners is whited out, even within the bounding box. Your pixel-perfect corner placement is preserved.

## Output

- Text, Markdown, HTML, and JSON formats
- Full polytonic Greek, Unicode NFC normalized
- Line numbers, footnotes, headers, and indentation levels identified and preserved
- Page structure maintained for cross-reference with the print edition
- Metadata for bibliographic tracking

Convert OCR JSON to Markdown programmatically:

```python
from utils.markdown_converter.markdown_handler import MarkdownHandler

MarkdownHandler.save_file_as_markdown(
    json_file_path="path/to/ocr_output.json",
    output_file_path="path/to/greek_text.md",
)
```

## The Broader Picture

PhilOcr is one component of the [Eulogikon Project](https://eulogikon.org), which aims to build a freely searchable, freely usable corpus of ancient Greek literature with sentence-level IDs and canonical reference mapping.

But the OCR tool itself is completely standalone and has no dependency on Eulogikon infrastructure. If you want to digitize a run of Loeb volumes, build your own corpus, feed texts into an LLM, or just read Thucydides on your e-reader without hunting for a good plain-text version — this works for all of that.

## License

CC0 1.0 Universal — Public Domain Dedication.

No rights reserved. Copy it, fork it, sell it, use it in your own project. No attribution required, no permission needed.

This is intentional. Knowledge about the ancient world belongs to everyone.

## Contributing

The most valuable contributions right now:

- **Test against diverse editions** — different publishers, typefaces, and scan qualities expose edge cases in the structure parser
- **Improve footnote detection** — critical apparatus footnotes are particularly complex and the current heuristics have known failure modes
- **Additional output formats** — TEI XML would make this useful to a much wider DH audience
- **Accuracy benchmarks** — comparative data against Tesseract on a standard set of scans would be genuinely useful to the field

Development conventions: source in `src/philocr/`, tests in `tests/`, absolute imports (`from philocr...`). Product and agent verification bars live in [`CLAUDE.md`](CLAUDE.md) § Commands (including **`make eukrinikon`** for EuKrinikon structural reads via `../eukrinikon_python`). Telos: [`docs/PURPOSE.md`](docs/PURPOSE.md).

Related: [Perseus Digital Library](https://www.perseus.tufts.edu) · [First1KGreek](https://opengreekandlatin.github.io/First1KGreek/) · [Open Greek and Latin](https://opengreekandlatin.org)
