# security-reviewer — Context Loading

Read these sources in order before performing the security review.

## 1. Project configuration (always)

- `kuraka.config.yaml` at the project root.

Use:

- `architecture.paths.backend_root` / `frontend_root` — scope for grep
  commands.
- `stack.backend.{language, framework}` — informs which file extensions
  to scan and which stack profile to load.
- `conventions.multi_tenant` — gate on whether to run the tenant audit.
- `conventions.tenant_column_name` — the column name to check in
  repositories and services.

## 2. Stack profile (when present)

- `.claude/stack-profiles/${stack.backend.framework}.md`

The profile documents:

- The framework's auth dependency mechanism (used in section 4 of the
  security framework).
- The framework's route declaration syntax (used to find endpoints).
- ORM-specific injection vectors (parameterization conventions, raw SQL
  escape hatches).
- Framework-specific security pitfalls and anti-patterns.

If a profile is missing for the configured framework, fall back to
generic OWASP guidance and flag the gap.

## 3. Project specialization layer (when present)

Read each in order:

1. `.claude/project/conventions/*.md` — team-owned security patterns,
   tenant isolation rules, PII handling rules.
2. `.claude/project/review-checks/security-reviewer.md` — project-specific
   greps (narrower paths, internal secret patterns), PII inventory cross-
   check, custom auth checks. Treat as required.
3. `.claude/project/lessons-learned/*.md` — read every file whose
   frontmatter `applies_to` includes `security-reviewer`.
4. `.claude/project/agents/security-reviewer.append.md` — if present,
   addendum.

## 4. Artifacts under review (always, for the current cycle)

- All code files modified or added in Phase 4.
- The REQ document (to understand the security context — what data flows,
  what authorization roles).
- `.env.example` and docker-compose files (for secrets / config review).

## 5. Output schema (always, before returning)

- `.claude/agents/contexts/output-schemas.md` — security-reviewer follows
  a similar structure to code-reviewer but uses the
  CRITICAL/HIGH/MEDIUM/LOW/INFO severity vocabulary instead of
  BLOCKER/IMPORTANT/MINOR/SUGGESTION/PRAISE.

## Loading rationale

The framework prompt defines the role (OWASP + tenant + auth + secrets).
The stack profile tells you how to find what to scan in this specific
framework. The project layer tells you what's specifically risky in this
codebase and what the team's PII boundaries are.

Most-specific wins (project > stack > framework). If a project rule
appears to relax a CRITICAL security check, flag the conflict — never
silently downgrade a CRITICAL.
