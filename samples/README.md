# Sample: one page, scan to corpus-ready text

A worked example on page 1 of von Arnim's *Stoicorum Veterum Fragmenta*
(Vol. I, 1903) — the opening of the Zeno testimonia (Diogenes Laertius VII).
It runs the full pipeline on a hard case: a dense 19th-century Teubner with a
critical apparatus and marginal line numbers.

## Files

| File | What it is |
|------|------------|
| `zeno_page1.png` | The source scan (page 1 of `scans/1_VOL_BB_01-10-pages.pdf`). |
| `zeno_page1.result.json` | The structured pipeline output for that page (metadata, per-stage timings, per-paragraph text and confidence). |
| `zeno_vit_7_1.ocr.txt` | The OCR text for the D.L. VII.1 passage, lifted from the result. |
| `zeno_vit_7_1.truth.txt` | A hand-checked reference reading of the same passage (Eulogikon corpus, Diogenes Laertius VII). |
| `cer.py` | Computes Character Error Rate of OCR against the reference. Pure standard library. |

## Reproduce the accuracy figure

```bash
cd samples
python cer.py zeno_vit_7_1.ocr.txt zeno_vit_7_1.truth.txt
```

Expected:

```
reference length : 557 chars
edit distance    : 6
CER              : 1.08%
base-char CER    : 0.54%  (diacritics ignored)
```

So **~1% character error rate** on running polytonic Greek — the same tier as
purpose-built research systems for this script — straight out of the pipeline.

### Honest caveats

- One ~560-character passage is a sample, not a corpus benchmark. Apparatus
  lines and more degraded pages score worse.
- The reference is a *different edition* of Diogenes Laertius than von Arnim's,
  so a few of the six edit-distance counts may be genuine edition variants, not
  OCR errors. The true CER is plausibly lower; this is a conservative figure.
- About half the remaining error is diacritic-level — chiefly dropped breathings
  on sentence-initial capitals (e.g. `Τον` for `Τὸν`, `Αθηναῖος` for `Ἀθηναῖος`).
  These form a small, systematic, post-correctable class, not random misreads.

## Timing

From `zeno_page1.result.json` → `stages_seconds`: stage 3 (Document AI OCR)
dominates at ~7s; normalisation, masking, and assembly together are under a
second (assembly is ~4ms). The machine time is trivial; the human's scan-area
and line-break decisions are where the minutes go — and they are what buys the
1% CER.

## The contrast

For comparison, `scans/10_pages_SVF.txt` is the kind of output an uncorrected
text layer / legacy OCR gives on the same edition: `β` for `σ`, `6` for `δ`,
`&` for `θ` throughout, scoring around 13% CER. That text is unsearchable and
unembeddable. The difference is the pipeline.
