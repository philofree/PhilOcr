// agentctl — the agent-configuration toolchain that travels with every repo
// seeded from universal_template. Zero dependencies, stdlib only.
//
// Subcommands:
//
//	init <target>   instantiate a new repo from this template
//	verify          health-gate the agent surfaces (symlinks, registrations, hooks)
//	link            (re)build the per-tool skill symlink farms from .claude/skills/
//	now             regenerate NOW.md from the live handover's quick-start block
package main

import (
	"fmt"
	"os"

	"github.com/philofree/PhilOcr/tools/agentctl/initcmd"
	"github.com/philofree/PhilOcr/tools/agentctl/linkcmd"
	"github.com/philofree/PhilOcr/tools/agentctl/nowcmd"
	"github.com/philofree/PhilOcr/tools/agentctl/verifycmd"
)

const usage = `agentctl — agent surface toolchain (canonical store: .claude/)

Usage:
  agentctl init <target-dir> [flags]   seed a new repository from this template
  agentctl verify [-root DIR]          health-gate all agent surfaces
  agentctl link   [-root DIR] [-prune] rebuild skill symlink farms
  agentctl now    [-root DIR]          regenerate NOW.md from the live handover

Init flags:
  -name        display name               (default: target dir basename)
  -package-dir cmd/ directory name        (default: sanitized -name)
  -module      Go module path             (default: package-dir)
  -purpose     one-line telos             (fills docs/PURPOSE.md and CLAUDE.md)
  -no-kimi  skip ~/.kimi-code/config.toml wiring
  -no-cursor  drop .cursor/ from the seeded repo
  -git      git init the target if needed (default true)

See README.md for the full contract. One-edit rule: edit canonical files only.
`

func main() {
	if len(os.Args) < 2 {
		fmt.Fprint(os.Stderr, usage)
		os.Exit(2)
	}
	switch os.Args[1] {
	case "init":
		os.Exit(initcmd.Run(os.Args[2:]))
	case "verify":
		os.Exit(verifycmd.Run(os.Args[2:]))
	case "link":
		os.Exit(linkcmd.Run(os.Args[2:]))
	case "now":
		os.Exit(nowcmd.Run(os.Args[2:]))
	case "help", "-h", "--help":
		fmt.Print(usage)
	default:
		fmt.Fprintf(os.Stderr, "agentctl: unknown command %q\n\n", os.Args[1])
		fmt.Fprint(os.Stderr, usage)
		os.Exit(2)
	}
}
