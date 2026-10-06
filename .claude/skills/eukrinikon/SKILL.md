---
name: eukrinikon
description: >
  Run EuKrinikon on PhilOcr's Python tissue — rot and liquefaction findings
  as located evidence. Use before structural refactors, after guardian churn,
  when ownership is split across modules, or when /cold-reading needs a
  frozen structural snapshot. Not a merge gate; not a substitute for guardians
  or pytest.
---

# `/eukrinikon` — structural read of Python tissue

**EuKrinikon** (family spelling — not "EuKryptikon") is the suite instrument
for structural confusion: rot, liquefaction, grain, and related axes. Go
repos use the Go binary; **PhilOcr uses the Python port** beside this repo.

| Piece | Where |
|---|---|
| Axes, vocabulary, reading contract | `../eukrinikon/README.md` (sibling of PhilOcr) |
| Python instrument (ast probers) | `../eukrinikon_python` (sibling checkout) |
| PhilOcr dispatcher | `go run ./tools/agentctl eukrinikon` or `make eukrinikon` |
| Stored readings (optional) | `../eukrinikon_python/readings/` |

## Procedure

1. **Run from PhilOcr root** (sibling `../eukrinikon_python` must exist, or set
   `EUKRINIKON_PYTHON_HOME`):

   ```sh
   make eukrinikon
   # or
   go run ./tools/agentctl eukrinikon --json
   ```

2. **Slice before you widen** — use `--zone path,fragments` when debugging one
   concern (same flag on `agentctl eukrinikon`).

3. **Treat output as evidence** — each finding names file, line, probe, and
   limitation. Fix at the owning stage or module; do not paper over with
   comments or compensating guards (`design/anti_patterns.jsonl`).

4. **Pair with other gates** — guardians enforce invariants on commit;
   EuKrinikon finds structural smell early. `pytest` proves product behaviour.
   None replaces the others.

## Environment

- `EUKRINIKON_PYTHON_HOME` — path to the `eukrinikon_python` checkout.
- `EUKRINIKON_PYTHON_BIN` — Python executable (default: `venv/bin/python`).

## Reject list

- Using a finding as "blocked" without reading the cited lines.
- Skipping EuKrinikon on cross-cutting worker/UI/temp refactors.
- Minting a second structural linter inside PhilOcr instead of extending probes
  in the sibling instrument.

Owner route: [`CLAUDE.md`](../../../CLAUDE.md) § Where to look.
