# Code Reviewer - Required Rules

Read ONLY these rules before reviewing implemented code:

1. `sie_v2/.claude/CLAUDE.md` - Project conventions and stack
2. `sie_v2/.claude/rules/01-solid-principles.md` - SOLID principles
3. `sie_v2/.claude/rules/02-clean-code.md` - Clean code, naming, early return, enums
4. `sie_v2/.claude/rules/03-file-organization.md` - File size limits
5. `sie_v2/.claude/rules/04-backend-architecture.md` - 4-layer architecture
6. `sie_v2/.claude/rules/05-backend-conventions.md` - Naming, types, hardcoded values
7. `sie_v2/.claude/rules/06-project-structure.md` - Monorepo structure
8. `sie_v2/.claude/rules/08-testing.md` - Testing patterns
9. `sie_v2/.claude/rules/10-code-review.md` - 6D review framework
10. `sie_v2/.claude/rules/18-duplication-aware-refactor.md` - Detect duplicated logic across providers/modules and report it as finding under the MAINTAINABILITY dimension of the 6D framework. Propose extraction as SUGGESTION with the standard format; do not demand it in-ticket.

## Conditional (only if the code touches that domain)

- `sie_v2/.claude/rules/07-providers.md` - Only if reviewing provider code
- `sie_v2/.claude/rules/09-frontend-standards.md` - Only if reviewing frontend code
- `sie_v2/.claude/rules/12-insurance-api-connector.md` - Only if reviewing insurance API integration

Do NOT read rules 11, 13, 14, 15, 16 — security (11) is handled by security-reviewer in Phase 5.5.
