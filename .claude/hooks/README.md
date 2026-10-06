# Hooks — the maintenance contract

| | |
|---|---|
| **Title** | `.claude/hooks/README.md` — the hook maintenance contract |
| **Status** | Binding |
| **Authority level** | 3 — a reference of [`../../CLAUDE.md`](../../CLAUDE.md), which owns agent work |
| **Scope** | Every hook shipped in this template and in a repository cloned from it |
| **Relationship-to** | Serves [`../../CLAUDE.md`](../../CLAUDE.md); arming is stated by [`../../docs/ROT.md`](../../docs/ROT.md). Restates neither |
| **Document class** | procedure |
| **Contract** | `epitomikon/document-contract/v1` |

Two hooks, one canonical location. Every tool's registration points at these
files; nothing else runs per-turn.

| Hook | Event | What it does | What it never does |
|---|---|---|---|
| `session_start.sh` | SessionStart | ~5-line orientation addressed to the user: optional live handover, Eustratikon frontier command, tree state | Restate rule text; carry copied status; invent a handover for an empty graph |
| `posture_check.sh` | UserPromptSubmit | One posture block per turn: authority pointer, language law, operating bar, owners | Rule text, findings, counts, status |

## Registration map (who points where)

| Tool | File | Path form |
|---|---|---|
| Claude | `.claude/settings.json` | `$CLAUDE_PROJECT_DIR/.claude/hooks/<script>` |
| ZCode | `.zcode/config.json` | `.claude/hooks/<script>` (relative, `hooks.enabled: true`) |
| Codex | `.codex/hooks.json` | absolute — stamped by `agentctl init`; one-time trust prompt on first fire |
| Kimi | `~/.kimi-code/config.toml` | absolute, user-level — hence the **self-scope guard** in both scripts (they exit silently outside this repo) |
| Cursor | `.cursor/hooks.json` | `sh .claude/hooks/session_start.sh` |

## When to update a hook

- A new **owner** file is created or an old one retires (the Owners line).
- A procedure **retires** — extend the retired-phrase guard in
  `posture_check.sh` so the turn is refused while any surface still
  advertises it.
- The orientation block stops matching what a session actually needs.

## How to update

Hooks are primary artefacts: **retire-or-rewrite, never amend-in-place.**
Replace the payload wholesale; do not accrete lines. After any change:

```sh
go run ./tools/agentctl verify   # runs both hooks and validates their JSON
```

A hook that fails validation is a red gate — fix before commit.

## Why shell (and not Go)

Hooks must fire instantly on a fresh clone with nothing built. They contain
no logic worth compiling: resolve root, self-scope, emit a fixed payload.
All real logic lives in `tools/agentctl` (Go).
