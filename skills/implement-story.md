---
name: implement-story
description: "Implement a single approved user story following 4-layer architecture. Creates models, schemas, repositories, services, endpoints, and migrations as needed. Used in Phase 4."
agent: "[[backend-developer]]"
phase: "4 — see [[kuraka]]"
---

# Implement Story

You are executing the Story Implementation skill (Phase 4 of the workflow).

## Input

A single approved story file from `sie_v2/docs/process/stories/{ticket}-S{N}.md`.

## Pre-flight Checks

Before writing ANY code:
1. Read the story file completely
2. Verify it was approved by Tech Lead (Phase 3)
3. Check for stale terminology (compare against latest user corrections)
4. If story references deprecated names, STOP and report

## Implementation Order

Always implement in this order (bottom-up):

### Step 1: Migration (if schema changes)
```
migrations/versions/{YYYYMMDD}_{NNNN}_{description}.py
```
- Run: `cd sie_v2 && python -m alembic upgrade head`

### Step 2: Models (SQLAlchemy)
```
api/models/{module}/{model}.py
```
- Include tenant_id
- Use Enums for status fields
- English names only

### Step 3: Schemas (Pydantic)
```
api/schemas/{module}/{schema}.py
```
- Create, Update, Response variants
- `str | None` not `Optional[str]`

### Step 4: Repository
```
repositories/{module}/{repository}.py
```
- ONLY queries, no business logic
- Filter by tenant_id in ALL queries

### Step 5: Service
```
api/services/{module}/{service}.py
```
- Business logic here
- Call repositories, never DB
- No try/except (let exceptions propagate)

### Step 6: Endpoint
```
api/endpoints/{module}/{endpoint}.py
```
- HTTP handling only, delegate to service
- No try/except
- No business logic

### After EACH file:
```bash
cd sie_v2 && ruff check .
```

### After ALL steps:
```bash
cd sie_v2 && make test
```

## Constraints

- Max 700 lines per file (split with orchestrator pattern if needed)
- Max 50 lines per function (extract `_helpers`)
- All imports at top of file
- No commented-out code
- No hardcoded values (enums, .env, DB config)
- No magic strings
- Use `python` not `python3`

## When Done

Report:
- Files created/modified
- `ruff check .` result
- `make test` result
- Any issues found during implementation
