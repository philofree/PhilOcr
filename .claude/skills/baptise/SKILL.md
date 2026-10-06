---
name: baptise
description: >
  Run the mechanical lexicon check BEFORE minting any name — class, module,
  function, port, predicate, JSON key, YAML key, DB column, CLI flag, or any
  term that names a kind of thing in the system. Import the existing
  signifier, or coin under the one-signifier-one-referent rule and record
  the registry entry in the same pass. Use when about to name anything new,
  when asked "what should I call this", "is there already a name for this",
  "check the lexicon", or when a reviewer flags a name. The naming analog
  of /cut: audits catch known-banned tokens at commit, but a freshly-coined
  synonym is a novel wrong name no banned-list sees — it is caught only
  here, at coin-time. Model-invocable whenever a turn is about to mint or
  rename a system predicate.
---

# `/baptise` — the lexicon check before any name is minted

You cannot do propositional reasoning without nailed predicates. Every
classification, every cross-reference, every invariant, and every field
name presupposes a vocabulary whose referents are agreed.

**Authorities** (this skill points, never restates):

- **This repo's join** — [`PREDICATES.json`](../../../PREDICATES.json).
  The four rules, suite-local baptisms, and banned patterns. Audited by
  `go run ./tools/agentctl verify`.
- **The family registry** — the path named in `PREDICATES.json` as
  `family_law` / `family_registry` (the `.eukoine/` lexicon at the hub).
  Authoritative for shared code signifiers. Consult before coining; mint
  locally only a referent absent from the family registry. How the family
  single source changes is owned at the hub
  (`../eukoine/.eukoine/WRITE_ACCESS.md`) — cite that path; do not
  restate it, and do not hand-edit a member mirror.
- **A member-local lexicon**, when the seeded repo has one (for example
  `docs/predicate_vocabulary/lexicon.yaml`) — suite-local terms only; it
  must not redefine a family entry.

## How to invoke

- Type `/baptise`, or ask what to call something / whether a name exists.
- Or don't — it fires at coin-time, before any new class, module, function,
  port, predicate, JSON/YAML key, DB column, or CLI flag is written.

## The four-step check (mechanical — run it, do not skip to coining)

1. **Is the term in `PREDICATES.json` baptisms, or in the family
   registry?** → **import** under the canonical signifier. Use it
   **verbatim**.
2. **Is the *referent* already bound under a different signifier?** →
   **import that signifier**; do not coin a synonym. The probe is
   cite-is-the-referent: cite what the name would denote; if the citation
   resolves to an existing entry, that entry's signifier wins.
3. **Does the family owner already bind this signifier or referent?** →
   **import, never re-derive or re-coin.** Identity-grid and schema terms
   live in `.eukoine/corpus_identity_and_schema.md` when that file is
   present — cite it; do not copy it.
4. **None of the above** → **coin**, **record the baptism in the same
   pass** (`PREDICATES.json` baptisms, and the member-local lexicon if the
   repo has one), and surface any disagreement. A coined name with no
   same-pass registry entry is a finding, not a convenience.

The failure this skill forbids is **proceeding without checking**.

## Reject list

- A **head that is a bare mechanism verb** (walk / scan / run / loop /
  emit / resolve) or a **generic plural** (handlers, runners, processors,
  managers) with no baptised subject.
- A name that **changes its head as it crosses a module / layer /
  boundary**.
- A **synonym** coined for a referent the registry already binds; a
  signifier that **drifts** across a chain of reasoning.
- A **banned token** still standing beside the word that replaced it
  (`PREDICATES.json` `banned`, and `on_correction_delete`).
- A family term **re-derived or re-coined locally** instead of imported.

## When NOT to run it

Prose in docstrings, comments, work reports, and doctrine. A user-facing
label is authored, not baptised. Name a *kind of thing in the system* →
run this. Write a sentence a human reads → do not.

## References

- [`references/lexicon_check.md`](references/lexicon_check.md) — the
  baptism block as a fill-in for plans and reviews.
