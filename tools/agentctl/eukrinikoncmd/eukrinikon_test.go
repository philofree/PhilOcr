package eukrinikoncmd

import (
	"os"
	"path/filepath"
	"testing"
)

func TestResolveRuntimeMissingInstrument(t *testing.T) {
	root := t.TempDir()
	_, _, err := resolveRuntime(root)
	if err == nil {
		t.Fatal("expected error when sibling instrument absent")
	}
}

func TestResolveRuntimeWithEnvHome(t *testing.T) {
	root := t.TempDir()
	home := t.TempDir()
	pkg := filepath.Join(home, "eukrinikon_python")
	if err := os.MkdirAll(pkg, 0o755); err != nil {
		t.Fatal(err)
	}
	cli := filepath.Join(pkg, "cli.py")
	if err := os.WriteFile(cli, []byte("# stub\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	t.Setenv("EUKRINIKON_PYTHON_HOME", home)
	gotHome, _, err := resolveRuntime(root)
	if err != nil {
		t.Fatal(err)
	}
	if gotHome != home {
		t.Fatalf("home %q want %q", gotHome, home)
	}
}
