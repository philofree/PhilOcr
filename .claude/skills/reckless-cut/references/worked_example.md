# Worked example — the boundary test: reckless vs conservative

The hardest judgment Reckless Cut asks is *when it applies*. Delete-and-
rebuild is what an agent's completion-drive wants, so the discipline is in
the **precondition**, not the cut.

## NOT a reckless-cut candidate — fragmented but flat (use `/cut`)

Imagine one fact re-derived at three short sites: three emitters each
concatenate an identifier inline. Cold reading finds **3 writable sites,
no convergence owner** — genuine fragmentation.

But the hop counts are **short**, and most hops are *load-bearing*. There
is almost no wrapper / relay / compensating-guard pile to excise. The
disease is **fragmentation (many short chains, no shared owner)**, not
**indirection density (one long chain of cheap hops)**.

→ **Use `/cut`, not `/reckless-cut`.** Merge the three sites into one
owner conservatively. Reckless-cutting a flat, low-hop surface deletes
working code to no topological gain: **vandalism, not excision.**

**The tell:** parallel-path count is high but each path is short and
mostly load-bearing.

## A reckless-cut candidate — high-indirection relay tangle (use `/reckless-cut`)

The opposite signature: one user gesture reaches its terminal effect
through a long chain where most hops are **cheap indirection** —
orchestrator → helper that re-parses a bag → coordinator → adapter that
re-derives identity → another helper with a compensating fallback → the
actual emitter. Most hops answer "here only because indirection was
cheap," not "does real domain work."

Every conservative `/cut` slice must thread the new owner *through* that
chain. The named port sketch is far narrower: one driver, a typed port,
adapters that cannot hold the invariant.

→ **Use `/reckless-cut`.** Excise the wrapper/helper/relay pile as whole
files; run the named oracle; watch what breaks; rebuild as **one**
`owner → port → terminal` chain.

**The tell:** one long chain dominated by cheap-indirection hops, and the
port sketch is far narrower than the current surface.

## The line, stated once

| Signature | Disease | Mode |
|---|---|---|
| many **short** chains, no shared owner, flat writes | fragmentation | **/cut** (create the owner) |
| one **long** chain, most hops cheap indirection, surface ≫ port sketch | indirection density | **/reckless-cut** (excise, then rebuild) |

When in genuine doubt, `/cut` is the safe default.
