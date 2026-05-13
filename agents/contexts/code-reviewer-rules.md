# code-reviewer — Context Loading

Read these sources in order before reviewing implemented code. Later
sources override earlier ones in case of conflict (most-specific wins).

## 1. Project configuration (always)

- `kuraka.config.yaml` at the project root.

Use:

- `stack.*` — language, framework, commands. Determines which stack
  profile(s) to load.
- `architecture.layers` — enforce "no skipping layers" and "no logic in
  inner layers" on the reviewed code.
- `architecture.paths.*` — assess "is this file in the right place".
- `conventions.max_file_loc` / `max_function_loc` — file/function size
  thresholds.
- `conventions.null_syntax`, `naming_language`, `enums_for_states` —
  style enforcement.

## 2. Stack profile(s) (when present)

- `.claude/stack-profiles/${stack.backend.framework}.md` — if reviewing
  backend code.
- `.claude/stack-profiles/${stack.frontend.framework}.md` — if reviewing
  frontend code.

Profiles define:

- Per-layer rules (what logic goes where).
- Anti-patterns to flag (with severity guidance).
- Common pitfalls.

If a profile is missing for the configured framework, flag this as a
SUGGESTION finding so the team can contribute one back to the framework.

## 3. Project specialization layer (when present)

Read each in order:

1. `.claude/project/conventions/*.md` — team-owned architecture and
   convention overrides.
2. `.claude/project/review-checks/code-reviewer.md` — operational checks
   the project requires (cache invalidation, audit logs, custom
   architecture rules). Treat as required.
3. `.claude/project/lessons-learned/*.md` — read every file whose
   frontmatter `applies_to` includes `code-reviewer`.
4. `.claude/project/agents/code-reviewer.append.md` — if present, addendum.

## 4. Artifacts under review (always, for the current cycle)

- All code files modified or added by `backend-developer` /
  `frontend-developer` in Phase 4.
- The approved story files
  (`${architecture.paths.docs_process_root}/stories/`).
- The test plan
  (`${architecture.paths.docs_process_root}/test-plans/`).

## 5. Output schema (always, before returning)

- `.claude/agents/contexts/output-schemas.md#code-reviewer` — your finding
  report's required sections. The `verify-output` skill validates.

## Loading rationale

The framework prompt defines the role (6D review + universal checklist).
The stack profile defines what counts as a violation in this stack.
The project layer defines what counts as a violation in this codebase.
The artifacts under review are the actual subject.

Most-specific wins (project > stack > framework). If a project rule
appears to relax a security/correctness rule, flag the conflict instead
of silently picking.
