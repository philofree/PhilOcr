// Package predicatecmd audits this repo's baptised vocabulary.
//
// It is the linguistic half of referent conservation. capability_port.md
// protects the identity of DATA as it crosses a boundary; PREDICATES.json
// protects the identity of WORDS as they cross a document. The same four
// operations break both: mutation, re-derivation, aliasing, equivocal
// polysemy.
//
// The rule this exists to hold is the parsimony contract applied to
// language: on correction, DELETE the wrong word — never add a synonym
// beside it. A synonym left standing next to the term that replaced it is
// an addition with no retirement, which is liquefaction (docs/ROT.md).
//
// The family law at ../eukoine/.eukoine/predicate_vocabulary.md is
// authoritative and obliges every family repo. This package holds the local
// registry to it; it does not restate its entries. When a sibling
// ../eukoine checkout is present, it goes further and reads the family
// registry (predicate_lexicon.yaml) directly, so "consult before coining"
// and "one signifier, one referent" are audited across the repo boundary,
// not just cited in prose. When no sibling checkout is present (a fresh
// clone, a CI runner, a repo seeded from this template elsewhere), that
// cross-check is skipped — the family registry is external to this repo
// and its absence is not this repo's defect.
package predicatecmd

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
)

// RegistryFile is the repo-root contract, owned by the repo.
const RegistryFile = "PREDICATES.json"

type Banned struct {
	ID          string   `json:"id"`
	Pattern     string   `json:"pattern"`
	Replacement string   `json:"replacement"`
	Unless      []string `json:"unless,omitempty"`
}

type Registry struct {
	ArtefactKind   string            `json:"artefact_kind"`
	FamilyLaw      string            `json:"family_law"`
	FamilyRegistry string            `json:"family_registry"`
	Rules          map[string]string `json:"rules"`
	Baptisms       map[string]string `json:"baptisms"`
	Banned         []Banned          `json:"banned"`
	WireDebt       map[string]string `json:"wire_debt"`
	ExemptPaths    []string          `json:"exempt_paths"`
}

// requiredRules are the four the family law imposes. A registry that drops
// one has quietly narrowed the obligation.
var requiredRules = []string{
	"one_signifier_one_referent",
	"on_correction_delete",
	"consult_before_coin",
	"identity_breaks",
}

// scanned extensions: prose and code alike. A retired word in a comment is
// still a retired word.
var scanExt = map[string]bool{
	".md": true, ".mdc": true, ".go": true, ".yaml": true, ".yml": true,
	".json": true, ".sh": true, ".py": true, ".ts": true, ".js": true,
}

// Check runs the audit. Every return is a defect, never a warning.
func Check(root string) []string {
	raw, err := os.ReadFile(filepath.Join(root, RegistryFile))
	if err != nil {
		return []string{fmt.Sprintf("%s unreadable: %v — without it no predicate is baptised and nothing is retired", RegistryFile, err)}
	}
	var r Registry
	if err := json.Unmarshal(raw, &r); err != nil {
		return []string{fmt.Sprintf("%s does not parse: %v", RegistryFile, err)}
	}

	var errs []string
	errs = append(errs, checkShape(root, r)...)
	errs = append(errs, checkFamily(root, r)...)
	scanErrs, filesScanned := scan(root, r)
	errs = append(errs, scanErrs...)

	// Prove the instrument ran. An audit that scanned nothing and reported
	// nothing is indistinguishable from a clean repo, and is not evidence.
	if filesScanned == 0 {
		errs = append(errs, "the audit scanned no files — refusing a clean zero; a scan that visited nothing has not proved the vocabulary is held")
	}
	return errs
}

func checkShape(root string, r Registry) []string {
	var errs []string

	if r.ArtefactKind != "predicate_registry" {
		errs = append(errs, fmt.Sprintf("%s: artefact_kind is %q, want \"predicate_registry\"", RegistryFile, r.ArtefactKind))
	}

	for _, want := range requiredRules {
		if strings.TrimSpace(r.Rules[want]) == "" {
			errs = append(errs, fmt.Sprintf("%s: rule %q is missing — the family law imposes it; dropping it narrows the obligation", RegistryFile, want))
		}
	}

	if r.FamilyLaw == "" {
		errs = append(errs, fmt.Sprintf("%s: family_law is unset — the obligation is cited, not restated", RegistryFile))
	}

	// One signifier, one referent — enforced on the registry itself. Two
	// baptisms sharing a referent is the aliasing the first rule forbids.
	byReferent := map[string][]string{}
	for sig, ref := range r.Baptisms {
		key := strings.Join(strings.Fields(strings.ToLower(ref)), " ")
		if key == "" {
			errs = append(errs, fmt.Sprintf("%s: baptism %q states no referent — a signifier with no referent is a name", RegistryFile, sig))
			continue
		}
		byReferent[key] = append(byReferent[key], sig)
	}
	for _, sigs := range byReferent {
		if len(sigs) > 1 {
			sort.Strings(sigs)
			errs = append(errs, fmt.Sprintf("%s: %s share one referent — one signifier, one referent. Delete the wrong word; do not keep both", RegistryFile, strings.Join(sigs, " and ")))
		}
	}

	// A banned pattern that is itself a live baptism would refuse the word
	// the registry tells you to use.
	for _, b := range r.Banned {
		if b.ID == "" || b.Pattern == "" {
			errs = append(errs, fmt.Sprintf("%s: a banned entry has no id or no pattern", RegistryFile))
			continue
		}
		if _, err := regexp.Compile(b.Pattern); err != nil {
			errs = append(errs, fmt.Sprintf("%s: banned %q pattern does not compile: %v", RegistryFile, b.ID, err))
		}
		if strings.TrimSpace(b.Replacement) == "" {
			errs = append(errs, fmt.Sprintf("%s: banned %q names no replacement — a ban with no replacement retires a word into nothing", RegistryFile, b.ID))
		}
	}
	return errs
}

// FamilyEntry is one baptism read from the family registry
// (predicate_lexicon.yaml on the EuKoine hub). Only the fields this audit
// needs are extracted; the family registry's other fields (canonical_sense,
// owner, pipeline_reach, cites, …) are the family's own concern and are
// deliberately not restated here (WRITE_ACCESS.md § No secondary sources).
type FamilyEntry struct {
	Key      string
	Forms    []string
	Referent string
	Status   string
}

var familyEntryKeyRe = regexp.MustCompile(`^  ([A-Za-z_][A-Za-z0-9_.-]*):\s*$`)
var familyFieldRe = regexp.MustCompile(`^    ([A-Za-z_][A-Za-z0-9_]*):(.*)$`)
var familyBlockMarkerRe = regexp.MustCompile(`^[|>][+-]?\d*$`)

// checkFamily cross-checks local baptisms against the family registry when
// a sibling ../eukoine checkout makes it readable. A missing family
// registry is not a defect of this repo — it is an external, optional
// dependency (a fresh clone or a CI runner will not have it). A family
// registry that is present but fails to parse, or a local baptism that
// duplicates or aliases one already in the family registry, is a defect.
func checkFamily(root string, r Registry) []string {
	if r.FamilyRegistry == "" || len(r.Baptisms) == 0 {
		return nil
	}
	data, err := os.ReadFile(filepath.Join(root, r.FamilyRegistry))
	if err != nil {
		if os.IsNotExist(err) {
			return nil
		}
		return []string{fmt.Sprintf("%s: family_registry %q unreadable: %v", RegistryFile, r.FamilyRegistry, err)}
	}
	family := parseFamilyLexicon(data)
	if len(family) == 0 {
		return []string{fmt.Sprintf("%s: family_registry %q parsed to zero entries — refusing a clean zero; the cross-check has not proved the family lexicon is held", RegistryFile, r.FamilyRegistry)}
	}

	bySig := map[string]FamilyEntry{}
	byRef := map[string][]FamilyEntry{}
	for _, e := range family {
		forms := e.Forms
		if len(forms) == 0 {
			forms = []string{e.Key}
		}
		for _, f := range forms {
			if f != "" {
				bySig[f] = e
			}
		}
		bySig[e.Key] = e
		if ref := normalizeReferent(e.Referent); ref != "" {
			byRef[ref] = append(byRef[ref], e)
		}
	}

	var errs []string
	for sig, ref := range r.Baptisms {
		if fam, ok := bySig[sig]; ok {
			note := ""
			if fam.Status == "retired" {
				note = " (family status: retired — see the family registry for its replacement, not this word)"
			}
			errs = append(errs, fmt.Sprintf(
				"%s: baptism %q duplicates family entry %q in %s%s — consult before coining; mint locally only a referent absent from the family registry",
				RegistryFile, sig, fam.Key, r.FamilyRegistry, note))
			continue
		}
		if fams, ok := byRef[normalizeReferent(ref)]; ok {
			for _, fam := range fams {
				errs = append(errs, fmt.Sprintf(
					"%s: baptism %q and family entry %q in %s share one referent — one signifier, one referent; delete the local word or use the family's",
					RegistryFile, sig, fam.Key, r.FamilyRegistry))
			}
		}
	}
	sort.Strings(errs)
	return errs
}

func normalizeReferent(s string) string {
	return strings.Join(strings.Fields(strings.ToLower(s)), " ")
}

func familyIndent(line string) int {
	return len(line) - len(strings.TrimLeft(line, " "))
}

func familyUnquote(s string) string {
	s = strings.TrimSpace(s)
	if len(s) >= 2 && s[0] == '"' && s[len(s)-1] == '"' {
		inner := s[1 : len(s)-1]
		inner = strings.ReplaceAll(inner, `\"`, `"`)
		inner = strings.ReplaceAll(inner, `\\`, `\`)
		return inner
	}
	if len(s) >= 2 && s[0] == '\'' && s[len(s)-1] == '\'' {
		inner := s[1 : len(s)-1]
		inner = strings.ReplaceAll(inner, `''`, `'`)
		return inner
	}
	return s
}

// familySplitFlow splits a YAML flow-sequence body (the inside of `[...]`)
// on top-level commas, respecting quoted elements that may themselves be
// arbitrary text.
func familySplitFlow(inner string) []string {
	var out []string
	var buf strings.Builder
	inQuote := false
	var quoteChar byte
	for i := 0; i < len(inner); i++ {
		c := inner[i]
		if inQuote {
			buf.WriteByte(c)
			if c == quoteChar {
				inQuote = false
			}
			continue
		}
		switch c {
		case '"', '\'':
			inQuote = true
			quoteChar = c
			buf.WriteByte(c)
		case ',':
			out = append(out, strings.TrimSpace(buf.String()))
			buf.Reset()
		default:
			buf.WriteByte(c)
		}
	}
	if s := strings.TrimSpace(buf.String()); s != "" {
		out = append(out, s)
	}
	return out
}

func familyParseFormValue(val string) []string {
	val = strings.TrimSpace(val)
	if strings.HasPrefix(val, "[") && strings.HasSuffix(val, "]") {
		parts := familySplitFlow(val[1 : len(val)-1])
		out := make([]string, 0, len(parts))
		for _, p := range parts {
			out = append(out, familyUnquote(p))
		}
		return out
	}
	if val == "" {
		return nil
	}
	return []string{familyUnquote(val)}
}

// familyCollectBlock gathers a folded/literal block scalar's continuation
// lines (indent > parentIndent) starting at lines[start]. Returns the
// joined text (folded: newlines become spaces) and the index of the first
// line not consumed.
func familyCollectBlock(lines []string, start, parentIndent int) (string, int) {
	var parts []string
	i := start
	for i < len(lines) {
		line := lines[i]
		if strings.TrimSpace(line) == "" {
			i++
			continue
		}
		if familyIndent(line) <= parentIndent {
			break
		}
		parts = append(parts, strings.TrimSpace(line))
		i++
	}
	return strings.Join(parts, " "), i
}

func familySkipNested(lines []string, start, parentIndent int) int {
	i := start
	for i < len(lines) {
		line := lines[i]
		if strings.TrimSpace(line) == "" {
			i++
			continue
		}
		if familyIndent(line) <= parentIndent {
			break
		}
		i++
	}
	return i
}

// parseFamilyLexicon reads only what this audit needs from the family
// registry's `entries:` map: each entry's key, its signifier_form (scalar
// or flow-list aliases), its canonical_referent (inline or folded block
// scalar), and its status. Every other field (canonical_sense, owner,
// pipeline_reach, used_at, variant_senses, polysemy_debt, cites, the
// ban-table projection, …) is the family registry's own concern — this is
// not a general YAML parser and does not attempt to hold them (stdlib-only:
// this repo's tooling carries no dependencies, and the family registry is
// read-only from here in any case — WRITE_ACCESS.md § No secondary
// sources).
func parseFamilyLexicon(data []byte) map[string]FamilyEntry {
	entries := map[string]FamilyEntry{}
	lines := strings.Split(string(data), "\n")
	inEntries := false
	var cur *FamilyEntry

	flush := func() {
		if cur != nil && cur.Key != "" {
			entries[cur.Key] = *cur
		}
		cur = nil
	}

	i := 0
	for i < len(lines) {
		line := strings.TrimRight(lines[i], "\r")
		trimmed := strings.TrimSpace(line)

		if trimmed == "" || strings.HasPrefix(trimmed, "#") {
			i++
			continue
		}

		if !inEntries {
			if trimmed == "entries:" {
				inEntries = true
			}
			i++
			continue
		}

		indent := familyIndent(line)

		if indent == 0 {
			flush()
			inEntries = false
			i++
			continue
		}

		if indent == 2 {
			if m := familyEntryKeyRe.FindStringSubmatch(line); m != nil {
				flush()
				cur = &FamilyEntry{Key: m[1]}
			} else {
				flush()
			}
			i++
			continue
		}

		if cur == nil {
			i++
			continue
		}

		if indent == 4 {
			if m := familyFieldRe.FindStringSubmatch(line); m != nil {
				field, val := m[1], strings.TrimSpace(m[2])
				switch field {
				case "signifier_form":
					cur.Forms = familyParseFormValue(val)
				case "status":
					cur.Status = familyUnquote(val)
				case "canonical_referent":
					if familyBlockMarkerRe.MatchString(val) {
						text, next := familyCollectBlock(lines, i+1, 4)
						cur.Referent = text
						i = next
						continue
					}
					cur.Referent = familyUnquote(val)
				default:
					if val == "" {
						i = familySkipNested(lines, i+1, 4)
						continue
					}
				}
			}
		}
		i++
	}
	flush()
	return entries
}

func scan(root string, r Registry) ([]string, int) {
	var errs []string
	if len(r.Banned) == 0 {
		// Nothing retired yet is a legitimate state for a young repo, but
		// the walk still runs so the clean-zero refusal above stays honest.
		return nil, countTracked(root, r)
	}

	type compiled struct {
		b  Banned
		re *regexp.Regexp
	}
	var pats []compiled
	for _, b := range r.Banned {
		re, err := regexp.Compile(b.Pattern)
		if err != nil {
			continue // already reported by checkShape
		}
		pats = append(pats, compiled{b, re})
	}

	files := trackedFiles(root)
	scanned := 0
	for _, rel := range files {
		if !scanExt[strings.ToLower(filepath.Ext(rel))] || exempt(rel, r.ExemptPaths) {
			continue
		}
		f, err := os.Open(filepath.Join(root, rel))
		if err != nil {
			continue
		}
		scanned++
		sc := bufio.NewScanner(f)
		sc.Buffer(make([]byte, 0, 64*1024), 4*1024*1024)
		for n := 1; sc.Scan(); n++ {
			line := sc.Text()
			for _, p := range pats {
				if !p.re.MatchString(line) || lawful(line, p.b.Unless) {
					continue
				}
				errs = append(errs, fmt.Sprintf("%s:%d: retired signifier (%s) — use %s", rel, n, p.b.ID, p.b.Replacement))
			}
		}
		f.Close()
	}
	return errs, scanned
}

func lawful(line string, unless []string) bool {
	for _, u := range unless {
		if strings.Contains(line, u) {
			return true
		}
	}
	return false
}

func exempt(rel string, paths []string) bool {
	for _, p := range paths {
		if p == rel || (strings.HasSuffix(p, "/") && strings.HasPrefix(rel, p)) {
			return true
		}
	}
	return false
}

// trackedFiles asks git for the census: the rule covers what the repository
// holds, and git is the authority on that. Falls back to a walk outside a
// repo so the audit still runs in a test fixture.
func trackedFiles(root string) []string {
	out, err := exec.Command("git", "-C", root, "ls-files", "-z").Output()
	if err == nil && len(out) > 0 {
		var files []string
		for _, s := range strings.Split(string(out), "\x00") {
			if s != "" {
				files = append(files, s)
			}
		}
		return files
	}
	var files []string
	_ = filepath.WalkDir(root, func(p string, d os.DirEntry, err error) error {
		if err != nil {
			return nil
		}
		if d.IsDir() {
			switch d.Name() {
			case ".git", "vendor", "node_modules", "bin", "out":
				return filepath.SkipDir
			}
			return nil
		}
		if rel, err := filepath.Rel(root, p); err == nil {
			files = append(files, filepath.ToSlash(rel))
		}
		return nil
	})
	return files
}

func countTracked(root string, r Registry) int {
	n := 0
	for _, rel := range trackedFiles(root) {
		if scanExt[strings.ToLower(filepath.Ext(rel))] && !exempt(rel, r.ExemptPaths) {
			n++
		}
	}
	return n
}
