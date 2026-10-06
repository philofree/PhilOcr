# PURPOSE — PhilOcr

| | |
|---|---|
| **Title** | docs/PURPOSE.md — the telos |
| **Status** | Binding |
| **Authority level** | 0 — above CLAUDE.md |
| **Scope** | Why this repository exists; what "done" means |
| **Relationship-to** | The apex document; everything else serves this file. The carrier of this header is owned by the family: [`../eukoine/.eukoine/document_contract.md`](../eukoine/.eukoine/document_contract.md). This repository is not an enrolled member and does not carry a local mirror |
| **Document class** | authority |
| **Contract** | `epitomikon/document-contract/v1` |

## Why this exists

Take a scanned PDF of an ancient Greek text and produce clean, accurate,
Unicode polytonic Greek that can enter the Philofree open corpus.

The person using it is looking at a page of an old edition. They mark the
body text, mask what the engine must not read, and receive structured Greek.
The four pipeline stages that do that work are owned by
[`design/CANONICAL_DESIGN_PRINCIPLES.md`](../design/CANONICAL_DESIGN_PRINCIPLES.md) §0.

## Say it to a nine-year-old

This program looks at photographs of old Greek books and writes the words
down as real Greek letters a computer can read, so the books can join a
free library of Greek texts.

## What "done" means

A scanned page, with the scholar's scan area and masks, comes out as
structured polytonic Unicode. `python -m pytest tests/`, `ruff check src/`,
and `python -m pyright src/` are green. When `guardians/` is present,
`python guardians/run_all_guardians.py --root .` is green on the files the
change touched. The agent house is green when `make verify` is green.

## What this repository is not

It is not the Greek corpus, and it does not translate. It is not a second
OCR engine beside Google Document AI. It is not a Go application. Go in
this tree is the house toolchain (`tools/agentctl`, the pinned Eustratikon
tool) and nothing else.

**Family grain pair.** Cite `../eukoine/.eukoine/predicate_lexicon.yaml`
(`grain_collapse`, `grain_preservation`; baptised together). Do not restate
the lexicon entries in this file.
