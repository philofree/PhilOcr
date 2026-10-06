---
name: reckless-cut
description: >
  Rebuild a maximally-entangled ENGINE surface by EXCISION, not incremental
  slicing: delete the knot wholesale — wrappers, relays, adapters, duplicate
  entry paths, compensating guards — run the narrowest truthful check, and
  use runtime breakage as the discovery instrument for what was actually
  load-bearing, then rebuild ONE port-shaped path. Use only when /cut's
  conservative slicing would polish the knot because every slice must
  thread through it ("you cannot knit your way out of knitting") —
  "reckless cut", "excise this knot", "the knot is too tangled to slice",
  repeated Cut Plan failure on the same invariant. Model-invocable at that
  signature only. Engine only. Sub-agents are ordinary — plan and seal
  dispatch /adversarial; do not wait for permission.
---

# `/reckless-cut` — excise the knot, let breakage teach you what mattered

Some engine code is so knitted that the only honest fix is to cut it up
and burn it. **You cannot knit your way out of knitting** — incremental
slicing on a maximally-entangled surface threads the new owner *through*
the tangle, preserves the surrounding relays "just in case," and
polishes the knot without ever reaching the clean shape.

Reckless Cut is the salvage-impossible execution branch of `/cut`.
**First job: excise the knot completely. Second job: deal with the
consequences — using runtime breakage as the discovery instrument, not a
pre-cut inventory of the old topology.** A layer survives only if
reality *proves* it mattered after removal.

Conservative `/cut` remains the default. This skill is the exception.

## Where it sits

| Mode | When | Skill |
|---|---|---|
| conservative | target path settled; slice one contiguous unit | [`/cut`](../cut/SKILL.md) |
| **salvage-impossible** | slicing would only polish the knot | **/reckless-cut** (this) |

Consumes [`/cold-reading`](../cold-reading/SKILL.md)'s hop count.
Plan and seal via [`/adversarial`](../adversarial/SKILL.md).
Sustained knots are a [`/campaign`](../campaign/SKILL.md).

## When to use it — confirm ≥4 of 6

1. Hop count from intent → terminal effect is obviously far above the
   port sketch.
2. Wrapper / adapter / relay / compensating-guard density is high.
3. ≥2 writable owners or parallel paths for one fact.
4. The current topology is visibly broader than the named port sketch.
5. Conservative inventory would mostly *preserve* indirection rather
   than expose the job.
6. Asking for incremental `/cut` would yield a slightly polished knot.

If **fewer than 4** hold, use `/cut` — see
[`references/worked_example.md`](references/worked_example.md).

**Do NOT use it** when:

- The surface is already near target shape — `/cut`.
- The disease is **fragmentation** (many **short** load-bearing chains,
  missing shared owner) — `/cut` to create/merge the owner.
- There is no runtime oracle you can actually run after the cut.

Reckless Cut on an already-clean surface is vandalism, not excision.

## When `/cut` keeps failing

Repeated **blocking** on question 2 (mechanism / topology) after one
fold is evidence the conservative path is polishing the knot — walk
the 4/6 preconditions above. Do not accumulate hunt passes until a
count licenses excision.

## Procedure

### A. Fill the brief

Copy [`references/reckless_cut_brief.md`](references/reckless_cut_brief.md)
and fill **all nine fields**. Load-bearing before excision: one-sentence
job · named port sketch · why salvage fails (≥4/6) · non-empty cut
ledger · singular surviving path · runnable runtime oracle.

### B. Plan-gate adversarial (before excision)

Run [`/adversarial`](../adversarial/SKILL.md) **plan** gate on the brief.
Dispatch an independent read-only sub-agent. Do not proceed to C until
the pass has been **run** and nothing blocking remains. A bare "looks
fine" is a non-run. Residual findings stay named; they do not keep the
gate open.

### C. Excise and discover

5. **Cut the knot** — delete ledger paths wholesale; whole modules/files
   preferred over local patches.
6. Run the named runtime oracle (never the suite as proxy).
7. Record what still works and what breaks.

### D. Rebuild and seal

8. Breakage is the discovery instrument. Rebuild through the named
   ports at the **owner** — never at the stack-trace site.
9. Complete [`references/reckless_seal_checklist.md`](references/reckless_seal_checklist.md);
   run `/adversarial` **sign-off**.

The form of the surviving path is
[`.claude/skills/cut/references/capability_port.md`](../cut/references/capability_port.md):
one driver, a typed port, adapters that cannot hold or break the
guarantee. Name the capability in `capability_ports.json` in the same
change.

## Guardrails

- **Cut topology, not obligations.** Restore at the owner. A dropped
  obligation with no restore path is a finding.
- **End with ONE path.** Leaving the old tangle beside a new owner is
  not a reckless cut.
- **Witnessed.** A campaign when `/campaign`'s membership test fires.
  A one-hit knot is still briefed, gated, and recorded in
  `work_reports/`.

## Reject list

- Reckless-cutting a near-target surface (use `/cut`).
- Fewer than 4 of 6 branch preconditions confirmed.
- Deleting an obligation instead of topology, or restoring at the
  stack-trace site.
- Leaving the old tangle beside the new owner.
- Author serving as their own adversary.
- Closing without seal checklist + `/adversarial` sign-off run.

## References

- [`references/reckless_cut_brief.md`](references/reckless_cut_brief.md)
- [`references/reckless_seal_checklist.md`](references/reckless_seal_checklist.md)
- [`references/worked_example.md`](references/worked_example.md)
- [`../cut/SKILL.md`](../cut/SKILL.md)
- [`../adversarial/SKILL.md`](../adversarial/SKILL.md)
