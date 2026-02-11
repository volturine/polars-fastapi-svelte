# Code Review Report: Nuclear Thrush (PR #14) vs DEV

**Reviewed by:** @copilot  
**Date:** 2026-02-11  
**Branch:** nuclear-thrush → dev  
**Changes:** 57 files, +3534/-542 lines  
**Review Standards:** High confidence (>80%) only, actionable feedback

---

## Executive Summary

**Issues Found:** 16 HIGH CONFIDENCE issues across Security, Correctness, and Architecture

| Category | Critical | High | Medium | Total |
|----------|----------|------|--------|-------|
| **Security** | 1 | 1 | 1 | 3 |
| **Correctness** | 3 | 3 | 3 | 9 |
| **Architecture** | 0 | 5 | 1 | 6 |
| **TOTAL** | 4 | 9 | 5 | 18 |

**Immediate Action Required:** 4 CRITICAL issues must be fixed before merge

---

## 🔴 CRITICAL Issues (Fix Immediately)

### 1. SQL Injection via DuckDB Table Name
**File:** `backend/modules/compute/service.py:459`  
**Severity:** CRITICAL  
**Confidence:** 95%

```python
conn.execute(f'CREATE TABLE {table_name} AS SELECT * FROM read_parquet(?)', [tmp_output])
```

**Problem:** User-controlled `table_name` from `DuckDBExportOptions` is interpolated directly into SQL via f-string.

**Attack:** `table_name="data; DROP TABLE users; --"` → `CREATE TABLE data; DROP TABLE users; -- AS SELECT...`

**Fix:**
```python
# Validate table name with strict whitelist
import re
if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
    raise ValueError(f"Invalid table name: {table_name}")
conn.execute(f'CREATE TABLE {table_name} AS SELECT * FROM read_parquet(?)', [tmp_output])
```

---

### 2. File Handle Leak on Export Failure
**File:** `backend/modules/compute/service.py:467-468`  
**Severity:** CRITICAL  
**Confidence:** 99%

```python
except Exception:
    if os.path.exists(tmp_db_path):
        os.unlink(tmp_db_path)
    raise
    # UNREACHABLE - tmp_output never cleaned up!
    if os.path.exists(tmp_output):
        os.unlink(tmp_output)
```

**Problem:** Cleanup code after `raise` is unreachable. Parquet file leaks on DuckDB conversion errors.

**Fix:**
```python
except Exception:
    if os.path.exists(tmp_db_path):
        os.unlink(tmp_db_path)
    if os.path.exists(tmp_output):
        os.unlink(tmp_output)
    raise
```

---

### 3. Pagination Boundary Bug (Off-by-One)
**File:** `frontend/src/lib/components/viewers/InlineDataTable.svelte:94-95`  
**Severity:** CRITICAL  
**Confidence:** 90%

```typescript
let canNext = $derived(pageSize === rowLimit);
```

**Problem:** Assumes full page = more data exists. If data count is exact multiple of `rowLimit`, last page incorrectly shows "Next" button leading to empty fetch.

**Fix:**
```typescript
// Backend should return has_more flag
let canNext = $derived(preview.data?.has_more ?? false);

// OR use total count approach:
let canNext = $derived(
    preview.data?.total_count != null && 
    currentPage * rowLimit < preview.data.total_count
);
```

---

### 4. Stale Query Key Missing Pagination
**File:** `frontend/src/lib/components/viewers/InlineDataTable.svelte:50`  
**Severity:** CRITICAL  
**Confidence:** 85%

```typescript
const runKey = $derived(`${datasource.id}-${snapshot?.id}-${JSON.stringify(pipeline)}`);
```

**Problem:** `currentPage` not included in cache key. With `staleTime: Infinity`, pagination shows wrong data.

**Fix:**
```typescript
const runKey = $derived(
    `${datasource.id}-${snapshot?.id}-${currentPage}-${JSON.stringify(pipeline)}`
);
```

---

## 🟠 HIGH Severity Issues

### 5. Race Condition on current_job_id
**File:** `backend/modules/compute/engine.py:242-244`  
**Severity:** HIGH  
**Confidence:** 80%

**Problem:** `current_job_id` set before queue put, cleared only on result. If job fails/times out, ID persists causing false health check failures.

**Fix:**
```python
# In timeout/error paths, add:
self.current_job_id = None
```

---

### 6. Exception Details Leakage
**File:** `backend/modules/engine_runs/routes.py:31`, `backend/core/error_handlers.py:77,110,128`  
**Severity:** HIGH  
**Confidence:** 85%

**Problem:** Full exception strings returned to HTTP clients expose paths, configs, versions.

**Fix:**
```python
# In error_handlers.py, replace:
detail=str(exc)
# with:
detail="An internal error occurred"
# Log full exception server-side only
```

---

### 7. Memory Leak in reorderSteps
**File:** `frontend/src/lib/stores/analysis.svelte.ts:475-482`  
**Severity:** HIGH  
**Confidence:** 80%

**Problem:** `reorderSteps` doesn't deep copy configs. Mutated objects leak between states.

**Fix:**
```typescript
const movedStep = {
    ...steps[fromIndex],
    config: JSON.parse(JSON.stringify(steps[fromIndex].config))
};
```

---

### 8. Missing Null Checks in Store
**File:** `frontend/src/lib/stores/analysis.svelte.ts:310,372,429-431`  
**Severity:** HIGH  
**Confidence:** 80%

**Problem:** `steps[index - 1]?.id` could be undefined but used without validation.

**Fix:** Add explicit null checks before operations.

---

### 9. Try/Catch Anti-Pattern (engine_runs)
**File:** `backend/modules/engine_runs/routes.py:20-31`  
**Severity:** HIGH  
**Confidence:** 90%

**Problem:** Violates STYLE_GUIDE.md ("Avoid try/catch where possible"). Other routes use `@handle_errors` decorator.

**Fix:**
```python
@router.get('/engine-runs', response_model=EngineRunListResponse)
@handle_errors(operation='list engine runs')
async def list_engine_runs(...):
    return service.list_engine_runs(...)  # Remove try/except
```

---

## 🟡 MEDIUM Severity Issues

### 10. Multiprocessing Queue Leak
**File:** `backend/modules/compute/engine.py:66-67`  
**Severity:** MEDIUM  
**Confidence:** 75%

**Problem:** Creating fresh `mp.Queue()` instances doesn't close old ones.

**Fix:** Call `.close()` on old queues before replacement.

---

### 11. Unvalidated Query Execution
**File:** `backend/modules/compute/operations/datasource.py:105`  
**Severity:** MEDIUM  
**Confidence:** 75%

**Problem:** `config.query` executed without validation (privilege escalation if datasource config compromised).

**Note:** Lower priority - requires prior compromise of datasource creation.

---

## 🔵 Architecture & Pattern Violations

### 12. Optional Type Anti-Pattern
**File:** `frontend/src/lib/components/datasources/DatasourcePreview.svelte:8`  
**Severity:** MEDIUM  
**Confidence:** 95%

```typescript
datasourceConfig?: Record<string, unknown> | null;
```

**Problem:** Per STYLE_GUIDE.md, using both `?` and `| null` is redundant. Should default to sensible value.

**Fix:**
```typescript
datasourceConfig: Record<string, unknown> = {};
```

---

### 13. $effect Anti-Pattern (Data Transformation)
**File:** `frontend/src/lib/components/viewers/InlineDataTable.svelte:97-106`  
**Severity:** HIGH  
**Confidence:** 95%

```typescript
$effect(() => {
    // $derived can't reset paging when the preview scope changes.
    void resetKey;
    currentPage = 1;
});
```

**Problem:** AGENTS.md line 102 explicitly forbids `$effect` for "data initialization, validation, derived state... transforming props/state". Must be side-effect only.

**Fix:**
```typescript
// Use $derived.by() instead
let currentPage = $derived.by(() => {
    void resetKey;
    return 1;
});
```

---

### 14. Unnecessary Comments (Restate Code)
**Files:** 
- `frontend/src/lib/components/viewers/InlineDataTable.svelte:97,102-103`
- `frontend/src/lib/components/pipeline/PipelineCanvas.svelte:43,46,187,195,200`  
**Severity:** LOW  
**Confidence:** 99%

**Problem:** STYLE_GUIDE.md: "Don't add comments unless they match the style of other comments in the file or are necessary to explain a complex change."

**Examples:**
```typescript
// Reset page when key dependencies change  ← Delete (obvious from code)
// Derived: whether we can accept drops  ← Delete (obvious from code)
// Check if pointer is near the bottom  ← Delete (obvious from code)
```

**Fix:** Remove all comments that restate what code clearly shows.

---

### 15. Silent Type Ignores
**File:** `backend/modules/engine_runs/service.py:72,74,76,78,80`  
**Severity:** LOW  
**Confidence:** 80%

**Problem:** Multiple `# type: ignore[arg-type]` without justification.

**Fix:** Add comments explaining why type ignores are necessary or fix type issues.

---

### 16. Bare ValueError in Decorated Context
**File:** `backend/modules/compute/routes.py:190`  
**Severity:** MEDIUM  
**Confidence:** 70%

**Problem:** Raising `ValueError` inside `@handle_errors` decorated function may bypass error handler.

**Fix:** Raise domain-specific exception or verify decorator handles ValueError correctly.

---

## Summary & Recommendations

### Must Fix Before Merge (CRITICAL)
1. ✅ SQL injection in DuckDB table name (service.py:459)
2. ✅ File handle leak on export failure (service.py:467)
3. ✅ Pagination boundary bug (InlineDataTable.svelte:94)
4. ✅ Stale query key missing currentPage (InlineDataTable.svelte:50)

### Should Fix (HIGH Priority)
5. Race condition on current_job_id cleanup
6. Exception details leakage to HTTP clients
7. Memory leak in reorderSteps
8. Missing null checks in analysis store
9. Try/catch anti-pattern in engine_runs routes

### Nice to Fix (MEDIUM/LOW)
10-16. Architecture and pattern compliance issues

### Testing Recommendations
- **Security:** Test SQL injection with malicious table names
- **Correctness:** Test pagination at exact page boundaries
- **Architecture:** Verify all Svelte components follow runes-only pattern

---

**Next Steps:**
1. Fix 4 CRITICAL issues immediately
2. Address HIGH severity issues before merge
3. Consider MEDIUM issues for follow-up PR
4. Run full test suite after fixes
