---
name: review-implementation
description: "Code review after implementation. Uses 6D framework: correctness, security, performance, maintainability, readability, tests. Used in Phase 5."
agent: "[[code-reviewer]]"
phase: "5 — see [[kuraka]]"
---

# Review Implementation

You are executing the Code Review skill (Phase 5 of the workflow).

## Input

Implemented code from Phase 4. The user may point to specific files or you review all changed files.

## Steps

### 1. Identify Changed Files

Check what was implemented:
```bash
cd sie_v2 && git diff --name-only HEAD~N  # or compare against main
```

Or review the files listed in the story files.

### 2. Read Each File and Apply 6D Framework

#### D1: Correctness
- Null/undefined handling in critical paths
- Edge cases: empty lists, zero values, null dates
- Off-by-one errors in loops/pagination
- Error propagation (no swallowed exceptions)

#### D2: Security
- SQL injection (parameterized queries?)
- Tenant isolation (all queries filter by tenant_id?)
- Auth on all endpoints (Depends(get_current_user)?)
- No secrets in code
- No data leaks in error responses

#### D3: Performance
- N+1 queries in loops
- Missing DB indexes on filtered/sorted columns
- Large result sets without pagination
- Blocking operations in async code

#### D4: Maintainability
- File size < 700 lines
- Function size < 50 lines
- No code duplication (DRY)
- Single responsibility per class/function
- No circular dependencies

#### D5: Readability
- Descriptive names (min 3 chars)
- Early returns (no pyramid nesting > 3 levels)
- No commented-out code
- Import order: stdlib -> third-party -> local

#### D6: Tests
- Happy path covered
- Error cases covered
- Edge cases covered
- AAA pattern used
- Proper mocking (no real DB in unit tests)

### 3. Architecture Compliance

- [ ] No try/except in endpoints
- [ ] No db.query() in services
- [ ] No logic in endpoints
- [ ] No logic in repositories
- [ ] Layers not skipped
- [ ] Enums for all states/types
- [ ] `str | None` not `Optional[str]`

### 4. Run Verification

```bash
cd sie_v2 && ruff check .
cd sie_v2 && make test
```

### 5. Output

Produce review report with verdict and findings table, following the format in the code-reviewer agent definition.
