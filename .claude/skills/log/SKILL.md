---
name: log
description: >
  Put a session down: the optional past-tense work report, the dated
  handover, and the campaign update that is not optional. Use when the
  user says "log this", "write a work report", "write a handover", or
  "put the session down"; when a landing is about to be narrated into a
  commit message; and at any landing that finished work a task in
  campaigns/graph.yaml still describes as outstanding.
---

# `/log` — put the session down, if it needs it

A work report is a past-tense note of one agent's activity in one session.
**Skipping is the default.** Write one when the session would otherwise
vanish into a commit-message essay or a chat the next agent will not see.

## Homes, two tenses

| What you have | Home |
|---|---|
| What you DID this session | `work_reports/YYYY-MM-DD_<topic>.md` — past |
| What one agent knew that the diff does not carry | `HANDOVER_YYYY-MM-DD_<topic>.md` — a **new** file, replacing the handover it supersedes; then `go run ./tools/agentctl now` |
| What to do NEXT | an open/doing node in `campaigns/graph.yaml` — forward |

One tense per home. A next step written into a report is lost the moment
it is written, because nobody reads that directory forward. A session
handover written over the pickup is lost the same way: the next agent
replaces it.

## The campaign update is not optional

The report is optional. This is not. If the session landed work that a
task's acceptance describes as outstanding, that task is deleted from
`campaigns/graph.yaml` — or its acceptance is corrected to say what is
actually still missing.

The check that catches more has no command: **read the plan's own claims
about what is outstanding.** A campaign goes stale the moment a sentence
in it says something does not land that now does, and the sentence will be
phrased with enough confidence that the next agent believes it. A campaign
whose plan you did not open is a campaign you did not check.

## How to write one

1. **Decide it is needed.** If the tree already carries what landed, stop.
   The note is for a human who will not re-read the diff.
2. **Path:** `work_reports/YYYY-MM-DD_<topic>.md`. Today's date, a short
   topic, one file per session.
3. **Past tense.** What landed, where it lives, which commands actually
   ran. Evidence is a path or a command whose exit you saw — never a
   remembered figure, never a count copied from an earlier run. **An
   empty result needs its instrument shown to fire.** A zero written into
   a report is the hardest figure to dislodge later: it reads as a fact
   and nobody re-runs it. Plant what it looks for, watch the detector go
   red, and say in the note that you did.
4. **Stop at what you did.** No forward plan — that is the campaign's.
   And **no chronicle of what went wrong.** A wrong turn written as
   narrative is a war story. If the session's value is what it refuted,
   say what the evidence now shows and stop; the temptation that produced
   the error earns a line in the rot register only if it is a shape,
   never as an incident.

```markdown
# 2026-08-24 — skill farms verified idempotent

`tools/agentctl/link` now rebuilds every farm from .claude/skills/ and a
second run changes nothing. `go test ./tools/agentctl/linkcmd/` green;
`agentctl verify` 34 passed, 0 failed.
```

That is a complete report. Commit it with a short subject and the diff —
this directory must not become where commit-message essays go to live.

Peer skills: [`/adversarial`](../adversarial/SKILL.md) refutes a claim
before it is trusted. [`/cold-reading`](../cold-reading/SKILL.md) maps
ownership; [`/cut`](../cut/SKILL.md) plans the collapse; [`/close`](../close/SKILL.md)
reconciles the session's gates. This one records.
