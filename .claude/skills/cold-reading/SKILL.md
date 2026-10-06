---
name: cold-reading
description: >
  Fresh-eyes assessment of the repository before changing it — evidence
  gathered from the surfaces themselves, not from memory or assumptions.
  Use when ownership of any area is unproven, at the start of structural
  work, when inheriting unfamiliar code, or when the agent's confidence
  exceeds its evidence.
---

# `/cold-reading` — read the surfaces before you trust them

## Procedure

1. **Probe the surfaces**
   ([`references/surface_probes.md`](references/surface_probes.md)) — run
   each probe, record the actual output. The probes are fixed so results
   are comparable across sessions. For structural code work, freeze an
   `make eukrinikon` before semantic reading when `../eukrinikon_python` is
   present; treat findings as located evidence, never as a verdict or gate
   (see `.claude/skills/eukrinikon/`).
2. **Name what the evidence supports** — and separately, what it does not.
   Confidence beyond evidence is the failure mode this skill exists for.
3. **Fill the assessment**
   ([`references/assessment_template.md`](references/assessment_template.md)):
   what this repo is, where the load-bearing code is, what is rotting,
   what is asserted but unproven.
4. **Decide the entry** — with the assessment on the table: is the
   proposed work a local change, structural, or a campaign? Route through
   `/open` if a session is starting.

## What `/cold-reading` is not

- Not a summary of the README — the README is a claim; the probes are the
  evidence.
- Not once-per-repo-forever — surfaces drift; assessments older than the
  last structural change are stale.

## Reject list

- Asserting ownership ("this module does X") without a probe quote.
- Reading the docs and skipping the code, or the reverse.
- An assessment with no "unproven" section — there is always one.

## References

- [`references/surface_probes.md`](references/surface_probes.md) — the
  fixed probe set.
- [`references/assessment_template.md`](references/assessment_template.md)
  — the assessment layout.
