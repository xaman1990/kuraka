---
name: schema-freeze
description: "Validate and freeze database schema before implementation begins. Ensures table inventory matches Jira, all names are English, tenant strategy is defined, and FKs are explicit. Gate between Phase 3 and Phase 4."
agent: "[[architect-reviewer]]"
phase: "3 (gate) — see `kuraka`"
---

# Schema Freeze

You are executing the Schema Freeze skill — a mandatory gate before implementation begins.

## Purpose

Prevent the #1 cause of rework: implementing against a moving schema. After this skill runs and the user approves, the schema is FROZEN. No DB changes during implementation.

## Steps

### 1. Collect All Schema Definitions

From the approved stories, extract:
- Every table (CREATE or ALTER)
- Every column with type, nullable, default
- Every FK relationship
- Every index
- Every enum

### 2. Validate Against Jira

| Table | In Stories | In Jira | Match? | Action |
|-------|-----------|---------|--------|--------|
| table_a | Yes | Yes | OK | Proceed |
| table_b | Yes | No | JUSTIFY | Need explicit reason |
| table_c | No | Yes | MISSING | Add to stories |

### 3. Naming Audit

For EVERY table and column:
- [ ] Name is in English (no Spanish)
- [ ] Name uses snake_case
- [ ] Name is descriptive (min 3 chars)
- [ ] No abbreviated names without justification

### 4. Tenant Strategy

For EVERY table:
- [ ] Has tenant_id column (or justified exception)
- [ ] FK to tenants.id defined
- [ ] All repository queries will filter by tenant_id

### 5. FK Completeness

For EVERY foreign key:
- [ ] Source column defined (table.column)
- [ ] Target defined (table.column, not just table)
- [ ] ON DELETE behavior specified
- [ ] Index on FK column planned

### 6. Migration Compatibility

- [ ] Migration naming follows convention
- [ ] No column drops without 2-week deprecation
- [ ] Data migration planned if renaming columns
- [ ] Downgrade path defined

### 7. Output: Frozen Schema Document

```markdown
# Schema Freeze - {ticket}

**Date:** {YYYY-MM-DD}
**Status:** FROZEN

## Tables

### {table_name}
| Column | Type | Nullable | Default | FK | Index |
|--------|------|----------|---------|-----|-------|

## Enums
- {EnumName}: value1, value2, value3

## Migration Plan
1. {migration_file}: {description}

## Approved By
- [ ] User approval
```

### 8. Gate

Present to user: "This is the frozen schema. After approval, NO DB changes during implementation. Approve?"
