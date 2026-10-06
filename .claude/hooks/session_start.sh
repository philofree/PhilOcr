#!/bin/sh
# SessionStart hook — the orientation block that fires once when a session
# opens, before anyone has typed anything. Addressed to the USER: the plain
# anchor, the handover, the campaign frontier, the tree state. ~6 lines max.
#
# Reads: docs/PURPOSE.md § Say it to a nine-year-old, the live HANDOVER_*
# when one exists, campaigns/graph.yaml pointer, git status. `/open` runs the
# pinned Eustratikon tool; this hook never performs a network/tool build.
# Never restates rule text — it points at owners (see CLAUDE.md). The one
# exception is the anchor paragraph itself: it is shown, not pointed at,
# because it is the thing every turn gets held against.
# Maintenance contract: hooks/README.md. Gate: go run ./tools/agentctl verify

repo_root=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd)

# Self-scope: no-op outside this project (Kimi registers hooks user-wide).
case "$PWD" in "$repo_root"|"$repo_root"/*) ;; *) exit 0 ;; esac

name=$(basename "$repo_root")

# --- the plain-language anchor (docs/PURPOSE.md § Say it to a nine-year-old) ---
anchor=$(awk '/^## Say it to a nine-year-old/{f=1;next} /^## /{f=0} f' "$repo_root/docs/PURPOSE.md" 2>/dev/null \
  | tr '\n' ' ' | sed 's/  */ /g; s/^ *//; s/ *$//')
[ -z "$anchor" ] && anchor='(docs/PURPOSE.md has no "Say it to a nine-year-old" section yet)'
if [ "${#anchor}" -gt 320 ]; then
  anchor=$(printf '%s' "$anchor" | cut -c1-300)
  anchor="${anchor}…"
fi
# Escape backslashes and quotes now — this line carries free prose, unlike
# the extracted headings below, and is the one field likely to hold a ".
anchor=$(printf '%s' "$anchor" | sed 's/\\/\\\\/g; s/"/\\"/g')

# --- the live handover (none is lawful for an empty campaign graph) ---
hv=$(ls "$repo_root"/HANDOVER_*.md 2>/dev/null | grep -v HANDOVER_TEMPLATE.md | sort | tail -1)
hvc=$(ls "$repo_root"/HANDOVER_*.md 2>/dev/null | grep -v HANDOVER_TEMPLATE.md | wc -l | tr -d ' ')

if [ -n "$hv" ]; then
  frontier=$(head -5 "$hv" | grep -E '^# ' | head -1 | sed 's/^# *//')
else
  frontier="(no live handover — run the campaign frontier; an empty graph needs none)"
fi

# --- campaign source pointer; /open runs the pinned interpreter explicitly ---
campaign_state="campaign graph: run go tool eustratikon campaign-frontier ."

# --- tree state ---
dirty=$(git -C "$repo_root" status --porcelain 2>/dev/null | grep -c .)
tree="clean tree"
[ "${dirty:-0}" -gt 0 ] && tree="UNCOMMITTED ($dirty changed)"

warn=""
[ "$hvc" -gt 1 ] && warn=" · ⚠ $hvc handovers live (expected exactly 1)"

ctx="[$name] session open
This repo, in one breath: $anchor
Frontier: $frontier
Work: $campaign_state · State: $tree$warn
Say 'start' (or describe the work) and I run /open first. One-off question: just ask."

# Escape real newlines as literal \n — the payload must be one JSON string.
ctx_escaped=$(printf '%s' "$ctx" | awk 'NR>1{printf "\\n"} {printf "%s", $0}')

printf '{"continue":true,"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%s"}}\n' "$ctx_escaped"
