# Kuraka Stack Profiles

A stack profile teaches agents how to work in a specific language/framework
combination without baking those assumptions into the agent prompts themselves.

## How agents consume a profile

At invocation, each agent reads `kuraka.config.yaml` to learn the project's
`stack.backend.framework` and `stack.frontend.framework`, then reads the
matching profile(s) from `.claude/stack-profiles/{name}.md` (mounted by
`mount-kuraka.sh` from this directory).

If no profile exists for the configured framework, the agent proceeds with
framework-neutral guidance and flags the gap in its output.

## What a profile contains

- Implementation order (which file types are created in what sequence).
- Idiomatic file paths (`api/services/X.py` vs `app/controllers/X.rb` vs ...).
- Stack-specific architecture invariants (no try/except in endpoints; no
  business logic in routes; etc.).
- Stack-specific test patterns (TestClient, jest, rspec, ...).
- Stack-specific naming/typing rules that wouldn't apply to other stacks.
- Reference commands idiomatic for the stack. The *actual* commands run
  come from `kuraka.config.yaml` (`stack.backend.lint_cmd`, etc.); the
  profile may show typical values as examples.

## What a profile does NOT contain

- Project-specific opinions, conventions, or vocabulary → those live in the
  consumer project's `.claude/project/` (the project specialization layer).
- Generic principles applicable to any stack → those stay in the agent prompt.
- Declarative parameters (paths, commands, flags) → those are in
  `kuraka.config.yaml`.

## Naming convention

`{language}-{framework}.md`, lowercase, hyphenated.

Examples: `python-fastapi.md`, `node-express.md`, `go-gin.md`, `vue-pinia.md`,
`react-redux.md`, `rails.md`.

A profile may bundle backend + frontend only when they're commonly paired and
heavily co-dependent; prefer two profiles in most cases.

## Available profiles

| Profile | Coverage |
|---|---|
| `python-fastapi.md` | Python 3.10+, FastAPI, SQLAlchemy, Pydantic, Alembic, pytest |
| `vue-pinia.md` | Vue 3, Pinia, Vite, TypeScript |
| `angular.md` | Angular 16–19 (standalone + signals), TypeScript, RxJS |
| `express.md` | Express 4–5, TypeScript, Node 20–22 |
| `react.md` | React 18–19 + Vite, TypeScript (set `framework: react`) |
| `_template.md` | Copy this to start a new profile |

> The agent looks up `.claude/stack-profiles/${stack.*.framework}.md` by the
> literal framework value in `kuraka.config.yaml`. Use `angular`, `express`,
> `react` (not `react-vite`) so the lookup resolves; for a different value, copy
> the matching profile to that name.

## Contributing a new profile

1. Copy `_template.md` to `{language}-{framework}.md`.
2. Fill in the sections. Prefer concrete examples over abstract rules.
3. Validate by setting `stack.backend.framework: {framework}` in a test
   project's `kuraka.config.yaml` and confirming agents produce
   stack-idiomatic output without further hand-holding.
4. Update the table above and submit (PR or retro note).
