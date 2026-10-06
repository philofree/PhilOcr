package portcmd

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// repoRoot walks up to the go.mod that owns this module.
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

// TestCapabilityPortRoster is the issuance join over the live repository.
// It never t.Skip()s: it needs only the source tree, so a machine that can
// run the tests can run this one. A skipped gate is an absent gate.
func TestCapabilityPortRoster(t *testing.T) {
	if errs := Check(repoRoot(t)); len(errs) > 0 {
		t.Fatalf("capability port join:\n  %s", strings.Join(errs, "\n  "))
	}
}

// --- planted faults ---------------------------------------------------------
//
// Each of these proves the join fires. Without them a permanently-green
// check is indistinguishable from a check that never looks at anything.

// lab builds a throwaway repo: a roster, a CLI that dispatches, a driver
// file, and the doctrine file, all consistent. Each test then breaks one
// thing and asserts the join names it.
func lab(t *testing.T, roster Roster, mainSrc string) string {
	t.Helper()
	root := t.TempDir()
	mustWrite(t, filepath.Join(root, "cmd", "app", "main.go"), mainSrc)
	mustWrite(t, filepath.Join(root, "internal", "kit", "kit.go"),
		"package kit\n\ntype Handle struct{}\n")
	mustWrite(t, filepath.Join(root, DoctrineFile),
		"# Capability port\n\ndriver, port, adapter. Roster: "+RosterFile+"\n")
	data, err := json.Marshal(roster)
	if err != nil {
		t.Fatal(err)
	}
	mustWrite(t, filepath.Join(root, RosterFile), string(data))
	return root
}

func mustWrite(t *testing.T, path, body string) {
	t.Helper()
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(path, []byte(body), 0o644); err != nil {
		t.Fatal(err)
	}
}

const twoCommandMain = `package main

func main() {
	switch os.Args[1] {
	case "serve":
		serve()
	case "audit":
		audit()
	}
}
`

func oneRunner(cmd, disp, port, driver string) Roster {
	return Roster{CLIs: []CLI{{
		Entry:   "cmd/app/main.go",
		Runners: []Runner{{Command: cmd, Disposition: disp, Port: port, Driver: driver}},
	}}}
}

func wantErr(t *testing.T, root, substr string) {
	t.Helper()
	errs := Check(root)
	if len(errs) == 0 {
		t.Fatal("join passed a repo it should have refused")
	}
	joined := strings.Join(errs, "\n")
	if !strings.Contains(joined, substr) {
		t.Fatalf("join fired but not on the planted fault.\nwant substring: %s\ngot:\n%s", substr, joined)
	}
}

func TestGoesRedOnUnnamedCapability(t *testing.T) {
	// "audit" is dispatched and unrostered — a capability nobody owns.
	root := lab(t, oneRunner("serve", "instrument", "", "internal/kit/kit.go"), twoCommandMain)
	wantErr(t, root, `dispatches "audit" with no row`)
}

func TestGoesRedOnOrphanRosterRow(t *testing.T) {
	r := oneRunner("serve", "instrument", "", "internal/kit/kit.go")
	r.CLIs[0].Runners = append(r.CLIs[0].Runners,
		Runner{Command: "audit", Disposition: "instrument", Driver: "internal/kit/kit.go"},
		Runner{Command: "gone", Disposition: "instrument", Driver: "internal/kit/kit.go"})
	root := lab(t, r, twoCommandMain)
	wantErr(t, root, `rosters "gone" but no longer dispatches it`)
}

func TestGoesRedWhenIssuedNamesNoPort(t *testing.T) {
	r := oneRunner("serve", "issued", "", "internal/kit/kit.go")
	r.CLIs[0].Runners = append(r.CLIs[0].Runners,
		Runner{Command: "audit", Disposition: "instrument", Driver: "internal/kit/kit.go"})
	root := lab(t, r, twoCommandMain)
	wantErr(t, root, "is issued but names no port")
}

func TestGoesRedWhenPortIsNotDeclared(t *testing.T) {
	r := oneRunner("serve", "issued", "kit.Missing", "internal/kit/kit.go")
	r.CLIs[0].Runners = append(r.CLIs[0].Runners,
		Runner{Command: "audit", Disposition: "instrument", Driver: "internal/kit/kit.go"})
	root := lab(t, r, twoCommandMain)
	wantErr(t, root, "no exported type of that name is declared")
}

func TestGoesRedWhenDriverIsMissing(t *testing.T) {
	r := oneRunner("serve", "instrument", "", "internal/kit/vanished.go")
	r.CLIs[0].Runners = append(r.CLIs[0].Runners,
		Runner{Command: "audit", Disposition: "instrument", Driver: "internal/kit/kit.go"})
	root := lab(t, r, twoCommandMain)
	wantErr(t, root, "which does not exist")
}

func TestGoesRedOnUnknownDisposition(t *testing.T) {
	r := oneRunner("serve", "probably-fine", "", "internal/kit/kit.go")
	r.CLIs[0].Runners = append(r.CLIs[0].Runners,
		Runner{Command: "audit", Disposition: "instrument", Driver: "internal/kit/kit.go"})
	root := lab(t, r, twoCommandMain)
	wantErr(t, root, "must be issued, instrument, remainder or retired-stub")
}

func TestGoesRedWhenDoctrineIsGone(t *testing.T) {
	r := oneRunner("serve", "instrument", "", "internal/kit/kit.go")
	r.CLIs[0].Runners = append(r.CLIs[0].Runners,
		Runner{Command: "audit", Disposition: "instrument", Driver: "internal/kit/kit.go"})
	root := lab(t, r, twoCommandMain)
	if err := os.Remove(filepath.Join(root, DoctrineFile)); err != nil {
		t.Fatal(err)
	}
	wantErr(t, root, "capability_port.md missing")
}

func TestRefusesAnEmptyRoster(t *testing.T) {
	root := t.TempDir()
	mustWrite(t, filepath.Join(root, RosterFile), `{"clis":[]}`)
	wantErr(t, root, "refusing a clean pass over an empty roster")
}

// A consistent repo must pass, or every red above proves nothing.
func TestPassesWhenTheRepoIsHonest(t *testing.T) {
	r := oneRunner("serve", "issued", "kit.Handle", "internal/kit/kit.go")
	r.CLIs[0].Runners = append(r.CLIs[0].Runners,
		Runner{Command: "audit", Disposition: "instrument", Driver: "internal/kit/kit.go"})
	root := lab(t, r, twoCommandMain)
	if errs := Check(root); len(errs) > 0 {
		t.Fatalf("honest repo refused:\n  %s", strings.Join(errs, "\n  "))
	}
}

// A stub CLI that dispatches nothing is a legitimate state, not a finding —
// otherwise a freshly seeded repo is red before it has written a line.
func TestStubCLIWithNoDispatchIsFine(t *testing.T) {
	r := Roster{CLIs: []CLI{{Entry: "cmd/app/main.go", Runners: nil}}}
	root := lab(t, r, "package main\n\nfunc main() {}\n")
	if errs := Check(root); len(errs) > 0 {
		t.Fatalf("stub CLI refused:\n  %s", strings.Join(errs, "\n  "))
	}
}

const commandPlusFlagMain = `package main

func main() {
	switch os.Args[1] {
	case "serve":
		serve()
	case "audit":
		audit()
	}
	for i := range args {
		switch args[i] {
		case "--imports":
			imports = true
		}
	}
}
`

// TestFlagSwitchIsNotACommand is the scar: a verify-flag walk is not a
// dispatched command. Treating "--imports" as unnamed capability is the
// join measuring the wrong switch.
func TestFlagSwitchIsNotACommand(t *testing.T) {
	r := oneRunner("serve", "issued", "kit.Handle", "internal/kit/kit.go")
	r.CLIs[0].Runners = append(r.CLIs[0].Runners,
		Runner{Command: "audit", Disposition: "instrument", Driver: "internal/kit/kit.go"})
	root := lab(t, r, commandPlusFlagMain)
	if errs := Check(root); len(errs) > 0 {
		t.Fatalf("flag switch treated as a command:\n  %s", strings.Join(errs, "\n  "))
	}
}

const flagArgMain = `package main

func main() {
	switch flag.Arg(0) {
	case "serve":
		serve()
	case "audit":
		audit()
	}
}
`

func TestFlagArgSwitchIsACommand(t *testing.T) {
	r := oneRunner("serve", "issued", "kit.Handle", "internal/kit/kit.go")
	root := lab(t, r, flagArgMain)
	wantErr(t, root, `dispatches "audit" with no row`)
}
