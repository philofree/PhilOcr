# Gov Sweep checklist — per-repo pass

| | |
|---|---|
| **Title** | references/sweep_checklist.md — the per-repo checklist of one Gov Sweep pass |
| **Status** | Binding while a pass is running |
| **Authority level** | 3 — a reference of [`../SKILL.md`](../SKILL.md), which owns the procedure |
| **Scope** | One `gov_sweep` pass over one repository |
| **Relationship-to** | Serves [`../SKILL.md`](../SKILL.md); the grain pair it tests is owned by [`.eukoine/predicate_lexicon.yaml`](../../../../.eukoine/predicate_lexicon.yaml) and the carrier by [`.eukoine/document_contract.md`](../../../../.eukoine/document_contract.md). Restates neither. Synced from the EuKoine hub; never hand-edited in a mirror |
| **Document class** | procedure |
| **Contract** | `epitomikon/document-contract/v1` |

## Before cut

- [ ] Inventory rows derived (Epitomikon profile ∪ `git ls-files` from the schema globs); only `disposition` / `owner_target` hand-set
- [ ] Epitomikon profile frozen (operational mode); output outside the tree
- [ ] Blind cold-read complete **before** reading the profile
- [ ] First question answered: which spans Grain Collapse?
- [ ] Second question answered: where is Grain Preservation held — test, port, or graph row?
- [ ] Assessment artefact contains exactly eight `layer_row` records, one per `layer_id` in `assessment_schema.yaml` (completeness rule). Missing, extra, or duplicate ids: the pass is not a pass
- [ ] Each `layer_row` quotes `job_stated` from the resolved path, or `(none)`, and sets `points_at_telos`
- [ ] `skip` on a layer_row names `skip_reason`; "did not look" does not appear
- [ ] Campaign rows included for every open/doing graph node, with regulator and `grain_preserving`
- [ ] Cut brief names authorized vs deferred dispositions
- [ ] No new synonym beside `grain_collapse`, `grain_elimination`, `grain_preservation`, `gov_sweep`, `governing_document_restatement`
- [ ] The word "semantic" appears nowhere a verbal explanation is meant (lexicon: `semantic`, polysemic)

## Owners only (default grain test)

- [ ] `/gov-sweep` — this pass
- [ ] `/epitomikon` — whole-surface observations
- [ ] `/doc-cold-reading` — one-concern topology when unclear

## Parsimony

- [ ] `Parsimony: cut|add|fix` on every commit
- [ ] `Retires:` names paths the diff actually shrinks or replaces
- [ ] Chronicles (`docs/DECISIONS.md`, `work_reports/`) not rewritten

## Done for one repo

- [ ] Every inventory row's disposition resolved or explicitly deferred
- [ ] The member's `gov_sweep_member_pass` task node `done` with proof (graph repos)
- [ ] The campaign of record's proof updated when the last enrolled member closes
