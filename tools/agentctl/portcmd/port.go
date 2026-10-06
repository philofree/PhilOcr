// Package portcmd is the capability issuance join.
//
// A capability is a thing this repo guarantees. It is built as a driver
// (one component holds the invariant; there is no second path to the
// effect), a port (the typed surface consumers hold), and adapters (I/O,
// flags — they feed the driver or they fail, and can neither hold nor
// break the guarantee). Doctrine:
// .claude/skills/cut/references/capability_port.md.
//
// This file enforces the one rule that makes the form real rather than
// aspirational: EVERY capability IS NAMED. A command a CLI dispatches
// without a roster row is a capability nobody owns, and it goes red.
//
// It is deliberately AST-based, not reflection-based. Reflection would
// need this package to import every package it checks, which does not
// travel to a seeded repo whose packages do not exist yet. Parsing means
// the join works on any Go repo seeded from this template, on a fresh
// clone, with nothing built.
package portcmd

import (
	"encoding/json"
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
)

// RosterFile is the repo-root contract, owned by the repo, not by this tool.
const RosterFile = "capability_ports.json"

// DoctrineFile must exist and must point back at the roster, or the form is
// prose with nothing behind it.
const DoctrineFile = ".claude/skills/cut/references/capability_port.md"

type Runner struct {
	Command     string `json:"command"`
	Disposition string `json:"disposition"`
	Port        string `json:"port,omitempty"`
	Driver      string `json:"driver"`
}

type CLI struct {
	Entry           string   `json:"entry"`
	Note            string   `json:"note,omitempty"`
	Runners         []Runner `json:"runners"`
	NotCapabilities []string `json:"not_capabilities,omitempty"`
}

// ProductCapability is one PhilOcr product guarantee. Disposition is
// closed on issued: a refactor that has not issued a port is not on
// this list.
type ProductCapability struct {
	Name        string `json:"name"`
	Disposition string `json:"disposition"`
	Port        string `json:"port"`
	Driver      string `json:"driver"`
}

type Roster struct {
	CLIs    []CLI               `json:"clis"`
	Product []ProductCapability `json:"product"`
}

var validDisposition = map[string]bool{
	"issued": true, "instrument": true, "remainder": true, "retired-stub": true,
}

// Check runs the whole join and returns every finding. A finding is a
// defect, never a warning: the point of the roster is that it cannot be
// quietly out of date.
func Check(root string) []string {
	var errs []string

	raw, err := os.ReadFile(filepath.Join(root, RosterFile))
	if err != nil {
		return []string{fmt.Sprintf("%s unreadable: %v — the roster is the contract; without it no capability is named", RosterFile, err)}
	}
	var r Roster
	if err := json.Unmarshal(raw, &r); err != nil {
		return []string{fmt.Sprintf("%s does not parse: %v", RosterFile, err)}
	}
	if !strings.Contains(string(raw), `"product"`) {
		return []string{fmt.Sprintf(
			"%s has no \"product\" list — a product refactor names an issued port",
			RosterFile,
		)}
	}
	if len(r.CLIs) == 0 {
		return []string{fmt.Sprintf("%s lists no CLIs — refusing a clean pass over an empty roster", RosterFile)}
	}

	for _, c := range r.CLIs {
		errs = append(errs, checkCLI(root, c)...)
	}
	errs = append(errs, checkProduct(root, r.Product)...)
	errs = append(errs, checkDoctrine(root)...)
	return errs
}

func checkCLI(root string, c CLI) []string {
	var errs []string
	entry := filepath.Join(root, filepath.FromSlash(c.Entry))

	if _, err := os.Stat(entry); err != nil {
		// A roster row pointing at a file that is gone is an orphan, and
		// the loudest kind: the capability was removed and nothing said so.
		if len(c.Runners) > 0 {
			errs = append(errs, fmt.Sprintf("%s: entry missing (%v) but %d runner(s) still rostered", c.Entry, err, len(c.Runners)))
		}
		return errs
	}

	dispatched, err := dispatchedCommands(entry)
	if err != nil {
		return append(errs, fmt.Sprintf("%s: %v", c.Entry, err))
	}

	exempt := map[string]bool{}
	for _, e := range c.NotCapabilities {
		exempt[e] = true
	}
	rostered := map[string]Runner{}
	for _, run := range c.Runners {
		if _, dup := rostered[run.Command]; dup {
			errs = append(errs, fmt.Sprintf("%s: %q rostered twice", c.Entry, run.Command))
		}
		rostered[run.Command] = run
	}

	// 1. Every dispatched command is named.
	var unnamed []string
	for cmd := range dispatched {
		if exempt[cmd] {
			continue
		}
		if _, ok := rostered[cmd]; !ok {
			unnamed = append(unnamed, cmd)
		}
	}
	sort.Strings(unnamed)
	for _, cmd := range unnamed {
		errs = append(errs, fmt.Sprintf("%s dispatches %q with no row in %s — an unnamed capability is one nobody owns; add it with an honest disposition", c.Entry, cmd, RosterFile))
	}

	// 2. Every rostered row still dispatches.
	var orphans []string
	for cmd := range rostered {
		if _, ok := dispatched[cmd]; !ok {
			orphans = append(orphans, cmd)
		}
	}
	sort.Strings(orphans)
	for _, cmd := range orphans {
		errs = append(errs, fmt.Sprintf("%s rosters %q but no longer dispatches it — retire the row, or say where the capability went", RosterFile, cmd))
	}

	// 3. Each row is internally honest.
	for _, cmd := range sortedKeys(rostered) {
		run := rostered[cmd]
		switch {
		case !validDisposition[run.Disposition]:
			errs = append(errs, fmt.Sprintf("%s: %q has disposition %q — must be issued, instrument, remainder or retired-stub", RosterFile, cmd, run.Disposition))
		case run.Disposition == "issued" && run.Port == "":
			errs = append(errs, fmt.Sprintf("%s: %q is issued but names no port — issued means a typed surface exists; name it or call it an instrument", RosterFile, cmd))
		case run.Disposition != "issued" && run.Port != "":
			errs = append(errs, fmt.Sprintf("%s: %q names port %q but is not issued — a port that consumers cannot hold is not a port", RosterFile, cmd, run.Port))
		}
		if run.Driver == "" {
			errs = append(errs, fmt.Sprintf("%s: %q names no driver — every capability has one owning file", RosterFile, cmd))
			continue
		}
		if _, err := os.Stat(filepath.Join(root, filepath.FromSlash(run.Driver))); err != nil {
			errs = append(errs, fmt.Sprintf("%s: %q names driver %s which does not exist", RosterFile, cmd, run.Driver))
		}
		if run.Disposition == "issued" && run.Port != "" {
			if msg := checkPortDeclared(root, run.Port); msg != "" {
				errs = append(errs, fmt.Sprintf("%s: %q port %s — %s", RosterFile, cmd, run.Port, msg))
			}
		}
	}
	return errs
}

// dispatchedCommands returns the string cases of every argv-index switch
// in the entry file: `switch os.Args[1]` and `switch flag.Arg(0)`. Other
// string switches (flag parsing, `switch args[i] { case "--imports": }`)
// are not commands. A CLI with no argv switch dispatches nothing, which
// is a legitimate state (a stub) and not an error.
func dispatchedCommands(path string) (map[string]struct{}, error) {
	fset := token.NewFileSet()
	f, err := parser.ParseFile(fset, path, nil, 0)
	if err != nil {
		return nil, fmt.Errorf("parse: %w", err)
	}
	out := map[string]struct{}{}
	ast.Inspect(f, func(n ast.Node) bool {
		s, ok := n.(*ast.SwitchStmt)
		if !ok || s.Tag == nil || !isArgvDispatchTag(s.Tag) {
			return true
		}
		for _, stmt := range s.Body.List {
			cc, ok := stmt.(*ast.CaseClause)
			if !ok {
				continue
			}
			for _, e := range cc.List {
				bl, ok := e.(*ast.BasicLit)
				if !ok || bl.Kind != token.STRING {
					continue
				}
				if cmd, err := strconv.Unquote(bl.Value); err == nil && cmd != "" {
					out[cmd] = struct{}{}
				}
			}
		}
		return true
	})
	return out, nil
}

func unwrapExpr(e ast.Expr) ast.Expr {
	for {
		p, ok := e.(*ast.ParenExpr)
		if !ok {
			return e
		}
		e = p.X
	}
}

// isArgvDispatchTag reports whether a switch tag is an argv index:
// flag.Arg(N) or os.Args[N] with N an integer literal. A switch on
// args[i] (flag walk) is not a command dispatcher.
func isArgvDispatchTag(tag ast.Expr) bool {
	tag = unwrapExpr(tag)
	switch t := tag.(type) {
	case *ast.CallExpr:
		if len(t.Args) != 1 {
			return false
		}
		lit, ok := t.Args[0].(*ast.BasicLit)
		if !ok || lit.Kind != token.INT {
			return false
		}
		sel, ok := unwrapExpr(t.Fun).(*ast.SelectorExpr)
		return ok && sel.Sel != nil && sel.Sel.Name == "Arg"
	case *ast.IndexExpr:
		lit, ok := t.Index.(*ast.BasicLit)
		if !ok || lit.Kind != token.INT {
			return false
		}
		sel, ok := unwrapExpr(t.X).(*ast.SelectorExpr)
		return ok && sel.Sel != nil && sel.Sel.Name == "Args"
	}
	return false
}

// checkPortDeclared confirms "pkg.Type" is really declared somewhere in the
// repo, so an issued row cannot name a surface that does not exist.
func checkPortDeclared(root, port string) string {
	pkg, typ, ok := strings.Cut(port, ".")
	if !ok {
		return "must be written pkg.Type"
	}
	found := false
	_ = filepath.WalkDir(root, func(p string, d os.DirEntry, err error) error {
		if err != nil || found {
			return nil
		}
		if d.IsDir() {
			if n := d.Name(); n == ".git" || n == "vendor" || n == "node_modules" || n == "bin" || n == "testdata" || n == "out" {
				return filepath.SkipDir
			}
			return nil
		}
		if !strings.HasSuffix(p, ".go") || strings.HasSuffix(p, "_test.go") {
			return nil
		}
		fset := token.NewFileSet()
		f, err := parser.ParseFile(fset, p, nil, 0)
		if err != nil || f.Name == nil || f.Name.Name != pkg {
			return nil
		}
		ast.Inspect(f, func(n ast.Node) bool {
			ts, ok := n.(*ast.TypeSpec)
			if ok && ts.Name != nil && ts.Name.Name == typ && ts.Name.IsExported() {
				found = true
			}
			return !found
		})
		return nil
	})
	if !found {
		return "no exported type of that name is declared in the repo"
	}
	return ""
}

// checkProduct enforces the PhilOcr binding: a product row is issued, or
// it is not a row. The class named by port is declared in the driver file.
func checkProduct(root string, rows []ProductCapability) []string {
	var errs []string
	seen := map[string]bool{}
	for _, row := range rows {
		if row.Name == "" {
			errs = append(errs, fmt.Sprintf("%s: a product row has no name", RosterFile))
			continue
		}
		if seen[row.Name] {
			errs = append(errs, fmt.Sprintf("%s: product %q is rostered twice", RosterFile, row.Name))
		}
		seen[row.Name] = true
		if row.Disposition != "issued" {
			errs = append(errs, fmt.Sprintf(
				"%s: product %q is %q — a product refactor is an issued port, or it is refused",
				RosterFile, row.Name, row.Disposition,
			))
			continue
		}
		module, class, ok := strings.Cut(row.Port, ".")
		if !ok || module == "" || class == "" || strings.Contains(class, ".") {
			errs = append(errs, fmt.Sprintf(
				"%s: product %q port %q must be module.Class",
				RosterFile, row.Name, row.Port,
			))
			continue
		}
		driver := filepath.Join(root, filepath.FromSlash(row.Driver))
		body, err := os.ReadFile(driver)
		if err != nil {
			errs = append(errs, fmt.Sprintf(
				"%s: product %q driver %s is missing (%v)",
				RosterFile, row.Name, row.Driver, err,
			))
			continue
		}
		stem := strings.TrimSuffix(filepath.Base(row.Driver), ".py")
		if stem != module || !strings.HasSuffix(row.Driver, ".py") || !strings.HasPrefix(filepath.ToSlash(row.Driver), "src/") {
			errs = append(errs, fmt.Sprintf(
				"%s: product %q driver %s must be src/<path>/%s.py",
				RosterFile, row.Name, row.Driver, module,
			))
			continue
		}
		if !pythonClassDeclared(string(body), class) {
			errs = append(errs, fmt.Sprintf(
				"%s: product %q port %s — class %s is not declared in %s",
				RosterFile, row.Name, row.Port, class, row.Driver,
			))
		}
	}
	return errs
}

func pythonClassDeclared(src, class string) bool {
	needle := "class " + class
	for _, line := range strings.Split(src, "\n") {
		trim := strings.TrimSpace(line)
		if strings.HasPrefix(trim, needle) {
			rest := strings.TrimPrefix(trim, needle)
			if rest == "" || rest == ":" || strings.HasPrefix(rest, "(") || strings.HasPrefix(rest, ":") {
				return true
			}
		}
	}
	return false
}

// checkDoctrine keeps the prose and the roster tied together. Doctrine that
// does not point at its enforcement is doctrine nothing holds to.
func checkDoctrine(root string) []string {
	path := filepath.Join(root, filepath.FromSlash(DoctrineFile))
	data, err := os.ReadFile(path)
	if err != nil {
		return []string{fmt.Sprintf("%s missing: %v", DoctrineFile, err)}
	}
	text := string(data)
	var errs []string
	for _, must := range []string{RosterFile, "driver", "port", "adapter", "product"} {
		if !strings.Contains(text, must) {
			errs = append(errs, fmt.Sprintf("%s never mentions %q", DoctrineFile, must))
		}
	}
	return errs
}

func sortedKeys(m map[string]Runner) []string {
	out := make([]string, 0, len(m))
	for k := range m {
		out = append(out, k)
	}
	sort.Strings(out)
	return out
}
