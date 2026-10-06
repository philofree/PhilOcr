// Package verifycmd is the health gate for every agent surface: canonical
// store, symlink farms, per-tool registrations, hook executability, hook
// output, and instruction files. Green exit means the five-tool fleet is
// wired; anything else is a finding, not a warning.
package verifycmd

import (
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"strings"

	"github.com/philofree/PhilOcr/tools/agentctl/agentlib"
	"github.com/philofree/PhilOcr/tools/agentctl/portcmd"
	"github.com/philofree/PhilOcr/tools/agentctl/predicatecmd"
)

type checker struct {
	root   string
	passed int
	failed int
}

func (c *checker) pass(format string, args ...any) {
	c.passed++
	fmt.Printf("PASS  "+format+"\n", args...)
}

func (c *checker) fail(format string, args ...any) {
	c.failed++
	fmt.Printf("FAIL  "+format+"\n", args...)
}

// Run is the CLI entry point.
func Run(args []string) int {
	fs := flag.NewFlagSet("verify", flag.ExitOnError)
	root := fs.String("root", ".", "repo root")
	_ = fs.Parse(args)

	abs, err := filepath.Abs(*root)
	if err != nil {
		fmt.Fprintf(os.Stderr, "verify: %v\n", err)
		return 2
	}
	c := &checker{root: abs}
	c.checkInstructionFiles()
	c.checkCanonicalStore()
	c.checkFarms()
	c.checkRegistrations()
	c.checkKimiHookLink()
	c.checkHookScriptsRun()
	c.checkParsimonyGate()
	c.checkCapabilityPorts()
	c.checkPredicates()
	c.checkDocumentaryBaseline()

	fmt.Printf("verify: %d passed, %d failed\n", c.passed, c.failed)
	if c.failed > 0 {
		return 1
	}
	return 0
}

func (c *checker) checkInstructionFiles() {
	claude := filepath.Join(c.root, "CLAUDE.md")
	if data, err := os.ReadFile(claude); err != nil || len(bytes.TrimSpace(data)) < 200 {
		c.fail("CLAUDE.md missing or too thin to be the authority")
	} else {
		c.pass("CLAUDE.md present (authority, %d bytes)", len(data))
	}
	for _, f := range []string{"AGENTS.md", "KIMI.md", "GEMINI.md"} {
		data, err := os.ReadFile(filepath.Join(c.root, f))
		switch {
		case err != nil:
			c.fail("%s missing (thin pointer twin)", f)
		case !strings.Contains(string(data), "CLAUDE.md is the authority"):
			c.fail("%s lacks the authority pointer line", f)
		default:
			c.pass("%s is a thin pointer to CLAUDE.md", f)
		}
	}
	if _, err := os.Stat(filepath.Join(c.root, ".kimi", "posture.md")); err != nil {
		c.fail(".kimi/posture.md missing")
	} else {
		c.pass(".kimi/posture.md present")
	}
	if _, err := os.Stat(filepath.Join(c.root, "campaigns", "graph.yaml")); err != nil {
		c.fail("campaigns/graph.yaml missing (the sole authored planning graph)")
	} else {
		c.pass("campaigns/graph.yaml present")
	}
	if data, err := os.ReadFile(filepath.Join(c.root, "docs", "PURPOSE.md")); err != nil {
		c.fail("docs/PURPOSE.md missing (the telos)")
	} else if !strings.Contains(string(data), "## Say it to a nine-year-old") {
		c.fail("docs/PURPOSE.md has no \"Say it to a nine-year-old\" section — the plain-language anchor every turn is held against (session_start.sh, posture_check.sh)")
	} else {
		c.pass("docs/PURPOSE.md carries the \"Say it to a nine-year-old\" anchor")
	}
}

func (c *checker) checkCanonicalStore() {
	skills, err := agentlib.CanonicalSkillNames(c.root)
	if err != nil || len(skills) == 0 {
		c.fail("canonical store .claude/skills/ empty or missing")
		return
	}
	c.pass("canonical store: %d skills (%s)", len(skills), strings.Join(skills, ", "))
	for _, s := range skills {
		path := filepath.Join(agentlib.CanonicalSkillsDir(c.root), s, "SKILL.md")
		data, err := os.ReadFile(path)
		if err != nil {
			c.fail("%s unreadable: %v", rel(c.root, path), err)
			continue
		}
		if err := agentlib.CheckFrontmatter(data); err != nil {
			c.fail("%s frontmatter: %v", rel(c.root, path), err)
			continue
		}
		c.pass("%s frontmatter: name+description only", rel(c.root, path))
	}
}

func (c *checker) checkFarms() {
	skills, _ := agentlib.CanonicalSkillNames(c.root)
	for _, farm := range agentlib.Farms() {
		dir := filepath.Join(c.root, filepath.FromSlash(farm.Dir))
		entries, err := os.ReadDir(dir)
		if err != nil {
			c.fail("%s missing (run: go run ./tools/agentctl link)", farm.Dir)
			continue
		}
		ok := true
		seen := map[string]bool{}
		for _, e := range entries {
			name := e.Name()
			seen[name] = true
			p := filepath.Join(dir, name)
			fi, err := os.Lstat(p)
			if err != nil {
				ok = false
				c.fail("%s/%s: %v", farm.Dir, name, err)
				continue
			}
			if fi.Mode()&os.ModeSymlink == 0 {
				ok = false
				c.fail("%s/%s is a REAL copy, not a symlink — copied skills drift; delete it and run agentctl link", farm.Dir, name)
				continue
			}
			want := agentlib.FarmTarget(farm, name)
			got, _ := os.Readlink(p)
			if got != want {
				ok = false
				c.fail("%s/%s points at %s, want %s", farm.Dir, name, got, want)
				continue
			}
			if _, err := os.Stat(p); err != nil {
				ok = false
				c.fail("%s/%s dangling (%v)", farm.Dir, name, err)
			}
		}
		for _, s := range skills {
			if !seen[s] {
				ok = false
				c.fail("%s/%s missing (run: go run ./tools/agentctl link)", farm.Dir, s)
			}
		}
		if ok {
			c.pass("%s farm: %d symlinks, all resolve (%s)", farm.Dir, len(skills), farm.For)
		}
	}
}

// registration shapes, one per tool.

type claudeSettings struct {
	Hooks map[string][]struct {
		Hooks []struct {
			Type    string `json:"type"`
			Command string `json:"command"`
		} `json:"hooks"`
	} `json:"hooks"`
}

type zcodeConfig struct {
	Hooks struct {
		Enabled bool `json:"enabled"`
		Events  map[string][]struct {
			Hooks []struct {
				Type      string `json:"type"`
				Command   string `json:"command"`
				TimeoutMs int    `json:"timeoutMs"`
			} `json:"hooks"`
		} `json:"events"`
	} `json:"hooks"`
	MCP struct {
		Servers map[string]json.RawMessage `json:"servers"`
	} `json:"mcp"`
}

type codexHooks struct {
	Hooks map[string][]struct {
		Hooks []struct {
			Type    string `json:"type"`
			Command string `json:"command"`
		} `json:"hooks"`
	} `json:"hooks"`
}

type cursorHooks struct {
	Version int `json:"version"`
	Hooks   map[string][]struct {
		Command string `json:"command"`
		Matcher string `json:"matcher"`
		Timeout int    `json:"timeout"`
	} `json:"hooks"`
}

func readJSON(path string, into any) error {
	data, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	return json.Unmarshal(data, into)
}

// commandPath resolves a hook command string to a repo file. Handles the
// $CLAUDE_PROJECT_DIR prefix, quoted absolute paths (Codex), interpreter
// prefixes (Cursor: "sh path"), and the template's {{REPO_ROOT}} token.
func (c *checker) commandPath(cmd string) string {
	cmd = agentlib.ExpandTemplateTokens(cmd, c.root)
	cmd = strings.Trim(strings.TrimSpace(cmd), `'"`)
	fields := strings.Fields(cmd)
	try := []string{strings.Join(fields, " ")}
	if len(fields) > 1 {
		interpreters := map[string]bool{"sh": true, "bash": true, "zsh": true, "dash": true, "env": true, "python3": true, "python": true, "node": true}
		if interpreters[fields[0]] {
			try = append(try, fields[1])
		}
	}
	for _, t := range try {
		t = strings.Trim(t, `'"`)
		t = strings.ReplaceAll(t, "$CLAUDE_PROJECT_DIR", c.root)
		if !filepath.IsAbs(t) {
			t = filepath.Join(c.root, t)
		}
		if fi, err := os.Stat(t); err == nil && !fi.IsDir() {
			return t
		}
	}
	return ""
}

func (c *checker) hookExecutable(path string) bool {
	fi, err := os.Stat(path)
	return err == nil && fi.Mode().Perm()&0o111 != 0
}

type regCmd struct {
	event string
	cmd   string
}

func (c *checker) checkRegisteredCommands(source string, commands []regCmd) {
	for _, rc := range commands {
		p := c.commandPath(rc.cmd)
		switch {
		case p == "":
			c.fail("%s [%s] registers %q — target not found", source, rc.event, rc.cmd)
		case !c.hookExecutable(p):
			c.fail("%s [%s] → %s lacks the executable bit (chmod +x)", source, rc.event, rel(c.root, p))
		default:
			c.pass("%s [%s] → %s", source, rc.event, rel(c.root, p))
		}
	}
}

func (c *checker) checkRegistrations() {
	// Claude
	var cs claudeSettings
	if err := readJSON(filepath.Join(c.root, ".claude", "settings.json"), &cs); err != nil {
		c.fail(".claude/settings.json: %v", err)
	} else {
		var cmds []regCmd
		for event, groups := range cs.Hooks {
			for _, g := range groups {
				for _, h := range g.Hooks {
					cmds = append(cmds, regCmd{event, h.Command})
				}
			}
		}
		if len(cmds) == 0 {
			c.fail(".claude/settings.json registers no hooks")
		} else {
			c.checkRegisteredCommands(".claude/settings.json", cmds)
		}
	}

	// ZCode
	var zc zcodeConfig
	if err := readJSON(filepath.Join(c.root, ".zcode", "config.json"), &zc); err != nil {
		c.fail(".zcode/config.json: %v", err)
	} else if !zc.Hooks.Enabled {
		c.fail(".zcode/config.json: hooks.enabled must be true for config-file hooks to run")
	} else {
		var cmds []regCmd
		for event, groups := range zc.Hooks.Events {
			for _, g := range groups {
				for _, h := range g.Hooks {
					cmds = append(cmds, regCmd{event, h.Command})
				}
			}
		}
		if len(cmds) == 0 {
			c.fail(".zcode/config.json registers no hook events")
		} else {
			c.checkRegisteredCommands(".zcode/config.json", cmds)
		}
	}

	// Codex
	var ch codexHooks
	if err := readJSON(filepath.Join(c.root, ".codex", "hooks.json"), &ch); err != nil {
		c.fail(".codex/hooks.json: %v", err)
	} else {
		var cmds []regCmd
		for event, groups := range ch.Hooks {
			for _, g := range groups {
				for _, h := range g.Hooks {
					cmds = append(cmds, regCmd{event, h.Command})
				}
			}
		}
		if len(cmds) == 0 {
			c.fail(".codex/hooks.json registers no hooks")
		} else {
			c.checkRegisteredCommands(".codex/hooks.json", cmds)
		}
	}

	// Cursor
	var cu cursorHooks
	cuPath := filepath.Join(c.root, ".cursor", "hooks.json")
	if _, err := os.Stat(cuPath); err == nil {
		if err := readJSON(cuPath, &cu); err != nil {
			c.fail(".cursor/hooks.json: %v", err)
		} else {
			var cmds []regCmd
			for event, hs := range cu.Hooks {
				for _, h := range hs {
					cmds = append(cmds, regCmd{event, h.Command})
				}
			}
			c.checkRegisteredCommands(".cursor/hooks.json", cmds)
		}
	}

	// Root MCP example (Claude + Cursor read .mcp.json when renamed in)
	if data, err := os.ReadFile(filepath.Join(c.root, ".mcp.json")); err == nil {
		var v any
		if err := json.Unmarshal(data, &v); err != nil {
			c.fail(".mcp.json does not parse: %v", err)
		} else {
			c.pass(".mcp.json parses")
		}
	}
}

func (c *checker) checkKimiHookLink() {
	p := filepath.Join(c.root, ".kimi", "hooks", "posture_check.sh")
	fi, err := os.Lstat(p)
	if err != nil {
		c.fail(".kimi/hooks/posture_check.sh missing (run: go run ./tools/agentctl link)")
		return
	}
	if fi.Mode()&os.ModeSymlink == 0 {
		c.fail(".kimi/hooks/posture_check.sh is a real file — must be a symlink into .claude/hooks/")
		return
	}
	if _, err := os.Stat(p); err != nil {
		c.fail(".kimi/hooks/posture_check.sh dangling: %v", err)
		return
	}
	c.pass(".kimi/hooks/posture_check.sh → .claude/hooks/posture_check.sh")
}

func (c *checker) checkHookScriptsRun() {
	for _, name := range []string{"session_start.sh", "posture_check.sh"} {
		p := filepath.Join(c.root, ".claude", "hooks", name)
		cmd := exec.Command(p)
		cmd.Dir = c.root
		cmd.Stdin = strings.NewReader("{}")
		var out bytes.Buffer
		cmd.Stdout = &out
		cmd.Stderr = io.Discard
		if err := cmd.Run(); err != nil {
			c.fail("%s does not run clean: %v", name, err)
			continue
		}
		var payload struct {
			HookSpecificOutput struct {
				HookEventName     string `json:"hookEventName"`
				AdditionalContext string `json:"additionalContext"`
			} `json:"hookSpecificOutput"`
		}
		if err := json.Unmarshal(bytes.TrimSpace(out.Bytes()), &payload); err != nil {
			c.fail("%s stdout is not valid JSON: %v", name, err)
			continue
		}
		if payload.HookSpecificOutput.AdditionalContext == "" {
			c.fail("%s emits no hookSpecificOutput.additionalContext", name)
			continue
		}
		c.pass("%s runs clean, emits valid JSON context", name)
	}
}

// checkParsimonyGate answers one question: is the gate actually firing?
//
// core.hooksPath is LOCAL git config. It is never committed, so a fresh
// clone of any repo seeded from this template has .githooks/ present and
// completely inert. That is the worst state available — a gate that reads
// as protection and is not — so an unarmed repo FAILS here rather than
// passing quietly. One command fixes it, and the failure prints it.
func (c *checker) checkParsimonyGate() {
	hook := filepath.Join(c.root, ".githooks", "commit-msg")
	fi, err := os.Stat(hook)
	switch {
	case err != nil:
		c.fail(".githooks/commit-msg missing — the parsimony gate is the one check on code growth")
		return
	case fi.Mode().Perm()&0o111 == 0:
		c.fail(".githooks/commit-msg is not executable (chmod +x) — git will skip it silently")
		return
	}
	c.pass(".githooks/commit-msg present and executable")

	if _, err := os.Stat(filepath.Join(c.root, ".githooks", "selftest")); err != nil {
		c.fail(".githooks/selftest missing — a gate nobody has watched fail is not known to work")
	} else {
		c.pass(".githooks/selftest present (sh .githooks/selftest)")
	}

	out, err := exec.Command("git", "-C", c.root, "config", "--get", "core.hooksPath").Output()
	got := strings.TrimSpace(string(out))
	if err != nil || got != ".githooks" {
		c.fail("core.hooksPath is %q, want \".githooks\" — the gate is DORMANT. Arm it:  git config core.hooksPath .githooks", got)
		return
	}
	c.pass("core.hooksPath = .githooks (the gate is armed for every agent that commits)")
}

// checkCapabilityPorts runs the issuance join: every capability named, every
// name honest. Doctrine: .claude/skills/cut/references/capability_port.md.
func (c *checker) checkCapabilityPorts() {
	errs := portcmd.Check(c.root)
	if len(errs) == 0 {
		c.pass("capability ports: every dispatched command is named and every row is honest")
		return
	}
	for _, e := range errs {
		c.fail("capability port: %s", e)
	}
}

// checkPredicates audits the baptised vocabulary: one signifier, one
// referent, and no retired word left standing beside the one that replaced
// it. The linguistic half of referent conservation.
func (c *checker) checkPredicates() {
	errs := predicatecmd.Check(c.root)
	if len(errs) == 0 {
		c.pass("predicates: registry honest, no retired signifier in the tree")
		return
	}
	for _, e := range errs {
		c.fail("predicate: %s", e)
	}
}

func rel(root, p string) string {
	r, err := filepath.Rel(root, p)
	if err != nil {
		return p
	}
	return r
}

// checkDocumentaryBaseline refuses a repository whose document contract has
// no baseline. init clears the template's own adoption_revision rather than
// let a seeded repository inherit a commit from another history — a pin that
// makes `epitomikon profile` fail on a revision the operator has never seen.
// Until it is pinned here, nothing measures this repository's documents.
func (c *checker) checkDocumentaryBaseline() {
	path := filepath.Join(c.root, ".epitomikon.json")
	b, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			return // a repository may decline the documentary contract
		}
		c.fail(".epitomikon.json: %v", err)
		return
	}
	var manifest struct {
		AdoptionRevision string `json:"adoption_revision"`
	}
	if err := json.Unmarshal(b, &manifest); err != nil {
		c.fail(".epitomikon.json: %v", err)
		return
	}
	if manifest.AdoptionRevision == "" {
		c.fail(".epitomikon.json has no adoption_revision — nothing measures this repository's documents.\n" +
			"      `agentctl init` pins it to the commit it seeds. Restore it with the\n" +
			"      commit this repository starts from, once one exists:\n" +
			"        git rev-parse HEAD   # then write it into .epitomikon.json")
		return
	}
	c.pass(".epitomikon.json pins a documentary baseline")
}
