---
name: review-stories
description: "Architect review of user stories before implementation begins. Validates architecture, naming, tenant strategy, and completeness. Used in Phase 3."
agent: "[[architect-reviewer]]"
phase: "3 — see `kuraka`"
---

# Review Stories

You are executing the Architect Review skill for stories (Phase 3 of the workflow).

## Input

Story files from Phase 2 at `sie_v2/docs/process/stories/`.

## Steps

### 1. Read All Rules

Read every file in `sie_v2/.claude/rules/` — you are the gatekeeper.

### 2. Review Each Story Against Checklist

For EACH story, verify:

| # | Check | How to Verify |
|---|-------|---------------|
| 1 | English names | Grep for Spanish words in table/column/variable names |
| 2 | Tenant strategy | Every table has tenant_id, every query filters by it |
| 3 | Explicit FK targets | "references users.id" not just "references users" |
| 4 | No extra tables | Compare against REQ and Jira ticket |
| 5 | Correct file paths | `api/` structure, NOT `modules/` |
| 6 | `Type \| None` syntax | No `Optional[Type]` anywhere |
| 7 | No hardcoded values | Enums or config for all constants |
| 8 | Independent stories | Each can be implemented alone |
| 9 | API contracts complete | Request AND response defined |
| 10 | Testable criteria | Each acceptance criterion is verifiable |
| 11 | Migration naming | Follows YYYYMMDD_NNNN convention |
| 12 | File size forecast | Will any file exceed 700 lines? Plan split |

### 3. Severity Classification

- **BLOCKER** - Must fix before implementation: missing tenant_id, wrong architecture, security flaw
- **IMPORTANT** - Should fix: naming issues, incomplete contracts, missing tests
- **MINOR** - Can note for later: style preferences, documentation gaps

### 4. Output

Produce review report with:
- Verdict: APPROVED or CHANGES_REQUIRED
- Findings table (severity, story, description, fix)
- List of approved stories
- List of stories needing changes

### 5. Gate Decision

- If ANY blocker exists: CHANGES_REQUIRED
- If only important/minor: APPROVED_WITH_NOTES (can proceed with fixes during implementation)
- If all clear: APPROVED
