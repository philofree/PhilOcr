# Arming matrix — the classification authority

| | |
|---|---|
| **Title** | Arming matrix — session classification |
| **Status** | Current procedure reference |
| **Authority level** | 3 — supports the open skill |
| **Scope** | Session work-type classification and transient gate state |
| **Relationship-to** | Cited by `.claude/skills/open/SKILL.md` |
| **Document class** | procedure |
| **Contract** | `epitomikon/document-contract/v1` |

Three signals, read in order, classify the session; the row arms the gates.
Do not improvise a work type to fit the gates you wanted.

## Signals

| # | Signal | Where read |
|---|---|---|
| 1 | The prompt | What the user actually asked |
| 2 | The tree | `git status` — uncommitted prior work |
| 3 | The campaign graph | `go tool eustratikon campaign-frontier` active/ready result |

## Rows

| Work type | Signals | `/plan` | `/verify` | `/close` bar |
|---|---|---|---|---|
| **One-off question** | Read-only prompt; no campaign graph node | not armed | not armed | LIGHT |
| **Local change** | Single-module prompt; tree clean; no campaign | sections 1–3 | armed | LIGHT |
| **Structural change** | Touches more than one module; or graph node `doing` | sections 1–5 | armed | FULL |
| **Campaign work** | Campaign graph node exists and names this work | sections 1–5 + campaign brief | armed | FULL |

A change is structural when it crosses a boundary the codebase treats as
real (module, package, schema, public interface) — not when it merely feels
big.

## Transient `session_state` schema

```yaml
session_state:
  opened: YYYY-MM-DD HH:MM
  work_type: one-off | local | structural | campaign
  gates:
    plan: {armed: bool, sections: [n..n]}
    verify: {armed: bool}
    close: FULL | LIGHT
  current_gate: open | plan | verify | close | done
```

Update `current_gate` in the active task as gates complete. At `/close` it
disappears; only changed campaign graph or handover state persists.
