# Canonical Design Principles — PhilOcr

| | |
|---|---|
| **Title** | design/CANONICAL_DESIGN_PRINCIPLES.md — pipeline invariants |
| **Status** | Binding |
| **Authority level** | 3 — below docs/GOVERNANCE.md, beside docs/ROT.md |
| **Scope** | How a scanned page becomes structured Greek, and the invariants of that pipeline |
| **Relationship-to** | Serves `docs/PURPOSE.md`. Forbidden shapes: `design/anti_patterns.jsonl`. Enforcement: `guardians/` |
| **Document class** | authority |
| **Contract** | `epitomikon/document-contract/v1` |

**tags:** `#canonical-design-principles` `#pipeline-architecture` `#single-authority`
`#fail-loud` `#ui-purity` `#layer-separation` `#structured-logging`
`#zero-mock` `#subtractive-closure` `#minimum-topology`
`#greek-normalisation` `#config-authority` `#agent-hygiene`
`#integration-over-addition` `#rate-limiter-as-infrastructure`

**This is the canonical source for the pipeline and its invariants.**
This document defines *what* and *why*. The guardians enforce *how*.
Anti-patterns that violate these principles live in
`design/anti_patterns.jsonl`.

---

## §0 The Scopos — target state

**The job, one sentence:** Take a scanned PDF of an ancient Greek text
and produce clean, accurate, Unicode polytonic Greek in a format that
can enter the Philofree open corpus.

**The four stages are the architecture.** Each stage has one job and one
owner. The minimum topology that can carry the scopos is:

```
Stage 1 Normalize   PDF → grayscale, deskewed PNG images
Stage 2 Mask        Apply user-defined scan areas and whiteout masks
Stage 3 OCR         Google Document AI → raw structured OCR result
Stage 4 Assemble    Raw result → clean Greek text with document structure
```

Plus: `ui/` (thin display layer), `workers/` (boundary: runs the pipeline
off the main thread), `models/` (shared typed data), `utils/` (cross-cutting
concerns owned once). No more layers than these.

**Acceptance criteria (all three must hold):**
```bash
python -m pytest tests/ -x -q              # zero failures
python guardians/run_all_guardians.py --root .  # zero ERROR findings on touched files
python -m pyright src/                     # zero structural errors (wrong signature, broken protocol, undefined reference)
```

**Direction of travel:** fewer files, fewer hops, simpler models, one
place per concern. A change that adds structure without retiring an
equivalent or greater amount is moving away from the scopos.

**Tags:** `#scopos` `#minimum-topology` `#pipeline-architecture`

---

## §1 The Pipeline is the Architecture

**Each stage has exactly one job and one owner.** Stage 1 normalises
images. Stage 2 applies masks. Stage 3 calls Google Document AI. Stage 4
assembles text. A stage that reaches into another stage's territory — an
assembler that re-normalises, a masker that calls OCR — is a violation of
this principle, not a shortcut.

**Pipeline boundaries are typed.** The output of each stage is a typed
model (`models/`). Stages communicate through those types. No stage passes
raw dicts, untyped tuples, or `Any`-typed objects to the next.

**The orchestrator coordinates, never processes.** `pipeline/orchestrator.py`
sequences stages. It does not perform normalisation, masking, or text
transformation. Orchestration logic that leaks into stages or processing
logic that leaks into the orchestrator is a violation of single authority
(§3).

**Why:** The 4-stage shape is the unit of reasoning, testing, and
evolution. Blurring boundaries makes stages impossible to test in isolation,
impossible to evolve independently, and impossible to reason about.

**Anti-patterns:** AP-006 (stage contamination), AP-010 (non-load-bearing
indirection between stages)

**Tags:** `#pipeline-architecture` `#single-authority`

---

## §2 Single Authority per Concern

**Every piece of state, every semantic interpretation, every write path
has exactly one owner.** There is one place that parses DocAI output
(`processing/document_ai.py`). One place that normalises polytonic
Greek (§10). One place that holds the rate limiter (§13). One place
that owns a given model field's value.

**Multiple writers produce drift.** When two code paths can write
the same state, they will diverge. When two interpreters parse the
same input, they will disagree. The fix is always to consolidate to
one, not to add a third to arbitrate.

**Why:** Distributed authority is the root cause of "fixed it in one
place, broken in another." Every discovered bug of this type is a
violation of §2.

**Anti-patterns:** AP-007 (parallel DocAI interpreters), AP-009 (Greek
normalisation proliferation), AP-011 (config fallback at runtime),
AP-008 (rate limiter bypass)

**Tags:** `#single-authority`

---

## §3 Fail Loud — Zero Tolerance for Silent Failures

**Infrastructure failures must be visible and immediate.** All exceptions
must be logged with `exc_info=True` before re-raising. `flush_loggers()`
must be called before re-raising. Returning `False`, `None`, or a default
value after catching an exception is a silent failure and a zero-tolerance
violation.

**No graceful degradation.** An OCR processor that silently produces
no output because a Google API call failed is worse than one that crashes
with a clear error. The user can retry a crash; they cannot recover from
invisible data loss.

**No dodgy fallbacks.** `x or SomeClass()` silently creates a default
instance when the real thing is absent. The correct shape is: validate at
startup that all dependencies are present; crash immediately if they are
not.

**Why:** This application processes irreplaceable scholarly data. A bug
that swallows an exception can delete a page of Greek text without the
user knowing. The cost of invisible failure is unbounded; the cost of a
visible crash is a restart.

**Guardians:** `guardian_067_silent_failures.py`, `guardian_010_catch_all_exceptions.py`,
`guardian_044_dodgy_fallback.py`
**Anti-patterns:** AP-001 (silent failure), AP-002 (dodgy fallback)

**Tags:** `#fail-loud` `#zero-tolerance`

---

## §4 UI Purity — UI is a Thin Delegation Wrapper

**The `ui/` layer receives user input, delegates to workers or utilities,
updates display state, and shows user-facing errors. Nothing else.** File
I/O, data transformation, OCR orchestration, format conversion, and
algorithmic work do not belong in `ui/`. A UI method longer than ~15 lines
of delegation is evidence of violation.

**UI does not compute.** `main_window.py` does not know what a `BoundingBox`
is or how to parse a DocAI response. It knows how to show progress, display
results, and forward user gestures to workers.

**Why:** UI purity is the precondition for testable business logic. Logic
embedded in `QMainWindow` subclasses cannot be tested without a running
Qt application. Logic in workers and utilities can be tested directly.

**Guardian:** `guardian_030_ui_purity.py`
**Anti-pattern:** AP-003 (UI second engine)

**Tags:** `#ui-purity`

---

## §5 Layer Separation — No Cross-Layer Imports

**The four layers form a one-way dependency graph:**

```
ui/          → workers/, utils/, models/
workers/     → pipeline/, processing/, utils/, models/
pipeline/    → processing/, utils/, models/
processing/  → utils/, models/
utils/       → models/
models/      → (nothing in src/)
```

**Backend never imports frontend.** `processing/document_ai.py` does not
import `ui/main_window.py`. `pipeline/stage3_ocr.py` does not import
`workers/`. Circular dependencies are always a violation.

**Workers are the boundary.** The `workers/` layer exists specifically
to bridge UI events and background processing. It may import from both
`ui/` (to emit signals) and `pipeline/` (to invoke stages), but only in
that role.

**Why:** Layer inversion couples the OCR engine to Qt. This makes the
engine untestable without a display, makes it impossible to run headless,
and makes every dependency on the Google Cloud client also a dependency
on PyQt6.

**Guardian:** `guardian_061_frontend_boundary_import.py`
**Anti-pattern:** AP-004 (layer boundary violation)

**Tags:** `#layer-separation`

---

## §6 Structured Logging — Events Not Messages

**All logging uses structlog. Events are things that happen; they are not
formatted messages.** The event name is the first positional argument:
`logger.info("ocr_page_complete", page=3, duration_ms=450)`. Never:
`logger.info(event="ocr_page_complete", ...)` (causes TypeError). Never:
`logger.info("page complete", extra={"page": 3})` (extra wrapper loses
context).

**Loggers are bound immutably.** `log = log.bind(component="stage3")`
returns a new logger. The original is unchanged. Ignoring the return value
loses context silently.

**Exceptions are logged before propagation.** Every `except` block that
re-raises must call `log.error("...", exc_info=True)` and
`flush_loggers()` before the `raise`.

**Why:** The app processes large batches of PDFs. When something fails,
the structured log is the only post-hoc evidence. Unstructured or
silent logging makes failures invisible in batch mode.

**Guardian:** `guardian_063_structured_logging.py`

**Tags:** `#structured-logging`

---

## §7 Zero-Mock Verification

**Verification uses real components, real files, real APIs.** No
`Mock`, `MagicMock`, `patch`, `@patch`, or `AsyncMock` in any
verification or test file. A test that mocks the Google Document AI
client is not a test of OCR; it is a test of the mock.

**`verif_*.py` files are experiments, not logical proofs.** The
hypothesis is "this component behaves correctly." The experiment
runs the real component against real input. The observation is
empirical evidence.

**Why:** PhilOcr's quality bar is the accuracy of output Greek text
against source. No mock can verify that the polytonic normalization
step produces the right diacritics. Only a real round-trip through
real OCR output can.

**Guardian:** `guardian_066_test_isolation.py`
**Anti-pattern:** AP-005 (mock contamination)

**Tags:** `#zero-mock`

---

## §8 Subtractive Closure — Eliminate Rot, Resist Liquefaction

**Rot** is the cross-repo name for non-load-bearing or expired-and-still-live
structure: code that costs maintenance but carries no invariant, dead
branches never reached, shims that forward unchanged, handlers with no
callers, documentation that describes what no longer exists.

**Liquefaction** is the structural failure that rot causes over time. It
is named by analogy: apparently solid ground that loses definition under
load. In a codebase, liquefaction is when the 4-stage pipeline stops
being four discrete stages — when the masker starts normalising, when the
assembler starts calling the Google API, when UI methods accumulate the
logic that should live in workers. Boundaries dissolve, authority
disperses, and the app can still "work" while its structure has become
untrustworthy. Liquefaction is harder to see than rot and harder to fix:
it requires re-establishing the stage boundary, not just deleting a dead
function.

**Every task must leave the edit zone with zero or negative rot.** "Edit
zone" means files you modify plus files you read in direct support of the
task. Rot seen in the edit zone is retired in the same turn — not
ticketed, not tagged as stale, not deferred.

**Code rot signatures:**
- UI methods with file I/O, data transformation, or business logic (§4) — early liquefaction
- Backend code importing from `ui/` or `workers/` (§5) — layer boundary rot
- Silent exception handlers — `except … pass`, catch-and-return-False (§3)
- Dodgy fallbacks — `x or SomeClass()` (§3)
- `Mock`/`patch` in test files (§7)
- Direct Google API calls bypassing the rate limiter (§13)
- Multiple places normalising polytonic Greek (§10) — authority liquefaction
- Dead pipeline stage functions with no callers
- `event=...` keyword in structlog calls (§6)
- `extra={...}` wrapper in log calls (§6)
- No-op shims that only forward to another function

**Documentary rot signatures:**
- Architecture docs showing old file structure
- Rules files with examples from deleted classes
- Work reports citing methods or classes that no longer exist
- Principles stated in present tense that the code has already superseded

**The liquefaction test:** Can you look at any file in `pipeline/` or
`processing/` and name its single job in one sentence without hedging?
If the answer requires "and also…", liquefaction has begun. Cure is
structural — re-establish the stage boundary, not add a comment.

**Why:** The bias of AI-assisted development is additive. Every session
adds helpers, adapters, intermediate layers. Without active subtraction,
the codebase grows away from the scopos and the 4-stage architecture
liquefies into a single entangled mass. Rot and liquefaction are not
different problems: rot is the precursor, liquefaction is what rot
becomes when ignored.

**Anti-pattern:** AP-006 (stage contamination), AP-012 (speculative
infrastructure)

**Tags:** `#subtractive-closure` `#code-rot` `#liquefaction`

---

## §9 Minimum Topology — Derive Structure from Requirements

**Before proposing any structural change, answer these questions:**

> What job is being done?
> How few lines of code can we use?
> Which files can we delete completely?
> What is the minimal possible structure for this?
> Where does this belong in the existing 4-stage pipeline?

**Add structure only when the existing owners cannot absorb the
obligation.** A new class, module, or helper must pass all five criteria
of AP-010 (non-load-bearing indirection) — if it doesn't add authority
narrowing, invariant enforcement, semantic transformation, genuine reuse,
or boundary error isolation, it doesn't exist.

**The pipeline stages are the primary owners.** Before creating a new
utility, check whether the stage that uses it could simply do the work
directly. Most "utility" abstractions are single-caller indirections that
exist because they felt cleaner at the time.

**Anti-pattern:** AP-010 (non-load-bearing indirection), AP-012 (speculative
infrastructure)

**Tags:** `#minimum-topology`

---

## §10 Single Greek Normaliser

**There is exactly one place in the codebase that normalises polytonic
Unicode Greek text.** All stages that need normalised Greek call that
one place. No stage reimplements Greek character decomposition,
combining diacritics handling, or NFC/NFD conversion.

**Why:** Ancient Greek has multiple valid Unicode representations of the
same glyph (composed vs. decomposed forms, variant combining character
sequences). Two normalisers will produce subtly different output. The
Philofree corpus requires bit-for-bit consistent normalisation across
all source texts.

**Anti-pattern:** AP-009 (Greek normalisation proliferation)

**Tags:** `#single-authority` `#greek-normalisation`

---

## §11 Config Authority — Environment is the Runtime Authority

**Runtime configuration is read from environment variables (`.env` /
`ENV.local`) only.** There are no hardcoded defaults in runtime code.
If a required environment variable is absent, the application raises
immediately at startup — it does not substitute a default.

**`env_config.json` is bootstrap/packaging data, not a runtime authority.**
Build scripts may embed it in the application bundle. The running
application reads from the OS environment, not from `env_config.json`
at runtime.

**Credentials never live in source files.** Google Cloud service account
keys, project IDs, and processor IDs live in `.env` / `ENV.local` only.
`guardian_064_secrets_leak.py` enforces this.

**Why:** Hardcoded defaults mask misconfiguration. An OCR processor
running against the wrong Google Cloud project silently bills the wrong
account and potentially writes to the wrong corpus. Missing-env-var crashes
are cheap; wrong-account silences are expensive.

**Guardian:** `guardian_064_secrets_leak.py`
**Anti-pattern:** AP-011 (config fallback at runtime), AP-014 (credentials in source)

**Tags:** `#config-authority`

---

## §12 Agent Hygiene — No Ephemeral Artifacts

**AI agents must not leave temporary files, backup copies, versioned
alternatives, duplicate documentation, or experimental scripts in the
repository.** Work reports go in `work_reports/`. Everything else is
cleaned up before the session closes.

**Prohibited residue:** `*.backup`, `*_original.*`, `*_v2.*`, `test_*.py`
files created for one-time investigation, alternative README files,
`NOTES.md` or `TODO.md` files, commented-out old implementations.

**Work reports are not residue, and they are not owed by every session.**
When one is written, `work_reports/SPECIFICATION.md` owns its shape.
When one is written is owned by `.claude/skills/close/SKILL.md`: the
campaign graph and the one live handover come first.

**Tags:** `#agent-hygiene`

---

## §13 The Rate Limiter is Infrastructure — Not Callers' Concern

**All Google Document AI API calls route through `RateLimiter`
inside `processing/document_ai.py`.** No call site bypasses it.
No stage, worker, or utility calls the Google client directly.
The rate limiter is not optional and not the caller's responsibility
to invoke.

**Why:** Google Document AI has a hard rate limit (15 requests/minute
on the default quota). A single stage that bypasses the rate limiter
will exhaust the quota for the entire batch, producing opaque 429 errors
that look like network failures.

**Anti-pattern:** AP-008 (rate limiter bypass)

**Tags:** `#single-authority` `#rate-limiter-as-infrastructure`

---

## §14 Integration over Addition

**Absorb new obligations into the existing owning causal chain before
creating a new file, class, or function.** The right question is not
"where should I put this?" but "which existing owner already has
responsibility for this concern?"

**New surfaces require justification against five criteria:**
1. Does it add authority narrowing?
2. Does it enforce an invariant the owner cannot enforce internally?
3. Does it perform a semantic transformation?
4. Is there genuine reuse (two or more independent call sites)?
5. Does it provide boundary error isolation?

If none of the five hold, integrate into the owner. If any holds,
a new surface is justified — and only then.

**Anti-pattern:** AP-010 (non-load-bearing indirection), AP-012 (speculative
infrastructure)

**Tags:** `#integration-over-addition` `#minimum-topology`
