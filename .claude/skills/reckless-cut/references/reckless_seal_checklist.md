# Reckless Cut seal checklist — post-rebuild closure

Complete after Pass 1 excision and port rebuild, **before** campaign wave
close or `/close`. Pairs with `/adversarial` sign-off.

---

## Pass 2 trigger — when to run a second bloat pass

Run Reckless Pass 2 when **any** holds after the first clean shape lands:

- After hop count still **above brief §7 target**
- Cut ledger rows marked `retire` still have live imports or call sites
- Wrapper/relay files remain beside the new owner
- A second writable path to the same fact is still representable

Pass 2 deletes residue only — do not expand scope beyond the one-sentence
job.

---

## Port landed — sign-off attacks

- [ ] Invariant logic lives in the **named owner module** in the diff —
      not only at call sites.
- [ ] Cut-ledger paths (brief §4) are **actually deleted or rewritten** —
      not left standing beside the new owner.
- [ ] **No** second writable path to the same fact was introduced.
- [ ] Callers route **through** the port — not around it.
- [ ] Breakage restores were integrated at the **owner**, never at the
      stack-trace site.
- [ ] `capability_ports.json` row is honest (`issued` names a real port).

---

## Verification stack

Run the oracle named in brief §6. Record results. A green suite is not
fitness.

```sh
make test && make lint
go run ./tools/agentctl verify
```

---

## Adversarial sign-off dispatch

Launch an **independent** read-only sub-agent per `/adversarial` with
gate **sign-off**. Author is not the adversary.

---

## Closure sentence

Correct form: excised per ledger → rebuilt through named ports → one
path → oracle green → adversarial sign-off run → Pass 2 only if
residue triggers fire.
