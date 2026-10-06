---
name: campaign
description: >
  Decide whether work belongs in the campaign graph as a campaign, a
  standalone task, or an external condition. Use when work spans sessions,
  has independently landable parts, changes a shared boundary, needs a
  per-item spine, or must be ordered against existing work. Link temporal work
  to its durable regulator; never turn the campaign into that owner.
---

# `/campaign` — register temporal work without minting a second authority

The durable contract belongs to Eustratikon's `docs/CAMPAIGN_GRAPH.md`. This
skill applies it; it does not restate the schema or implement another parser.

## Procedure

1. **Classify the work.** Apply the campaign bar in
   [`references/campaign_anatomy.md`](references/campaign_anatomy.md). A
   campaign coordinates several independently landable units. A smaller item
   is a standalone task. A fact outside repository control is a condition.
2. **Link the durable owner.** Select an existing regulator under
   `campaigns/regulators/`, or create one only when the regulated variable is
   genuinely new. A campaign serves it; it does not copy or replace it.
3. **Name the semantic owner.** Every node links `owner` to the plan, campaign
   document, code contract, or other file that explains the work.
4. **Add one graph node.** Edit `campaigns/graph.yaml`. Use `needs` only for a
   real readiness prerequisite and `after` only for chosen order. Before
   declaring a campaign `doing`, leave every other campaign `open` or absent; tasks may still be `doing` concurrently.
5. **Audit before pickup.** Run:
   ```sh
   go tool eustratikon campaign-audit .
   go tool eustratikon campaign-frontier .
   ```
6. **Finish by leaving.** Delete the finished node (and a finished campaign's members)
   in the same commit as the receipt. Drop `needs`/`after` edges that cited the
   removed ids. Do not stamp `done`. Absence is completion.

## What this is not

- Not a second backlog or a queue in chat.
- Not a workflow executor or permission to infer an external condition.
- Not a place to copy the regulator's variable or the owner document's plan.
- Not a reason to wrap one small task in a fake campaign.

## Reject list

- Campaign node with no regulator link.
- Member task repeating its parent campaign's `serves` list.
- `after` used to disguise a hard dependency.
- More than one campaign declared `doing`.
- Finished work left on the live graph as `done` or `dropped`.
- Authored frontier, coverage, or status projection outside the graph.

## References

- [`references/campaign_anatomy.md`](references/campaign_anatomy.md) — the
  campaign/task/condition classification and pickup receipt.
- Eustratikon's `docs/CAMPAIGN_GRAPH.md` — the durable schema, ownership,
  and live-graph contract.
