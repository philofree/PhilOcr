---
name: open
description: >
  Session entry for agent work. Orients (live handover, campaign frontier, git
  status), classifies the work against the arming matrix, and arms the gates
  the session must pass (plan, verify, close). Use at session start and
  whenever the work type genuinely changes mid-session. Self-invoked — it
  does not wait for a slash command.
---

# `/open` — session entry: orient, classify, arm

A mission starts at entry, not at the first edit. `/open` does three things
once per session — orient, classify, arm — and emits one transient checklist in
the active task. Persistent forward state belongs only in the campaign graph or
live handover.

## Procedure

1. **Orient.**
   - The live `HANDOVER_YYYY-MM-DD_*.md`. None is lawful while the campaign
     graph and frontier are empty; otherwise there must be exactly one.
   - `go tool eustratikon campaign-frontier .` — current effective work.
   - `git status` — uncommitted prior work changes what "current" means.
2. **Classify.** Read the three signals (prompt, dirty files, campaign frontier)
   against [`references/arming_matrix.md`](references/arming_matrix.md) —
   the classification authority. Follow its decision order; do not improvise
   a work type to fit the gates you wanted.
3. **Arm.** From the matrix row: whether `/plan` arms, which sections; how
   `/verify` arms; the `/close` bar (FULL or LIGHT).
4. **Emit** `session_state` (schema in the matrix file) as the armed checklist:
   one line per gate, what arms it, why. Do not create a file merely to hold
   transient gate state.

After each gate completes, update the task's `session_state` and proceed. The
checklist is the transient schedule; the campaign graph remains the persistent schedule.

## What `/open` is not

- Not a gate itself — it fills no sheet and discharges no obligation.
- Not a chronicle — `session_state` is working state and disappears at close.
- Not per-turn — once per session, or on a genuine work-type change. The
  per-turn surface is the posture hook.

## Reject list

- Classifying by convenience — picking the row whose gates look cheapest.
- Skipping `/open` because the task "looks small" — small work arms fewer
  sections, never no classification.
- A persistent scratch file or TODO surface for gate state. The active task is
  the transient owner; the campaign graph and handover own what must survive it.
- Re-running `/open` to re-roll an unfavourable classification.

## References

- [`references/arming_matrix.md`](references/arming_matrix.md) — the
  classification authority and transient `session_state` schema.
