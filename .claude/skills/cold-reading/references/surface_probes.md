# Surface probes

| | |
|---|---|
| **Title** | `references/surface_probes.md` — the surface probes of one cold read |
| **Status** | Binding while a cold read is running |
| **Authority level** | 3 — a reference of [`../SKILL.md`](../SKILL.md), which owns the procedure |
| **Scope** | One cold reading of one concern |
| **Relationship-to** | Serves [`../SKILL.md`](../SKILL.md); restates none of it |
| **Document class** | procedure |
| **Contract** | `epitomikon/document-contract/v1` |

Fixed commands, run from the repo root. Record actual output; never
paraphrase. If a probe fails, that is data — record the failure.

| # | Surface | Probe |
|---|---|---|
| 1 | Identity | `head -30 CLAUDE.md` — what does the authority claim? |
| 2 | Telos | `head -40 docs/PURPOSE.md` |
| 3 | Build | `make build 2>&1 \| tail -5` |
| 4 | Tests | `make test 2>&1 \| tail -10` |
| 5 | Vet/lint | `make lint 2>&1 \| tail -10` |
| 6 | Tree | `git status --porcelain \| head -20` and `git log --oneline -5` |
| 7 | Shape | `find . -name '*.go' -not -path './.git/*' \| head -30` |
| 8 | Agent surfaces | `go run ./tools/agentctl verify` |
| 9 | Campaign frontier | `go tool eustratikon campaign-frontier .` |
| 10 | Rot | `head -60 docs/ROT.md` — known failure modes claimed |
| 11 | Python structure | `make eukrinikon 2>&1 \| tail -20` — EuKrinikon findings tail (skip if sibling missing) |

Probes answer "what is on the disc" — never "what should be true". Two
sessions' probe outputs are comparable because the probe set is fixed; add
project-specific probes at the end of the table, never reorder the first
ten.
