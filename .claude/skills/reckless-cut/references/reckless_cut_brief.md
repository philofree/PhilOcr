# The Reckless Cut Brief — named ports + cut ledger before excision

| | |
|---|---|
| **Title** | `references/reckless_cut_brief.md` — the brief a reckless cut must fill |
| **Status** | Binding while a reckless cut is planned |
| **Authority level** | 3 — a reference of [`../SKILL.md`](../SKILL.md), which owns the procedure |
| **Scope** | One excision, its named ports and its cut ledger |
| **Relationship-to** | Serves [`../SKILL.md`](../SKILL.md); the port form is [`../../cut/references/capability_port.md`](../../cut/references/capability_port.md). Restates neither |
| **Document class** | procedure |
| **Contract** | `epitomikon/document-contract/v1` |

Fill every field **before deleting a line of production code**. A plan that
cannot name the ports it rebuilds toward and the paths it deletes is not a
reckless cut — it is an undisciplined rewrite.

For a campaign wave, brief answers land in its graph-linked owner plan — one shape, not
two.

---

## 1. One-sentence job

> This surface exists to: __________ (for a real user / the system).

If you cannot say it in one sentence, you are not ready to cut.

---

## 2. Named capability-port sketch — the surviving shape

> Regulated variable / invariant (one sentence): __________

> Single driver / owner (`file` / module): __________

Form: [`.claude/skills/cut/references/capability_port.md`](../../cut/references/capability_port.md).
Roster the capability in `capability_ports.json` in the same change.

### Port signatures — write the actual surface

```go
type <Name>Port interface {
    <Verb>(...) (<Result>, error)
}
```

| Port name | Signature | Issued by | Consumed by |
|---|---|---|---|
| | | | |

- [ ] The **driver holds the invariant**; the port is only the behaviour
      boundary.
- [ ] Callers cannot bypass it without editing the owner module.
- [ ] Adapters return a typed result or a genuine I/O error — they can
      **neither hold nor break** the guarantee.

**Owner-only exception:** pure consolidation with no infra seam — say so,
skip the port table, still name the single owner.

---

## 3. Why salvage fails — hop / competing-element census

Paste `/cold-reading` findings here — do not author this map from your own
read alone.

### Branch selection gate — score ≥4 of 6

| # | Precondition | Y/N |
|---|---|---|
| 1 | Hop count obviously far above port sketch | |
| 2 | Wrapper / adapter / relay / compensating-guard density high | |
| 3 | ≥2 writable owners or parallel paths for one fact | |
| 4 | Topology visibly broader than port sketch | |
| 5 | Conservative inventory preserves indirection | |
| 6 | Incremental `/cut` would polish the knot | |

> **Score:** ___ / 6 (must be ≥4). If <4, use `/cut`.

---

## 4. The cut ledger — what is DELETED

`cut` is **`retire` or `rewrite`** only. This table must be **non-empty**.

| Deleted (`file:line` / symbol / module) | Why redundant after port sketch | `cut` |
|---|---|---|
| | | |

---

## 5. Surviving path — after the cut

> `owner → port → terminal authority`: __________

Exactly one path.

---

## 6. Runtime oracle — the narrowest truthful check

> After excision, I will run: __________

Must be runnable here. Never the suite as proxy. If there is no oracle,
STOP — use conservative `/cut`.

---

## 7. Net line delta — reported, not targeted

> Before: _____ lines   After (target): _____ lines   Δ: _____

When excising, Δ must be **negative**. LOC is reported, not targeted.

---

## 8. Falsifier survival

- [ ] Invariant **not** smeared across two+ copies after rebuild.
- [ ] **No** two parallel paths left standing after seal.
- [ ] **No** adapter with power to end/fail the guaranteed outcome.
- [ ] **No** downstream guard added where the owner could preclude.
- [ ] Roster row in `capability_ports.json` is honest.

---

## 9. Held-state

> `by-construction` | `by-convention` (+ conversion target)

---

## Pre-cut gate (do not skip)

- [ ] Score ≥4/6 on branch gate (§3).
- [ ] Runtime oracle named and runnable (§6).
- [ ] Campaign gate per `/campaign`, or one-hit recorded in `work_reports/`.
- [ ] `/adversarial` **plan** gate dispatched (independent sub-agent).
