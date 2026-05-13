# migration-reviewer — Context Loading

Read these sources in order before reviewing migrations.

## 1. Project configuration (always)

- `kuraka.config.yaml` at the project root.

Use:

- `stack.database.{engine, migration_tool}` — informs which tool's
  conventions apply (Alembic, Prisma, Flyway, etc.).
- `architecture.paths.migrations_root` — where migrations live.

## 2. Stack profile (when present)

- `.claude/stack-profiles/${stack.backend.framework}.md`

The profile documents the migration tool's idiomatic patterns:

- Revision chain mechanics.
- Autogenerate caveats (what it gets wrong).
- Batch operations and zero-downtime tricks.
- Filename naming convention.

## 3. Project specialization layer (when present)

Read each in order:

1. `.claude/project/conventions/migrations.md` if present — project's
   migration vs seed conventions, naming standards.
2. `.claude/project/review-checks/migration-reviewer.md` — operational
   pre-checks the project requires (these run BEFORE the generic safety
   checklist).
3. `.claude/project/lessons-learned/*.md` — read every file whose
   frontmatter `applies_to` includes `migration-reviewer`.
4. `.claude/project/agents/migration-reviewer.append.md` — if present,
   addendum.

## 4. Artifacts under review (always, for the current cycle)

- Every migration file modified in this cycle.
- The frozen schema document from Phase 3
  (`${architecture.paths.docs_process_root}/schemas/SCHEMA-FROZEN-{ticket}.md`).
- Production data size estimates (if available in the REQ).

## 5. Output schema (always, before returning)

- `.claude/agents/contexts/output-schemas.md#migration-reviewer` — your
  report's required sections.

## Loading rationale

The framework defines your role (zero-downtime safety).
The stack profile tells you the tool-specific patterns.
The project layer tells you convention-specific failures the team has
hit before (e.g., "we don't put data in Alembic; use SQL seeds").

Most-specific wins (project > stack > framework). The project pre-checks
often catch convention violations the generic safety checklist misses.
