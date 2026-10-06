# GOVERNANCE — document law

| | |
|---|---|
| **Title** | docs/GOVERNANCE.md — how documents work here |
| **Status** | Binding |
| **Authority level** | 2 — below CLAUDE.md, above all other docs |
| **Scope** | Every governing document in this repository |
| **Relationship-to** | Implements CLAUDE.md § Authority order |
| **Document class** | authority |
| **Contract** | `epitomikon/document-contract/v1` |

## Document format

Every governing document opens with the carrier defined by
[`DOCUMENT_CONTRACT.md`](DOCUMENT_CONTRACT.md). `SKILL.md` retains its
cross-agent `name` + `description` frontmatter and carries procedure by path;
it does not receive the governing-document table.

## The laws

1. **Normative-only.** Governing documents carry rules, not history.
   Chronicles live in `docs/DECISIONS.md` and `work_reports/`.
2. **Rule-delta on every edit.** A change to a governing document states
   what changed and why — in the commit message at minimum; in
   `docs/DECISIONS.md` when it is a ruling.
3. **One signifier, one referent.** A term means one thing across every
   document. Synonyms for the same concept are drift.
4. **Single authority per concern.** Every rule has exactly one owner file.
   Other files cite; they do not restate. A restatement is a second
   authority and will diverge.
5. **Functional grouping.** Same concern, same home. A concern split across
   files is two concerns pretending to be one. When the repo keeps a
   placement index, that index answers "where do I look?" — it cites
   owners; it does not restate their rules. A restatement in the index is
   a second authority.

**Documentary cold-read.** Whole-surface stoic cut: `/epitomikon` (sibling
resolve when absent here). One-concern topology: `/doc-cold-reading`. Fleet
governing-document sweep: [`/gov-sweep`](.claude/skills/gov-sweep/SKILL.md).
Grain Collapse / Grain Preservation: cite
`../eukoine/.eukoine/predicate_lexicon.yaml`; do not restate.

## The family single source

Cite `../eukoine/.eukoine/WRITE_ACCESS.md`. Do not restate it. Coin-time
check: `/baptise`. This repo's vocabulary join is `PREDICATES.json`.

## The language law

**Python is the product spine.** Application code is Python. Before work
is complete it passes:

- `ruff check src/`
- Black at 88 columns, and isort on the Black profile
- `python -m pyright src/`
- `python -m pytest tests/`
- `python guardians/run_all_guardians.py --root .` when `guardians/` is
  present in the working tree

**Go is the house toolchain.** `tools/agentctl` and the Eustratikon tool
pinned in `go.mod` verify the agent surfaces, the campaign graph, and the
predicate registry. They are not the application. New product behaviour is
not written in Go. This repository has no `cmd/` program. The campaign
form `go_static_quality` is not enqueued here.

**Shell** is for hook scripts, which must run on a fresh clone with
nothing built.

Family law: `../eukoine/docs/governance/canonical_design_principles.md`
EKDP-025 — cite; do not restate. A repository with no Go product keeps the
Python bar. This repository is not an enrolled member. The citation is the
bar. It does not enrol PhilOcr.

House Go under `tools/` is held to `gofmt`, `go vet`, and `staticcheck` by
`make lint`. That command does not type-check the Python application.
`make test` runs `go test ./tools/agentctl/...`. `make pytest` is the
product.

## The vocabulary law

Distinct from the language law above: that one governs which *programming*
language, this one governs which *word*.

**One signifier, one referent.** Two words for one thing is aliasing; one
word for two things is equivocal polysemy. Both are forbidden, and both are
identity breaks — the same four the capability port forbids on data
(`.claude/skills/cut/references/capability_port.md`). A predicate registry
protects words; a port protects data.

**On correction, delete the wrong word — never add a synonym beside it.**
A synonym left standing next to the term that replaced it is an addition
with no retirement: liquefaction at the level of language
([`ROT.md`](ROT.md)).

The obligation is the family's, not this repo's invention:
`../eukoine/.eukoine/predicate_vocabulary.md` is authoritative and binds
every family repo — consult before coining, use the canonical term
verbatim, delete on correction, cite the path rather than restating
entries. Mint locally **only** a referent genuinely absent from the family
registry; a second copy of a family entry is drift, not thoroughness.

Held by [`../PREDICATES.json`](../PREDICATES.json), audited by
`go run ./tools/agentctl verify` and `go test ./...`. The audit refuses a
registry that drops one of the four rules, two baptisms sharing a referent,
a ban with no replacement, and a scan that visited no files — a clean zero
from a dead instrument is not evidence.

## Settled vs open

A question is either **settled** (recorded in CLAUDE.md § Settled stances
or here, with its ruling) or **open** (recorded nowhere as a stance — free
to relitigate). There is no third state of "everyone knows".
