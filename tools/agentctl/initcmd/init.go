// Package initcmd instantiates a new repository from the template: copies the
// tree, stamps tokens, rewrites the Go module identity, rebuilds the symlink
// farms, and (unless declined) wires the Kimi user-level hook entry.
package initcmd

import (
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"strings"
	"time"

	"github.com/philofree/PhilOcr/tools/agentctl/agentlib"
	"github.com/philofree/PhilOcr/tools/agentctl/linkcmd"
	"github.com/philofree/PhilOcr/tools/agentctl/verifycmd"
)

// templateModule is this template's own module path; init rewrites it to the
// target's module in go.mod and in every import path.
const templateModule = "github.com/philofree/PhilOcr"

// textExts are the file extensions (and exact names) eligible for token
// replacement.
var (
	textExts = map[string]bool{
		".md": true, ".json": true, ".toml": true, ".yaml": true, ".yml": true,
		".mod": true, ".sh": true, ".go": true, ".mdc": true, ".example": true,
	}
	textNames = map[string]bool{"Makefile": true, ".gitignore": true}

	// skipRel are local/tool artefacts never copied into a seeded repo. The
	// tracked repository surfaces themselves are the template; there is no
	// second seed overlay.
	skipRel = []string{".git", "bin", "node_modules", ".DS_Store", ".specstory",
		".zcode/plans", ".claude/plans", ".claude/worktrees", ".cursor/plans", ".claude/skills/.metadata-registry.json"}
)

// Run is the CLI entry point: `agentctl init <target> [flags]`.
func Run(args []string) int {
	fs := flag.NewFlagSet("init", flag.ExitOnError)
	from := fs.String("from", ".", "template root (this repo)")
	name := fs.String("name", "", "project display name (default: target basename)")
	packageDir := fs.String("package-dir", "", "cmd/ directory name (default: sanitized name)")
	module := fs.String("module", "", "Go module path (default: package-dir)")
	purpose := fs.String("purpose", "One line describing why this repository exists — fill me in.", "one-line telos")
	noKimi := fs.Bool("no-kimi", false, "skip ~/.kimi-code/config.toml wiring")
	noCursor := fs.Bool("no-cursor", false, "drop .cursor/ from the seeded repo")
	git := fs.Bool("git", true, "git init the target if it is not already a repo")

	// Go's flag package stops at the first positional; allow flags after the
	// target (`init <target> -name …`) by consuming positionals as they block.
	var positional []string
	rest := args
	for {
		_ = fs.Parse(rest)
		if fs.NArg() == 0 {
			break
		}
		positional = append(positional, fs.Arg(0))
		rest = fs.Args()[1:]
	}

	if len(positional) != 1 {
		fmt.Fprintln(os.Stderr, "init: exactly one target directory required")
		return 2
	}
	target, _ := filepath.Abs(positional[0])
	fromAbs, err := filepath.Abs(*from)
	if err != nil || target == "" {
		fmt.Fprintf(os.Stderr, "init: bad paths: %v\n", err)
		return 2
	}
	if samePath(fromAbs, target) {
		fmt.Fprintln(os.Stderr, "init: target must differ from the template root")
		return 2
	}
	if entries, err := os.ReadDir(target); err == nil && len(entries) > 0 {
		fmt.Fprintf(os.Stderr, "init: %s exists and is not empty\n", target)
		return 2
	}

	projectName := *name
	if projectName == "" {
		projectName = filepath.Base(target)
	}
	pkgDir := *packageDir
	if pkgDir == "" {
		pkgDir = SanitizePackageDir(projectName)
	}
	modulePath := *module
	if modulePath == "" {
		modulePath = pkgDir
	}
	tokens := agentlib.TokenMap(projectName, pkgDir, modulePath, *purpose, target)

	fmt.Printf("init: seeding %s\n  name=%s package-dir=%s module=%s\n", target, projectName, pkgDir, modulePath)

	// 1. Copy the tree, replacing tokens in text files.
	nFiles, nLinks, err := copyTree(fromAbs, target, tokens, *noCursor)
	if err != nil {
		fmt.Fprintf(os.Stderr, "init: copy failed: %v\n", err)
		return 1
	}
	fmt.Printf("  copied %d files, %d symlinks\n", nFiles, nLinks)

	// 2. Rewrite module identity: go.mod + import paths.
	if err := rewriteModule(target, modulePath); err != nil {
		fmt.Fprintf(os.Stderr, "init: module rewrite failed: %v\n", err)
		return 1
	}

	// 3. Rename cmd/project → cmd/<package_dir> and fix its package line.
	if err := renameCmdStub(target, pkgDir); err != nil {
		fmt.Fprintf(os.Stderr, "init: cmd stub rename failed: %v\n", err)
		return 1
	}

	// 3b. Keep the capability roster pointed at the file that now exists.
	// Without this, capability_ports.json's stub row still names
	// cmd/project/main.go after every seed, and portcmd only flags a
	// missing entry when it still has runners rostered against it — the
	// stub ships with none, so the orphan is invisible to `verify` forever.
	if err := rewriteCapabilityPortsEntry(target, pkgDir); err != nil {
		fmt.Fprintf(os.Stderr, "init: capability roster rewrite failed: %v\n", err)
		return 1
	}

	// 4. Executable hooks.
	for _, h := range []string{"session_start.sh", "posture_check.sh"} {
		_ = os.Chmod(filepath.Join(target, ".claude", "hooks", h), 0o755)
	}

	// 5. Symlink farms.
	if _, err := linkcmd.Build(target, os.Stdout, false); err != nil {
		fmt.Fprintf(os.Stderr, "init: link failed: %v\n", err)
		return 1
	}

	// 6. Kimi user-level wiring.
	if !*noKimi {
		if err := WireKimi(target, os.Stdout); err != nil {
			fmt.Fprintf(os.Stderr, "init: kimi wiring failed: %v (wire by hand — see README)\n", err)
		}
	}

	// 7. git init if needed.
	if *git {
		if _, err := os.Stat(filepath.Join(target, ".git")); err != nil {
			c := exec.Command("git", "init", "-q")
			c.Dir = target
			if err := c.Run(); err != nil {
				fmt.Fprintf(os.Stderr, "init: git init failed: %v\n", err)
			} else {
				fmt.Println("  git initialized")
			}
		}
	}

	// 7a. Seed the history, and pin the documentary baseline to it.
	//
	// .epitomikon.json's adoption_revision names a commit in the TEMPLATE's
	// history; copied verbatim it names nothing here, and `epitomikon
	// profile` fails on the first run with a git error about a revision the
	// operator has never seen. The baseline a new repository wants is the
	// commit it starts from, so init makes that commit and pins it. Leaving
	// the field empty instead was tried and was worse: init exited 1, and
	// the remedy it printed ran `git rev-parse HEAD` in a repository with no
	// HEAD.
	//
	// The gate armed below exempts a root commit — it has no parent, so
	// there is nothing it could retire (.githooks/commit-msg, selftest case
	// 17) — so this commit needs no bypass and the trace stays honest.
	if *git {
		if err := seedHistory(target); err != nil {
			fmt.Fprintf(os.Stderr, "init: could not seed the history: %v\n", err)
			return 1
		}
	}

	// 7b. Arm the parsimony gate.
	//
	// core.hooksPath is local git config and is never committed, so the
	// seeded repo would otherwise carry .githooks/ inert — a gate that
	// reads as protection and is not. Arm it here, and verify (step 9)
	// fails loudly if this did not take. Anyone cloning the seeded repo
	// afterwards must run the same command; verify tells them so.
	if _, err := os.Stat(filepath.Join(target, ".git")); err == nil {
		if err := os.Chmod(filepath.Join(target, ".githooks", "commit-msg"), 0o755); err != nil {
			fmt.Fprintf(os.Stderr, "init: could not make the gate executable: %v\n", err)
		}
		_ = os.Chmod(filepath.Join(target, ".githooks", "selftest"), 0o755)
		c := exec.Command("git", "config", "core.hooksPath", ".githooks")
		c.Dir = target
		if err := c.Run(); err != nil {
			fmt.Fprintf(os.Stderr, "init: parsimony gate NOT armed: %v (run: git config core.hooksPath .githooks)\n", err)
		} else {
			fmt.Println("  parsimony gate armed (core.hooksPath = .githooks)")
		}
	}

	// 8. Leftover-token scan.
	if strays := scanLeftovers(target); len(strays) > 0 {
		fmt.Printf("  WARNING: unreplaced tokens remain in:\n")
		for _, s := range strays {
			fmt.Printf("    %s\n", s)
		}
	}

	// 9. Health gate on the seeded repo.
	fmt.Println("  verifying seeded repo:")
	return verifycmd.Run([]string{"-root", target})
}

func samePath(a, b string) bool {
	ea, erra := filepath.EvalSymlinks(a)
	eb, errb := filepath.EvalSymlinks(b)
	if erra != nil || errb != nil {
		return a == b
	}
	return ea == eb
}

// SanitizePackageDir lowercases and reduces to [a-z0-9_-].
func SanitizePackageDir(name string) string {
	s := strings.ToLower(name)
	var b strings.Builder
	for _, r := range s {
		switch {
		case r >= 'a' && r <= 'z', r >= '0' && r <= '9', r == '-', r == '_':
			b.WriteRune(r)
		default:
			b.WriteRune('-')
		}
	}
	out := strings.Trim(b.String(), "-")
	if out == "" {
		out = "project"
	}
	return out
}

func skipPath(rel string, noCursor bool) bool {
	if noCursor && (rel == ".cursor" || strings.HasPrefix(rel, ".cursor/")) {
		return true
	}
	for _, s := range skipRel {
		if rel == s || strings.HasPrefix(rel, s+string(filepath.Separator)) {
			return true
		}
	}
	// any path component named .DS_Store / node_modules
	for _, part := range strings.Split(rel, string(filepath.Separator)) {
		if part == ".DS_Store" || part == "node_modules" {
			return true
		}
	}
	return false
}

func isTextFile(name string) bool {
	if textNames[name] {
		return true
	}
	return textExts[strings.ToLower(filepath.Ext(name))]
}

func copyTree(from, to string, tokens map[string]string, noCursor bool) (int, int, error) {
	if err := os.MkdirAll(to, 0o755); err != nil {
		return 0, 0, err
	}
	nFiles, nLinks := 0, 0
	err := filepath.WalkDir(from, func(path string, d os.DirEntry, err error) error {
		if err != nil {
			return err
		}
		rel, err := filepath.Rel(from, path)
		if err != nil {
			return err
		}
		if rel == "." {
			return nil
		}
		if skipPath(rel, noCursor) {
			if d.IsDir() {
				return filepath.SkipDir
			}
			return nil
		}
		dst := filepath.Join(to, rel)
		switch {
		case d.IsDir():
			return os.MkdirAll(dst, 0o755)
		case d.Type()&os.ModeSymlink != 0:
			target, err := os.Readlink(path)
			if err != nil {
				return err
			}
			if err := os.Symlink(target, dst); err != nil {
				return err
			}
			nLinks++
			return nil
		default:
			data, err := os.ReadFile(path)
			if err != nil {
				return err
			}
			// Content files get token replacement; the toolchain under
			// tools/ travels intact (its tests carry token literals).
			if isTextFile(d.Name()) && !strings.HasPrefix(rel, "tools"+string(filepath.Separator)) {
				data = []byte(agentlib.ReplaceAll(string(data), tokens))
			}
			info, err := d.Info()
			if err != nil {
				return err
			}
			perm := info.Mode().Perm()
			if strings.HasSuffix(d.Name(), ".sh") {
				perm |= 0o755
			}
			if err := os.WriteFile(dst, data, perm); err != nil {
				return err
			}
			nFiles++
			return nil
		}
	})
	return nFiles, nLinks, err
}

var moduleLine = regexp.MustCompile(`(?m)^module\s+\S+`)

func rewriteModule(root, modulePath string) error {
	modFile := filepath.Join(root, "go.mod")
	data, err := os.ReadFile(modFile)
	if err != nil {
		return err
	}
	out := moduleLine.ReplaceAll(data, []byte("module "+modulePath))
	if err := os.WriteFile(modFile, out, 0o644); err != nil {
		return err
	}
	// import paths
	return filepath.WalkDir(root, func(path string, d os.DirEntry, err error) error {
		if err != nil || d.IsDir() || !strings.HasSuffix(d.Name(), ".go") {
			return err
		}
		if strings.Contains(path, string(filepath.Separator)+".git"+string(filepath.Separator)) {
			return nil
		}
		data, err := os.ReadFile(path)
		if err != nil {
			return err
		}
		replaced := bytes.ReplaceAll(data, []byte(templateModule+"/"), []byte(modulePath+"/"))
		if !bytes.Equal(replaced, data) {
			return os.WriteFile(path, replaced, 0o644)
		}
		return nil
	})
}

// PackageName derives a valid Go identifier from a package_dir: module
// paths may carry hyphens and dots, package identifiers may not.
func PackageName(packageDir string) string {
	var b strings.Builder
	for _, r := range packageDir {
		switch {
		case r >= 'a' && r <= 'z', r >= 'A' && r <= 'Z', r >= '0' && r <= '9', r == '_':
			b.WriteRune(r)
		}
	}
	out := b.String()
	if out == "" {
		out = "app"
	}
	if out[0] >= '0' && out[0] <= '9' {
		out = "p" + out
	}
	return out
}

func renameCmdStub(root, packageDir string) error {
	old := filepath.Join(root, "cmd", "project")
	if _, err := os.Stat(old); err != nil {
		return nil // no stub present (library-only template use)
	}
	data, err := os.ReadFile(filepath.Join(old, "main.go"))
	if err != nil {
		return err
	}
	fixed := regexp.MustCompile(`(?m)^package project$`).ReplaceAll(data, []byte("package "+PackageName(packageDir)))
	newDir := filepath.Join(root, "cmd", packageDir)
	if err := os.MkdirAll(newDir, 0o755); err != nil {
		return err
	}
	if err := os.WriteFile(filepath.Join(newDir, "main.go"), fixed, 0o644); err != nil {
		return err
	}
	return os.RemoveAll(old)
}

// rewriteCapabilityPortsEntry keeps capability_ports.json's stub row named
// after the renamed cmd/<package_dir>/main.go, the same way rewriteModule
// keeps go.mod named after the target module. Left alone, the roster's
// "entry" field for the CLI stub still reads "cmd/project/main.go" after
// every single seed — a roster row naming a file that no longer exists,
// silent because the stub ships with zero runners and portcmd only flags
// a missing entry when runners are still rostered against it. That is
// docs/ROT.md's rot A7 (retirement claimed, not performed) baked into
// every repo this template produces.
func rewriteCapabilityPortsEntry(root, packageDir string) error {
	path := filepath.Join(root, "capability_ports.json")
	data, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			return nil // no roster shipped — nothing to keep honest
		}
		return err
	}
	const oldEntry = `"entry": "cmd/project/main.go"`
	if !bytes.Contains(data, []byte(oldEntry)) {
		return nil // already renamed, or the roster never named the stub
	}
	newEntry := fmt.Sprintf(`"entry": "cmd/%s/main.go"`, packageDir)
	fixed := bytes.Replace(data, []byte(oldEntry), []byte(newEntry), 1)
	return os.WriteFile(path, fixed, 0o644)
}

func scanLeftovers(root string) []string {
	var strays []string
	_ = filepath.WalkDir(root, func(path string, d os.DirEntry, err error) error {
		if err != nil || d.IsDir() || !isTextFile(d.Name()) {
			return err
		}
		rel, _ := filepath.Rel(root, path)
		if strings.HasPrefix(rel, "tools"+string(filepath.Separator)) {
			return nil // the toolchain carries token literals by design
		}
		data, err := os.ReadFile(path)
		if err != nil {
			return nil
		}
		if len(agentlib.LeftoverTokens(string(data))) > 0 {
			strays = append(strays, rel)
		}
		return nil
	})
	return strays
}

// HookTOMLEntry renders the [[hooks]] block Kimi expects in
// ~/.kimi-code/config.toml.
func HookTOMLEntry(command string) string {
	return fmt.Sprintf("\n[[hooks]]\nevent = \"UserPromptSubmit\"\ncommand = %q\ntimeout = 5\n", command)
}

// NeedsWiring reports whether the Kimi config already registers command.
func NeedsWiring(existing, command string) bool {
	return !strings.Contains(existing, command)
}

// WireKimi appends the project hook to ~/.kimi-code/config.toml, backing the
// file up first. The hook script self-scopes by cwd, so a user-level entry is
// safe in every other repository.
func WireKimi(repoRoot string, w io.Writer) error {
	home, err := os.UserHomeDir()
	if err != nil {
		return err
	}
	cfgDir := filepath.Join(home, ".kimi-code")
	cfg := filepath.Join(cfgDir, "config.toml")
	command := filepath.Join(repoRoot, ".kimi", "hooks", "posture_check.sh")

	existing := []byte{}
	if data, err := os.ReadFile(cfg); err == nil {
		existing = data
	} else if !os.IsNotExist(err) {
		return err
	}
	if !NeedsWiring(string(existing), command) {
		fmt.Fprintln(w, "  kimi: hook already wired")
		return nil
	}
	if len(existing) > 0 {
		backup := cfg + ".bak-" + time.Now().Format("20060102-150405")
		if err := os.WriteFile(backup, existing, 0o600); err != nil {
			return fmt.Errorf("backup failed, refusing to edit: %w", err)
		}
		fmt.Fprintf(w, "  kimi: backed up %s\n", filepath.Base(backup))
	}
	if err := os.MkdirAll(cfgDir, 0o755); err != nil {
		return err
	}
	f, err := os.OpenFile(cfg, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0o600)
	if err != nil {
		return err
	}
	defer f.Close()
	if _, err := f.WriteString(HookTOMLEntry(command)); err != nil {
		return err
	}
	fmt.Fprintf(w, "  kimi: wired %s\n", command)
	return nil
}

// seedHistory makes the seeded repository's first commit and pins the
// document contract's adoption_revision to it, so the tree measures itself
// from the state it was seeded in. Every field of the declaration but that
// one is preserved. A repository that declines the documentary contract
// (no .epitomikon.json) still gets its first commit.
func seedHistory(root string) error {
	add := exec.Command("git", "add", "-A")
	add.Dir = root
	if out, err := add.CombinedOutput(); err != nil {
		return fmt.Errorf("git add: %v: %s", err, out)
	}
	msg := "Parsimony: add\n\nSeed the repository from github.com/philofree/PhilOcr.\n\nRetires: nothing (this commit creates the history)\n"
	commit := exec.Command("git", "commit", "-q", "-F", "-")
	commit.Dir = root
	commit.Stdin = strings.NewReader(msg)
	if out, err := commit.CombinedOutput(); err != nil {
		return fmt.Errorf("git commit: %v: %s", err, out)
	}
	rev := exec.Command("git", "rev-parse", "HEAD")
	rev.Dir = root
	head, err := rev.Output()
	if err != nil {
		return fmt.Errorf("git rev-parse HEAD: %w", err)
	}
	seed := strings.TrimSpace(string(head))
	pinned, err := pinAdoptionRevision(root, seed)
	if err != nil {
		return err
	}
	if !pinned {
		fmt.Println("  history seeded")
		return nil
	}
	// A second commit, not an amend: amending changes the very hash just
	// pinned, so the declaration would name a commit that no longer exists.
	// The baseline is the seeded state; this commit is the first change
	// after it, which is what the prospective rule is for.
	pin := exec.Command("git", "commit", "-q", "-F", "-", "--", ".epitomikon.json")
	pin.Dir = root
	pin.Stdin = strings.NewReader("Parsimony: add\n\nPin the documentary baseline to the seeded state.\n\nRetires: nothing\n")
	if out, err := pin.CombinedOutput(); err != nil {
		return fmt.Errorf("git commit (baseline pin): %v: %s", err, out)
	}
	fmt.Printf("  history seeded; documentary baseline pinned to %s\n", seed[:12])
	return nil
}

// pinAdoptionRevision writes revision into the seeded repository's document
// contract, preserving every other declared field. Absent file: nothing to do.
func pinAdoptionRevision(root, revision string) (bool, error) {
	path := filepath.Join(root, ".epitomikon.json")
	b, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			return false, nil
		}
		return false, err
	}
	var manifest map[string]any
	if err := json.Unmarshal(b, &manifest); err != nil {
		return false, fmt.Errorf("%s: %w", path, err)
	}
	if _, ok := manifest["adoption_revision"]; !ok {
		return false, nil
	}
	manifest["adoption_revision"] = revision
	out, err := json.MarshalIndent(manifest, "", "  ")
	if err != nil {
		return false, err
	}
	return true, os.WriteFile(path, append(out, '\n'), 0o644)
}
