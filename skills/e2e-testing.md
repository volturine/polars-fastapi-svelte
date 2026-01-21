# E2E Testing Skill

Use this skill when running end-to-end tests for the polars-fastapi-svelte project.

## Quick Start

```bash
# Start services
cd /home/kripso/workspace/polars-fastapi-svelte
uv run main.py &    # Backend on port 8000
cd frontend
npm run dev -- --port 5173 --host &  # Frontend on port 5173

# Run tests via Playwright MCP
```

## Prompt Template

Use this template when testing new features:

```
Test [FEATURE] at http://192.168.1.140:5173

CURRENT PROGRESS:
- [What was tested before]

TASK: Test [FEATURE]

Steps:
1. [Test step 1]
2. [Test step 2]
3. [Test step 3]

BACKEND: http://localhost:8000

Report back: Success/failure, any errors, config options visible.
```

## Checklist for Complete E2E Coverage

### Phase 1: Home Page

- [ ] Gallery display (analyses cards)
- [ ] Search functionality
- [ ] Sort functionality (Newest, Oldest, A-Z, Z-A)
- [ ] Navigation to analysis editor
- [ ] New Analysis button
- [ ] Delete with confirmation

### Phase 2: Create Analysis Wizard

- [ ] Step 1: Analysis details (name, description)
- [ ] Step 2: Data source selection
- [ ] Step 3: Review & Create
- [ ] Back navigation preserves values
- [ ] Validation (empty name blocks next)

### Phase 3: Data Sources

- [ ] List page display
- [ ] File upload (CSV, Parquet, JSON)
- [ ] Database connection form
- [ ] API connection form
- [ ] Delete datasource with confirmation

### Phase 4: Analysis Editor

- [ ] 3-pane layout (Library, Canvas, Config)
- [ ] Theme toggle
- [ ] Operations library (all 21 operations)
- [ ] Pipeline canvas (add, select, delete steps)
- [ ] Config panel for each operation
- [ ] Save/load persistence

### Phase 5: Operations

Test each operation:

- [ ] filter
- [ ] select
- [ ] drop
- [ ] group_by
- [ ] sort
- [ ] rename
- [ ] join
- [ ] expression
- [ ] pivot
- [ ] unpivot
- [ ] fill_null
- [ ] deduplicate
- [ ] explode
- [ ] timeseries
- [ ] string_transform
- [ ] sample
- [ ] limit
- [ ] topk
- [ ] null_count
- [ ] value_counts
- [ ] view
- [ ] export

### Phase 6: Engine Lifecycle

- [ ] Engine creation on page open
- [ ] Engine listing in monitor
- [ ] Keepalive pings
- [ ] Manual shutdown
- [ ] State persistence

### Phase 7: Export

- [ ] Export to CSV
- [ ] Export to Parquet
- [ ] Export to JSON
- [ ] Export to NDJSON

### Phase 8: Error Handling

- [ ] Invalid column names (blocked by UI)
- [ ] Invalid data types (validation)
- [ ] Malformed expressions (clear error)
- [ ] Missing required fields (disabled buttons)
- [ ] No crashes

## Reporting Format

Use this format for test results:

### Summary Table

| Feature | Status     | Notes     |
| ------- | ---------- | --------- |
| [Test]  | ✅ PASS    | [Details] |
| [Test]  | ❌ FAIL    | [Error]   |
| [Test]  | ⚠️ BLOCKED | [Reason]  |

### Key Findings

**What Works**:

- List working features

**Known Issues**:

- List bugs or limitations

**Blocked Items**:

- List items that need manual testing

## Docker MCP Limitations

| Feature          | Status     | Workaround          |
| ---------------- | ---------- | ------------------- |
| Host file access | ❌ Blocked | Run from host       |
| Slow network     | ❌ Blocked | Manual test         |
| Drag-drop        | ⚠️ Partial | Manual verification |

## Tips

1. **Use subagents**: `await task(subagent_type="general", command="/test-feature-x")`
2. **Fresh analysis**: Create new analysis for each test session
3. **Check uploads**: `ls -la /home/kripso/workspace/polars-fastapi-svelte/data/uploads/`
4. **Check logs**: `tail -30 /tmp/backend.log`
5. **Update results**: Document in `/home/kripso/workspace/polars-fastapi-svelte/E2E_TEST_RESULTS.md`

## Common Commands

```bash
# Backend
uv run main.py

# Frontend
npm run dev -- --port 5173 --host

# Check health
curl http://localhost:8000/health

# List analyses
curl http://localhost:8000/api/v1/analysis
```
