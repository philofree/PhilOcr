# Cursor Rules for PhilOcr

This directory contains Cursor AI rules in `.mdc` format (Markdown with YAML frontmatter) that guide AI behavior when working on the PhilOcr codebase.

## Rule Files

### Critical Priority (Zero Tolerance)

- **`exception-handling.mdc`** - Zero tolerance for silent failures, graceful degradation, and error swallowing
  - References: `rules_exception_handling.yaml`
  - Guardians: `guardian_010_catch_all_exceptions.py`, `guardian_067_silent_failures.py`

- **`dodgy-fallback.mdc`** - Zero tolerance for dodgy fallbacks and hardcoded defaults
  - References: `rules_dodgy_fallback.yaml`
  - Guardians: `guardian_044_dodgy_fallback.py`

- **`verification-testing.mdc`** - Zero mocking policy for verification
  - References: `rules_verification_snagging_shakedown.yaml`
  - Guardians: `guardian_066_test_isolation.py`

### High Priority

- **`structured-logging.mdc`** - Structured logging standards using structlog
  - References: `rules_structured_logging.yaml`
  - Guardians: `guardian_063_structured_logging.py`

- **`ui-purity.mdc`** - UI layer must remain a thin delegation wrapper
  - References: `rules_ui_purity.yaml`
  - Guardians: `guardian_030_ui_purity.py`

- **`frontend-boundary.mdc`** - Strict separation between UI and business logic layers
  - References: `rules_frontend_boundary.yaml`
  - Guardians: `guardian_061_frontend_boundary_import.py`

### Medium Priority

- **`code-quality.mdc`** - Code complexity, god classes, docstrings, security
  - References: `RULES_OVERVIEW.md`
  - Guardians: `guardian_023_code_complexity.py`, `guardian_028_god_class.py`, `guardian_065_docstring_completeness.py`, `guardian_064_secrets_leak.py`

- **`agent-hygiene.mdc`** - AI agent cleanup and hygiene requirements
  - References: `rules_agent_hygiene.yaml`, `work_reports/SPECIFICATION.md`

- **`general-standards.mdc`** - General coding standards (formatting, types, documentation)
  - References: Project standards

## How Cursor Uses These Rules

Cursor automatically loads `.mdc` files from this directory and includes them in the AI's context based on:
- `alwaysApply: true` - Rule is always included
- `globs` - File patterns that trigger the rule
- `priority` - Rule importance level

## Related Documentation

- `RULES_OVERVIEW.md` - Complete overview of all rules and guardians
- `rules_*.yaml` - Authoritative rule definitions
- `guardians/guardian_*.py` - Automated enforcement scripts
- `work_reports/SPECIFICATION.md` - Work report requirements

## Updating Rules

When updating rules:
1. Update the authoritative YAML rule file first
2. Update the corresponding `.mdc` file in this directory
3. Update `RULES_OVERVIEW.md` if needed
4. Verify guardians still enforce the rules correctly
