# CLAUDE — PhilOcr

| | |
|---|---|
| **Title** | CLAUDE.md — the authority for agent work in PhilOcr |
| **Status** | Binding |
| **Authority level** | 1 — the single authority for how agents work here |
| **Scope** | Every AI coding agent (Claude, Kimi, Codex, ZCode, Cursor, and any other) |
| **Relationship-to** | `docs/PURPOSE.md` sits above this file; everything else sits below it |
| **Document class** | authority |
| **Contract** | `epitomikon/document-contract/v1` |

This file is addressed to **every agent that works here**. AGENTS.md, KIMI.md
and GEMINI.md are thin pointers to this file — they exist because those tools
expect those filenames; they carry no rule of their own.

## What this project is

Take a scanned PDF of an ancient Greek text and produce clean, accurate,
Unicode polytonic Greek that can enter the Philofree open corpus.

The telos — why this repository exists and what "done" means — lives in
[`docs/PURPOSE.md`](docs/PURPOSE.md). Read it before proposing direction.

## Authority order

1. `docs/PURPOSE.md` — the telos (why)
2. `CLAUDE.md` — this file (how agents work)
3. `docs/GOVERNANCE.md` — document law, the language law, the vocabulary law
4. `docs/ROT.md` — the rot register (named failure modes)
5. `design/CANONICAL_DESIGN_PRINCIPLES.md` — the pipeline and its invariants
6. `docs/DECISIONS.md` — the chronicle of owner rulings
7. `campaigns/graph.yaml` — the sole authored planning graph

A conflict between documents is a **finding** — fix the wrong document, never
average between them, never quietly pick one.

## Where to look — cite owners, do not restate

| Need | Ask | Not this |
|---|---|---|
| Why does this repo exist? | `docs/PURPOSE.md` | Guessing from the code |
| What am I allowed to relitigate? | "Settled stances" below | Reopening a settled question |
| Is this failure mode known? | `docs/ROT.md` | Debugging from scratch |
| How does a page become Greek? | `design/CANONICAL_DESIGN_PRINCIPLES.md` §0 | Restating the four stages here |
| Which pattern is forbidden, and which guardian catches it? | `design/anti_patterns.jsonl` | A second anti-pattern list |
| What does this command guarantee, and who owns it? | `capability_ports.json` | Reading the CLI switch and guessing |
| Which word do I use for this thing? | `PREDICATES.json`, then the family registry it cites; `/baptise` before coining | Coining a synonym beside the one that exists |
| How do I build a new capability? | `.claude/skills/cut/references/capability_port.md` | A function reachable by three routes |
| A fork about to become a menu of options | [`.claude/skills/adjudicate/`](.claude/skills/adjudicate/SKILL.md) | Handing the owner a preference menu before the walk |
| The knot is too tangled to slice | `.claude/skills/reckless-cut/` | Incremental `/cut` that would only polish it |
| Which document actually owns this rule? | `.claude/skills/doc-cold-reading/` | Rewriting doctrine from a single read |
| Fleet governing-document sweep | [`.claude/skills/gov-sweep/`](.claude/skills/gov-sweep/SKILL.md) — cite `../eukoine/.eukoine/predicate_lexicon.yaml` (`grain_collapse`, `grain_preservation`); do not restate | restating the grain pair in every skill |
| Do the layers point at the same job? | [`.claude/skills/gov-sweep/references/layer_alignment.md`](.claude/skills/gov-sweep/references/layer_alignment.md) | Recutting README while PURPOSE still names a retired neighbour |
| Family identity / schema / shared lexicon | the hub `../eukoine/.eukoine/` (this repo is not enrolled and has no local mirror) | Hand-editing a mirror that is not here; restating the spec |
| Why was my commit refused? | `docs/ROT.md` § The parsimony contract | `--no-verify` |
| What work is next? | `go tool eustratikon campaign-frontier .` over `campaigns/graph.yaml` | Inventing a queue or persisted frontier in chat |
| What happened in past sessions? | `work_reports/`, `HANDOVER_*.md` | Chat memory |
| Why was X decided? | `docs/DECISIONS.md` | Re-deriving the reasoning |
| How is a doc written here? | `docs/GOVERNANCE.md` | Freeform prose |
| What language is new work in? | `docs/GOVERNANCE.md` § The language law | Restating Python / Go / Shell here |
| The whole kit, in plain words | `dummies_guide/how_this_template_works.md` | Re-deriving the loop from CLAUDE.md |
| How do the agent surfaces sync? | this file § The assistant fleet | Editing a symlink farm by hand |
| Rot / liquefaction in **Python** tissue? | [`go run ./tools/agentctl eukrinikon`](tools/agentctl/eukrinikoncmd/eukrinikon.go), [`make eukrinikon`](Makefile), [`.claude/skills/eukrinikon/`](.claude/skills/eukrinikon/SKILL.md); axes [`../eukrinikon/README.md`](../eukrinikon/README.md); instrument [`../eukrinikon_python`](../eukrinikon_python) | Hand-auditing ownership splits; confusing EuKrinikon with guardians or pytest |
| Go-repo structural read? | sibling `../eukrinikon` (Go instrument) | Pointing PhilOcr agents at the wrong language port |

## EuKrinikon — what every agent should know

**EuKrinikon** is the family's structural-reading instrument (correct spelling;
"EuKryptikon" is a common mishearing). It emits **located findings** on rot and
liquefaction — evidence with file, line, probe, and stated limitation — not a
single score and not a substitute for guardians or tests.

PhilOcr's product code is Python. Run the **Python port** from this repo:

```sh
make eukrinikon
go run ./tools/agentctl eukrinikon [--json] [--zone fragment,other]
```

Default layout: clone [`eukrinikon_python`](../eukrinikon_python) beside PhilOcr
(`../eukrinikon_python`). Doctrine and axis definitions live in
[`../eukrinikon`](../eukrinikon). Use [`.claude/skills/eukrinikon/`](.claude/skills/eukrinikon/SKILL.md)
before structural refactors and in `/cold-reading` when ownership is unclear.

## Language law

Owner: [`docs/GOVERNANCE.md`](docs/GOVERNANCE.md) § The language law.

## Settled stances — do NOT relitigate

- **CLAUDE.md is the authority.** AGENTS.md, KIMI.md and GEMINI.md are thin
  pointers. Do not invert this.
- The agent-surface architecture is settled: canonical store `.claude/`,
  symlink farms everywhere else (this file § The assistant fleet).
- SKILL.md frontmatter is `name` + `description` only — one file must pass
  every tool's parser.
- **Every commit declares what it retires.** Owner: `docs/ROT.md` § The
  parsimony contract. The gate is `.githooks/commit-msg`. Python pre-commit
  (Ruff, Black, isort, Pyright) still runs: `core.hooksPath` is `.githooks`,
  and `.githooks/pre-commit` calls the generated hook that remains in
  `.git/hooks/pre-commit` (pre-commit refuses to install while that path
  is set).
- **Python is the product.** New application code is Python. Go in this
  tree is `tools/agentctl` and the pinned Eustratikon tool. There is no
  `cmd/` program, and the Go static-quality campaign form is not enqueued.
- **Every capability is named.** A command `agentctl` dispatches with no row
  in `capability_ports.json` is rot and fails `agentctl verify`. The
  application entry `src/philocr/main.py` is not a dispatched CLI and has
  no row.
- **One signifier, one referent**, and on correction the wrong word is
  deleted, not shadowed by a synonym. Held by `PREDICATES.json`; coin-time
  check is `/baptise`.
- **This repository is not an EuKoine member.** Cite the hub by the sibling
  path `../eukoine/`. Do not add a hand-edited `.eukoine/` mirror. Enrolment
  is a separate ruling.
- **Same concern, same home.** Pipeline invariants live in
  `design/CANONICAL_DESIGN_PRINCIPLES.md`. Forbidden shapes live in
  `design/anti_patterns.jsonl`. Guardians enforce them. Those files are not
  restated here.
- **Campaign state has one authored home.** `campaigns/graph.yaml` starts
  empty. Eustratikon owns audit and the derived frontier. At most one
  campaign node may be `doing`. Finishing a campaign deletes the node.
- **A work report is not owed by every session.** `/close` reconciles the
  graph and the one live handover. Write `work_reports/` only when that
  record would lose evidence. The shape, when a report is written, is
  `work_reports/SPECIFICATION.md`.
- `guardians/` and `work_reports/` stay gitignored. Their canonical copy
  has been the PhilOcr-private tree. This working tree is where agents
  edit them. `design/` is tracked: CLAUDE cites it.

## Operating posture

- **Verify before claiming.** Run the command, read the output, quote it.
  "Should pass" is not passing. (`/verify`)
- **Eliminate before escalating.** A mechanism fork is walked against the
  four gates; only a residual reaches the owner. (`/adjudicate`)
- **Refute before trusting.** A claim proved only by its author is
  unproved. (`/adversarial`)
- **Default direction is subtractive**, and it is enforced. (`/cut`,
  `docs/ROT.md` § The parsimony contract)
- **Name the capability before you build it.** Driver, port, adapters —
  and a row in `capability_ports.json` when the capability is a command
  `agentctl` dispatches.
- **Sessions reconcile.** (`/close`, `/log`)
- **No invented live state.** An empty graph has no live handover and no
  `NOW.md`. Once a real frontier exists, keep exactly one
  `HANDOVER_YYYY-MM-DD_*.md` at root and regenerate `NOW.md` with
  `go run ./tools/agentctl now`.
- **A gap named beats an answer manufactured to close it.**
- **Fix a pipeline defect at the stage that owns it.** UI displays.
  Workers cross the thread boundary. Stages do not borrow each other's job.

## The assistant fleet — one canonical store

Edit canonical files only:

- Skills: `.claude/skills/<name>/` — the farms (`.zcode/`, `.agents/`,
  `.kimi/`, `.cursor/` `skills/`) are symlinks. A copy beside a symlink is
  drift and fails `agentctl verify`.
- Hooks: `.claude/hooks/` — every tool's registration points here.
  `posture_check.sh` points at owners. It does not carry rule text.
- Instructions: this file. The thin pointers are not a second authority.

After adding a skill: `go run ./tools/agentctl link`, then
`go run ./tools/agentctl verify` — both must be green before commit.

## Commands

```sh
python -m philocr                              # the application
python -m pytest tests/ -x -q                  # product tests
python guardians/run_all_guardians.py --root . # structural gate, when present
ruff check src/
python -m pyright src/

make build      # go build -o bin/agentctl ./tools/agentctl
make verify     # health-gate every agent surface
make link       # rebuild skill symlink farms
make now        # regenerate NOW.md from the live handover
make test       # go test ./tools/agentctl/... — the house, including the parsimony self-test
make pytest     # python -m pytest tests/ -q
make eukrinikon # structural read via ../eukrinikon_python (EuKrinikon)
make vet        # go vet ./...
make lint       # gofmt and staticcheck on tools/ only

sh .githooks/selftest                # prove the parsimony gate still refuses
git config --local core.hooksPath .githooks
# .githooks/pre-commit calls .git/hooks/pre-commit. If that file is
# missing: unset core.hooksPath, run `pre-commit install`, set it back.
```

`make verify` **fails while the parsimony gate is dormant**. That is
deliberate: a gate present but unarmed reads as protection and is not.
