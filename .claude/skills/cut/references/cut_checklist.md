# Cut checklist

Each class names its rot register counterpart (`docs/ROT.md`).

| Class | Question to ask | Rot |
|---|---|---|
| Dead code | Does anything reference this? (`grep` the identifier — quoted) | A1 |
| False identity | Does the name still say what the thing does? | A2 |
| Duplicated authority | Is this the second copy of something with an owner? | A3 |
| Projection drift | Is this a copied projection of a canonical file? | A4 |
| Retired procedure | Does any doc still advertise the old way? | A5 |
| Speculative surface | Was this built for a need that never arrived? | A1 |

## The three cuts, in order

1. **Cut the dead** — unreferenced, unreachable, test-only-in-name.
2. **Cut the false** — a name that lies is cut or renamed; never documented
   around.
3. **Cut the duplicate** — when two things carry one concern, one dies and
   the survivor inherits the references.

## Verification bar for cuts

```sh
make build && make test && make lint   # all green, output quoted
go run ./tools/agentctl verify         # if surfaces were touched
```

A cut that cannot pass green is not a cut — it is a breakage with good
intentions.
