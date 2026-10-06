package nowcmd

import (
	"os"
	"path/filepath"
	"testing"
)

func TestExtractQuickStart(t *testing.T) {
	body := "# HANDOVER 2026-08-24 — something\n\nIntro.\n\n" +
		"<!-- now:begin -->\n1. Do this.\n2. Then that.\n<!-- now:end -->\n\nTrailing.\n"
	got := ExtractQuickStart(body)
	want := "1. Do this.\n2. Then that."
	if got != want {
		t.Fatalf("got %q want %q", got, want)
	}
	if ExtractQuickStart("no markers here") != "" {
		t.Fatal("missing markers must yield empty")
	}
	if ExtractQuickStart("<!-- now:begin -->\nunterminated") != "" {
		t.Fatal("missing end marker must yield empty")
	}
}

func TestLatestHandoverIgnoresTemplate(t *testing.T) {
	dir := t.TempDir()
	write := func(name string) {
		_ = os.WriteFile(filepath.Join(dir, name), []byte("x"), 0o644)
	}
	write("HANDOVER_TEMPLATE.md")
	if got := LatestHandover(dir); got != "" {
		t.Fatalf("template-only dir must yield empty, got %q", got)
	}
	write("HANDOVER_2026-08-20_first.md")
	write("HANDOVER_2026-08-24_second.md")
	got := LatestHandover(dir)
	if filepath.Base(got) != "HANDOVER_2026-08-24_second.md" {
		t.Fatalf("latest = %q", got)
	}
}

func TestNowRefusesToInventStateWithoutLiveHandover(t *testing.T) {
	dir := t.TempDir()
	if code := Run([]string{"-root", dir}); code == 0 {
		t.Fatal("now succeeded without a live handover")
	}
	if _, err := os.Stat(filepath.Join(dir, "NOW.md")); !os.IsNotExist(err) {
		t.Fatalf("NOW.md was written without a live handover: %v", err)
	}
}
