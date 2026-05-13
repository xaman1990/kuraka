# deployment-verifier — Context Loading

Read these sources in order before validating deployment artifacts.

## 1. Project configuration (always)

- `kuraka.config.yaml` at the project root.

Use:

- `stack.backend.{lint_cmd, test_cmd}` and `stack.frontend.{lint_cmd,
  test_cmd, typecheck_cmd}` — to validate CI pipelines run them.
- `stack.database.migration_tool` — to apply migrations against the test DB.
- `architecture.paths.*` — locations of Dockerfiles, .env.example, etc.

## 2. Stack profile (when present)

- `.claude/stack-profiles/${stack.backend.framework}.md` — for
  stack-specific Dockerfile conventions, healthcheck endpoint patterns,
  CI patterns.

## 3. Project specialization layer (when present)

Read each in order:

1. `.claude/project/conventions/*.md` — including `deployment.md` if
   present (project's deployment topology, env var inventory).
2. `.claude/project/review-checks/deployment-verifier.md` — extra checks
   the project requires (e.g., specific env vars, specific secrets
   layout).
3. `.claude/project/lessons-learned/*.md` — `applies_to` includes
   `deployment-verifier`.
4. `.claude/project/agents/deployment-verifier.append.md` — if present,
   addendum.

## 4. Artifacts (always, for the current cycle)

- `docker-compose.yml`, `docker-compose.prod.yml` (if exist).
- Dockerfiles per service.
- `nginx.conf` (if exists).
- `.env.example` and per-service `.env.example`.
- `.github/workflows/*.yml` (if exists).
- Any modified config files in this cycle.

## 5. Output schema (always, before returning)

- `.claude/agents/contexts/output-schemas.md#deployment-verifier` (if
  defined; the agent's prompt has a default template otherwise).

## Loading rationale

The framework defines the universal checks (Docker validates, env vars
documented, CI runs lint+test, migrations apply). The stack profile
tells you what the stack's healthcheck endpoint typically looks like.
The project layer tells you which env vars are required in THIS project
beyond the universal set.
