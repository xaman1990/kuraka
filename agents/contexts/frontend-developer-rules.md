# frontend-developer — Context Loading

Read these sources in order before writing any code.

## 1. Project configuration (always)

- `kuraka.config.yaml` at the project root.

Use:

- `stack.frontend.{language, framework, package_manager, state_mgmt}` —
  determines which stack profile to load.
- `stack.frontend.{lint_cmd, typecheck_cmd, test_cmd, format_cmd}` —
  the commands to run at the file/story gates.
- `architecture.paths.frontend_root` — where to put each generated file.
- `conventions.max_frontend_file_loc` (falls back to `max_file_loc`) —
  component size limit.
- `conventions.naming_language`, `null_syntax` — applied to generated code.

If `kuraka.config.yaml` is missing or has no `stack.frontend`, stop and
ask the user — `frontend-developer` cannot operate without a frontend stack.

## 2. Stack profile (required)

- `.claude/stack-profiles/${stack.frontend.framework}.md`

This profile is your primary reference. It defines:

- Implementation order (Types → Services → Stores → Composables → Components for Vue/Pinia, etc.).
- Idiomatic file paths.
- Per-layer rules (what logic goes where, what's forbidden).
- Test patterns specific to the stack.
- Common pitfalls and anti-patterns.

If no profile exists for the configured framework, **stop and report**.
Implementing without a profile risks stack-mismatched output.

## 3. Project specialization layer (when present)

Read each in order:

1. `.claude/project/conventions/*.md` — including:
   - `frontend-branding.md` if present — brand tokens (use these, do not
     inline hex values).
   - `accessibility.md` if present — a11y requirements.
2. `.claude/project/review-checks/frontend-developer.md` — extra checks.
3. `.claude/project/lessons-learned/*.md` — `applies_to` includes
   `frontend-developer`.
4. `.claude/project/agents/frontend-developer.append.md` — addendum.
5. `.claude/project/glossary.md` — domain vocabulary used in
   component/store/composable names.

## 4. Story file + reference components (per implementation)

- The approved story file (from Phase 2).
- 1-2 existing components in `${architecture.paths.frontend_root}` that
  follow the same pattern you're about to implement — use them as
  reference for style and structure.

## 5. Output schema (always, before returning)

- `.claude/agents/contexts/output-schemas.md#backend-developer` (same
  schema applies, with frontend command names substituted).

## Loading rationale

The framework prompt defines your role.
The stack profile defines HOW to implement in your specific frontend stack.
The project layer defines team-specific overrides (branding, a11y).
The story file defines WHAT to implement.

Most-specific wins (project > stack > framework). If layers conflict on
visual identity (branding) or security boundary (auth in localStorage),
the project layer wins.
