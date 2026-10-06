#!/bin/sh
# UserPromptSubmit hook — session posture only. Points at owners; carries no
# rule text, no findings, no counts, no status.
#
# Registered by:
#   Claude  .claude/settings.json      ($CLAUDE_PROJECT_DIR prefix)
#   ZCode   .zcode/config.json         (relative path)
#   Codex   .codex/hooks.json          (absolute path, stamped by agentctl init)
#   Kimi    ~/.kimi-code/config.toml   (user-level — hence the self-scope guard)
#
# Maintenance contract: hooks/README.md. Gate: go run ./tools/agentctl verify

repo_root=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd)

# --- self-scope: Kimi fires user-registered hooks in every session ---
case "$PWD" in "$repo_root"|"$repo_root"/*) ;; *) exit 0 ;; esac
payload=$(cat 2>/dev/null || true)
hook_cwd=$(printf '%s' "$payload" | sed -n 's/.*"cwd"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)
if [ -n "$hook_cwd" ]; then
  case "$hook_cwd" in "$repo_root"|"$repo_root"/*) ;; *) exit 0 ;; esac
fi

# --- retired-phrase guard (optional) ------------------------------------
# When a procedure retires, grep the surfaces that could still advertise it
# and refuse the turn (exit 1) naming the file. Keep the list short; the
# guard is a tripwire, not a linter.
#
# hits=$(grep -rniE 'the old build command|<retired phrase>' \
#   "$repo_root/CLAUDE.md" "$repo_root/docs" "$repo_root/.claude/skills" \
#   "$repo_root/.cursor/rules" 2>/dev/null || true)
# if [ -n "$hits" ]; then
#   printf 'posture check refused: active documentation advertises a retired procedure:\n%s\n' "$hits" >&2
#   exit 1
# fi

cat <<'JSON'
{
  "continue": true,
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": "[posture — every turn]\n\nCLAUDE.md is the authority (thin pointers: AGENTS.md, KIMI.md, GEMINI.md). A conflict between documents is a finding — fix the wrong document, never average.\n\nLanguage law: docs/GOVERNANCE.md § The language law.\n\nDefault direction is subtractive: .claude/skills/cut. Salvage-impossible knots: .claude/skills/reckless-cut. Verify: .claude/skills/verify. Refute: .claude/skills/adversarial. Coin before naming: .claude/skills/baptise. Close: .claude/skills/close.\n\nBefore non-trivial work: hold it against docs/PURPOSE.md § Say it to a nine-year-old. If what you're about to do would not fit inside that paragraph, that is a finding — say so before continuing, don't quietly widen the paragraph to fit the work.\n\nOwners: CLAUDE.md (routing) · docs/PURPOSE.md (telos) · docs/GOVERNANCE.md (document + language law) · docs/ROT.md (rot) · campaigns/graph.yaml (planning source) · Eustratikon (audit and derived frontier) · PREDICATES.json (vocabulary join) · the one live HANDOVER_*.\n\nA gap named beats an answer manufactured to close it."
  }
}
JSON
