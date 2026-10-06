---
name: plan
description: >
  Plan-time forcing function for structural work. Use before writing code on
  any multi-module change, schema change, or campaign task. Forces the plan
  to state the problem, the mechanism, the falsifiers, and what gets cut —
  a plan that cannot name its falsifiers is not a plan.
---

# `/plan` — the plan that survives contact

## Procedure

Write the plan with the sections armed by `/open`
([`references/plan_sections.md`](references/plan_sections.md) defines them).
The non-negotiables:

1. **Problem** — one paragraph, in the user's terms. If it cannot be said
   plainly, it is not understood.
2. **Mechanism** — how the change works, named modules and boundaries.
   No unnamed steps.
3. **Falsifiers** — what observation would prove this plan wrong, and where
   to look for it. A plan with no falsifiers is a wish.
4. **Cut list** — what this change removes or retires. Default direction is
   subtractive; a plan that only adds must say why nothing can be cut.
5. **Verification plan** — which commands, in what order, gate the work.
   Named commands, not "run the tests".

## What `/plan` is not

- Not a todo list — sequence lives in the campaign graph, not the plan.
- Not an implementation transcript — it states intent and tests, not steps
  of typing.

## Reject list

- A mechanism step that names no module ("handle the edge cases", "clean
  up as needed").
- Zero falsifiers.
- A cut list omitted because "this is purely additive".
- A verification plan that names no command.
- Two mechanism branches presented as equally open — that is
  [`/adjudicate`](../adjudicate/SKILL.md) unfinished.

## References

- [`references/plan_sections.md`](references/plan_sections.md) — the
  section definitions and arming rules.
