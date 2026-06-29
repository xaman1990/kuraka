# Stack Profile — TypeScript / Angular

**Profile version**: 1
**Covers**: Angular 16–19 (standalone components + signals), TypeScript 5.x, RxJS,
package manager npm/pnpm. Companion backend is profile-independent.
**Status**: draft (seeded from clinica-dental-2026 retros — expand as cycles run)

---

## When this profile applies

The agent loads this profile when `stack.frontend.framework` in
`kuraka.config.yaml` equals `angular`.

## Implementation order

When implementing a story, create/modify files in this order:

1. Models / interfaces (`*.model.ts`, types).
2. Services (HTTP + state).
3. Routing (`*.routes.ts`) — wire the route BEFORE the component if lazy-loaded.
4. Components (`*.component.ts` + `.html` + `.css`).
5. Guards / interceptors (if any).

Order matters because components depend on services and routes; reversing it
produces unimportable files and broken lazy-load shapes.

## Idiomatic file paths

Relative to `architecture.paths.frontend_root` unless
`.claude/project/conventions/architecture.md` overrides.

| Artifact | Path |
|---|---|
| Feature module | `src/app/features/{feature}/` |
| Component | `src/app/features/{feature}/{name}.component.{ts,html,css}` |
| Service | `src/app/features/{feature}/{name}.service.ts` |
| Routes | `src/app/features/{feature}/{feature}.routes.ts` |
| Shared models | `src/app/shared/models/{name}.model.ts` |

## Architecture invariants

- **Reactive primitives (`signal`, `computed`, `effect`, `inject`) are created in
  an injection context only** — never inside an event handler, callback, or
  `setTimeout`. Doing so throws **NG0203** at runtime (invisible to `ng build`).
  If a reactive primitive must be created lazily, wrap it in
  `runInInjectionContext(this.injector, () => …)`. WHY: Angular's DI binds
  reactivity to the construction context.
- **A green `ng build` is necessary but NOT sufficient** — NG0203 and other
  runtime-only failures only appear when the dynamic path executes. Require a
  live authenticated smoke that exercises the dynamic action (e.g. "click add row").
- **One submit path per form/modal** — a `<form (ngSubmit)>` AND a footer button
  `(click)` both wired = double-POST. Wire exactly one trigger and disable it
  with a `submitting` guard while the request is in flight.
- **Normalize external strings before matching** — route/permission strings from
  the backend arrive with inconsistent leading slashes; normalize idempotently
  before using them as a map key or `*appCanAccess` match.
- **Render external date strings verbatim** — never `new Date(x)` to display a
  backend `YYYY-MM-DD` / `Y-m-d H:i:s` string (TZ off-by-one + verbose toString).

## Test patterns

- **Unit tests**: `*.spec.ts` next to the source; `TestBed.configureTestingModule`
  with provided mocks; `HttpClientTestingModule` for services.
- **Component tests**: `ComponentFixture` + `fixture.detectChanges()`.
- **E2E**: Playwright (see `e2e-tester`) — full-page snapshots for modal/overlay state.
- **Naming**: `should {action} when {condition}`.

## Naming and typing conventions

- Interfaces are `PascalCase`, no `I` prefix.
- Strict TS: distinguish `field?: T` (optional property) from `field: T | null`
  (nullable) — they are not interchangeable; the AC must specify which.
- Component selectors: `app-{kebab}`.

## Reference command surface

| Purpose | Typical command |
|---|---|
| Lint | `ng lint` / `eslint .` |
| Format | `prettier --write .` |
| Typecheck | `tsc --noEmit` (or `ng build` for full graph) |
| Test | `ng test --watch=false` / `vitest run` |
| Serve (smoke) | `ng serve` |

## Common pitfalls

- **NG0203** — reactive primitive created outside injection context (see invariants).
- **Sibling route collision** — two sibling routes with the same `path` (e.g. two
  `path: 'customer'`) silently shadow each other. The story must embed the exact
  corrected routing block, not a prose warning.
- **Closing on a proxy** — declaring "done" on HTTP 200 / correct `href` / green
  build instead of the observed visible behavior.
- **Double-submit** — see invariants.

## Anti-patterns flagged by reviewers

- Logic in templates instead of `computed()`.
- Manual subscription without `takeUntilDestroyed` / async pipe (leak).
- `any` types in service return signatures.
- Permission smoke that can't tell "no access configured" from "matching bug".
