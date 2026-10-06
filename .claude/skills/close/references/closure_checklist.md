# Work report anatomy

| | |
|---|---|
| **Title** | Optional work report anatomy |
| **Status** | Current procedure reference |
| **Authority level** | 3 — supports the close and log skills |
| **Scope** | Retained past-tense session evidence when the repository otherwise loses it |
| **Relationship-to** | Cited by `.claude/skills/close/SKILL.md`; `/log` decides whether a report exists |
| **Document class** | procedure |
| **Contract** | `epitomikon/document-contract/v1` |

When `/log` says a report is warranted, use
`work_reports/YYYY-MM-DD_<topic>.md`. There is no one-report-per-session rule.

```markdown
---
date: YYYY-MM-DD
status: final | partial
work_type: one-off | local | structural | campaign   # from /open
---

# <what this session was about>

## Attempted
- (the mission in one or two lines)

## Landed
- (what changed, files touched, with verification quotes — the sheet from
  /verify, not a paraphrase)

## Not landed
- (what was attempted and did not finish; what was deliberately left)

## Next
- (the single hand-off line: where the next session starts)
```

Rules:

- **Landed** carries quoted command output; a landed claim with no quote
  did not land.
- **Not landed** is not a failure section — it is the honest frontier.
- **Next** is one line. Detail belongs in the handover, not the report.
- `status: partial` requires the hand-off line and an updated handover.
- A report that only restates the diff is omitted.

## Status vocabulary

| status | meaning |
|---|---|
| `final` | session reconciled; gates done or explicitly not-reached |
| `partial` | session cut short; hand-off line present; handover updated |
