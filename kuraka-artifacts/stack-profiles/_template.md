# Stack Profile — {Language} / {Framework}

> Copy this file to `{language}-{framework}.md` and fill in the sections.
> Delete this banner and any sections that don't apply to your stack.

**Profile version**: 1
**Covers**: {language version range, framework version range, common companions
(ORM, migration tool, package manager)}
**Status**: draft | stable

---

## When this profile applies

The agent loads this profile when `stack.backend.framework` (or
`stack.frontend.framework`) in `kuraka.config.yaml` equals
`{framework-key}`.

## Implementation order

When implementing a story, create files in this order:

1. {Step 1 — e.g., "Migration"}
2. {Step 2 — e.g., "Model"}
3. ...

The order matters because {short reason — e.g., "later layers depend on
earlier ones; reversing the order produces unimportable files"}.

## Idiomatic file paths

These paths are relative to `architecture.paths.backend_root` (or
`frontend_root`) from the config. The agent should mirror this layout
unless the project's `.claude/project/conventions/architecture.md`
overrides it.

| Artifact | Path |
|---|---|
| {Models} | `{path/to/models}/` |
| {Schemas/DTOs} | `{path/to/schemas}/` |
| ... | ... |

## Architecture invariants

Rules the agent enforces specifically because of this framework's idioms.
The agent flags violations as findings during review.

- {Rule 1 — e.g., "No try/except in route handlers — middleware handles errors."}
- {Rule 2}
- ...

For each rule, briefly explain WHY it applies to this framework so the agent
can defend the rule when challenged.

## Test patterns

- **Unit tests**: {framework-specific guidance — fixtures, isolation, mocking}
- **Integration tests**: {framework-specific guidance — test client, in-memory
  DB, etc.}
- **File location**: {convention for where tests live for a given source file}
- **Naming**: {test function naming convention}

## Naming and typing conventions

Stack-specific naming/typing rules that wouldn't apply to other stacks.
Generic conventions (English identifiers, max LOC) live in
`kuraka.config.yaml`; this section is for things unique to this stack.

- {Convention 1 — e.g., "Use `T | None` not `Optional[T]` (Python 3.10+)."}
- {Convention 2}

## Reference command surface

Typical commands for this stack. Actual commands run come from
`stack.backend.{lint,test,typecheck,format}_cmd` in the config; this section
is reference for someone writing a fresh config.

| Purpose | Typical command |
|---|---|
| Lint | `{lint command}` |
| Format | `{format command}` |
| Typecheck | `{typecheck command}` |
| Test | `{test command}` |
| Migration apply | `{migration command}` |

## Common pitfalls

Mistakes the agent should specifically avoid in this stack. Each pitfall
should be flagged as a finding if observed during implementation/review.

- {Pitfall 1 — what it looks like, why it's wrong, how to fix}
- {Pitfall 2}

## Anti-patterns flagged by reviewers

Patterns that *parse* and *run* but violate this stack's community
conventions. The reviewer agents should flag these as IMPORTANT or BLOCKER
depending on severity.

- {Anti-pattern 1}
- {Anti-pattern 2}
