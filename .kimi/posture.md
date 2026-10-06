---
description: What an answer has to survive here before it is said — pointers only
---

# Before you answer from what you can see

Pointer only. The authority is [`CLAUDE.md`](../CLAUDE.md) — read it first,
especially the routing table ("Where to look"). Language law:
[`docs/GOVERNANCE.md`](../docs/GOVERNANCE.md) § The language law.

How a session runs: [`CLAUDE.md` § Operating posture](../CLAUDE.md). The
planning graph is [`campaigns/graph.yaml`](../campaigns/graph.yaml); derive its
frontier with Eustratikon. Known
failure modes: [`docs/ROT.md`](../docs/ROT.md).

Kimi skills: [`.kimi/skills/`](skills/) — symlinks into
[`.claude/skills/`](../.claude/skills/), one per entry there. A write
through a symlink lands on the canonical file.

Every-turn hook: [`.kimi/hooks/posture_check.sh`](hooks/posture_check.sh) —
wiring lives in the user config (`~/.kimi-code/config.toml`), added by
`agentctl init`; the script self-scopes by cwd and exits silently in every
other repository.

Whenever an empty result is the finding, prove the instrument ran. A gap
named is worth more than an answer manufactured to close it.
