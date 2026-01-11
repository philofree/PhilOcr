# PhilOcr Rules and Guardians Overview

**Version**: 1.0.0  
**Date**: 2026-01-11  
**Purpose**: Comprehensive reference guide for all rules and guardians in the PhilOcr project

---

## Table of Contents

1. [Rules Documentation](#rules-documentation)
2. [Guardians (Automated Enforcement)](#guardians-automated-enforcement)
3. [Rules-to-Guardians Mapping](#rules-to-guardians-mapping)
4. [Enforcement Strategy](#enforcement-strategy)
5. [Quick Reference](#quick-reference)

---

## Rules Documentation

The PhilOcr project maintains authoritative rules in YAML format that define coding standards, architectural principles, and best practices. All rules are **MANDATORY** and enforced through automated guardians.

### Core Rules

#### 1. `rules_exception_handling.yaml`
**Purpose**: Fail-fast exception handling doctrine  
**Status**: AUTHORITATIVE - Zero Tolerance Policy  
**Version**: 1.0.0

**Key Principles**:
- **ZERO TOLERANCE** for silent failures, graceful degradation, and error swallowing
- All failures MUST fail loudly, visibly, and immediately
- All exceptions MUST be logged with `exc_info=True` before re-raising
- `flush_loggers()` MUST be called before re-raising exceptions

**Prohibited Patterns**:
- Silent failures (catching exceptions and continuing without logging)
- Graceful degradation (continuing with degraded functionality)
- Swallowed exceptions (caught but not logged or re-raised)
- Return `False`/`None` after error handling without raising

**Enforcement**: `guardian_010_catch_all_exceptions.py`, `guardian_067_silent_failures.py`

**Cross-references**:
- `rules_structured_logging.yaml` (exception logging requirements)
- `rules_verification_snagging_shakedown.yaml` (fail-fast philosophy)
- `rules_dodgy_fallback.yaml` (hardcoded fallback prohibition)

---

#### 2. `rules_structured_logging.yaml`
**Purpose**: Canonical structured logging guide using structlog  
**Status**: AUTHORITATIVE  
**Version**: 1.0.0  
**Migration Status**: ✅ COMPLETE (as of 2026-01-09)

**Key Principles**:
- Events not messages: Log **events that happen** with structured context
- Event name is first positional argument, followed by keyword arguments
- Never use `event` as a keyword argument (causes TypeError)
- Never wrap structured data in `extra` dictionary
- Binding is immutable - must reassign returned logger

**Critical Anti-Patterns**:
- Using `event` as keyword argument (CRITICAL - causes crash)
- `extra` dictionary wrapper (HIGH - architectural mistake)
- Ignoring returned bound logger (HIGH - context lost)
- Multiple configuration calls (MEDIUM - inconsistent behavior)

**Enforcement**: `guardian_063_structured_logging.py`

**Cross-references**:
- `rules_exception_handling.yaml` (exception logging requirements)
- `src/philocr/utils/logging_config.py` (configuration implementation)

---

#### 3. `rules_dodgy_fallback.yaml`
**Purpose**: Infrastructure must fail loudly, not silently  
**Status**: AUTHORITATIVE - Zero Tolerance Policy  
**Version**: 1.0.0

**Key Principles**:
- **ZERO TOLERANCE** for dodgy fallbacks, silent fallbacks, and graceful degradation
- Infrastructure failures MUST fail loudly and immediately
- No automatic creation of default instances when infrastructure is missing
- No lazy initialization without validation

**Prohibited Patterns**:
- Dodgy fallbacks: `x or SomeClass()` (creating instances in fallback patterns)
- Silent fallbacks: Automatically creating default instances
- Graceful degradation: Continuing with degraded infrastructure
- Lazy initialization: Creating instances on first access without validation

**Enforcement**: `guardian_044_dodgy_fallback.py`

**Cross-references**:
- `rules_exception_handling.yaml` (fail-fast philosophy)

---

#### 4. `rules_ui_purity.yaml`
**Purpose**: UI layer must remain a thin delegation wrapper  
**Status**: AUTHORITATIVE  
**Version**: 1.0.0

**Key Principles**:
- UI layer must be a thin delegation wrapper
- Complex business logic belongs in workers/utils layers
- UI methods should only: receive input, delegate to workers/utils, update UI state, handle user-facing errors

**Prohibited Patterns**:
- Complex business logic in UI methods
- File I/O operations in UI methods
- Data transformations in UI methods
- Complex algorithms in UI methods

**Enforcement**: `guardian_030_ui_purity.py`

**Cross-references**:
- `rules_frontend_boundary.yaml` (import boundary enforcement)

---

#### 5. `rules_frontend_boundary.yaml`
**Purpose**: Strict separation between UI and business logic layers  
**Status**: AUTHORITATIVE  
**Version**: 1.0.0

**Key Principles**:
- Frontend (UI) and backend (processing) layers must remain strictly separated
- No cross-layer imports are allowed
- Backend must not know about UI
- Workers are boundary components (UI can import workers)

**Architecture Layers**:
- **Frontend**: `src/philocr/ui/` - User interface, input handling, UI state
- **Backend**: `src/philocr/processing/` - Business logic, document processing, OCR
- **Cross-cutting**: `src/philocr/utils/` - Utilities used by both layers
- **Boundary**: `src/philocr/workers/` - Bridge between UI and processing

**Prohibited Patterns**:
- UI layer importing backend processing modules directly
- Backend importing UI modules
- Circular dependencies

**Enforcement**: `guardian_061_frontend_boundary_import.py`

**Cross-references**:
- `rules_ui_purity.yaml` (UI layer architecture)

---

#### 6. `rules_verification_snagging_shakedown.yaml`
**Purpose**: The scientific method for software verification  
**Status**: AUTHORITATIVE  
**Version**: 2.1.0

**Key Principles**:
- Verifs are EXPERIMENTS, not logical proofs
- Use `verif_*.py` naming (NOT `test_*.py`)
- **ZERO MOCKING** - NO Mock, MagicMock, patch, @patch, AsyncMock
- All exceptions MUST be logged before propagation
- Real components only: Google Document AI API, PyQt6 UI, filesystem, network, PDF processing

**Core Principle**:
1. Hypothesis: "System should work"
2. Experiment: Run REAL system with REAL data
3. Observation: Capture empirical evidence (telemetry, state changes)
4. Conclusion: Does evidence prove it works?

**Enforcement**: `guardian_066_test_isolation.py` (checks for mocking violations)

**Cross-references**:
- `rules_structured_logging.yaml` (exception logging requirements)
- `rules_exception_handling.yaml` (fail-fast patterns)

---

#### 7. `rules_agent_hygiene.yaml`
**Purpose**: Prevent AI agents from generating junk and polluting codebase  
**Status**: AUTHORITATIVE  
**Version**: 2.0.0

**Key Principles**:
- AI agents must behave like responsible, professional developers
- Clean up after yourself - delete temporary artifacts
- Avoid duplicate documentation
- Write maintainable code, not throwaway code
- Respect existing project structure

**Prohibited Patterns**:
- Multiple README files
- Duplicate explanatory files
- Transient documentation in permanent directories
- Throwaway verification scripts left behind
- Backup files (*.backup, *_original, versioned names)
- Utility scripts that never get maintained

**Enforcement**: Manual review, work report requirements

**Cross-references**:
- `work_reports/SPECIFICATION.md` (cleanup requirements)

---

## Guardians (Automated Enforcement)

Guardians are automated code quality checks that analyze the codebase and detect violations of the rules. All guardians run automatically via pre-commit hooks and can be run manually.

### Active Guardians

#### `guardian_010_catch_all_exceptions.py`
**Purpose**: Detect broad or bare exception handlers and silent failures  
**Enforces**: `rules_exception_handling.yaml`

**Detects**:
- Broad exception handlers: `except Exception as e:`
- Bare exception handlers: `except:`
- Error swallowed after logging (exception logged but not re-raised)
- Exception re-raised without logging

**Severity Levels**:
- **ERROR**: Error swallowed after logging (in infrastructure code)
- **WARNING**: Broad exception handler (in acceptable boundaries like UI/workers)

**Exceptions**: Configurable via `guardian_010_catch_all_exceptions_exceptions.json`

**Score Calculation**: 100 - (errors × 10) - (warnings × 2)

---

#### `guardian_067_silent_failures.py`
**Purpose**: Detect silent failures in exception handlers  
**Enforces**: `rules_exception_handling.yaml`

**Detects**:
- `SILENT_FAILURE_LOGGED_NOT_RAISED`: Exception logged but not re-raised
- `RETURN_FALSE_AFTER_ERROR`: `return False` after error handling
- `RETURN_NONE_AFTER_ERROR`: `return None` after error handling
- `SILENT_FAILURE_NO_HANDLING`: Exception caught but not logged or re-raised

**Severity**: All violations are **ERROR** level (zero tolerance policy)

**Scope**: All Python files except tests and guardian files

---

#### `guardian_044_dodgy_fallback.py`
**Purpose**: Hunt for dodgy fallback logic  
**Enforces**: `rules_dodgy_fallback.yaml`

**Detects**:
- `x or SomeClass()` patterns (creating instances in fallback)
- Ternary fallbacks: `x if condition else SomeClass()`
- Dictionary `.get()` with object creation fallback
- `getattr()` with object creation fallback

**Severity**: All violations are **ERROR** level (zero tolerance policy)

**Scope**: All Python files except tests and guardian files

---

#### `guardian_063_structured_logging.py`
**Purpose**: Enforce structured logging standards  
**Enforces**: `rules_structured_logging.yaml`

**Detects**:
- Using `event` as keyword argument (CRITICAL)
- `extra` dictionary wrapper (HIGH)
- Ignoring returned bound logger (HIGH)
- Multiple configuration calls (MEDIUM)
- String formatting in log messages (MEDIUM)
- Missing structured context (LOW)

**Severity Levels**: CRITICAL, HIGH, MEDIUM, LOW

**Scope**: All Python files except exempt files (tests, guardians, config files)

---

#### `guardian_030_ui_purity.py`
**Purpose**: Ensure UI layer remains a thin delegation wrapper  
**Enforces**: `rules_ui_purity.yaml`

**Detects**:
- Complex business logic in UI methods
- File I/O operations in UI methods
- Data transformations in UI methods
- Complex algorithms in UI methods

**Severity**: All violations are **ERROR** level

**Scope**: Files in `src/philocr/ui/` directory

---

#### `guardian_061_frontend_boundary_import.py`
**Purpose**: Enforce strict layer separation  
**Enforces**: `rules_frontend_boundary.yaml`

**Detects**:
- Backend modules importing UI modules
- Cross-layer import violations

**Severity**: All violations are **ERROR** level

**Scope**: All Python files

---

#### `guardian_023_code_complexity.py`
**Purpose**: Detect code complexity anti-patterns  
**Enforces**: General code quality standards

**Detects**:
- Long functions (> 50 lines)
- Deep nesting (> 4 levels)
- Too many parameters (> 5)
- Large modules (> 500 lines)

**Severity Levels**: HIGH, MEDIUM, LOW (based on thresholds)

**Scope**: All Python files

---

#### `guardian_028_god_class.py`
**Purpose**: Detect potential God Classes  
**Enforces**: General code quality standards

**Detects**:
- Oversized classes (> 300 lines)
- Too many methods (> 10)
- Low cohesion (< 0.8)

**Thresholds**:
- MAX_LINES: 300
- MAX_METHODS: 10
- MIN_COHESION: 0.8
- MIN_METHODS_FOR_COHESION: 3

**Severity**: All violations are **ERROR** level

**Scope**: All Python files except tests

---

#### `guardian_065_docstring_completeness.py`
**Purpose**: Ensure all public functions/classes have docstrings  
**Enforces**: Documentation standards

**Detects**:
- Missing docstrings on public functions
- Missing docstrings on public classes
- Missing docstrings on public methods

**Severity**: All violations are **WARNING** level

**Scope**: All Python files

---

#### `guardian_066_test_isolation.py`
**Purpose**: Detect mocking violations in tests  
**Enforces**: `rules_verification_snagging_shakedown.yaml`

**Detects**:
- Use of `Mock`, `MagicMock`, `AsyncMock`
- Use of `@patch`, `patch()`, `mock.patch`
- Zero mocking policy violations

**Severity**: All violations are **ERROR** level (zero mocking policy)

**Scope**: Test files (`test_*.py`, `verif_*.py`)

---

#### `guardian_064_secrets_leak.py`
**Purpose**: Detect potential secrets leaks in code  
**Enforces**: Security standards

**Detects**:
- Hardcoded API keys
- Hardcoded passwords
- Hardcoded tokens
- Hardcoded credentials

**Severity**: All violations are **CRITICAL** level

**Scope**: All Python files

---

## Rules-to-Guardians Mapping

| Rule File | Guardian(s) | Enforcement Level |
|-----------|-------------|-------------------|
| `rules_exception_handling.yaml` | `guardian_010_catch_all_exceptions.py`<br>`guardian_067_silent_failures.py` | Zero Tolerance |
| `rules_structured_logging.yaml` | `guardian_063_structured_logging.py` | Mandatory |
| `rules_dodgy_fallback.yaml` | `guardian_044_dodgy_fallback.py` | Zero Tolerance |
| `rules_ui_purity.yaml` | `guardian_030_ui_purity.py` | Mandatory |
| `rules_frontend_boundary.yaml` | `guardian_061_frontend_boundary_import.py` | Mandatory |
| `rules_verification_snagging_shakedown.yaml` | `guardian_066_test_isolation.py` | Zero Tolerance |
| `rules_agent_hygiene.yaml` | Manual review (work reports) | Mandatory |

---

## Enforcement Strategy

### Pre-commit Hooks
All guardians run automatically before commits via `.pre-commit-guardians.py`. Commits are blocked if guardians detect violations.

### Manual Execution
Guardians can be run manually:
```bash
# Run all guardians
python3 guardians/run_all_guardians.py --root .

# Run specific guardian
python3 guardians/guardian_010_catch_all_exceptions.py path/to/file.py
```

### Exception Lists
Some guardians support exception lists for legitimate cases:
- `guardian_010_catch_all_exceptions_exceptions.json` - Documents UI/worker boundaries with proper error handling

### Zero Tolerance Policies
The following rules have **ZERO TOLERANCE** policies:
- Silent failures (`rules_exception_handling.yaml`)
- Graceful degradation (`rules_exception_handling.yaml`)
- Hardcoded fallbacks (`rules_dodgy_fallback.yaml`)
- Mocking in tests (`rules_verification_snagging_shakedown.yaml`)

**NO EXCEPTIONS** are allowed for zero tolerance policies.

---

## Quick Reference

### Most Critical Rules
1. **Zero Tolerance for Silent Failures** - All errors must fail loudly
2. **Zero Tolerance for Mocking** - Use real components in verification
3. **Structured Logging** - Events not messages, structured context
4. **UI Purity** - UI is thin wrapper, logic in workers/utils
5. **Layer Separation** - No cross-layer imports

### Guardian Priority
1. **CRITICAL**: `guardian_064_secrets_leak.py` (security)
2. **ERROR**: `guardian_067_silent_failures.py`, `guardian_044_dodgy_fallback.py` (zero tolerance)
3. **ERROR**: `guardian_010_catch_all_exceptions.py` (infrastructure code)
4. **WARNING**: `guardian_010_catch_all_exceptions.py` (UI/worker boundaries)
5. **WARNING**: `guardian_065_docstring_completeness.py` (documentation)

### Common Violations
- **Silent failures**: Returning `False`/`None` after error handling
- **Dodgy fallbacks**: `x or SomeClass()` patterns
- **Structured logging**: Using `event` as keyword argument
- **UI purity**: Complex logic in UI methods
- **Layer separation**: Backend importing UI modules

---

## Related Documentation

- `work_reports/SPECIFICATION.md` - Work report requirements and zero tolerance policy
- `guardians/framework/core/guardian_base_class.py` - Guardian base class
- `guardians/run_all_guardians.py` - Guardian runner
- `.pre-commit-guardians.py` - Pre-commit hook integration

---

**Last Updated**: 2026-01-11  
**Maintained By**: PhilOcr Development Team
