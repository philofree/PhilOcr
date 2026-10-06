package agentlib

import (
	"strings"
	"testing"
)

func TestCheckFrontmatter(t *testing.T) {
	cases := []struct {
		name string
		in   string
		want string // "" = ok, else substring of the error
	}{
		{"minimal ok", "---\nname: cut\ndescription: Use before writing.\n---\n\n# Cut\n", ""},
		{"folded description ok", "---\nname: open\ndescription: >\n  Long multi-line\n  trigger surface.\n---\nbody\n", ""},
		{"empty continuation lines ok", "---\nname: x\ndescription: >\n\n  text\n---\n", ""},
		{"no frontmatter", "# Just a heading\n", "no frontmatter"},
		{"unterminated", "---\nname: x\n", "not terminated"},
		{"missing name", "---\ndescription: d\n---\n", "missing 'name'"},
		{"missing description", "---\nname: x\n---\n", "missing 'description'"},
		{"metadata key banned", "---\nname: x\ndescription: d\nmetadata:\n  version: \"1.0\"\n---\n", `"metadata" not allowed`},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			err := CheckFrontmatter([]byte(tc.in))
			if tc.want == "" {
				if err != nil {
					t.Fatalf("want ok, got %v", err)
				}
				return
			}
			if err == nil {
				t.Fatalf("want error containing %q, got nil", tc.want)
			}
			if !strings.Contains(err.Error(), tc.want) {
				t.Fatalf("error %q does not contain %q", err.Error(), tc.want)
			}
		})
	}
}

func TestReplaceAllAndLeftovers(t *testing.T) {
	tokens := TokenMap("My Repo", "my-repo", "github.com/james/my-repo", "does things", "/tmp/x")
	in := "{{PROJECT_NAME}} / {{PACKAGE_DIR}} / {{MODULE_PATH}} / {{ONE_LINE_PURPOSE}} / {{REPO_ROOT}}"
	got := ReplaceAll(in, tokens)
	want := "My Repo / my-repo / github.com/james/my-repo / does things / /tmp/x"
	if got != want {
		t.Fatalf("got %q want %q", got, want)
	}
	if l := LeftoverTokens(ReplaceAll(in, tokens)); len(l) != 0 {
		t.Fatalf("leftovers: %v", l)
	}
	if l := LeftoverTokens("still {{PROJECT_NAME}}"); len(l) != 1 || l[0] != TokenProjectName {
		t.Fatalf("leftover detection: %v", l)
	}
}

func TestFarmTarget(t *testing.T) {
	z := Farm{Dir: ".zcode/skills", Ups: 2}
	if got := FarmTarget(z, "cut"); got != "../../.claude/skills/cut" {
		t.Fatalf("two-up target: %q", got)
	}
	a := Farm{Dir: ".agents/skills", Ups: 2}
	if got := FarmTarget(a, "cut"); got != "../../.claude/skills/cut" {
		t.Fatalf("agents target: %q", got)
	}
}
