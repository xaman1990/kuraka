# backend-developer — Context Loading

Read these sources in order before writing any code. Later sources override
earlier ones in case of conflict (most-specific wins).

## 1. Project configuration (always, first)

- `kuraka.config.yaml` at the project root.

Extract and use:

- `stack.backend.{language, framework, package_manager, orm}` — informs
  which stack profile to load and which idioms apply.
- `stack.backend.{lint_cmd, test_cmd, typecheck_cmd, format_cmd}` — the
  commands to run at the file/story gates.
- `stack.database.{engine, migration_tool}` — informs how to write
  migrations.
- `architecture.layers` — the layer names and order; the agent enforces
  "no skipping layers" and "no logic in inner layers".
- `architecture.paths.{backend_root, tests_root, migrations_root}` — where
  to put each generated file.
- `conventions.{naming_language, null_syntax, multi_tenant,
  tenant_column_name, enums_for_states, max_file_loc, max_function_loc}` —
  language and style rules applied to every generated artifact.

If `kuraka.config.yaml` is missing, stop and ask the user to run
`kuraka init`.

## 2. Stack profile (required)

- `.claude/stack-profiles/${stack.backend.framework}.md`

This is your primary reference. It defines:

- Implementation order for a story.
- Idiomatic file paths for each layer.
- Per-layer rules (what logic goes where; what's forbidden).
- Test patterns specific to the stack.
- Common pitfalls and anti-patterns to flag.

If no profile exists for the configured framework, **stop and report**.
Implementing without a profile risks producing stack-mismatched code that
later phases will reject. The framework ships profiles for the major
stacks; extending the framework with a new profile is preferred over
guessing from training data.

## 3. Project specialization layer (when present)

Read each in order:

1. `.claude/project/conventions/*.md` — team-owned architecture rules,
   tenant patterns, naming nuances, domain-specific rules. These extend
   or override the stack profile.
2. `.claude/project/review-checks/backend-developer.md` — operational
   checks the project wants you to execute (e.g., specific grep patterns,
   anti-patterns to avoid). Treat as required.
3. `.claude/project/lessons-learned/*.md` — read every file whose YAML
   frontmatter contains `applies_to:` list that includes
   `backend-developer`. Ignore files that target other agents.
4. `.claude/project/agents/backend-developer.append.md` — if present,
   addendum to your prompt.
5. `.claude/project/glossary.md` — domain vocabulary; use the project's
   terms when naming new entities.

If `.claude/project/` does not exist or is empty, the project is using
framework + stack profile defaults only. That is valid; proceed.

## 4. Story file (per implementation)

- The approved story file from Phase 2 (path comes from the calling
  phase / orchestrator).
- Re-read between stories; do not rely on memory across multi-story
  cycles. Stories can be corrected between phases and the latest version
  is the contract.

## 5. Output schema (always, before returning)

- `.claude/agents/contexts/output-schemas.md#backend-developer` — your
  completion report's required sections. The `verify-output` skill
  validates against this.

## Loading rationale

- The framework prompt defines your role (implement stories, run gates).
- The stack profile defines HOW to implement in your specific stack.
- The project layer defines team-specific overrides and historical lessons.
- The story file defines WHAT to implement in this iteration.

If layers conflict, most-specific wins (project > stack > framework). If
the conflict touches security or correctness (e.g., the project layer
relaxes a security rule from the stack profile), flag the conflict to the
user instead of silently choosing.
