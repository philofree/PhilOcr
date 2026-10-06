package predicatecmd

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

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

// TestPredicateRegistry audits the live repo. It never t.Skip()s — it reads
// only the source tree.
func TestPredicateRegistry(t *testing.T) {
	if errs := Check(repoRoot(t)); len(errs) > 0 {
		t.Fatalf("predicate audit:\n  %s", strings.Join(errs, "\n  "))
	}
}

// --- planted faults ---------------------------------------------------------

func base() Registry {
	return Registry{
		ArtefactKind: "predicate_registry",
		FamilyLaw:    "../eukoine/.eukoine/predicate_vocabulary.md",
		Rules: map[string]string{
			"one_signifier_one_referent": "one signifier, one referent",
			"on_correction_delete":       "delete the wrong word",
			"consult_before_coin":        "consult first",
			"identity_breaks":            "no mutation, re-derivation, aliasing, polysemy",
		},
		Baptisms:    map[string]string{},
		Banned:      []Banned{},
		ExemptPaths: []string{RegistryFile},
	}
}

func lab(t *testing.T, r Registry, files map[string]string) string {
	t.Helper()
	root := t.TempDir()
	data, err := json.Marshal(r)
	if err != nil {
		t.Fatal(err)
	}
	write(t, filepath.Join(root, RegistryFile), string(data))
	// One prose file always exists so the clean-zero refusal is not what
	// fires when a different fault is under test.
	write(t, filepath.Join(root, "README.md"), "# fixture\n")
	for name, body := range files {
		write(t, filepath.Join(root, name), body)
	}
	return root
}

func write(t *testing.T, path, body string) {
	t.Helper()
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(path, []byte(body), 0o644); err != nil {
		t.Fatal(err)
	}
}

func wantErr(t *testing.T, root, substr string) {
	t.Helper()
	errs := Check(root)
	if len(errs) == 0 {
		t.Fatal("audit passed a registry it should have refused")
	}
	if joined := strings.Join(errs, "\n"); !strings.Contains(joined, substr) {
		t.Fatalf("audit fired but not on the planted fault.\nwant: %s\ngot:\n%s", substr, joined)
	}
}

// The rule the whole registry exists for: a synonym left standing beside the
// word that replaced it.
func TestGoesRedOnTwoSignifiersOneReferent(t *testing.T) {
	r := base()
	r.Baptisms = map[string]string{
		"russian_crib": "The Russian reading of the disc",
		"rus_crib":     "the   RUSSIAN reading of the Disc",
	}
	root := lab(t, r, nil)
	wantErr(t, root, "share one referent")
}

func TestGoesRedOnARetiredSignifierInProse(t *testing.T) {
	r := base()
	r.Banned = []Banned{{
		ID: "bare_crib", Pattern: `\bthe crib\b`,
		Replacement: "russian_crib when the Russian reading is meant; a crib / the three cribs for the kind",
	}}
	root := lab(t, r, map[string]string{"docs/note.md": "we read the crib for this\n"})
	wantErr(t, root, "retired signifier (bare_crib)")
}

func TestUnlessMakesALongerCompoundLawful(t *testing.T) {
	r := base()
	r.Banned = []Banned{{
		ID: "bare_crib", Pattern: `\bcrib\b`, Replacement: "russian_crib",
		Unless: []string{"russian_crib", "tlgu_crib", "diogenes_crib"},
	}}
	root := lab(t, r, map[string]string{"docs/note.md": "russian_crib is one of three\n"})
	if errs := Check(root); len(errs) > 0 {
		t.Fatalf("lawful compound refused:\n  %s", strings.Join(errs, "\n  "))
	}
}

func TestGoesRedOnAMissingRule(t *testing.T) {
	r := base()
	delete(r.Rules, "on_correction_delete")
	root := lab(t, r, nil)
	wantErr(t, root, `rule "on_correction_delete" is missing`)
}

func TestGoesRedOnABanWithNoReplacement(t *testing.T) {
	r := base()
	r.Banned = []Banned{{ID: "x", Pattern: `\bzzz\b`}}
	root := lab(t, r, nil)
	wantErr(t, root, "names no replacement")
}

func TestGoesRedOnAnUncompilablePattern(t *testing.T) {
	r := base()
	r.Banned = []Banned{{ID: "x", Pattern: `[unclosed`, Replacement: "y"}}
	root := lab(t, r, nil)
	wantErr(t, root, "does not compile")
}

func TestGoesRedWhenFamilyLawIsUncited(t *testing.T) {
	r := base()
	r.FamilyLaw = ""
	root := lab(t, r, nil)
	wantErr(t, root, "family_law is unset")
}

// An audit that scanned nothing is not evidence of a clean repo.
func TestRefusesACleanZeroScan(t *testing.T) {
	r := base()
	r.ExemptPaths = []string{RegistryFile, "README.md"}
	root := lab(t, r, nil)
	wantErr(t, root, "refusing a clean zero")
}

func TestPassesWhenTheRegistryIsHonest(t *testing.T) {
	r := base()
	r.Baptisms = map[string]string{
		"russian_crib":  "the Russian reading of the disc",
		"tlgu_crib":     "the TLGU reading of the disc",
		"diogenes_crib": "the Diogenes reading of the disc",
	}
	root := lab(t, r, map[string]string{"docs/note.md": "three cribs: russian_crib, tlgu_crib, diogenes_crib\n"})
	if errs := Check(root); len(errs) > 0 {
		t.Fatalf("honest registry refused:\n  %s", strings.Join(errs, "\n  "))
	}
}

// --- family registry cross-check --------------------------------------------

const familyFixture = `artefact_kind: predicate_lexicon
repo: eukoine

entries:

  eul_wid:
    signifier_form: eul_wid
    canonical_referent: >-
      The canonical primary database key of a Work.
    status: aligned

  slug:
    signifier_form: [slug, slugs, url_slug]
    canonical_referent: "A url-safe identifier string derived from a title."
    status: retired
`

// A sibling ../eukoine checkout is an external dependency of this repo, not
// a part of it. Its absence (a fresh clone, CI, a repo seeded elsewhere)
// must not fail the audit.
func TestFamilyRegistryAbsentIsNotADefect(t *testing.T) {
	r := base()
	r.FamilyRegistry = "../eukoine/.eukoine/predicate_lexicon.yaml"
	r.Baptisms = map[string]string{"suite_local_thing": "a referent nobody else has"}
	root := lab(t, r, map[string]string{"docs/note.md": "suite_local_thing appears here\n"})
	if errs := Check(root); len(errs) > 0 {
		t.Fatalf("missing family registry should not be this repo's defect:\n  %s", strings.Join(errs, "\n  "))
	}
}

// Minting a signifier the family registry already baptised — even under an
// alias, not the entry's primary key — is exactly what "consult before
// coining" forbids.
func TestGoesRedOnABaptismThatDuplicatesTheFamilyRegistry(t *testing.T) {
	r := base()
	r.FamilyRegistry = "family/predicate_lexicon.yaml"
	r.Baptisms = map[string]string{"slugs": "our local id-from-title string"}
	root := lab(t, r, map[string]string{
		"family/predicate_lexicon.yaml": familyFixture,
		"docs/note.md":                  "slugs appears here\n",
	})
	wantErr(t, root, `duplicates family entry "slug"`)
}

// A different word for a referent the family already named is the cross-
// repo half of "one signifier, one referent".
func TestGoesRedOnABaptismThatAliasesAFamilyReferent(t *testing.T) {
	r := base()
	r.FamilyRegistry = "family/predicate_lexicon.yaml"
	r.Baptisms = map[string]string{"local_wid": "The canonical primary database key of a Work."}
	root := lab(t, r, map[string]string{
		"family/predicate_lexicon.yaml": familyFixture,
		"docs/note.md":                  "local_wid appears here\n",
	})
	wantErr(t, root, `and family entry "eul_wid"`)
}

func TestPassesWhenTheLocalBaptismIsGenuinelyAbsentFromTheFamily(t *testing.T) {
	r := base()
	r.FamilyRegistry = "family/predicate_lexicon.yaml"
	r.Baptisms = map[string]string{"suite_local_thing": "a referent nobody else has"}
	root := lab(t, r, map[string]string{
		"family/predicate_lexicon.yaml": familyFixture,
		"docs/note.md":                  "suite_local_thing appears here\n",
	})
	if errs := Check(root); len(errs) > 0 {
		t.Fatalf("genuinely local baptism refused:\n  %s", strings.Join(errs, "\n  "))
	}
}
