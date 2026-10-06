// Package eukrinikoncmd runs the sibling Python EuKrinikon instrument against
// this repository (or a --target tree). Axes and doctrine live in ../eukrinikon;
// the Python port lives in ../eukrinikon_python by default.
package eukrinikoncmd

import (
	"flag"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
)

const defaultInstrumentRel = "../eukrinikon_python"

// Run is the CLI entry for `agentctl eukrinikon`.
func Run(args []string) int {
	fs := flag.NewFlagSet("eukrinikon", flag.ExitOnError)
	repoRoot := fs.String("root", ".", "PhilOcr repo root (resolves sibling instrument)")
	target := fs.String("target", "", "repository root to scan (default: same as -root)")
	jsonOut := fs.Bool("json", false, "emit findings JSON on stdout")
	zone := fs.String("zone", "", "comma-separated path fragments (training slices)")
	if err := fs.Parse(args); err != nil {
		return 2
	}

	absRoot, err := filepath.Abs(*repoRoot)
	if err != nil {
		fmt.Fprintf(os.Stderr, "eukrinikon: root: %v\n", err)
		return 2
	}
	scanRoot := absRoot
	if *target != "" {
		scanRoot, err = filepath.Abs(*target)
		if err != nil {
			fmt.Fprintf(os.Stderr, "eukrinikon: target: %v\n", err)
			return 2
		}
	}

	home, py, err := resolveRuntime(absRoot)
	if err != nil {
		fmt.Fprintf(os.Stderr, "eukrinikon: %v\n", err)
		return 2
	}

	cmdArgs := []string{"-m", "eukrinikon_python", "scan", scanRoot}
	if *jsonOut {
		cmdArgs = append(cmdArgs, "--json")
	}
	if *zone != "" {
		cmdArgs = append(cmdArgs, "--zone", *zone)
	}

	cmd := exec.Command(py, cmdArgs...)
	cmd.Dir = home
	cmd.Env = append(os.Environ(), "PYTHONPATH="+home)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	if err := cmd.Run(); err != nil {
		if ee, ok := err.(*exec.ExitError); ok {
			return ee.ExitCode()
		}
		fmt.Fprintf(os.Stderr, "eukrinikon: run failed: %v\n", err)
		return 2
	}
	return 0
}

func resolveRuntime(repoRoot string) (string, string, error) {
	var instrumentHome string
	var err error
	if v := os.Getenv("EUKRINIKON_PYTHON_HOME"); v != "" {
		instrumentHome, err = filepath.Abs(v)
		if err != nil {
			return "", "", fmt.Errorf("EUKRINIKON_PYTHON_HOME: %w", err)
		}
	} else {
		instrumentHome, err = filepath.Abs(filepath.Join(repoRoot, defaultInstrumentRel))
		if err != nil {
			return "", "", err
		}
	}
	cli := filepath.Join(instrumentHome, "eukrinikon_python", "cli.py")
	if _, err := os.Stat(cli); err != nil {
		return "", "", fmt.Errorf(
			"Python EuKrinikon not found at %s (set EUKRINIKON_PYTHON_HOME)",
			instrumentHome,
		)
	}

	if v := os.Getenv("EUKRINIKON_PYTHON_BIN"); v != "" {
		return instrumentHome, v, nil
	}
	for _, candidate := range []string{
		filepath.Join(repoRoot, "venv/bin/python"),
		filepath.Join(repoRoot, ".venv/bin/python"),
	} {
		if _, err := os.Stat(candidate); err == nil {
			return instrumentHome, candidate, nil
		}
	}
	return instrumentHome, "python3", nil
}
