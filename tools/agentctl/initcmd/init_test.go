package initcmd

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestSanitizePackageDir(t *testing.T) {
	cases := map[string]string{
		"My New Repo":   "my-new-repo",
		"Eulogikon 2!":  "eulogikon-2",
		"already-named": "already-named",
		"***":           "project",
	}
	for in, want := range cases {
		if got := SanitizePackageDir(in); got != want {
			t.Errorf("SanitizePackageDir(%q) = %q, want %q", in, got, want)
		}
	}
}

func TestPackageName(t *testing.T) {
	cases := map[string]string{
		"demo-app": "demoapp",
		"my.repo":  "myrepo",
		"plain":    "plain",
		"2fast":    "p2fast",
		"---":      "app",
	}
	for in, want := range cases {
		if got := PackageName(in); got != want {
			t.Errorf("PackageName(%q) = %q, want %q", in, got, want)
		}
	}
}

func TestHookTOMLEntryShape(t *testing.T) {
	cmd := filepath.Join("/x", ".kimi", "hooks", "posture_check.sh")
	e := HookTOMLEntry(cmd)
	for _, want := range []string{"[[hooks]]", `event = "UserPromptSubmit"`, `command = "` + cmd + `"`, "timeout = 5"} {
		if !strings.Contains(e, want) {
			t.Errorf("entry missing %q:\n%s", want, e)
		}
	}
}

func TestNeedsWiringIdempotent(t *testing.T) {
	cmd := "/x/.kimi/hooks/posture_check.sh"
	existing := "default_model = \"k3\"\n" + HookTOMLEntry(cmd)
	if !NeedsWiring("hooks = []\n", cmd) {
		t.Error("config without the command needs wiring")
	}
	if NeedsWiring(existing, cmd) {
		t.Error("config already carrying the command must not need wiring")
	}
}

func TestCopyTreeCopiesCampaignGraphFromRoot(t *testing.T) {
	from := t.TempDir()
	target := t.TempDir()
	graph := filepath.Join(from, "campaigns", "graph.yaml")
	if err := os.MkdirAll(filepath.Dir(graph), 0o755); err != nil {
		t.Fatal(err)
	}
	want := []byte("version: eustratikon/campaign-graph/v1\nnodes: []\n")
	if err := os.WriteFile(graph, want, 0o644); err != nil {
		t.Fatal(err)
	}

	if _, _, err := copyTree(from, target, nil, false); err != nil {
		t.Fatal(err)
	}
	got, err := os.ReadFile(filepath.Join(target, "campaigns", "graph.yaml"))
	if err != nil {
		t.Fatal(err)
	}
	if string(got) != string(want) {
		t.Fatalf("copied graph = %q, want %q", got, want)
	}
}
