# Capability port — the constructive form

| | |
|---|---|
| **Title** | capability_port.md — how a capability is built here |
| **Status** | Canonical |
| **Authority level** | 3 |
| **Scope** | Universal — every repository seeded from this template |
| **Relationship-to** | The form `/cut` builds toward; enforced by `capability_ports.json` |
| **Document class** | procedure |
| **Contract** | `epitomikon/document-contract/v1` |

A **capability** is something this repository guarantees. It is never a
loose function reachable by several routes. It is built as three parts,
and the first rule is that all three are **named**.

- **driver / owner** — one component holds the invariant, in one place.
  There is no second path to the effect. If two files can both produce
  the guarantee, there is no driver; there are two writers and a future
  divergence.
- **port** — the typed surface consumers hold. A concrete Go type, not a
  `map[string]any` bag, not a string that means whatever the next reader
  infers. The port is what makes the guarantee *already answered* for a
  caller instead of something they reconstruct.
- **adapter** — I/O, CLI flags, transport, config. An adapter returns a
  typed result or a genuine error. It can neither hold the guarantee nor
  break it. If an adapter can decide the answer, it is a second driver
  wearing an adapter's name.

## Every capability is named — the roster

The form is worth nothing as prose. It is enforced by
[`capability_ports.json`](../../../../capability_ports.json) at the repo
root, joined against the source by
`go run ./tools/agentctl verify` and by `go test ./...`.

The roster is the repo's own contract, not the tool's. Every command a
CLI dispatches **must** appear in it. The join goes red on:

| Finding | Why it is a defect |
|---|---|
| a dispatched command with no roster row | an unnamed capability is one nobody owns |
| a roster row that no longer dispatches | the capability went somewhere and nothing said where |
| `issued` with no `port` named | "issued" claims a surface exists; name it or call it an instrument |
| a `port` on a row that is not issued | a port consumers cannot hold is not a port |
| a `port` naming a type not declared in the repo | the surface is fictional |
| a `driver` file that does not exist | the owner is fictional |
| an unknown disposition | the roster's vocabulary is closed on purpose |
| this file missing, or not naming the roster | doctrine nothing holds to |

## Dispositions — honesty over completeness

- **`issued`** — a typed port exists and consumers hold it. Name the type
  in `port` and the owning file in `driver`.
- **`instrument`** — the runner is live and no port is issued yet. This
  is **honesty, not failure**. Most commands in a young repo are
  instruments. Marking one `issued` before the surface exists is the
  lie the join is built to catch.
- **`remainder`** — still advertised, but outside the CLI spine: a
  script, another language, a manual step. Naming it keeps it visible
  until it is retired.
- **`retired-stub`** — kept only to refuse, and to tell the caller where
  the capability went. A stub that errors is better than a command that
  silently does the wrong thing, and far better than a dangling doc.

## Falsifiable ownership

The test of a driver is not that it is tidy. It is that **violation is
unrepresentable through the owner** — by type, by sole constructor, by a
single emission entry — rather than caught downstream by a guard.

A guard that *owns* an invariant at its boundary is clean structure. A
guard that *compensates* for an invariant owned elsewhere is rot
([`docs/ROT.md`](../../../../docs/ROT.md)). The difference is whether
removing the guard makes the violation impossible or merely invisible.

Honest gaps stay representable. A named "not yet answered" is a
first-class value; it is manufacturing an answer that is forbidden.

## Interrogation — before code, not after

1. What invariant does this preserve?
2. What is its **single** owner afterward?
3. If I am not the owner, route there — do not re-implement the check here.
4. Is violation still representable through the owner? If yes, make it
   unrepresentable.
5. What typed surface do consumers hold?
6. What paths does this change **retire**? (`Retires:` on the commit —
   [`docs/ROT.md`](../../../../docs/ROT.md) § The parsimony contract.
   `Parsimony: add` must hunt; `Parsimony: fix` mints no new file.)
7. Which existing test goes red if this is wrong?

If you cannot answer 2 and 5, you do not have a port. You have knitting,
and the roster will say so.

The join reads the **argv-index switch** (`os.Args[1]`, `flag.Arg(0)`),
not every string `case` in the file. A flag walk (`switch args[i] { case
"--imports": }`) is not a command, and treating it as one is a false
unnamed-capability.

## PhilOcr product binding

This section binds the form onto PhilOcr's Python application. It does
not open a second shape.

A change that moves, splits, or replaces a product behaviour is a
**cutover**. It is finished only when all of these hold:

1. One driver owns the invariant, in one file under `src/`.
2. Consumers hold one typed Python port, written `module.Class`, and
   that class is declared in the driver file. `dict`, `Any`, and a
   stringly mode flag are not a port.
3. Adapters — UI, workers, config — return that type or raise. They do
   not decide the guarantee.
4. Every previous route to the same effect is deleted in the same
   change. A compatibility wrapper, a flag that selects the old path,
   or a second caller left "for now" is refused.
5. The row in `capability_ports.json` under `product` has disposition
   `issued`, with `port` and `driver` named. `instrument`, `remainder`,
   and `retired-stub` are refused on a product row. Those dispositions
   stay available only on the house CLI (`clis`).

The `product` list may be empty. Empty means no product capability has
been cut over yet. It is not permission to refactor without issuing one.
The next refactor adds the row and deletes the old route in the same
change. There is no phased migration and no menu of shapes.

The join (`go test ./tools/agentctl/portcmd`, and `make verify`) goes
red when the `product` key is absent, when a product row is not
`issued`, or when the named class is not declared in the named driver.
It does not infer that an arbitrary diff was a refactor. The obligation
on the agent does not wait for that inference.

## Campaign pickup

A campaign stage that adds or extends a command goes through a named
capability port. The roster is
[`capability_ports.json`](../../../../capability_ports.json). An unnamed
capability is one nobody owns ([`docs/ROT.md`](../../../../docs/ROT.md)
A8). This is the same issuance join, not a third gate.
