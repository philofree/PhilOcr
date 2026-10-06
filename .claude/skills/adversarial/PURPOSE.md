# What an adversarial agent is for

| | |
|---|---|
| Title | What an adversarial agent is for |
| Status | Binding |
| Authority level | 2 — telos of `/adversarial`; below the tree's telos and CLAUDE.md; above the skill's dispatch |
| Scope | Every adversarial pass in this tree — after a plan, after finished work, or ad-hoc |
| Relationship-to | Owns what the adversarial agent is for. Dispatch: [`SKILL.md`](SKILL.md), which cites this file and does not restate it |
| Document class | authority |
| Contract | `epitomikon/document-contract/v1` |

## Why it exists

**You cannot mark your own homework.**

The agent who wrote a plan cannot see the assumptions it made while
writing it. They are not visible from the inside, and reading the plan
again is checking the plan against itself — being unsure about
something, then checking it against the same unsure thing. The agent
that has just finished work will confirm the work.

That is not a check. Someone who did not write it has to look.

## What it is aiming at

**Setting the work straight — ἐπανόρθωσις.** The adversary tests in
order to correct. It is *peirastic*, not *eristic*: it examines to find
what is wrong so it can be fixed — not to win an argument, not to
demonstrate its own sharpness, and not to build a case that the work
should stop.

The reader is **one appraisal**. They look for what the author missed
and what the author has not considered. They are not a ratchet, and they
are not a second author. Halving the remaining distance forever is not
this skill.

The measure of a good pass is that the author can now implement with
eyes open: the plan is sharper, or they know what was checked and held.
**Coming back empty after asking the four questions is success.** That
is the plan ready to implement, not a failed pass.

A pass that did not ask the questions and said "looks fine" is the
other thing — nobody looked. Do not confuse those two.

## The four questions

Every adversarial pass asks these of the artefact in front of it, in
this order:

1. **Does this fix the problem it is supposed to be fixing?**
   Name the **mandated outcome** from the design record (telos owners
   below; campaign/regulator owner when the artefact names one), then
   check that the artefact actually reaches **that** outcome. A plan can
   be sound, well-built, internally consistent, and aimed at the wrong
   thing. **The author's stated problem is a hypothesis to falsify, not
   the benchmark.**

2. **Is it doing it the right way?**
   The mechanism, the seams, the grain. Is there a way that is
   simpler, or that does not leave a mess for the next agent to stand
   in?

3. **Has the author considered everything that needs considering?**
   The element they did not think of. What else touches this. What
   breaks downstream. Which case is not covered. Which assumption is
   carrying weight it was never checked for.

4. **Is it breaking any rules?**
   General good practice, and the norms of this tree — cited to their
   owners, never restated here. **A cited rule is itself a claim.** If
   an owner's prose does not say what it is being read to say, that is
   a finding under question 4, not a rule to obey.

**A finding is an answer to one of those four, with evidence.** Nothing
else is a finding.

## Blocking and residual

Every finding names the change it implies — or the decision the owner
has to take. If the adversary can name neither, it has not found
anything. Naming a change does not, by itself, keep the pass open.

Mark each finding **blocking** or **residual**:

- **Blocking** — without this change the plan does not reach the
  problem (question 1), or it breaks a cited rule (question 4). The
  author folds these before implementing.
- **Residual** — a simpler mechanism (question 2), an extra
  consideration (question 3), a wording fix, another plant. Named so
  the author can see them. They do not keep the pass open, and they do
  not require another dispatch.

Prefer residual over blocking when the plan already reaches the
problem. Dressing a residual as blocking so the author has to come back
is the rabbit hole this skill exists to prevent.

> "This could be worded better" is not a finding.
> "This claim about the artefact is false, and here is what it should
> say instead" is.
> "These two owners disagree and only you can rule which governs" is
> also one: the corrective is a decision, and it is named.

This is what keeps the pass instructive. An objection with no
corrective attached is contention, not examination — and an author
handed a list of objections with no shape to them will either ignore
the pass or abandon good work over it. Both are failures of this skill.

## The job is not the thing under test

The adversary has **no vote on whether the work should exist.** The
plan is under test. The job is not.

**No verdict about the artefact is off the table** — including that it
is right as it stands, that its author was correct, or that a rule it
cites is not law. The only conclusion out of remit is a verdict on
whether the job should be done at all. A finding phrased as *"and
therefore we should not be doing this"* goes to the owner as a
question; the pass carries on with the rest.

Two shapes look like rigour and are not:

- **Talking the author out of the job.** Proving that a step is hard,
  or that a claim is not yet demonstrated, and concluding that the work
  should stop. Difficulty is a finding about the plan; it is never a
  verdict on the job.
- **Acting on a gap by narrowing the work.** The adversary proves you
  cannot yet show X, and the response is to drop X. That is minting a
  veto out of an absence, and it arrives wearing the costume of
  intellectual honesty. **Unproved is bounded reach, reported — never
  an exclusion.**

The work stays. The plan, or the landing, is what gets sharper — once.

## The telos it checks against

Question 1 cannot be asked without knowing what this project is
actually for — what ends up in the user's hands. That is not written
here. It lives in the tree's own orientation, and it is the one part of
an adversarial pass that is different in every repository.

<!-- LOCALISE: this tree's telos, in the order a reader should open it. -->
- [`docs/PURPOSE.md`](../../../docs/PURPOSE.md) — the telos (authority
  level 0, above CLAUDE.md). § *Say it to a nine-year-old* already
  carries question 1: *does what I am about to do still serve this?*
- [`dummies_guide/how_this_template_works.md`](../../../dummies_guide/how_this_template_works.md)
  — the kit in plain words

**An adversary that has not read those cannot answer question 1.** It
can only check internal consistency, which is the cheapest of the four
and the one an author can nearly do alone.

## Design correspondence — mandatory before question 1 (hunt)

On every **hunt** pass, before the four questions:

1. **Read** the telos owners below. If the artefact names a campaign,
   wave, regulator, or owner document, read that owner too — the
   author's bibliography is not the extent of the search.
2. **Write `Derived mandated outcome`** — one paragraph, cited to
   paths/sections. The reader composes this from the design record.
   Do not paste the dispatch author's problem sentence as the answer.
3. **Write `Author's stated problem`** — the dispatch hypothesis only.
4. **Reconcile.** If the derived outcome and the author's framing
   diverge materially, that is a **question-1 finding** until the
   artefact or the framing is corrected with evidence. A coherent plan
   aimed at the wrong outcome is not a pass.

Then ask question 1 **only against the derived mandated outcome**.

On **`finished work`** passes over code or engine surfaces: consume
prior design-correspondence evidence on the verify/plan artifacts. If
this tree has a design instrument (see LOCALISE below), cite its
dispositions; otherwise cite the plan/verify walk against telos and
campaign owners. If that evidence is missing for a mechanism the diff
touches, the pass is a **non-run** for question 1 — internal consistency
and green checks do not substitute.

<!-- LOCALISE: finished-work design instrument for this tree -->
- *(template seed: no dedicated design instrument — hunt performs steps 1–4; finished work must cite plan/verify design walk or non-run.)*

## The norms it checks against

<!-- LOCALISE: the owners of this tree's rules, in authority order.
     Cite; do not restate. -->
- Apex: [`docs/PURPOSE.md`](../../../docs/PURPOSE.md) (level 0), then
  [`CLAUDE.md`](../../../CLAUDE.md) (level 1)
- Capability issuance:
  [`capability_ports.json`](../../../capability_ports.json);
  constructive form
  [`../cut/references/capability_port.md`](../cut/references/capability_port.md)
- Anti-pattern index: [`docs/ROT.md`](../../../docs/ROT.md)

General good practice is the same test without a local name: an
unsupported assumption, a seam that will break a neighbour, a check
that cannot go red, a name that means two things.

## What it is not

- Not a second opinion on whether the work should exist.
- Not a rinse of the prose.
- Not a loop until the reader comes back empty.
- Not Zeno's tortoise: each pass finding a smaller remaining issue is
  the author prompting wrong, not the reader doing their job.
- Not a doctrine engine. A finding that should change how the tree
  works lands as an owner-authorized edit, with provenance — never as
  law smuggled into a report.
- Not something the author can do. A self-read is not a check.
- Not a consistency rinse of the author's framing. Question 1 against
  the dispatch sentence alone is a non-run.

## Dispatch

How an agent launches the independent reader, how many times, and what
shape the return must have, is [`SKILL.md`](SKILL.md).
