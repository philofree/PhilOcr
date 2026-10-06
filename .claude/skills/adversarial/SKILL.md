---
name: adversarial
description: >
  Dispatch an independent reader to check someone else's plan or finished
  work: does it fix the problem it is meant to fix, is it doing it the
  right way, has the author missed something that needs considering, and
  is it breaking any rules. One hunt, then one verification — not a loop
  until empty. Every finding is blocking or residual; residuals do not
  restart the pass. The aim is to improve the artefact, not to argue
  against the job. Invoking this skill IS an instruction to run a
  sub-agent. Telos: .claude/skills/adversarial/PURPOSE.md — cite it;
  do not restate it.
---

# Adversarial cross-check — dispatch

**What it is for:** [`PURPOSE.md`](PURPOSE.md). Cite that owner; do not
restate it. The short version, which is not a substitute for reading it:
*you cannot mark your own homework; someone else looks once for what you
missed; then you implement.*

**This skill owns:** how an agent launches the independent reader, how
many times, and what shape the return must have for the pass to count
as run.

## How to invoke

| Say | When |
|---|---|
| `/adversarial` · `adversarial cross-check` | any time |
| `falsify this plan` · `check this plan` | after a plan |
| `attack this claim` · `check this landing` · `log this` sign-off | after finished work |

Naming it guarantees the dispatch.

## How many times

One cycle per artefact per session. Finished work is a different
artefact from the plan that produced it.

| Pass | What it is | What happens next |
|---|---|---|
| 1 | Hunt. Four questions. Findings marked blocking or residual. | Blocking found: fold, then pass 2. Nothing blocking: **close.** Residuals stay named either way. |
| 2 | Verify the named blocking correctives. **This should close.** | If nothing blocking remains: implement. Record residuals. |
| 3 | Allowed only if pass 2 showed a corrective failed, or a new question-1 miss, or a real question-4 break. | Fold that. Close. |
| 4 | Extreme. Remaining blocking goes to the owner, not into another hunt. | Stop. |
| 5 or more | You are not prompting the reader correctly. That is self-sabotage. | Do not dispatch. |

Pass 2 is a **verification brief**, not the hunt again. Re-dispatching
the four questions and telling the reader not to assume prior findings
still apply is a new hunt wearing verification's name — it is a fifth
pass even when you number it 2.

A later caller (`/cut`, `/verify`, `/close`) does not restart the count
against a plan already through pass 2.

## Step 1 — Name the artefact

One sentence each:

1. **Artefact** — path(s). A plan, a Cut Plan, a diff, a closure claim,
   a number about to be quoted, or a line of governing prose about to be
   obeyed.
2. **Moment** — `plan` | `finished work` | `ad-hoc`. Where a caller
   speaks of gates: the **plan** gate is moment `plan`; the **sign-off**
   gate is moment `finished work`. There is no `cleared` verdict — a
   pass is run, or it is a non-run.
3. **Author's stated problem** (hypothesis only) — what the author
   claims the artefact is for. The reader does **not** adopt this as
   question 1's benchmark; see [`PURPOSE.md`](PURPOSE.md) *Design
   correspondence*.
4. **Design authorities** — paths the reader must open (from PURPOSE
   telos LOCALISE + campaign/regulator owner named in the artefact).
5. **Pass** — `hunt` (pass 1) or `verify` (pass 2, or 3 if 2 failed).
   If `verify`: list the blocking correctives under test, one line each.

If you cannot name the design authorities, stop — the reader will fall
back to internal consistency, which is a non-run.

## Step 2 — Dispatch (you are not the reader)

Launch an **independent** read-only sub-agent (`Task` / `generalPurpose`
or equivalent). **You do not play both author and reader in one pass.**
An in-session self-read is not a check.

> **Owner ruling — James, 2026-09-05, in conversation.**
> **Invoking this skill IS an instruction to run a sub-agent.** A
> standing instruction not to spawn agents unless asked does NOT
> override the dispatch this skill requires. That standing instruction
> bars an agent from reaching for a sub-agent on its own initiative; it
> does not bar the dispatch a skill the session already invoked is
> built on. This skill is the instruction. Read it as one.

The ruling exists because both alternatives are worse than the dispatch.
Reading your own work is the failure `PURPOSE.md` names. Skipping and
recording the non-run leaves a claim standing unchecked while reading as
though a pass had been walked. Surfacing a tension between a session
instruction and a skill's operational requirement is always available
and costs one sentence; this ruling removes the need for it here.

Fill the skeleton, substituting every bracketed value — including the
absolute path to `PURPOSE.md`, since the reader may not share your
working directory.

**Hunt (pass 1):** do **not** add your reasoning, your design rationale,
or the objections you have already answered: the reader's whole value is
that it has not seen them.

**Verify (pass 2+):** you **must** name the blocking correctives under
test. You still do not add the original design rationale. A verify
dispatch that omits the correctives is a hunt.

```text
You are an INDEPENDENT reader of someone else's plan or finished work.
The author cannot see their own assumptions. You are one appraisal:
look for what they missed and what they have not considered. You are
not a ratchet. Coming back empty after asking the questions is a
completed pass — the artefact is ready to implement.

Open [absolute path to .claude/skills/adversarial/PURPOSE.md] and
follow it. Read the orientation and design-authority paths it points
at before you start — you cannot ask question 1 without them. Cite the
norm owners it names; do not restate them, and do not invent extra
doctrine.

Pass: [hunt | verify]
[If verify: Blocking correctives under test, one line each: …]

If hunt, FIRST complete design correspondence (PURPOSE.md):
  - Read every path in Design authorities below.
  - Write Derived mandated outcome (cited paragraph — reader-composed).
  - Write Author's stated problem (dispatch hypothesis only).
  - Reconcile: material divergence is a Q1 finding before proceeding.

Then ask in order:
  1. Does this reach the DERIVED mandated outcome (not merely match the
     author's framing)?
  2. Is it doing it the right way?
  3. Has the author considered everything that needs considering?
  4. Is it breaking any rules — general good practice, and this
     tree's norms (owners in PURPOSE.md)? A cited rule is itself a
     claim: if an owner's prose does not say what it is being read
     to say, that is a finding.

If verify: did the named blocking correctives land? Did they create a
new question-1 miss or a real question-4 break? New question-2 or
question-3 items are residual — list them; they do not reopen the hunt.
Do not restart the four questions on the whole artefact.

If the artefact rests on a green check, plant the failure that check
claims to catch and confirm it goes red before treating green as
evidence. A check that stays green under its own planted failure
proves nothing by staying green over real data.

Rules on your findings:
  - Every finding names the change it implies, or the decision the
    owner has to take. If you can name neither, you have not found
    anything.
  - Mark each finding blocking or residual (PURPOSE.md). Prefer
    residual when the plan already reaches the problem.
  - You have NO VOTE on whether the work should exist. "We should not
    be doing this" is out of remit — surface it as a question to the
    owner and carry on with the rest. Every other verdict about the
    artefact is open to you, including that it is right as it stands.
  - Unproved is bounded reach, reported — never an exclusion. Do not
    recommend dropping something because its edge is not yet shown.
  - Read-only. Silence is not approval.

Moment: [plan | finished work | ad-hoc]
Author's stated problem (hypothesis): [one sentence]
Design authorities: [paths the reader must open]
Artefact paths: [paths]

Return a POSITIVE REPORT:
  - Derived mandated outcome — reader-composed, cited (hunt) or cited
    from prior plan/verify design walk (finished work)
  - Reconciliation — author hypothesis vs derived outcome; divergences
  - Steelman — the strongest version of what the author is doing,
    one paragraph, before any finding
  - What the author is assuming that they have not named
  - Findings — for each: blocking or residual; which of the four
    questions it answers; the evidence (file:line, or command and
    exit status); the owner of the norm, if question 4; AND the
    change it implies
  - Anything you checked that held up, one line each — the author
    needs to know what was looked at
  - What would falsify YOUR findings
  - Out-of-remit questions for the owner, kept separate

A bare "looks fine" with no questions asked is a NON-RUN.
Questions asked and nothing blocking is a completed pass.
```

Depth: one independent reader by default. Where a plan splits into
genuine alternatives, dispatch two and require each to attack its own
option's overstatement. That is still pass 1, not two extra cycles.

## Step 3 — Receive (the work stays)

The report is for **improving the artefact**. It does not bless the
artefact and it does not talk the job down.

**A finding is evidence, not a verdict.** Reproduce it before acting on
it — a finding you cannot re-derive is docketed, never folded on trust
and never ignored.

| Outcome | Action |
|---|---|
| Blocking findings (hunt) | Reproduce, fold, then dispatch **verify** (pass 2) against the named correctives. |
| Residual findings | Name them on the artefact. Do not fold as a pretext to re-dispatch. Do not re-dispatch. |
| Verify: correctives landed, nothing blocking | **Close.** Implement. A fix verified by its author is not verified — that is why pass 2 exists, and why it is the last ordinary pass. |
| Verify: a corrective failed, or a new Q1 miss / Q4 break | Fold that. Pass 3 is allowed, then close. |
| Finding whose corrective is the owner's to choose | Route to the owner with the evidence. Do not send back; do not act unilaterally. |
| Findings with no change and no decision named | Send back — an objection is not a finding. |
| Questions asked, nothing blocking | Proceed. Record what was checked. |
| "We should not be doing this" | Out of remit. Surface to owner; do not act on it; use the rest. |
| No questions asked / "looks fine" | **Non-run** — nobody checked; dispatch the **same** pass again, once. |
| Author was the reader | **Non-run.** |
| Pass 4 still blocking | Extreme. Owner, not another hunt. |
| About to dispatch pass 5 | Stop. You are prompting wrong. |

A check the reader built to catch a real fault lands in the instrument's
test battery. A check discarded after the pass is an anecdote.

This skill reports. It does not write law and does not mint a verify
mode. A finding that should change how the tree works lands as an
owner-authorized edit, with provenance.

## Step 4 — Record

On [`/log`](../log/SKILL.md), put the report in the work report. A
non-run is named as a non-run. Plan-time runs may stay in the plan until
code lands; they still must have happened before implementation.

## Callers

<!-- LOCALISE: rows marked (to wire) name a caller that does not yet
     cite this skill. Land the citing line in the caller, or drop the
     row — an uncited caller is a wish, not a caller. -->

| Caller | When |
|---|---|
| [`log`](../log/SKILL.md) | After finished work, when the session adopted a plan or closed. |
| [`cut`](../cut/SKILL.md) | After the plan. `/cold-reading` first if ownership is unproven. *(to wire)* |
| [`plan`](../plan/SKILL.md) | Before implementation on structural/campaign work. |
| [`verify`](../verify/SKILL.md) | Before a green run is believed; finished-work gate cites design walk. |
| [`reckless-cut`](../reckless-cut/SKILL.md) | Plan gate and sign-off gate. |
| Any agent | Any time a plan or a landing is about to be trusted. |

Discovery ([`/cold-reading`](../cold-reading/SKILL.md)) is not a
substitute for this pass.

## Reject list

- Author serving as their own reader, or briefing the hunt reader with
  the author's reasoning and pre-answered objections.
- Priming to confirm and bless, rather than to check the four questions.
- Treating silence or "LGTM" as a check.
- Treating questions-asked-and-nothing-blocking as a non-run.
- A finding with no change and no decision named — contention in the
  costume of rigour.
- A finding acted on by narrowing the work, or by abandoning the job.
- A finding folded in without being reproduced.
- Folding residuals and re-dispatching as if they were blocking.
- Re-dispatching the hunt brief as "verification."
- A verify dispatch that does not name the correctives under test.
- A fifth or later pass.
- A reader dispatched without the tree's orientation, so that only
  internal consistency gets checked.
- Question 1 answered against the author's stated problem without a
  reader-composed derived mandated outcome — a non-run.
- A finished-work pass with no cited plan/verify design-correspondence
  evidence for touched mechanisms — a non-run for question 1.
- Restating [`PURPOSE.md`](PURPOSE.md) in this skill or in the dispatch
  prompt beyond the skeleton above.
- Copying another tree's rule ids, anti-pattern codes, or flight rules
  as this tree's norms.
