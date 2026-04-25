---
name: refine-stories
description: "Break an approved REQ document into detailed implementable user stories. Used by story-refiner agent in Phase 2 of the workflow."
agent: "[[story-refiner]]"
phase: "2 — see [[kuraka]]"
---

# Refine Stories

You are executing the Story Refinement skill for the SIE v2 development workflow.

## Input

An approved REQ document from Phase 1.

## Steps

### 1. Read Project Rules

Read ALL rules in `sie_v2/.claude/rules/` to understand:
- Architecture patterns (4-layer, file locations)
- Naming conventions (English, snake_case, str | None)
- Testing requirements
- File size limits

### 2. Decompose REQ into Stories

Break the requirement into the smallest implementable units. Each story should be:
- **Independent** - can be implemented without other stories being complete
- **Testable** - has clear acceptance criteria
- **Small** - 1-3 files to create/modify

Typical story breakdown for a new module:
- S1: Models + Migration (DB layer)
- S2: Repositories (data access layer)
- S3: Schemas (Pydantic request/response)
- S4: Services (business logic)
- S5: Endpoints (REST API)
- S6: Frontend (if applicable)

### 3. For Each Story, Define

1. **Acceptance criteria** - numbered, testable checklist
2. **Schema changes** - exact table, column, type, nullable, default
3. **API contract** - method, path, request body, response body
4. **Files to create/modify** - exact paths per project structure
5. **Dependencies** - which stories must be complete first
6. **Tests needed** - what test cases this story requires

### 4. Naming Validation

Before outputting, scan every story for:
- Spanish names in code artifacts -> rename to English
- `Optional[Type]` -> change to `Type | None`
- Hardcoded values -> replace with enums or config
- Missing tenant_id -> add to all DB queries
- Vague FK targets -> make explicit (table.column)

### 5. Staleness Check

If user has made corrections since the REQ was written:
- Compare current stories against latest corrections
- Regenerate any stale sections
- Never carry outdated terminology forward

### 6. Output

Create story files at `sie_v2/docs/process/stories/{ticket}-S{N}.md` and present summary table to user.
