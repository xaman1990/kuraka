# Architect Reviewer - Required Rules

Read ONLY these rules before reviewing stories + test plan:

1. `sie_v2/.claude/CLAUDE.md` - Project conventions and stack
2. `sie_v2/.claude/rules/03-file-organization.md` - File size limits and orchestrator pattern
3. `sie_v2/.claude/rules/04-backend-architecture.md` - 4-layer architecture
4. `sie_v2/.claude/rules/05-backend-conventions.md` - Naming, types, hardcoded values
5. `sie_v2/.claude/rules/06-project-structure.md` - Monorepo structure and file paths
6. `sie_v2/.claude/rules/08-testing.md` - Testing patterns (to validate test plan)
7. `sie_v2/.claude/rules/13-db-migrations.md` - Migration naming (only if schema changes exist)

## Conditional (only if touched by the REQ)

- `sie_v2/.claude/rules/07-providers.md` - Only if reviewing provider stories
- `sie_v2/.claude/rules/09-frontend-standards.md` - Only if reviewing frontend stories

Do NOT read rules 01, 02, 10, 11, 12, 14, 15, 16 — they are for code review or unrelated domains.
