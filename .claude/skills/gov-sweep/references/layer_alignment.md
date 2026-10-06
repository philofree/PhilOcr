# Layer alignment — every surface names the same job

| | |
|---|---|
| **Title** | references/layer_alignment.md — the pointing check inside one Gov Sweep pass |
| **Status** | Binding while a pass is running |
| **Authority level** | 3 — a reference of [`../SKILL.md`](../SKILL.md), which owns the procedure |
| **Scope** | One repository of any kind: seed, face, store, lab, instrument |
| **Relationship-to** | Serves [`../SKILL.md`](../SKILL.md). The grain heads and `governing_document_restatement` live in [`.eukoine/predicate_lexicon.yaml`](../../../../.eukoine/predicate_lexicon.yaml); `wall_of_gates` is the same lexicon. This file cites them; it does not restate them. The eight `layer_id` values and the `layer_row` fields are owned by [`assessment_schema.yaml`](assessment_schema.yaml). Synced from the EuKoine hub; never hand-edited in a mirror |
| **Document class** | procedure |
| **Contract** | `epitomikon/document-contract/v1` |

The product of a repository is the nine-year-old paragraph in
`docs/PURPOSE.md`. A cold agent holding only that paragraph must be
routed to the same job by every layer below. A layer that still names a
*previous* job — leftover seed identity, a neighbour wait that has
already landed, a producer that has already moved — is a lottery.

This is not a new skill and not a new regulated variable. Restatement
drift is one disease; **layers that do not point** are how it ships.

A pass whose assessment artefact is missing any of the eight `layer_id`
values **has not run this step.**

## The eight layers (closed vocabulary)

Resolve each `layer_id` by the locator. Do not assume a member looks
like the seed, a dictionary, a store, or a website. Quote the job *this
layer* states. Compare it to the paragraph.

| `layer_id` | Locator | `points_at_telos: false` when |
|---|---|---|
| `telos` | `docs/PURPOSE.md` § Say it to a nine-year-old, plus § What this repository is not | the paragraph and the not-this list name different live products |
| `product_law` | every path PURPOSE cites as the job's own law (not the fleet kit) | those docs exist and the agent door never sends anyone there |
| `agent_door` | the file that names itself agent authority (`CLAUDE.md` or `AGENTS.md`), § Where to look | fleet rows only, or a kit/dummies file is the orientation for the *job* |
| `orientation_readme` | root `README.md` | it names a job that is not the paragraph (leftover seed identity on a member; a member's product on the seed) |
| `live_orientation` | the one `HANDOVER_YYYY-MM-DD_*.md` and derived `NOW.md` | it waits on a neighbour campaign that has landed, or next work is not the paragraph's job |
| `roster` | `capability_ports.json` | it advertises a capability that does not exist, or hides the one that does |
| `issued_capability` | every `driver` / `port` path the roster names — open those files | those files' job and the paragraph disagree, and the gap is not a named campaign stage |
| `neighbours` | PURPOSE § What this repository is not | a successor is live and this list still assigns that successor's job here |

`issued_capability` is not "the Go under `cmd/`". It is whatever the
roster already named. Python remainder, Perl, a skipped `instrument`
row: honesty is pointing; a lie in the roster is not.

## How to fill one `layer_row`

For each of the eight ids, in order:

1. Resolve `path` from the locator. If the locator finds nothing, do
   not omit the row.
2. `job_stated` — one quoted sentence from that file, or `(none)`.
3. `points_at_telos` — `true` if that sentence is the paragraph's job;
   `false` if it names a different job; `n/a` only for lawful absence.
4. `verbal_explanation` — why true, false, or n/a. Not a score.
5. `disposition` — `preserve` (points) · `rewrite` / `integrate` (does
   not) · `skip` (lawful absence). `skip` requires `skip_reason` naming
   the rule that allows absence. "Did not look" is not a skip.

Lawful absence is rare and named: an empty campaign graph that the
repo's own agent guide says has no live handover; a seed whose product
*is* the seed (README calling itself a template then points). Unnamed
absence is `points_at_telos: false`.

## Record shape

One artefact, eight rows. Values here are the *shape*; do not copy them
into a pass.

```yaml
layer_row:
  - layer_id: telos
    path: docs/PURPOSE.md
    job_stated: "<quote the nine-year-old paragraph, one sentence>"
    points_at_telos: true
    verbal_explanation: "the paragraph is the product"
    disposition: preserve
  - layer_id: live_orientation
    path: ""
    job_stated: "(none)"
    points_at_telos: n/a
    verbal_explanation: "empty campaign graph"
    disposition: skip
    skip_reason: "the repo's agent guide: no live handover until a frontier exists"
```

The other six ids follow the same keys. `issued_capability.path` is the
roster's driver paths, joined, not a guess at `cmd/`.

## Completeness (the pass/not-pass)

The assessment artefact contains exactly eight `layer_row` records, one
per `layer_id`, no extras, no duplicates. Missing, extra, or duplicate
ids: the pass is not a pass. `campaign_row` and grain observations stay
required beside this table; this table does not replace them.

## Specimens (shape, not content)

Do not copy another member's product docs. Copy the pointing.

- **Points.** EuLexikon, 2026-09-13: PURPOSE, agent door, README, and
  handover name one product; the door has rows to that product's own
  law. The product there is a dictionary; here it is whatever the
  paragraph says.
- **Does not point.** Cite
  [`wall_of_gates`](../../../../.eukoine/predicate_lexicon.yaml); do not
  restate it. `eulogikon_grid` and `russian_bcm_greenfield` are the
  family specimens: locally right gates, or locally right deletions,
  composing so the tree cannot do what PURPOSE says.

A layer that withholds the product until an organ is green, or that
removes the substrate the paragraph names, fails even when every local
rule is sincere.

## When this table is obligatory

- Every `/gov-sweep` pass (the assessment artefact carries it).
- After a neighbour's blocking campaign lands.
- Before a succession — any organ (store, mint, database, decode)
  leaving a face that used to own it. The face's eight rows must still
  name *that face's* paragraph once the organ is next door.

## What this method is not

- Not a second skill beside `/gov-sweep`.
- Not a CI gate and not a reason to withhold the product.
- Not a licence to mint a domain skill that only restates PURPOSE.
- Not a score.
