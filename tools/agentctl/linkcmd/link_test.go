package linkcmd

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/philofree/PhilOcr/tools/agentctl/agentlib"
)

func fixture(t *testing.T) string {
	t.Helper()
	root := t.TempDir()
	for _, s := range []string{"open", "cut"} {
		dir := filepath.Join(root, ".claude", "skills", s)
		if err := os.MkdirAll(dir, 0o755); err != nil {
			t.Fatal(err)
		}
		_ = os.WriteFile(filepath.Join(dir, "SKILL.md"), []byte("---\nname: "+s+"\ndescription: d\n---\n"), 0o644)
	}
	return root
}

func TestBuildCreatesAndIsIdempotent(t *testing.T) {
	root := fixture(t)
	res, err := Build(root, os.Stdout, false)
	if err != nil {
		t.Fatal(err)
	}
	if res.Created != len(agentlib.Farms())*2+1 { // 2 skills × N farms + kimi hook
		t.Fatalf("created = %d, want %d", res.Created, len(agentlib.Farms())*2+1)
	}
	// Second run must change nothing.
	res2, err := Build(root, os.Stdout, false)
	if err != nil {
		t.Fatal(err)
	}
	if res2.Created != 0 || res2.Fixed != 0 || len(res2.Errors) != 0 {
		t.Fatalf("not idempotent: %+v", res2)
	}
}

func TestBuildFlagsRealDirDrift(t *testing.T) {
	root := fixture(t)
	if _, err := Build(root, os.Stdout, false); err != nil {
		t.Fatal(err)
	}
	// Replace a symlink with a real directory (the EuMorphikon failure mode).
	p := filepath.Join(root, ".agents", "skills", "cut")
	_ = os.Remove(p)
	if err := os.MkdirAll(p, 0o755); err != nil {
		t.Fatal(err)
	}
	res, err := Build(root, os.Stdout, false)
	if err != nil {
		t.Fatal(err)
	}
	if len(res.Errors) == 0 {
		t.Fatal("real-dir farm entry must be reported as drift")
	}
}

func TestBuildFixesWrongTarget(t *testing.T) {
	root := fixture(t)
	if _, err := Build(root, os.Stdout, false); err != nil {
		t.Fatal(err)
	}
	p := filepath.Join(root, ".zcode", "skills", "open")
	_ = os.Remove(p)
	if err := os.Symlink("../../elsewhere/open", p); err != nil {
		t.Fatal(err)
	}
	res, err := Build(root, os.Stdout, false)
	if err != nil {
		t.Fatal(err)
	}
	if res.Fixed != 1 {
		t.Fatalf("fixed = %d, want 1", res.Fixed)
	}
	got, _ := os.Readlink(p)
	if want := "../../.claude/skills/open"; got != want {
		t.Fatalf("target = %q want %q", got, want)
	}
}
