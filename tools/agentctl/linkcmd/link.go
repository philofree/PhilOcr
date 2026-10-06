// Package linkcmd rebuilds the per-tool skill symlink farms from the
// canonical store (.claude/skills/). Idempotent: a second run changes nothing.
package linkcmd

import (
	"flag"
	"fmt"
	"io"
	"os"
	"path/filepath"

	"github.com/philofree/PhilOcr/tools/agentctl/agentlib"
)

// Result summarizes one build pass.
type Result struct {
	Created int
	Fixed   int
	Errors  []error
}

// Build (re)creates every farm symlink under root. A farm entry that is a
// real file or directory is reported as drift, never silently replaced —
// copied skills are exactly the failure mode the farms exist to prevent.
func Build(root string, w io.Writer, prune bool) (*Result, error) {
	res := &Result{}
	skills, err := agentlib.CanonicalSkillNames(root)
	if err != nil {
		return nil, fmt.Errorf("canonical store unreadable: %w (run from the repo root, or pass -root)", err)
	}
	if len(skills) == 0 {
		return nil, fmt.Errorf("no skills found under .claude/skills/ — nothing to farm out")
	}

	ensure := func(link, want string) {
		fi, err := os.Lstat(link)
		if err == nil {
			if fi.Mode()&os.ModeSymlink == 0 {
				res.Errors = append(res.Errors,
					fmt.Errorf("drift: %s is a real file/dir, not a symlink — resolve by hand (copied skills rot; delete it and re-run link)", rel(root, link)))
				return
			}
			cur, _ := os.Readlink(link)
			if cur == want {
				return
			}
			os.Remove(link)
			_ = os.Symlink(want, link)
			res.Fixed++
			fmt.Fprintf(w, "fixed: %s → %s\n", rel(root, link), want)
			return
		}
		_ = os.Symlink(want, link)
		res.Created++
		fmt.Fprintf(w, "linked: %s → %s\n", rel(root, link), want)
	}

	for _, farm := range agentlib.Farms() {
		dir := filepath.Join(root, filepath.FromSlash(farm.Dir))
		if err := os.MkdirAll(dir, 0o755); err != nil {
			res.Errors = append(res.Errors, fmt.Errorf("cannot create %s: %w", farm.Dir, err))
			continue
		}
		for _, s := range skills {
			ensure(filepath.Join(dir, s), agentlib.FarmTarget(farm, s))
		}
		if prune {
			entries, _ := os.ReadDir(dir)
			for _, e := range entries {
				if !contains(skills, e.Name()) {
					p := filepath.Join(dir, e.Name())
					if fi, err := os.Lstat(p); err == nil && fi.Mode()&os.ModeSymlink != 0 {
						_ = os.Remove(p)
						fmt.Fprintf(w, "pruned: %s (no canonical counterpart)\n", rel(root, p))
					}
				}
			}
		}
	}

	// Kimi hook entry: a symlink into the canonical hooks, matching the farm rule.
	kimiHooks := filepath.Join(root, ".kimi", "hooks")
	if err := os.MkdirAll(kimiHooks, 0o755); err == nil {
		ensure(filepath.Join(kimiHooks, "posture_check.sh"), "../../.claude/hooks/posture_check.sh")
	}

	return res, nil
}

func contains(list []string, s string) bool {
	for _, x := range list {
		if x == s {
			return true
		}
	}
	return false
}

func rel(root, p string) string {
	r, err := filepath.Rel(root, p)
	if err != nil {
		return p
	}
	return r
}

// Run is the CLI entry point.
func Run(args []string) int {
	fs := flag.NewFlagSet("link", flag.ExitOnError)
	root := fs.String("root", ".", "repo root")
	prune := fs.Bool("prune", false, "remove farm symlinks with no canonical counterpart")
	_ = fs.Parse(args)

	res, err := Build(*root, os.Stdout, *prune)
	if err != nil {
		fmt.Fprintf(os.Stderr, "link: %v\n", err)
		return 1
	}
	fmt.Printf("link: %d created, %d fixed, %d drift findings\n", res.Created, res.Fixed, len(res.Errors))
	for _, e := range res.Errors {
		fmt.Fprintf(os.Stderr, "link: %v\n", e)
	}
	if len(res.Errors) > 0 {
		return 1
	}
	return 0
}
