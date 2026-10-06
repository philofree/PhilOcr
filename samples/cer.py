#!/usr/bin/env python3
"""Character Error Rate (CER) for PhilOcr output against a reference text.

Measures how close OCR output is to a hand-checked reference, as the fraction
of single-character edits (Levenshtein distance / reference length).

Usage:
    python cer.py OCR_FILE TRUTH_FILE

Reports two figures:
  - CER:            full polytonic comparison (accents and breathings count)
  - base-char CER:  diacritics stripped, so only base letters are compared

Both texts are NFC-normalised and whitespace-collapsed. Quote and dash
variants are folded so the metric reflects character recognition rather than
differences in editorial punctuation style between editions.

Reference texts here come from the Eulogikon corpus (Diogenes Laertius VII),
which is a different edition from von Arnim's SVF; a handful of edit-distance
counts may therefore be genuine edition variants rather than OCR errors, so
the reported CER is a conservative upper bound.
"""

from __future__ import annotations

import re
import sys
import unicodedata


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFC", s)
    s = s.replace("—", " ").replace("–", " ")
    s = re.sub(r'["„""«»]', "", s)
    return re.sub(r"\s+", " ", s).strip()


def _strip_diacritics(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", s) if not unicodedata.combining(c)
    )


def _levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(
                min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb))
            )
        prev = cur
    return prev[-1]


def cer(ocr: str, truth: str) -> tuple[float, float, int, int]:
    o, g = _norm(ocr), _norm(truth)
    dist = _levenshtein(o, g)
    full = 100.0 * dist / len(g)
    so, sg = _strip_diacritics(o), _strip_diacritics(g)
    base = 100.0 * _levenshtein(so, sg) / len(sg)
    return full, base, dist, len(g)


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    with open(sys.argv[1], encoding="utf-8") as f:
        ocr = f.read()
    with open(sys.argv[2], encoding="utf-8") as f:
        truth = f.read()
    full, base, dist, n = cer(ocr, truth)
    print(f"reference length : {n} chars")
    print(f"edit distance    : {dist}")
    print(f"CER              : {full:.2f}%")
    print(f"base-char CER    : {base:.2f}%  (diacritics ignored)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
