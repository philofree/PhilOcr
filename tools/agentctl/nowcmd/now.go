// Package nowcmd regenerates NOW.md from the live handover's quick-start
// block. The handover owns the content; NOW.md is always derived.
package nowcmd

import (
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

const (
	beginMark = "<!-- now:begin -->"
	endMark   = "<!-- now:end -->"
)

// LatestHandover returns the newest HANDOVER_*.md at root, ignoring
// HANDOVER_TEMPLATE.md.
func LatestHandover(root string) string {
	matches, _ := filepath.Glob(filepath.Join(root, "HANDOVER_*.md"))
	var live []string
	for _, m := range matches {
		if filepath.Base(m) == "HANDOVER_TEMPLATE.md" {
			continue
		}
		live = append(live, m)
	}
	if len(live) == 0 {
		return ""
	}
	sort.Strings(live) // HANDOVER_YYYY-MM-DD_* sorts chronologically
	return live[len(live)-1]
}

// ExtractQuickStart pulls the delimited block from a handover's body.
func ExtractQuickStart(body string) string {
	i := strings.Index(body, beginMark)
	if i < 0 {
		return ""
	}
	rest := body[i+len(beginMark):]
	j := strings.Index(rest, endMark)
	if j < 0 {
		return ""
	}
	return strings.TrimSpace(rest[:j])
}

// Build renders the NOW.md content for root.
func Build(root string) (string, error) {
	hv := LatestHandover(root)
	if hv == "" {
		return "", fmt.Errorf("no live handover; an empty campaign frontier has no NOW.md")
	}
	var b strings.Builder
	b.WriteString("# NOW — generated quick-start\n\n")
	b.WriteString("Regenerate with `go run ./tools/agentctl now`. Do not edit by hand.\n\n")
	body, err := os.ReadFile(hv)
	if err != nil {
		return "", err
	}
	qs := ExtractQuickStart(string(body))
	if qs == "" {
		return "", fmt.Errorf("%s has no %s … %s block — add one to the handover", filepath.Base(hv), beginMark, endMark)
	}
	fmt.Fprintf(&b, "Source: `%s` (the one live handover).\n\n", filepath.Base(hv))
	b.WriteString(qs)
	b.WriteString("\n")
	return b.String(), nil
}

// Run is the CLI entry point.
func Run(args []string) int {
	fs := flag.NewFlagSet("now", flag.ExitOnError)
	root := fs.String("root", ".", "repo root")
	_ = fs.Parse(args)

	content, err := Build(*root)
	if err != nil {
		fmt.Fprintf(os.Stderr, "now: %v\n", err)
		return 1
	}
	if err := os.WriteFile(filepath.Join(*root, "NOW.md"), []byte(content), 0o644); err != nil {
		fmt.Fprintf(os.Stderr, "now: %v\n", err)
		return 1
	}
	fmt.Println("now: NOW.md regenerated")
	return 0
}
