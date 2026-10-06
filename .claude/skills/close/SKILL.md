---
name: close
description: >
  Session closure. Use at the end of every working session — including
  interrupted ones. Reconciles the gates, campaign graph and handover; writes a dated
  work report only when retained historical evidence is useful. A session
  that does not reconcile is a session the next one cannot trust.
---

# `/close` — end in reconciled repository state

## Procedure

1. **Reconcile the gates.** Walk the armed checklist from `/open`: each
   gate is `done`, or named as not-reached with the reason. Nothing silently
   drops.
2. **Reconcile the graph.** If the session finished a campaign or task, delete
   that node (and a finished campaign's member tasks) from `campaigns/graph.yaml`
   in the same change as the receipt. Drop `needs`/`after` edges that cited the
   removed ids. Do not stamp `done`. Run Eustratikon audit and frontier; never
   copy their answers into a second queue.
3. **Hand over.** If the frontier becomes non-empty or changes, copy
   `HANDOVER_TEMPLATE.md` to `HANDOVER_YYYY-MM-DD_<topic>.md`, fill the
   quick-start block, delete the handover it replaces, then:
   ```sh
   go run ./tools/agentctl now
   ```
   Exactly one handover stays live while there is a frontier. An empty graph
   has no handover and no `NOW.md`.
4. **Record only if needed.** Use [`/log`](../log/SKILL.md) when retained
   past-tense evidence would otherwise vanish. Do not create a report merely
   to prove that close ran.
5. **Commit** changed closure surfaces together. An optional report, graph,
   handover and NOW.md form one atomic unit when they change together.

## What `/close` is not

- Not a summary for the user's reading pleasure — it is the next session's
  input. Write for a cold-started agent.
- A one-off question with no persistent state closes LIGHT without inventing a
  repository artifact.

## Reject list

- Leaving changed graph or frontier evidence only in chat.
- Writing a report that merely restates the diff or says nothing landed.
- Two live handovers.
- A report whose verification section summarizes instead of quoting.

## References

- [`references/closure_checklist.md`](references/closure_checklist.md) —
  the report anatomy and status vocabulary.
