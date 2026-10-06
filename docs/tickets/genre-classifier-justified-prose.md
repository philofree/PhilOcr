# Genre classifier misreads justified 19th-c. prose as verse

**Type:** bug / heuristic design
**Severity:** low (advisory `genre_hint` only; does not affect extracted text or CER)
**Stage:** 4 (assemble)

## Symptom

On page 1 of `scans/1_VOL_BB_01-10-pages.pdf` (Diogenes Laertius VII, continuous
prose), the pipeline emits `genre_hint: "verse"` at `genre_confidence: 0.7`.
The passage is prose.

## Root cause

Confirmed in `src/philocr/pipeline/stage4_assemble.py`, `analyse_line_lengths()`.
The verse test keys on **character-count per line** and its coefficient of
variation:

```python
is_verse_like = (
    line_stats["avg_length"] < config.verse_avg_line_threshold   # 60
    and line_stats["cv"] < config.verse_cv_threshold             # 0.3
)
```

A 19th-century Teubner sets prose **fully justified**, so every line is padded
to (nearly) the same width. Character counts therefore cluster tightly → **low
CV** → the page reads as verse. The docstring asserts "prose: variable line
lengths (justified to margins)", which is exactly backwards: justification
*removes* visual line-length variance. The heuristic is measuring the wrong
quantity for this document class.

This is a feature-design bug, not a threshold-tuning miss. Justified prose and
stichic verse are close to indistinguishable on right-margin geometry alone.

## Fix — add a discriminant that separates the two

Any one of these flips the page; the first is cheapest and deterministic (fits
the pipeline's "deterministic where possible" principle):

1. **Terminal hyphenation rate.** Justified prose hyphenates at the right margin
   constantly (this page: `Παροι-/μιῶν`, `Κρά-/τητι`); verse essentially never
   breaks a word at line end. A high end-of-line hyphen rate is a near-decisive
   prose signal.
2. **Marginal line numbers.** A regular column of arabic numerals down the right
   (or left) edge is a prose-edition signal, not a verse one. `has_line_numbers_left`
   / `has_line_numbers_right` already exist on the template but do not currently
   feed the genre decision — wire them in.
3. **Content-length vs. visual-length.** Measure un-justified content length
   (word count), not padded character count, so justification stops masking the
   real variance.

## Acceptance

- Page 1 of `1_VOL_BB_01-10-pages.pdf` classifies as prose (or at least not
  verse at ≥0.7).
- A known verse page still classifies as verse (no regression — add a fixture).
- `analyse_line_lengths()` docstring corrected.
- Guardians clean on touched files; `pytest tests/ -x -q` green.
