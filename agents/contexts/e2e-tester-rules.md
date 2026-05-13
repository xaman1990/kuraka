# e2e-tester — Context Loading

Read these sources in order before writing E2E tests.

## 1. Project configuration (always)

- `kuraka.config.yaml` at the project root.

Use:

- `architecture.paths.frontend_root` — to locate `playwright.config.ts`
  and existing E2E tests.
- `stack.frontend.framework` — informs which stack profile to load.

## 2. Stack profile (when present)

- `.claude/stack-profiles/${stack.frontend.framework}.md`

The profile may document framework-specific selectors, routing patterns,
or component conventions useful when writing tests.

## 3. Project specialization layer (when present)

Read each in order:

1. `.claude/project/conventions/*.md` — including any e2e-specific
   conventions.
2. `.claude/project/review-checks/e2e-tester.md` if present.
3. `.claude/project/lessons-learned/*.md` — `applies_to` includes
   `e2e-tester`.
4. `.claude/project/agents/e2e-tester.append.md` — if present, addendum.
5. `.claude/project/glossary.md` — domain vocabulary used in test names
   (e.g., the project's actual terms for "user", "tenant", "case").

## 4. Artifacts (always, for the current cycle)

- `<frontend_root>/playwright.config.ts` (if exists).
- Existing E2E tests in `<frontend_root>/tests/e2e/` — read 1-2 as
  reference for the project's style.
- The REQ to understand which user flows changed.

## 5. Output schema (always, before returning)

- `.claude/agents/contexts/output-schemas.md#e2e-tester` (if defined; the
  agent's prompt has a default template otherwise).

## Loading rationale

The framework defines what to test (critical flows only) and how
(Playwright + page objects). The project layer tells you what the
project's flows actually are and what vocabulary to use in test names.
