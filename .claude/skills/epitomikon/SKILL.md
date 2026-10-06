---
name: epitomikon
description: >
  Apply the stoic cut to a repository's WHOLE documentary surface: if
  removing it would change no reader's answer, it ought to be removed.
  Cold-read the operational or product documentation, use the read-only
  Epitomikon CLI to nominate candidates, and produce evidence-backed
  assessments and a non-mutating cut brief with a retirement ledger. Use
  when documentation must get smaller without losing what a reader needs,
  and for restatement, stale chronicles of systems that no longer exist,
  stale/current mixing, authority confusion, or citation hops. This is the
  campaign-grain documentary instrument. /cut is one change, one agent's
  work — not the hopper for this reading. The brief is a proposal: the
  owner authorizes, never automatic cleanup.
---

# Epitomikon — cold reading before documentary cuts

The CLI records deterministic `Observation` and `Evidence` artifacts. You are
the reader: the verbal explanation is yours, the observations are the CLI's. Never call an observation rot, liquefaction, or a reason
to delete until the cold reading warrants an `Assessment`.

## Where it sits

| Scope | Owner |
|---|---|
| One concern's ownership topology | the target's `/cold-reading`, where it has one |
| One change's collapse onto an owner | the target's `/cut`, with its subtractive ledger |
| **The whole documentary surface at once** | **this skill** |
| The queue those catastrophes enter | the target's campaign queue |

This skill replaces neither `/cold-reading` nor `/cut`. It is not a
hopper for `/cut`. What it names at whole-surface grain is campaign
work. Where a target has no such skills this one still reads; it
never thereby gains the right to edit.

## Choose the reading

- **Operational mode**: agent instructions, skills, governance, orientation,
  live state, evidence, and chronicles.
- **Product mode**: user-facing documentation under roots the caller names.
  Never infer a whole repository as one publication or audience.
- **Both**: run two independent readings. Never merge their counts or
  conclusions.

If product roots or the reader's concrete task cannot be established from the
request and repository, ask the owner. Do not manufacture them.

## Freeze, then read blind

1. Run `epitomikon profile --json` for the chosen mode and redirect the output
   to a temporary file outside the target. An adopted repository uses its root
   `.epitomikon.json` or an owner-supplied `--contract`; otherwise record the
   legacy measurement. Do **not** inspect the profile yet.

   Resolve the executable in this order: `epitomikon` on `PATH`; then
   `<sibling>/epitomikon/bin/epitomikon` beside the target; then build it once
   with `make -C <sibling>/epitomikon build`. If none of those produce a
   working binary, that is a refusal — say so and stop. Never recreate the
   analyzer ad hoc, and never hand-count what the CLI is there to measure.
2. Cold-read the repository from its own plausible entry surfaces. Record the
   exact question, documents and spans opened, answer, authority cited, hop
   count, and anything still unproven.
3. Operational readings normally test: what work happens next; where one
   governing rule actually lives; which status is current; and what proves a
   task fit rather than merely green. Product readings test the concrete user
   task and audience established above.
4. Only after the trace is complete, read the frozen profile. For every useful
   observation, test the healthy twin: necessary local context, quotation,
   accessibility warning, generated projection, translation, versioned
   guidance, or legitimate chronicle.

Ordinary appraisal uses one reader. A calibration round or disputed
high-impact proposal uses three independent readers, each blind to the profile
and to the other readers. Two-of-three agreement is a calibration fact, not a
truth substitute; preserve the disagreement.

## The stoic cut, at repository scope

The law is family `inverted_burden`. Owner:
[`../eukoine/docs/doctrine/stoic_cut_elimination.md`](../../../../eukoine/docs/doctrine/stoic_cut_elimination.md)
§ Standing state. Cite it; do not restate it. Presence, not removal, carries
the burden. The scope is the repository, not the session: `/cut` reaches one
change; this skill runs the same cut over the whole declared documentary
surface. A reading that covers only what the current session touched has
not run it.

Volume is not the defect, and `docs/PURPOSE.md` does not move. A long
document every line of which a reader needs is sound; three stale lines are
not.

### The kill list

The profile is larger than this. Contract coverage, section roles, the
four lenses, and the reference graph are the reading. `kill_list` is one
derived view of the unreachable and restatement observations. Every entry
on it is on trial and guilty until a positive argument for continued
existence is made. An unanswered entry is an incomplete reading, not a
backlog item and not "profile noise."

Dispose every entry. Choose exactly one of:

| Charge | Acquittal | Default |
|---|---|---|
| `navigation/unreachable-from-entrypoints` | Connect it from a real owner, and only because a reader will actually ask for it by that route | Eliminate it |
| `restatement/exact-passage` or `restatement/near-passage` | The extra copy is a healthy twin (quotation, warning, translation, generated projection, necessary local context), or load-bearing residue is extracted into the owner first | The extra copy goes. The whole document goes only if nothing extractable remains |

A link added only to take a document off the list is forbidden. Unreachability
is a reason to delete, not a reason to cite. Git is the archive. A synced
family mirror or a generated projection the target's own contract already
names is a named argument; it is not a licence to sprinkle citations, and it
is not a licence to delete the hub's bytes from a member.

`graph` still answers what would notice if this went and what this would take
with it. Read it while disposing the list. Entry points are the corpus's own
surfaces plus the agent-discovered ones (`SKILL.md`, editor rules). A route
this probe does not model — a generated index, a tool, a harness — can be the
positive argument. It must be named. "A human who knows" is not an argument.

The probe remains experimental until a blind round grades it. Experiment
does not suspend the burden.

## Grain Collapse priority (operational mode)

Before **Author assessments**, every operational observation must pass
this falsifier: does removal, merge, coarsening, or generic typing
destroy a `preservation_kind` or sense-grain identity the reader must
distinguish? Cite **`grain_collapse`** and **`grain_preservation`** in the target's
`.eukoine/predicate_lexicon.yaml`; do not restate the lexicon entries.

| Scope | Owner |
|---|---|
| Single-repo whole-surface read | **this skill** |
| Fleet inventory + extra-class surfaces | target's `/gov-sweep` when present |
| One-concern topology | target's `/doc-cold-reading` |

## Author assessments

An assessment must contain:

- a stable assessment ID and the cited observation IDs;
- reader/model provenance and the concrete question tested;
- exact supporting spans;
- verdict and uncertainty;
- what the evidence supports and what remains unproven.

Use `liquefaction` only when several located observations show creation beside
an existing responsibility without integration. Use `identity_break` only
when one referent demonstrably has competing names or one signifier competing
referents. Use **Grain Collapse** (`grain_collapse`, cite the target's
`.eukoine/predicate_lexicon.yaml`; do not restate) when governing prose or
instrument design merges unlike particulars into generic buckets, teaches
coarsening as convenience, or restates sense-grain law at a grain that
destroys what a reader must distinguish. **Grain Preservation**
(`grain_preservation`, same lexicon path; do not restate) is the positive
dual — cite both when stating mission telos. Git churn and document volume are
evidence only.

## Produce the cut brief

For each warranted assessment, choose exactly one proposal:

| Disposition | Meaning |
|---|---|
| `integrate` | move the load-bearing matter into its one owner and retire the former carrier |
| `retire` | remove matter whose removal would change no reader's answer — the stoic cut. Provenance alone is not reader load |
| `rewrite` | replace misleading current-facing matter with the present truth |
| `preserve-as-chronicle` | retain history that still answers a question a reader will ask, while removing its claim to current authority. A chronicle no one will interrogate is `retire` |
| `refuse` | evidence is insufficient or the proposed cut risks reader correctness |

Name the authority destination, affected spans, counterfactual reader task,
expected post-cut route, and a falsifier. A shorter route is not success if
answer correctness, authority recovery, accessibility, or necessary context
declines.

Warranted observations from every lens belong in the brief. Every
`kill_list` entry is one of those and must not be left unanswered.

Every disposition carries a retirement ledger: matter moved, matter retired,
and the net line delta. A cut brief whose ledger is empty across every
disposition has proposed nothing. The ledger is a consequence of the
proposals and never nominates a document; Git churn still cannot author an
observation (`internal/history/history.go`). The form is the subtractive
ledger a target's `/cut` already proves in its Step 3 — import that, do not
mint a second.

Return the assessment and cut brief in the conversation unless the user names
an external destination. Never write them into the target by default. Never
edit, delete, gate, docket, or require clearance of the target's documents.

When a repository has adopted the prospective contract, a new operational
Markdown document and any changed older operational document use its lawful
carrier. Untouched older documents remain legacy; their age alone is neither
a finding nor a disposition. Age is not the test, and neither is size. A
repository-wide reading is lawful and is this skill's proper scope; what it
may not do is make age or size the reason.
