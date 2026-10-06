# Campaign anatomy

| | |
|---|---|
| **Title** | Campaign anatomy — classify and register temporal work |
| **Status** | Current procedure reference |
| **Authority level** | 3 — supports the campaign skill |
| **Scope** | Choosing campaign, standalone task, or condition nodes |
| **Relationship-to** | Applies Eustratikon's `docs/CAMPAIGN_GRAPH.md`; cited by `.claude/skills/campaign/SKILL.md` |
| **Document class** | procedure |
| **Contract** | `epitomikon/document-contract/v1` |

## The campaign bar

Use a campaign when any one is true:

1. Work spans more than one session.
2. It has more than one independently landable deliverable.
3. It changes a boundary other work depends on.
4. "One more thing" has been said twice.
5. It needs a per-item spine with a named owner.

Work that can land in one hit is a standalone task even when it crosses files.
A prerequisite outside repository control is a condition, not a fake task.

## Registration receipt

Before pickup, be able to answer:

- Which durable regulator does the campaign or standalone task serve?
- Which file owns the work's meaning and acceptance?
- Which `needs` edges genuinely control readiness?
- Which `after` edges express preference only?
- What receipt would justify deleting the node?

Then add exactly one node to `campaigns/graph.yaml` and run both Eustratikon
commands. The frontier output is the pickup receipt; no status is copied into a
handover or secondary queue.

## Finish receipt

Finishing work is not a status edit: the node leaves the graph in the same
commit as the receipt. Remaining nodes drop `needs`/`after` edges that cited
it. The regulator stays; git is the archive.
