# ROT — the rot register

| | |
|---|---|
| **Title** | docs/ROT.md — rot doctrine and evidence classes |
| **Status** | Canonical |
| **Authority level** | 3 |
| **Scope** | Universal — every repository, every language, every domain |
| **Relationship-to** | Feeds `/cut` and `/cold-reading`; cited by the posture hook |
| **Document class** | authority |
| **Contract** | `epitomikon/document-contract/v1` |

## Core definition

**Rot is displaced responsibility for an invariant.**

Every codebase has invariants — rules that must always hold — and for each
one there is a correct owner: the single place where that rule should live
and be enforced. Rot is the measurable distance between where an invariant
is *owned* (ideally **precluded** at one boundary) and where it is actually
*observed or compensated for* elsewhere.

When that distance is zero, the structure is clean. When responsibility
has drifted away from its owner — into a wrapper, a cache, a guard, a UI
layer, a second copy of the same rule — the structure has rotted.

## Rot and rotting — one phenomenon, two tenses

- **Rotting** is the *process*: responsibility dissolving through
  accumulated local fixes.
- **Rot** is the *state*: responsibility already dispersed.
- **Liquefaction** is the same failure by *volume* rather than by place.

## Liquefaction

Rot displaces responsibility; liquefaction dissolves the ground it stood
on. Each session adds without retiring — a restatement here, a guard
there, a second file saying what one already said. No single addition is
wrong. Past a threshold the surface stops being a structure and becomes a
medium: nothing bears load, every claim has five homes, and a reader who
greps finds a copy and takes it for the owner.

**The measure is not size. It is the ratio of additions to retirements.**
A tree that grows while retiring nothing is liquefying, however good each
commit looked. **A reductive change that adds more than it removes has
liquefied the ground it was sent to firm.**

This is the measured default of the agents working here, not a worry
about style — which is why it is measured and never trusted:

- Models edit the correct file in >92% of cases but remove the target
  lines in only **44.6–51.6%** (arXiv 2607.28887).
- **29.0% of *passing* patches** wrap the code the human deleted in a new
  conditional instead of removing it. Tests stay green — class A7.
- Where the correct patch is **no patch**, agents change code anyway in
  **35–65%** of cases (arXiv 2605.07769).
- Asking for deletion moves the outcome by **−2.5 to +2.5 points**.
  Naming the **exact line spans** moves it by **+6.5 to +31.5**.

That last measurement is the whole design of the contract below: telling
an agent to be parsimonious is worth approximately nothing; requiring it
to name what it retires is worth a great deal.

## The parsimony contract

Every commit declares what it retires. Enforced by
[`../.githooks/commit-msg`](../.githooks/commit-msg) at the **git layer**,
so every agent that commits is bound — Claude, Kimi, Codex, ZCode, Cursor
— with no per-tool registration to drift. Commit trailers:

```
Parsimony: cut
Retires: internal/oldpath/driver.go
```

| Trailer | Held to |
|---|---|
| `Parsimony: cut` | net code delta ≤ 0, **and** every `Retires:` path actually deleted or shrunk by the diff |
| `Parsimony: add` | net-new capability; **must** name `Retires:` what the new code made redundant, and those paths must actually shrink. A declaration with no hunt is accumulation wearing a trailer |
| `Parsimony: fix` | a repair of an existing owner; **no new files** |

Any net accumulation must declare itself — not a 50-line threshold.
Twelve lines of a second path is still a second path. Prose is measured
and never refused — this gate is about implementation growing. Merges
and reverts are exempt. `--no-verify` still works and leaves a trace
rather than silence. An unknown `Parsimony:` intent is not a
declaration. Trailers are the last paragraph of the message; a sentence
about `Retires:` in the body is not a path list.

**Arming is not automatic.** `core.hooksPath` is local git config and is
never committed, so a fresh clone carries the gate inert — protection that
reads as present and is not. `agentctl init` arms a seeded repo;
`agentctl verify` and `go test ./...` **fail** while it is dormant.

```sh
git config core.hooksPath .githooks   # arm it in a fresh clone
sh .githooks/selftest                 # 16 cases; prove it still refuses
```

## The mechanism of rotting

Rotting proceeds by **local compensation** — locally reasonable edits that
add parallel paths, second sources of truth, and compensating guards
without returning invariants to their owners.

## The fastest accelerant: completion drive

Agent completion drive patches locally without perceiving prior patches.
Review-at-the-diff cannot catch rotting; governance by construction at
boundaries is the durable defence.

## The opposite of rot: coherent structure

**Clean, clear, deterministic** — one owner per invariant, causality
legible from structure, same state same result. The cure is *collapsing
distance* back to the owner.

## Bugs as evidence of deep rot

Every bug is almost invariably evidence of deep rot. Trace the owner chain
before patching locally. **Fix at the owner, not at the symptom.**

## Evidence classes

Each class is *evidence of displacement*, not a separate definition:

| Id | Class | Signature | Detection |
|---|---|---|---|
| A1 | Dead code left behind | Unreferenced code kept "just in case" | `grep` the identifier — zero hits outside its own definition |
| A2 | False identity | The name says what the thing no longer does | Read the name; read the body; wince = finding |
| A3 | Duplicated authority | Two files carry one rule; they will diverge | `go run ./tools/agentctl verify` (surface copies); review (doc copies) |
| A4 | Projection drift | A copied projection of a canonical file went stale | `agentctl verify` FAIL: real copy, not a symlink |
| A5 | Retired procedure advertised | Docs/hooks still teach the old way | the retired-phrase guard in `posture_check.sh` |
| A6 | Queue-in-chat | Work scheduled in conversation, not in the authored planning graph | Any "next let's…" with no `campaigns/graph.yaml` node |
| A7 | Retirement claimed, not performed | The commit says it removed the old path; the old path still compiles. Deleted logic kept behind a new conditional, "for safety" | `.githooks/commit-msg` rule 2 — a `Retires:` path the diff does not delete or shrink is refused |
| A8 | Unnamed capability | A command the CLI dispatches that no roster row owns. Nobody can say what guarantees it, or who owns the invariant | `go run ./tools/agentctl verify`; `go test ./tools/agentctl/portcmd` |
| A9 | Synonym beside the correction | The wrong word was replaced and left standing; both now circulate, and a reader picks whichever they met first | `go test ./tools/agentctl/predicatecmd` — two baptisms sharing a referent, or a retired signifier still in the tree |

## The guard qualifier

Static instruments (guardians, verify scripts) that **flag** without
touching production are observation, not rot. Runtime compensating
branches that make violations survivable are rot.

## The repair principle

**Consolidation** — collapse displaced responsibility to a single owner;
delete parallel paths.

## The practical rule

> **Who owns this invariant, and am I about to hold or compensate for it
> somewhere else?**

## Outside the edit zone

Rot elsewhere in the live graph is still rot. **Value elimination** — rot
you can see and safely remove is good work, not scope creep.

The disposition ladder:

- **In the edit zone** — remove (required).
- **Outside the edit zone, visible, and safely removable** — remove and
  record in the work report.
- **Outside the edit zone, visible, but removal needs design judgment** —
  flag in the work report.
- **Serious defects** (verify failure, silent failure, data-integrity
  violations) — surface immediately; never close by logging alone.

## Short definition

> **Rot** — displaced responsibility for an invariant. **Rotting** — that
> distance growing through local compensation. **Liquefaction** — the
> ground itself dissolving as additions accumulate without retirements,
> until nothing bears load and every claim has five homes. **Grain Collapse**
> and **Grain Preservation** — cite `../eukoine/.eukoine/predicate_lexicon.yaml`
> (`grain_collapse`, `grain_preservation`; baptised as a pair); do not restate.
> **Every bug is
> almost invariably evidence of deep rot** — trace the owner chain first.
> The cure is consolidation; the opposite is clean-clear-deterministic
> structure.

## Adding a class

A new class earns an entry when it has been observed **twice**. One
occurrence is an incident; two is a pattern; the register holds patterns.
Each entry needs: signature (how it looks when you're inside it) and
detection (a command or a check that names it).
