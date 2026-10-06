package verifycmd

import (
	"os"
	"os/exec"
	"path/filepath"
	"testing"
)

func repoRoot(t *testing.T) string {
	t.Helper()
	dir, err := os.Getwd()
	if err != nil {
		t.Fatal(err)
	}
	for {
		if _, err := os.Stat(filepath.Join(dir, "go.mod")); err == nil {
			return dir
		}
		parent := filepath.Dir(dir)
		if parent == dir {
			t.Fatal("no go.mod above the test directory")
		}
		dir = parent
	}
}

// TestParsimonyGate runs the gate's own self-test under `go test ./...`, so
// the gate cannot rot silently between the rare occasions someone thinks to
// run it by hand.
//
// It never t.Skip()s. It needs sh and git, which any machine that can clone
// this repo already has, and a skipped gate is an absent gate. It takes a
// few seconds; the self-test rewinds one throwaway repo rather than
// initialising ten, precisely so nobody has a reason to disable it.
func TestParsimonyGate(t *testing.T) {
	root := repoRoot(t)
	script := filepath.Join(root, ".githooks", "selftest")
	if _, err := os.Stat(script); err != nil {
		t.Fatalf(".githooks/selftest missing: %v — the gate has no proof", err)
	}
	cmd := exec.Command("sh", script)
	cmd.Dir = root
	out, err := cmd.CombinedOutput()
	if err != nil {
		t.Fatalf("parsimony gate self-test failed: %v\n%s", err, out)
	}
	t.Logf("\n%s", out)
}

// TestParsimonyGateIsArmed proves the gate is not merely present.
//
// core.hooksPath is local git config and is never committed: a fresh clone
// has .githooks/ inert. This is the check that turns "dormant" from silence
// into a failing test.
func TestParsimonyGateIsArmed(t *testing.T) {
	root := repoRoot(t)
	out, err := exec.Command("git", "-C", root, "config", "--get", "core.hooksPath").Output()
	got := ""
	if err == nil {
		got = string(out)
		got = got[:len(got)-1] // trailing newline
	}
	if got != ".githooks" {
		t.Fatalf("core.hooksPath = %q, want %q — the parsimony gate is DORMANT in this clone.\n"+
			"Arm it:  git config core.hooksPath .githooks", got, ".githooks")
	}
}
