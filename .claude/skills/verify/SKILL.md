---
name: verify
description: >
  The verification gate. Use before claiming any work is done, fixed, or
  passing — and before any commit that claims a behaviour change. Requires
  running the real commands and quoting their actual output; evidence
  before assertions, always.
---

# `/verify` — evidence before assertions

"Should pass" is not passing. Nothing is claimed done until the command ran
and its output was read.

## Procedure

1. **List the claims.** What exactly will be asserted as true when this
   work is "done"? One line each.
2. **Map each claim to a command** — build, test, vet, a targeted run, a
   grep. A claim with no command is an opinion.
3. **Run them. Read the output. Quote it** — the work report carries the
   actual output lines, not a summary of them.
4. **Empty results are findings, not proof.** An empty test run, zero
   matches, a tool that did not fire — each of those must be shown to be
   the instrument working, not the instrument silent.
5. **Record** on the
   [`references/verification_sheet.md`](references/verification_sheet.md):
   claim → command → observed output → verdict.

## Agent-surface work

For changes to skills, hooks, or registrations, the gate is:

```sh
go run ./tools/agentctl verify
```

Green verify is the only acceptable evidence for surface claims.

For **structural** Python changes (workers, UI wiring, cross-module cleanup),
also run `make eukrinikon` when the sibling instrument is installed and quote
the finding count or the probes you acted on — see `.claude/skills/eukrinikon/`.

## Reject list

- "Tests pass" with no output quoted.
- Verifying a weaker claim than the one being made (ran unit tests; claimed
  the bug is fixed).
- Treating an error-free log as success when the command never executed the
  changed path.
- Skipping the sheet because "it's a small change" — small changes verify
  faster, not never.

## References

- [`references/verification_sheet.md`](references/verification_sheet.md) —
  the claim → command → output → verdict sheet.
