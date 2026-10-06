---
name: cut
description: >
  The subtractive gate. Use before writing on any non-trivial change, and
  whenever code sounds knitted together, when a feature is being added, or
  when the question "should this be here?" arises. Asks what the change
  removes before what it adds; dead code left behind is rot A1.
---

# `/cut` — before you add, name what you remove

The default direction here is subtractive. Most defects are additions that
outlived their justification; the cut is how the repo stays knowable.

## Procedure

1. **Name the addition's opposite.** For every capability this change adds,
   what becomes unnecessary? If the answer is "nothing, ever", write that
   down explicitly — it is a claim the plan must carry.
2. **Walk the cut list**
   ([`references/cut_checklist.md`](references/cut_checklist.md)) — dead
   code, false identities, duplicated authority, retired procedures still
   advertised.
3. **Cut with the verification bar.** A cut is verified like any change:
   build, tests, vet green — quoted, not summarized.
4. **When in doubt, cut and say so.** A wrong cut is recoverable from git;
   uncut accumulation is only recoverable by archaeology.

## Escalation — when slicing would only polish the knot

Conservative `/cut` is the default. A salvage-impossible surface — hop
histogram dominated by **cheap indirection**, ≥4 of 6 preconditions in
[`../reckless-cut/SKILL.md`](../reckless-cut/SKILL.md) — is not this
skill. Route to [`/reckless-cut`](../reckless-cut/SKILL.md): excise the
knot, use runtime breakage as discovery, rebuild **one** port-shaped
path. Fragmentation (many **short** load-bearing chains, missing owner)
stays here. Doubt stays here.

## What `/cut` is not

- Not a licence for reckless deletion — the checklist is walked, and every
  cut lands with green verification. Salvage-impossible knots are
  [`/reckless-cut`](../reckless-cut/SKILL.md), not this skill.
- Not only for clean-up sessions — it is a gate inside normal work:
   `/plan` §4 (cut list) is this skill's output.

## Reject list

- "Might be used later" — git is the archive; the working tree is the
  present.
- Commenting out instead of deleting.
- A rename smuggled in as a cut, or a cut smuggled in as a rename — one
  change, one kind.
- Leaving the old path alive "just in case" behind a flag nobody tests.

## References

- [`references/cut_checklist.md`](references/cut_checklist.md) — the cut
  classes, mapped to the rot register.
- [`references/capability_port.md`](references/capability_port.md) — the
  constructive form: what an addition must look like (driver, port,
  adapter) once the cut list clears it.
- [`../reckless-cut/SKILL.md`](../reckless-cut/SKILL.md) — the
  salvage-impossible branch.
- [`../baptise/SKILL.md`](../baptise/SKILL.md) — coin-time lexicon check
  before a new name exists.
- [`../adjudicate/SKILL.md`](../adjudicate/SKILL.md) — two mechanism
  branches presented as equally open: eliminate first; this worksheet is
  the how after the branch is forced.
