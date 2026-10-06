# How this template works — the dummy's guide

| | |
|---|---|
| **Title** | dummies_guide/how_this_template_works.md — the whole kit in plain words |
| **Status** | Explanatory — this file binds nothing |
| **Authority level** | none — it carries no rule of its own |
| **Scope** | Anyone meeting this folder for the first time |
| **Relationship-to** | Explains README.md and CLAUDE.md; if this file disagrees with them, or with docs/PURPOSE.md, THEY win and this file is the one to fix |
| **Document class** | orientation |
| **Contract** | `epitomikon/document-contract/v1` |

## What is this thing?

This folder is a starter house for computer helpers. You copy the
house into an empty plot. Then every helper — Claude, Kimi, Codex,
ZCode, Cursor, and any new one — reads the SAME rules through their
own door.

It does not do your real job. It is the house. You still have to
say what the house is for.

## One boss page

There is one page that tells helpers how to work here:
[`CLAUDE.md`](../CLAUDE.md). A few other pages exist only because
some helpers look for their own filename. Those pages say "go read
the boss page." They are not a second boss.

If two pages disagree, that is a finding. You fix the wrong page.
You never split the difference.

## The why-page, and the little paragraph

Why the house exists lives on a different page:
[`docs/PURPOSE.md`](../docs/PURPOSE.md). That page is above every
other page. Everything else serves it.

On that page there is a short bit called **Say it to a nine-year-old**.
That bit is the test, not a summary. Before anyone does a big job
they hold the job against that paragraph: does this still serve
THAT? If the job would not fit, you say so. You do not secretly
make the paragraph bigger so the job fits.

A tiny helper reads that paragraph at the start of every sitting
and shows it again, so nobody can forget what the house is for.

If you cannot say the job in that paragraph, either you do not
understand it yet, or it needs to be more than one house.

## One cupboard, many windows

The helpers' tools live in ONE cupboard: `.claude/skills/`. The
other helpers get a window that looks into that same cupboard. A
window is not a copy. Write through the window and you write in
the cupboard. Make a copy beside the window and the copies will
drift apart — and the health check will fail.

The same idea holds for the little start-of-sitting scripts: one
copy, many doorbells.

Owner: [README.md § Fleet](../README.md).

## The map of work

There is exactly one drawn map of jobs:
[`campaigns/graph.yaml`](../campaigns/graph.yaml). Lines marked `needs`
mean one job truly cannot start before another. Lines marked `after` only say
which job we would rather do first. A separate tool called Eustratikon reads
the map, checks the evidence, and tells you what is ready. It never writes a
second list.

When a job is finished, its status is always called `done`.

When you copy this house, the map is empty. The house does not pretend to
know the new project's first job. When real work begins, that project draws
its first job and names what the job is trying to keep steady.

The map may hold several big jobs for later, but only one big job can be marked
as the one happening now. Smaller jobs inside it may happen together. This
stops the house being pulled in two directions at once.

## The robot's good manners

- Before the robot says "it works," it must RUN the check and READ
  what came out. "Should pass" is not passing.
- Before the robot adds a toy, it asks which toy to throw away. A
  house where nothing is ever thrown away fills up until you cannot
  find the door.
- Before the robot makes up a new word for a kind of thing, it
  checks the word-book. One thing, one name. Two names for one dog,
  and nobody knows which dog you mean. On a fix, the wrong word is
  thrown away — not left beside the right one.
- When a sitting ends, the robot reconciles the work map and leaves exactly
  one note for tomorrow. It writes a diary entry (`work_reports/`) only when
  useful evidence would otherwise disappear. Two
  notes for tomorrow is a mess.

Owners: CLAUDE.md § Operating posture; [`docs/ROT.md`](../docs/ROT.md);
[`PREDICATES.json`](../PREDICATES.json).

## The lock on the door

When anyone saves a change, they must write down what they threw
away. The lock on the door checks. It is the same lock for every
helper, because it sits on the door itself, not in any helper's
private settings.

- If you say you added something, you must name what the new thing
  made old — and that old thing must really shrink.
- If you say you only fixed something, you may not mint a new file.
- If you say you cut, the pile must get smaller.

A lock that is sitting there but not turned on is a pretend lock.
The health check fails until the lock is really on.

Owner: [`docs/ROT.md`](../docs/ROT.md) § The parsimony contract.

## Name the job before you build it

A button the robot can press that has no name on the roster is a
job nobody owns. Before you build a new button you write: who owns
it, what it promises, and how you talk to it. Then you put a row
on the roster.

If you cannot name the single owner and the front door, you do not
have a job. You have knitting: rooms joined by holes smashed
through the walls instead of doors.

Owner: [`capability_ports.json`](../capability_ports.json).

## Sister houses

Some houses belong to one family. They share a dictionary that
lives at the family's main house. This house only keeps a
photocopy. You do not write on the photocopy. You write at the
main house, then take a new photocopy.

Owner: [`../eukoine/.eukoine/WRITE_ACCESS.md`](../../eukoine/.eukoine/WRITE_ACCESS.md).

## Copying the house

There is a helper command that copies this house into an empty
folder, writes your project's name on the door, and turns the
lock on. After that, YOU fill in the why-page. Until you do, the
house is a house with no "what we are for."

The helper copies the house itself. It does not copy a hidden second version,
and it does not bring this template's old jobs, notes, or diaries with it.

This page travels with the copy, because the house rules are the
same in every copy. The why-page is what you write new.

Owner: [README.md § Instantiate](../README.md).

## This page is not the law

If this page and an owner disagree, the owner wins and this page
is the one to fix. This page is so you can see the whole house at
once. It binds nothing.
