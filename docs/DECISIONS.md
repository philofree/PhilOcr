# DECISIONS — the chronicle

| | |
|---|---|
| **Title** | docs/DECISIONS.md — owner rulings, append-only |
| **Status** | Chronicle (never edited, only appended) |
| **Authority level** | 4 — explains the rules above it; carries none of its own |
| **Scope** | Every ruling that settled a question |
| **Relationship-to** | Rulings land here; their one-line outcome lands in CLAUDE.md § Settled stances |
| **Document class** | chronicle |
| **Contract** | `epitomikon/document-contract/v1` |

Append-only. Entries are never edited or reordered — a superseded ruling is
superseded by a new entry, not by rewriting history.

## Format

```markdown
## YYYY-MM-DD — <one-line topic>

**Question.** <what was open>

**Ruling.** <what was decided>

**Because.** <the reason, in one or two lines>

**Touches.** <files or rules this ruling settled>
```

---

## 2026-10-06 — the house, adapted for a Python product

**Question.** Can PhilOcr take the universal-template agent house without
becoming a Go application?

**Ruling.** Yes. The house is overlaid onto this tree. Python remains the
product spine. Go is present only as `tools/agentctl` and the Eustratikon
tool pin in `go.mod`. `agentctl init` was not used: it refuses a non-empty
directory and would plant a `cmd/` program. The Go static-quality campaign
form is not copied and is not enqueued. This repository is not enrolled in
EuKoine; the hub is cited by sibling path and there is no local
`.eukoine/` mirror.

The per-turn hook that pasted rot doctrine into every prompt
(`.claude/hooks/code_rot_check.sh`) is retired. `posture_check.sh` points
at the owners. Citations of `rules_*.yaml` and of
`docs/plans/philocr_pipeline_architecture_v1_4.md` are retired: neither
exists. Guardians remain the structural gate. `design/` is tracked so
CLAUDE can cite it. `guardians/` and `work_reports/` stay gitignored.

`core.hooksPath` is `.githooks`, so the parsimony `commit-msg` binds every
agent. `.githooks/pre-commit` calls the generated hook that `pre-commit
install` left in `.git/hooks/pre-commit` — that installer refuses to write
into `.githooks` while `core.hooksPath` is set. The push identity check
lives in `.githooks/pre-push`.

**Because.** The previous `CLAUDE.md` was telos, architecture, logging
cookbook, guardian catalogue, and session-report law in one file, and two
of its citations were already dead. The seed separates those jobs. The
seed's language law ("Go is the production spine") does not describe this
application.

**Falsifiers that would have voided the ruling.** `make verify` red on a
missing farm, a thin CLAUDE, or a dormant hooks path. `core.hooksPath`
causing pre-commit to stop running. A telos paragraph that described a Go
port or a corpus repository.

**Touches.** `CLAUDE.md`, `docs/PURPOSE.md`, `docs/GOVERNANCE.md` § The
language law, `docs/ROT.md`, `docs/DOCUMENT_CONTRACT.md`,
`design/CANONICAL_DESIGN_PRINCIPLES.md`, `.claude/hooks/`,
`campaigns/graph.yaml`, `tools/agentctl`, `go.mod`, `.githooks/`,
`.gitignore`. PhilOcr-private was not updated. The Python structural read is
`agentctl eukrinikon`, which runs the sibling `../eukrinikon_python`. It
is not a substitute for the guardians.

## 2026-10-06 — product refactoring is a capability-port cutover

**Question.** May a refactor of the Python application keep the old path,
stop at `instrument`, or offer a choice of shapes?

**Ruling.** No. A change that moves, splits, or replaces a product
behaviour is finished only as a capability port: one driver under `src/`,
one typed Python port (`module.Class`) declared in that driver, adapters
that return the type or raise, and every previous route deleted in the
same change. The row lives in `capability_ports.json` under `product` and
its disposition is `issued`. `instrument`, `remainder`, and `retired-stub`
are refused on that list. They remain lawful only for house CLI commands.
An empty `product` list means nothing has been cut over yet. It is not
permission to refactor without issuing a row. Agents do not present a
phased migration or a menu of owners.

**Because.** The seed's roster treats `instrument` as an honest gap for a
young CLI. Used on the OCR pipeline, that gap is a second path left alive.
The form is the cutover. Negotiation is how the second path survives.

**Touches.** `.claude/skills/cut/references/capability_port.md` § PhilOcr
product binding, `capability_ports.json` `product`,
`tools/agentctl/portcmd/port.go`, `CLAUDE.md` § Settled stances.

