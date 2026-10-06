# Verification sheet

One row per claim. Carried into the work report at `/close`.

| Claim | Command | Observed (quoted) | Verdict |
|---|---|---|---|
| the bug no longer reproduces | `./bin/app --case x` | `"error: case x: not found"` → `""` | pass |
| new skill discovered by all tools | `go run ./tools/agentctl verify` | `verify: 34 passed, 0 failed` | pass |

Rules:

- **Observed** is a quote of the actual output lines — never a paraphrase.
- An empty observation must prove the instrument ran (exit status, line
  count, a known-present control case).
- A claim that maps to no command does not go on the sheet; it goes back to
  the plan.
- Verdict vocabulary: `pass`, `fail`, `not-run (say why)`. There is no
  "mostly".
