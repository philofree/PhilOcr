---
name: gov-sweep
description: >
  Fleet governing-document sweep: inventory normative surfaces per repo,
  cold-read with Grain Collapse as the primary anti-pattern test, fill
  the eight required layer_row records (every layer names the same job
  as PURPOSE, or the row says why not), author assessments and cut briefs
  (verbal explanations, never scores), and register work on the campaign
  graph. Fourth campaign-grain procedure (not a sibling PURPOSE.md CLI
  tree). Holds governing_document_restatement end-to-end. Use for fleet
  propagation of a governance change, c2 documentary campaigns, when
  restatement drift threatens comparability, or before a succession
  (an organ leaving a face). Not a /cut hopper; not automatic deletion.
---

# Gov Sweep — fleet governing-document sweep

One text, synced byte-identical from the EuKoine hub to every member
(`naming/sync_manifest.toml`, kind `procedure`); never hand-edited in a
mirror. Routing for the repo you are in: its own agent guide — `CLAUDE.md` in a member,
`AGENTS.md` where that is the entry — and the routing table it carries, under
whatever heading that repository gives it.
Telos (cite; do not restate):
[`grain_preservation`](../../../.eukoine/predicate_lexicon.yaml) /
[`grain_collapse`](../../../.eukoine/predicate_lexicon.yaml) /
[`grain_elimination`](../../../.eukoine/predicate_lexicon.yaml) — three
grain heads at token grain; the population pair is type grain. Collapse
is the primary merge test; elimination is a token gone; preservation is
what done means at transfer grain. Regulated variable:
`governing_document_restatement` (same lexicon). Procedure owner: this
file.

## Where it sits

| Scope | Owner |
|---|---|
| Global Go-tissue catastrophes | the repo's `/eukrinikon` (sibling resolve) |
| Whole-surface documentary stoic cut | the repo's `/epitomikon` |
| Campaign identity, frontier, and proof | the repo's `/eustratikon` |
| **Fleet governing-document sweep (the grain heads as the test)** | **this skill** |
| One concern's ownership topology | the repo's `/doc-cold-reading` (or `/cold-reading`) |
| One change's collapse onto an owner | the repo's `/cut` |

This skill is not merged into `/epitomikon`. `/epitomikon` owns the
single-repo whole-surface read; this skill owns the fleet inventory, the
extra-class surfaces Epitomikon does not profile, and the
`governing_document_restatement` campaign procedure. The campaign of record
is `c2_governing_document_restatement` on `betalytes_external_check`
(`campaigns/graph.yaml`); a member shows its own pass as a local
`kind: task` node serving `governing_document_restatement`, because
Eustratikon has no cross-repo edge. The fleet manifest lives on that repo:
`campaigns/gov-sweep/inventory.yaml`.

## Resolve the instruments

- **Epitomikon:** `epitomikon profile --json --mode operational <repo>` —
  redirect outside the target tree. Resolve: PATH → sibling `bin/` →
  `make -C <sibling>/epitomikon build`.
- **Eustratikon:** `go tool eustratikon campaign-audit .` and
  `campaign-frontier .` on the target repo.
- If either binary is missing, refuse and say so — do not hand-count.

## Procedure

1. **Inventory** — every governing surface, derived, never hand-listed:
   the Epitomikon profile's documents (the repo's `.epitomikon.json`
   declares roots, chronicles and entrypoints) **plus** the extra-class
   surfaces Epitomikon does not read, enumerated by
   `git ls-files -- ':(glob)…'` from the globs in
   [`references/inventory_schema.yaml`](references/inventory_schema.yaml).
   Rows land in the fleet manifest; only `disposition` and `owner_target`
   are hand-set.
2. **Freeze profile** — per target repo, run Epitomikon operational mode;
   read the frozen JSON only after the blind cold-read is complete.
3. **Blind cold-read** — the repo's entry surfaces. **First question:**
   does any span Grain Collapse unlike particulars? **Second:** where is
   Grain Preservation *held* — which test, port, or graph row? Cite the
   lexicon; do not restate it.
3b. **Layer alignment** — fill eight `layer_row` records, one per
   `layer_id` in
   [`references/assessment_schema.yaml`](references/assessment_schema.yaml).
   Locators and the completeness rule:
   [`references/layer_alignment.md`](references/layer_alignment.md).
   A pass whose assessment artefact is missing, extra, or duplicate in
   those eight ids **has not run this step.** Do not cite the method in
   place of the table. Specimens in the method file are shape, not
   content. Obligatory before a succession.
4. **`/doc-cold-reading`** — when one concern's topology is unclear
   before a cut.
5. **Assessment artefact** — `campaigns/gov-sweep/assessments/<date>_<repo>.yaml`
   on the campaign-owning repo, schema
   [`references/assessment_schema.yaml`](references/assessment_schema.yaml):
   separate **observations** (narrow spans) from **assessments** (a verdict
   — a verbal explanation — plus a disposition). Include a **campaign row**
   for every open/doing node of the target's `campaigns/graph.yaml`, its
   regulator, and whether its regulated variable is grain-preserving.
   Include **exactly eight `layer_row` records** (completeness rule in
   the schema). Without them the artefact is not an assessment.
6. **Cut brief** — `campaigns/gov-sweep/cut_brief/<date>_<repo>.md`;
   dispositions `integrate`, `retire`, `rewrite`, `preserve-as-chronicle`,
   `refuse`. An unreachable campaign brief is `integrate` into a routing
   index the apex cites — never a link added to clear a list. Checklist:
   [`references/sweep_checklist.md`](references/sweep_checklist.md).
7. **`/cut`** — warranted collapses with a retirement ledger
   (`Retires:` on the commit).
8. **`/eustratikon`** — the member's task node to `done` with proof;
   the campaign of record closes when every enrolled member has.

## The pair is cited, never stamped

Only three skills carry the grain test by default: this one, `/epitomikon`
(single-repo whole-surface read), `/doc-cold-reading` (one-concern
topology). Each member cites the pair **once, at its apex governing
document**, routing to where preservation is held or naming the gap as a
graph row. A one-line stamp in every skill is restatement liquefaction
(owner ruling 2026-09-03, recorded in
`betalytes_external_check/docs/DECISIONS.md`).

## What this skill is not

- Not a fourth CLI repo or a fourth sibling `docs/PURPOSE.md` tree.
  Skill-owned names the procedure's home. It does not exempt a member
  command from a named port. A port need not be a capability port.
- Not a synonym of `governing_document_restatement` (that is the regulated
  variable; this is the sweep procedure).
- Not automatic cleanup — cut briefs are proposals until the owner authorizes.
- Not in scope: FAMILY domain campaigns (Euepikon, svf_translation) until
  those trees exist on disk and are enrolled.

## References

- [`references/inventory_schema.yaml`](references/inventory_schema.yaml)
- [`references/assessment_schema.yaml`](references/assessment_schema.yaml)
- [`references/sweep_checklist.md`](references/sweep_checklist.md)
- [`references/layer_alignment.md`](references/layer_alignment.md)
