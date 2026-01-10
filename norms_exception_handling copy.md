# Exception Handling Agent Guidance

**Purpose:** Guide AI agents on proper exception handling patterns to prevent silent failures and maintain fail-fast policy compliance.

**Status:** Active guidance for all code changes
**Last Updated:** 2025-11-21

---

## Core Principle: Fail Fast, Not Silent

**The Golden Rule:** If an operation fails, it MUST fail loudly and visibly. Silent failures are worse than crashes.

### Why Fail-Fast?

1. **Silent failures hide bugs** - Errors that are caught and ignored create corrupt state
2. **Debugging becomes impossible** - No logs, no stack traces, no diagnostic data
3. **Production issues manifest later** - Problems compound until system is unrecoverable
4. **Violates observability** - Can't monitor what you can't see

---

## Banned Patterns (ABSOLUTELY FORBIDDEN)

### ❌ Pattern 1: Bare `except:`

```python
# BANNED - Catches EVERYTHING including KeyboardInterrupt, SystemExit
try:
    critical_operation()
except:  # ❌ ABSOLUTELY FORBIDDEN
    pass
```

**Why banned:** Catches system-level exceptions that should terminate the process.

**Fix:** Use specific exception types: `except ValueError:` or `except (TypeError, KeyError):`

---

### ❌ Pattern 2: `except Exception:` Without Re-Raise

```python
# BANNED - Too broad, swallows errors
try:
    critical_operation()
except Exception as e:  # ❌ Too broad
    logger.warning("error", error=str(e))
    # No raise - error is swallowed!
```

**Why banned:** Catches all exceptions including programming errors. If you catch it, you must either:
- Handle it properly (fix the root cause)
- Re-raise it (fail fast)
- Log and exit (fail fast with diagnostics)

**Fix:** Either use specific exceptions OR re-raise:

```python
# Option 1: Specific exceptions
except (ConnectionError, RuntimeError) as e:
    logger.error("operation_failed", error=str(e), exc_info=True)
    raise  # Re-raise to fail fast

# Option 2: Catch-all with re-raise (only for top-level handlers)
except Exception as e:
    logger.critical("unhandled_exception", error=str(e), exc_info=True)
    # Flush logger before re-raising
    import logging
    for handler in logging.root.handlers[:]:
        handler.flush()
    raise  # Re-raise to fail fast
```

---

### ❌ Pattern 3: Silent Swallowing (`pass`, `continue`, `return None`)

```python
# BANNED - Silent failure
try:
    critical_operation()
except Exception:
    pass  # ❌ Error completely ignored

# BANNED - Silent continuation
try:
    process_item(item)
except Exception:
    continue  # ❌ Error ignored, loop continues

# BANNED - Returns success on failure
try:
    result = critical_operation()
except Exception:
    return None  # ❌ Returns success value when operation failed
```

**Why banned:** Errors are completely hidden. System continues in corrupt state.

**Fix:** Log and re-raise, or handle properly:

```python
# CORRECT - Log and fail fast
try:
    critical_operation()
except Exception as e:
    logger.error("operation_failed", error=str(e), exc_info=True)
    raise RuntimeError(f"CRITICAL: Operation failed - {e}") from e

# CORRECT - Handle specific recoverable errors
try:
    process_item(item)
except ConnectionError as e:
    logger.warning("transient_error", item=item, error=str(e))
    # Retry logic or skip this item with logging
    continue  # OK if logged and error is transient
```

---

### ❌ Pattern 4: Fail-Fast Contradiction

**THE PATTERN WE JUST FIXED:**

```python
# Function says "FAIL FAST" but caller catches and continues
async def _create_edges_for_chunk(self, chunk: Dict) -> int:
    try:
        # ... operation ...
    except (OSError, ValueError, RuntimeError) as e:
        logger.error("create_edges_failed", error=str(e))
        # FAIL FAST: Edge creation failures indicate system problems
        raise RuntimeError(f"CRITICAL: Failed - {e}") from e

# Caller contradicts the function's intent
for chunk in chunks:
    try:
        await self._create_edges_for_chunk(chunk)
    except RuntimeError:  # ❌ Contradicts function's "FAIL FAST" intent
        failed_chunks.append(chunk)
        # Continue processing - violates fail-fast policy
```

**Why banned:** Function explicitly says "system corruption, cannot continue" but caller catches and continues. This creates:
- Inconsistent behavior (function says fail-fast, caller says continue)
- Hidden failures (errors logged but system continues)
- Corrupt state (system continues despite "corruption" errors)

**Fix:** Align exception handling with function's intent:

```python
# Option 1: Only catch transient errors for partial failure
for chunk in chunks:
    try:
        await self._create_edges_for_chunk(chunk)
    except ConnectionError as e:  # Only transient network errors
        logger.warning("transient_error", chunk=chunk["_key"], error=str(e))
        failed_chunks.append(chunk)
        # Continue - ConnectionError is transient, not system corruption
    # RuntimeError, ValueError, OSError propagate (fail fast)

# Option 2: Remove partial failure tolerance - fail fast on any error
for chunk in chunks:
    # No try/except - let all errors propagate
    await self._create_edges_for_chunk(chunk)
```

**Detection:** Look for:
- Function comments saying "FAIL FAST", "system corruption", "cannot continue"
- Function re-raising RuntimeError with "CRITICAL" message
- Caller catching RuntimeError and continuing
- Mismatch between function's documented intent and caller's behavior

---

## Required Patterns

### ✅ Pattern 1: Specific Exceptions with Logging and Re-Raise

```python
try:
    result = operation()
except (ValueError, TypeError) as e:
    logger.error(
        "operation_failed",
        component="component_name",
        operation="operation_name",
        error=str(e),
        error_type=type(e).__name__,
        exc_info=True,
    )
    raise  # Re-raise to fail fast
```

**When to use:** For expected, specific error types that indicate bugs or invalid state.

---

### ✅ Pattern 2: Transient Error Handling (Partial Failure Tolerance)

```python
failed_items: List[str] = []
for item in items:
    try:
        await process_item(item)
    except ConnectionError as e:
        # Transient network error - log and continue with other items
        logger.warning(
            "item_processing_failed_transient",
            component="component_name",
            item=item["_key"],
            error=str(e),
            error_type=type(e).__name__,
        )
        failed_items.append(item["_key"])
        # Continue - this is a transient error, not system corruption
    # Let RuntimeError, ValueError propagate (fail fast for system errors)

# Fail fast if too many transient errors (indicates systemic issue)
if len(failed_items) > len(items) * 0.5:
    raise RuntimeError(
        f"CRITICAL: Too many transient errors ({len(failed_items)}/{len(items)}) - "
        f"indicates systemic issue, not transient failures"
    )
```

**When to use:**
- Batch processing where individual items can fail independently
- Only catch **transient** errors (ConnectionError, temporary network issues)
- **Never** catch RuntimeError, ValueError, OSError for partial failure tolerance
- Always fail fast if failure rate indicates systemic issue

---

### ✅ Pattern 3: Top-Level Exception Handler (Main Loops)

```python
async def run(self) -> None:
    """Main worker loop - must log all crashes before exit."""
    try:
        while True:
            await self._process_items()
            await asyncio.sleep(self.poll_interval)
    except KeyboardInterrupt:
        logger.info("worker_stopped_by_user", component="worker_name")
        raise
    except Exception as e:
        # CRITICAL: Log ALL unhandled exceptions before process exit
        logger.critical(
            "worker_unhandled_exception_CRITICAL",
            component="worker_name",
            operation="run",
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True,
        )
        # Force logger to flush before process exit
        import logging
        for handler in logging.root.handlers[:]:
            handler.flush()
        # Re-raise to maintain fail-fast behavior
        raise
```

**When to use:**
- Main loops (`async def run()` methods)
- Top-level entry points
- Long-running processes

**Requirements:**
- Must catch `Exception` at top level (to log before exit)
- Must log with `exc_info=True` (full traceback)
- Must flush logger before re-raising
- Must re-raise (don't swallow)

---

### ✅ Pattern 4: Error Boundaries (Service Layer)

```python
# High-level service method - catches and wraps errors
async def process_request(self, request: Request) -> Response:
    try:
        return await self._handle_request(request)
    except (ValueError, TypeError) as e:
        # Input validation errors - return 400
        logger.warning("invalid_request", error=str(e))
        return Response(status=400, body={"error": str(e)})
    except Exception as e:
        # Unexpected errors - log and return 500
        logger.error("request_processing_failed", error=str(e), exc_info=True)
        return Response(status=500, body={"error": "Internal server error"})
```

**When to use:**
- Service boundaries (API handlers, HTTP endpoints)
- User-facing interfaces
- Where you need to convert exceptions to responses

**Requirements:**
- Log all errors (even if converting to response)
- Use appropriate HTTP status codes
- Don't expose internal details to users
- Still log full details for debugging

---

## Exception Type Guidelines

### ConnectionError
**Meaning:** Transient network/database connection issues
**Handling:** Can be caught for partial failure tolerance (retry, skip item)
**Example:** Database connection lost, network timeout

### RuntimeError
**Meaning:** System corruption, programming errors, unrecoverable state
**Handling:** **NEVER** catch for partial failure tolerance - always fail fast
**Example:** "CRITICAL: System corruption detected"

### ValueError
**Meaning:** Invalid input data or programming error
**Handling:** Usually fail fast (indicates bug), but can be caught for input validation
**Example:** Invalid enum value, None where value required

### OSError
**Meaning:** Filesystem or system-level errors
**Handling:** Usually fail fast (indicates system problems)
**Example:** Disk full, permission denied, file not found

### TypeError, AttributeError, KeyError
**Meaning:** Programming errors (bugs)
**Handling:** **NEVER** catch for partial failure tolerance - always fail fast
**Example:** Accessing attribute that doesn't exist, wrong type passed

---

## Decision Tree: Should I Catch This Exception?

```
Is this a top-level handler (main loop, entry point)?
├─ YES → Catch Exception, log with exc_info=True, flush logger, re-raise
└─ NO → Continue below

Is this a service boundary (API handler, user-facing)?
├─ YES → Catch specific exceptions, log, convert to appropriate response
└─ NO → Continue below

Is this a batch operation where individual items can fail?
├─ YES → Only catch transient errors (ConnectionError)
│        └─ Fail fast if failure rate > threshold
└─ NO → Continue below

Does the function say "FAIL FAST" or "system corruption"?
├─ YES → Don't catch RuntimeError - let it propagate
└─ NO → Continue below

Is this a specific, expected error type?
├─ YES → Catch specific type, log, re-raise or handle
└─ NO → Don't catch - let it propagate to top-level handler
```

---

## Common Mistakes

### Mistake 1: Catching RuntimeError for Partial Failure

```python
# WRONG
try:
    await critical_operation()
except RuntimeError:  # ❌ RuntimeError means system corruption
    logger.warning("error", error=str(e))
    continue  # Continuing despite "system corruption"!
```

**Fix:** Only catch transient errors (ConnectionError) for partial failure tolerance.

---

### Mistake 2: Function Says Fail-Fast But Caller Catches

```python
# Function
async def _operation(self) -> None:
    # FAIL FAST: System corruption
    raise RuntimeError("CRITICAL: Cannot continue")

# Caller
try:
    await self._operation()
except RuntimeError:  # ❌ Contradicts function's intent
    logger.warning("error")
    # Continue - violates fail-fast policy
```

**Fix:** Align exception handling with function's documented intent. If function says fail-fast, don't catch RuntimeError.

---

### Mistake 3: Logging Without Re-Raising

```python
# WRONG
try:
    critical_operation()
except Exception as e:
    logger.error("operation_failed", error=str(e))
    # No raise - error is swallowed!
    return None  # Returns success when operation failed
```

**Fix:** Always re-raise unless you're handling the error properly:

```python
# CORRECT
try:
    critical_operation()
except Exception as e:
    logger.error("operation_failed", error=str(e), exc_info=True)
    raise RuntimeError(f"CRITICAL: Operation failed - {e}") from e
```

---

## Guardian Detection

The `guardian_silent_failures` guardian detects:
- ✅ Bare `except:`
- ✅ `except Exception:` without re-raise
- ✅ `except X: pass`
- ✅ `except X: return 0/None/False`
- ✅ `except X: continue` without logging
- ✅ `except X: ...` (ellipsis placeholder)
- ✅ `except X: return` (bare return)
- ✅ `except X: # noqa` (suppressed with comment)
- ✅ `except X: logger.error(...)` without re-raise
- ✅ Main loops without exception handlers
- ✅ Re-raise without flushing logger

**TODO:** Enhance guardian to detect fail-fast contradiction pattern:
- Function comments containing "FAIL FAST", "system corruption", "cannot continue"
- Function re-raising RuntimeError with "CRITICAL" message
- Caller catching RuntimeError and continuing (contradiction)

---

## References

- `norms/norms_structured_logging.md` - Logging requirements
- `norms/norms_verification_doctrine.yaml` - Verification doctrine (fail-fast philosophy)
- `src/guardian_cluster/` - Guardian detection patterns (planned: guardian_silent_failures.yaml)

---

## Summary

1. **Fail fast, not silent** - Errors must be visible and logged
2. **Specific exceptions** - Catch only what you can handle
3. **Re-raise by default** - Unless you're handling the error properly
4. **Align intent** - Don't contradict function's documented fail-fast behavior
5. **Transient errors only** - Only ConnectionError for partial failure tolerance
6. **Log before exit** - Top-level handlers must log and flush before re-raising

**Remember:** Silent failures are worse than crashes. A crashed system is visible and can be fixed. A silently failing system creates corrupt state that manifests later.



















