---
name: analyze-testability
description: "Analyze source code to determine what tests are needed. Identifies public API, dependencies to mock, test categories (happy/error/edge), and coverage strategy."
agent: "[[test-engineer]]"
phase: "6 — see `kuraka`"
---

# Analyze Testability

Analyze a source file to produce a test plan before writing any tests.

## Input

A source file path (e.g., `api/services/tools/new_scale/service.py`).

## Steps

### 1. Read and Understand

Read the entire source file. For each public function/method, extract:
- Function signature (name, params, return type)
- Dependencies (what it imports/calls)
- Side effects (DB writes, API calls, file I/O)
- Error conditions (what raises exceptions)
- Business rules (status checks, validations)

### 2. Classify Dependencies

| Dependency | Mock Strategy |
|-----------|---------------|
| Repository functions | `@patch("repositories.tools.new_scale.job_repository")` |
| Other services | `@patch("api.services.tools.new_scale.analyzer")` |
| AI client (LLM calls) | `@patch("api.services.tools.new_scale.ai_client.call_llm")` |
| File system | `@patch("api.services.tools.new_scale.file_handler.prepare_document")` |
| DB session | Use `db_session` fixture for integration, mock for unit |

### 3. Generate Test Matrix

For each public function, produce:

```markdown
| Function | Test Case | Type | Category | Priority |
|----------|-----------|------|----------|----------|
| create_job | valid data → returns job | Unit | Happy | P0 |
| create_job | stores source file | Unit | Happy | P0 |
| run_analysis | valid job → returns analysis | Unit | Happy | P0 |
| run_analysis | job not found → raises 404 | Unit | Error | P0 |
| run_analysis | wrong status → raises 400 | Unit | Error | P1 |
| run_analysis | LLM fails → job status=error | Unit | Error | P1 |
| get_results | empty results → returns empty list | Unit | Edge | P2 |
```

### 4. Determine Test Type

- **Unit test** if: function has mockable dependencies, no real DB needed
- **Integration test** if: tests cross-module behavior, needs real DB
- **Endpoint test** if: testing HTTP layer (status codes, response format)

### 5. Output: Test Plan

```markdown
## Test Plan: {filename}

### Public API (N functions)
1. `function_name(params)` → return_type

### Dependencies to Mock
- repository_x.method_y
- external_service.call

### Test Matrix
| # | Function | Test Name | Category | Mocks |
|---|----------|-----------|----------|-------|

### Files to Create
- `tests/unit/services/tools/test_{name}.py` (N tests)
- `tests/unit/repositories/tools/test_{name}.py` (N tests)

### Estimated Tests: N
```
