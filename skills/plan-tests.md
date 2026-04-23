---
name: plan-tests
description: "Pre-implementation test planning. Produces a test plan from stories BEFORE code is written. Defines what to test, fixtures needed, mocks, edge cases, and testability constraints that the developer must respect."
agent: "[[test-engineer]]"
phase: "2.5 — see `kuraka`"
---

# Plan Tests (Pre-Implementation)

Produce a test plan from approved stories BEFORE implementation begins. This plan
serves as a contract: the developer must write code that is testeable according to
this plan.

## Difference from [[analyze-testability]]

| | [[plan-tests]] (Phase 2.5) | [[analyze-testability]] (Phase 6) |
|---|---|---|
| **Input** | Stories (no code yet) | Implemented source files |
| **Purpose** | Define testability constraints upfront | Analyze existing code for test gaps |
| **Output** | Test plan with expected signatures | Test matrix with mock strategies |
| **When** | Before implementation | After implementation |

## Input

- Approved story files from Phase 2
- Frozen schema from Phase 3 (if available)
- Project testing rules: `sie_v2/.claude/rules/08-testing.md`

## Steps

### 1. Extract Testable Units from Stories

For each story, identify:
- **Service functions** described in the story (with expected signature)
- **Repository functions** implied by data access needs
- **Endpoint routes** with expected status codes
- **Business rules** that MUST have test coverage

### 2. Define Testability Constraints

List constraints the developer must respect for the code to be testeable:

```markdown
### Testability Constraints

1. `{service_function}` must accept `{dependency}` as injectable parameter
   (not instantiate internally) — needed for mocking
2. `{business_rule}` must be in a separate function (not inline in the
   orchestrator) — needed for unit testing in isolation
3. Side effects (DB writes, API calls) must go through repository/client
   interfaces — needed for mocking without touching real resources
```

### 3. Plan Test Cases (Pre-Implementation)

```markdown
### Test Plan

| # | Story | Function (expected) | Test Case | Type | Category |
|---|-------|-------------------|-----------|------|----------|
| 1 | S1 | create_resource() | valid data returns resource | Unit | Happy |
| 2 | S1 | create_resource() | duplicate raises 409 | Unit | Error |
| 3 | S1 | create_resource() | missing required field raises 400 | Unit | Edge |
| 4 | S2 | process_batch() | empty list returns zero count | Unit | Edge |
| 5 | S2 | process_batch() | partial failure logs warning, continues | Unit | Error |
```

### 4. Define Required Fixtures

```markdown
### Fixtures Needed

| Fixture | Source | Purpose |
|---------|--------|---------|
| `db_session` | conftest.py (exists) | Transaction-scoped DB session |
| `mock_{service}` | Create in test file | Mock for {service} dependency |
| `sample_{entity}` | Create in conftest or test | Test data factory |
```

### 5. Identify Risks to Testability

Flag any story element that may be hard to test:

```markdown
### Testability Risks

| Risk | Story | Impact | Mitigation |
|------|-------|--------|------------|
| External API call in service | S2 | Can't unit test without mock | Developer must inject client |
| File I/O in handler | S3 | Needs temp files in test | Use BytesIO mock |
| Async semaphore logic | S1 | Hard to test concurrency | Test sequential behavior, mock semaphore |
```

## Output

Create a test plan file at: `sie_v2/docs/process/test-plans/TEST-PLAN-{ticket}.md`

```markdown
# Test Plan: {ticket}

## Stories Covered
- S1: {title}
- S2: {title}

## Testability Constraints
[from step 2]

## Test Cases
[from step 3]

## Fixtures
[from step 4]

## Testability Risks
[from step 5]

## Estimated Test Count: N
- Unit: N
- Integration: N
- Endpoint: N

## Files to Create
- `tests/unit/{module}/test_{name}.py`
- `tests/integration/test_{name}.py`
```

## Rules

1. **No implementation details** — plan based on stories and expected interfaces, not code
2. **Every business rule in AC must have at least one test case** — if a rule is untesteable, flag it
3. **Prefer injectable dependencies** — flag any story that implies tight coupling
4. **Happy + Error + Edge for every public function** — minimum 3 test cases per function
5. **The developer reads this plan** — write it as a contract, not a suggestion
