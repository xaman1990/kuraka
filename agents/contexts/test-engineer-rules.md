# test-engineer — Context Loading

Read these sources in order before planning or writing tests.

## 1. Project configuration (always)

- `kuraka.config.yaml` at the project root.

Use:

- `stack.*` — language, framework, commands.
- `architecture.paths.tests_root` — test file root.
- `conventions.multi_tenant` — gate on whether to enforce tenant tests.
- `conventions.tenant_column_name` — the column to check in tenant tests.

## 2. Stack profile (when present)

- `.claude/stack-profiles/${stack.backend.framework}.md`

The profile defines:

- The test framework idioms (AAA, fixture style, mocking).
- Per-layer test patterns (e.g., for FastAPI: repository tests use
  real DB; service tests mock repos; endpoint tests use TestClient).
- File location conventions under tests_root.

If no profile exists for the configured framework, fall back to generic
AAA + mock-external-deps guidance and flag the gap.

## 3. Project specialization layer (when present)

Read each in order:

1. `.claude/project/conventions/*.md` — including:
   - `test-fixtures.md` if maintained — catalog of available fixtures in
     this codebase. Read this BEFORE writing any test so you don't
     recreate a fixture that already exists.
   - `tenant-isolation.md` if present — patterns to verify in tenant tests.
2. `.claude/project/review-checks/test-engineer.md` — operational checks
   the project requires (e.g., out-of-scope respect, coverage thresholds).
3. `.claude/project/lessons-learned/*.md` — read every file whose
   frontmatter `applies_to` includes `test-engineer`.
4. `.claude/project/agents/test-engineer.append.md` — if present, addendum.

## 4. Phase-specific artifacts (always, for the current cycle)

- **Phase 2.5**: approved story files (path:
  `${architecture.paths.docs_process_root}/stories/`).
- **Phase 6**: test plan from Phase 2.5 + the source files you're testing.

## 5. Output schema (always, before returning)

- `.claude/agents/contexts/output-schemas.md` — your mode determines which
  section applies (TEST_PLANNING or TEST_WRITING). The `verify-output`
  skill validates against it.

## Loading rationale

The framework defines your role (plan + write tests).
The stack profile tells you HOW to test in this stack.
The project layer tells you which fixtures already exist (so you don't
duplicate) and which checks are required for this specific codebase.

Most-specific wins (project > stack > framework).
