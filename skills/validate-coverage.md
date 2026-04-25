---
name: validate-coverage
description: "Validate test coverage after generating tests. Runs ruff + pytest, identifies gaps, reports coverage metrics."
agent: "[[test-engineer]]"
phase: "6 — see [[kuraka]]"
---

# Validate Coverage

After generating tests, validate they pass and cover the required scenarios.

## Steps

### 1. Lint Check

```bash
cd sie_v2 && ruff check backend/tests/
```

Fix any issues before proceeding.

### 2. Run Tests

```bash
# Run only the new test file
cd sie_v2 && make test-file F=test_new_scale_service

# Run full suite to check no regressions
cd sie_v2 && make test
```

### 3. Coverage Analysis

Check what's covered vs what's missing:

| Layer | Must Cover | Check |
|-------|-----------|-------|
| **Models** | Columns, FKs, constraints, tenant_id | `test_tools_models_new_scale.py` |
| **Repositories** | CRUD, pagination, tenant isolation | `test/unit/repositories/tools/new_scale/` |
| **Services** | Business logic, state transitions, errors | `test/unit/services/tools/new_scale/` |
| **Endpoints** | HTTP codes, auth, response shapes | `test/unit/tools/test_new_scale_endpoints.py` |

### 4. Gap Report

For each source file, verify:

```markdown
| Source File | Test File | Tests | Happy | Error | Edge | Status |
|-------------|-----------|-------|-------|-------|------|--------|
| service.py | test_service.py | 12 | 4 | 5 | 3 | OK |
| analyzer.py | test_analyzer.py | 8 | 2 | 4 | 2 | OK |
| excel_writer.py | test_excel.py | 6 | 2 | 2 | 2 | OK |
| endpoints | test_endpoints.py | 15 | 8 | 5 | 2 | OK |
```

### 5. Quality Checklist

- [ ] All tests follow AAA pattern
- [ ] Test names: `test_should_{action}_when_{condition}`
- [ ] No `any` types in test code
- [ ] Mocks properly scoped (no leaking between tests)
- [ ] No hardcoded IDs (use fixtures/builders)
- [ ] Each test is independent (no order dependency)
- [ ] `ruff check` passes on all test files
- [ ] `make test` green (all tests pass, including existing)
- [ ] No print/console.log in tests (use pytest captures)

### 6. Coverage Targets

| Layer | Target |
|-------|--------|
| Services | 80% line coverage |
| Repositories | 80% line coverage |
| Endpoints | 90% route coverage |
| Models | 100% column/constraint coverage |

### 7. Report

```markdown
## Coverage Report

**Tests written:** N
**Tests passing:** N
**Ruff issues:** 0
**Regression:** None

### By Layer
| Layer | Files | Tests | Pass | Fail |
|-------|-------|-------|------|------|

### Gaps Identified
- [ ] Missing: error case for X
- [ ] Missing: edge case for Y
```
