// Package agentlib holds the shared primitives of the agent surface system:
// the token set, the symlink-farm map, and the SKILL.md frontmatter contract.
package agentlib

import (
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

// Token names replaced by `agentctl init`. They appear in template files as
// {{NAME}}; init stamps real values so the seeded repo never carries them.
const (
	TokenProjectName = "PROJECT_NAME"
	TokenPackageDir  = "PACKAGE_DIR"
	TokenModulePath  = "MODULE_PATH"
	TokenPurpose     = "ONE_LINE_PURPOSE"
	TokenRepoRoot    = "REPO_ROOT" // absolute path of the seeded repo
)

// TokenMap builds the replacement table for init.
func TokenMap(name, packageDir, module, purpose, repoRoot string) map[string]string {
	return map[string]string{
		TokenProjectName: name,
		TokenPackageDir:  packageDir,
		TokenModulePath:  module,
		TokenPurpose:     purpose,
		TokenRepoRoot:    repoRoot,
	}
}

// ReplaceAll applies every token to s.
func ReplaceAll(s string, tokens map[string]string) string {
	for k, v := range tokens {
		s = strings.ReplaceAll(s, "{{"+k+"}}", v)
	}
	return s
}

// LeftoverTokens reports which tokens still appear unreplaced in s.
func LeftoverTokens(s string) []string {
	var found []string
	for _, k := range []string{TokenProjectName, TokenPackageDir, TokenModulePath, TokenPurpose, TokenRepoRoot} {
		if strings.Contains(s, "{{"+k+"}}") {
			found = append(found, k)
		}
	}
	return found
}

// Farm is one per-tool skills directory of symlinks into the canonical store.
// Ups is the directory depth of the farm relative to repo root (used to build
// relative symlink targets).
type Farm struct {
	Dir string // e.g. ".zcode/skills"
	Ups int    // e.g. 2 → target ../../.claude/skills/<name>
	For string // tool name, for error messages
}

// Farms returns every symlink farm, in stable order.
func Farms() []Farm {
	return []Farm{
		{Dir: ".zcode/skills", Ups: 2, For: "ZCode"},
		{Dir: ".agents/skills", Ups: 2, For: "cross-tool (.agents)"},
		{Dir: ".kimi/skills", Ups: 2, For: "Kimi"},
		{Dir: ".cursor/skills", Ups: 2, For: "Cursor"},
	}
}

// FarmTarget computes the relative symlink target for a skill in a farm.
func FarmTarget(f Farm, skill string) string {
	return strings.Repeat("../", f.Ups) + ".claude/skills/" + skill
}

// CanonicalSkillsDir is the single source of truth for skills.
func CanonicalSkillsDir(root string) string { return filepath.Join(root, ".claude", "skills") }

// CanonicalSkillNames lists skill directory names under .claude/skills/ that
// carry a SKILL.md (hidden dirs and dirs without SKILL.md are ignored).
func CanonicalSkillNames(root string) ([]string, error) {
	entries, err := os.ReadDir(CanonicalSkillsDir(root))
	if err != nil {
		return nil, err
	}
	var names []string
	for _, e := range entries {
		if !e.IsDir() || strings.HasPrefix(e.Name(), ".") || strings.HasPrefix(e.Name(), "_") {
			continue
		}
		if _, err := os.Stat(filepath.Join(CanonicalSkillsDir(root), e.Name(), "SKILL.md")); err == nil {
			names = append(names, e.Name())
		}
	}
	sort.Strings(names)
	return names, nil
}

// CheckFrontmatter enforces the one-file-everywhere contract: a SKILL.md's
// YAML frontmatter may contain exactly `name` and `description` — nothing
// else. Extra keys (Claude's `metadata:` blocks) are what force Kimi-side
// copies and drift; the check keeps the symlink farms legal.
func CheckFrontmatter(data []byte) error {
	lines := strings.Split(string(data), "\n")
	if len(lines) == 0 || strings.TrimRight(lines[0], "\r") != "---" {
		return fmt.Errorf("no frontmatter block (expected leading '---')")
	}
	var keys []string
	closed := false
	for _, raw := range lines[1:] {
		l := strings.TrimRight(raw, "\r")
		if l == "---" || l == "..." {
			closed = true
			break
		}
		if l == "" {
			continue
		}
		// Indented lines are continuations of the previous key's value.
		if l[0] == ' ' || l[0] == '\t' {
			continue
		}
		key := l
		if i := strings.IndexByte(l, ':'); i >= 0 {
			key = l[:i]
		}
		keys = append(keys, strings.TrimSpace(key))
	}
	if !closed {
		return fmt.Errorf("frontmatter not terminated (missing closing '---')")
	}
	has := func(k string) bool {
		for _, key := range keys {
			if key == k {
				return true
			}
		}
		return false
	}
	for _, key := range keys {
		if key != "name" && key != "description" {
			return fmt.Errorf("frontmatter key %q not allowed — name and description only (one file must pass every tool's parser)", key)
		}
	}
	if !has("name") {
		return fmt.Errorf("frontmatter missing 'name'")
	}
	if !has("description") {
		return fmt.Errorf("frontmatter missing 'description'")
	}
	return nil
}

// ExpandTemplateTokens makes registration files checkable inside the template
// itself: an unreplaced {{REPO_ROOT}} stands for the repo root under test.
func ExpandTemplateTokens(s, root string) string {
	return ReplaceAll(s, map[string]string{TokenRepoRoot: root})
}
