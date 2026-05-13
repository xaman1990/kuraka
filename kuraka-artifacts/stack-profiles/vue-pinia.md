# Stack Profile — Vue / Pinia

**Profile version**: 1
**Covers**: Vue 3 (Composition API), TypeScript strict, Pinia for state,
Vite or similar build tool. Frontend test framework: Vitest, Jest, or
Playwright (covered separately for E2E).
**Status**: stable

---

## When this profile applies

The agent loads this profile when `stack.frontend.framework` in
`kuraka.config.yaml` equals `vue`. Companion conventions assumed:

- `stack.frontend.language: typescript`
- `stack.frontend.state_mgmt: pinia` (most common; `vuex`/`none` are
  variants — adapt this section's "Stores" rules accordingly).

## Implementation order

When implementing a story that crosses the frontend layers, create files
in this order:

1. **Types** — TypeScript interfaces for everything the layer below will
   consume. Define before any logic so the rest of the stack type-checks
   incrementally.
2. **Services** — typed API client calls. Pure functions returning
   `Promise<T>` with concrete types.
3. **Stores** — Pinia stores. Hold reactive state and orchestrate calls
   to services.
4. **Composables** — reusable logic. Pull from stores, do not duplicate
   their state.
5. **Components** — `<script setup lang="ts">`. Consume composables and
   stores; render UI; no business logic.

## Idiomatic file paths

Paths are relative to `architecture.paths.frontend_root` (typically
`frontend/` or `web/`).

| Artifact | Path |
|---|---|
| Types | `frontend/src/types/{domain}.ts` |
| Services | `frontend/src/services/{domain}Service.ts` |
| Stores | `frontend/src/stores/{domain}Store.ts` (or `use{Domain}Store.ts`) |
| Composables | `frontend/src/composables/use{Feature}.ts` |
| Components | `frontend/src/components/{domain}/{Component}.vue` |
| Pages / Views | `frontend/src/views/{Domain}{Page}.vue` |
| Router | `frontend/src/router/` |
| Tests (unit) | `frontend/src/{layer}/__tests__/{name}.spec.ts` |

## Architecture invariants

Rules the agent enforces because of Vue/Pinia idioms. Violations are
flagged as IMPORTANT or BLOCKER during review.

- **`<script setup lang="ts">` always.** No `<script>` Options-API style.
  No untyped `<script>`.
- **Composition API only.** No Options API mixins. No class components.
- **Pinia for global state.** No prop drilling for state shared across
  routes. No `provide`/`inject` for cross-page state.
- **Stores via `defineStore(name, () => {...})`** (Composition API style).
  Avoid the Options-API style of `defineStore({state, getters, actions})`
  unless the team has an explicit reason.
- **`ref<T>()` and `computed<T>()` always have explicit generics.**
  Untyped `ref('')` infers `Ref<string>` but breaks the moment the value
  becomes nullable. Spell it out.
- **API calls only via service files.** Never `fetch()` directly from a
  component or composable. Components import services or composables that
  wrap services.
- **`defineProps<T>()` and `defineEmits<T>()`** with generic types, not
  runtime arrays.
- **Tailwind for styling.** No inline `style="..."`. No global CSS unless
  unavoidable. Scoped styles use Tailwind apply directives or class
  composition.
- **Token reads via store/composable.** A component must not read
  `localStorage` directly; the auth store/composable owns that boundary.

## Test patterns

- **Unit tests**: Vitest or Jest. Mock services with `vi.mock` (Vitest)
  or `jest.mock`.
- **Component tests**: `@vue/test-utils` with `mount` or `shallowMount`.
  Prefer testing component behavior over implementation details
  (interactions, emitted events, rendered output).
- **Store tests**: instantiate the Pinia store via `createPinia()` in a
  test-only setup; test action/computed behavior against the live store.
- **File location**: `__tests__/` next to the source, or
  `tests/unit/{mirror}/` if the team prefers a parallel tree.
- **Naming**: `<Component>.spec.ts`, `<store>.spec.ts`. Test cases
  named `it('renders X when Y', ...)` or `it('emits Z on click', ...)`.

For E2E tests, see the `e2e-tester` agent (Playwright-based).

## Naming and typing conventions

Stack-specific (generic conventions like `naming_language` come from CFG).

- **Components**: `PascalCase.vue`. Pages: `<Domain><Action>Page.vue`.
- **Composables**: `useCamelCase.ts`, return value object with explicit
  interface.
- **Stores**: `use<Domain>Store.ts` exporting a `defineStore` result.
- **Services**: `<domain>Service.ts` exporting named pure functions.
- **Types**: `PascalCase` interfaces or `type` aliases. Avoid `any`
  always; `unknown` when truly unknown + narrow with type guards.
- **Strict TypeScript**: `// @ts-ignore`, `// @ts-expect-error`, and
  `any` are findings. Strict-null-checks always on.

## Reference command surface

Typical Vue project commands (actual commands come from `stack.frontend.*_cmd`):

| Purpose | Typical command |
|---|---|
| Lint | `npm run lint` (often `eslint --ext .vue,.ts,.tsx src/`) |
| Format | `npm run format` |
| Typecheck | `npm run typecheck` (often `vue-tsc --noEmit`) |
| Unit tests | `npm run test` (Vitest) or `npm run test:unit` |
| Dev server | `npm run dev` |
| Build | `npm run build` |

## Common pitfalls

- **`ref<T>()` without the generic.** `const items = ref([])` infers
  `Ref<never[]>` and rejects later `items.value.push(x)` if `x` is typed.
  Always `ref<Item[]>([])`.
- **Mutating store state outside the store.** Pinia allows it but it
  defeats the actions/intent boundary. Always go through an action.
- **`v-if` + `v-for` on the same element.** Vue 3 changed the priority
  but still confusing — use a wrapper or `computed` filter.
- **`watch` on reactive object without `deep`.** Only triggers on
  reference change; for nested mutation use `deep: true` or watch a
  computed of the specific field.
- **Polling for live data instead of WebSocket/SSE.** If the project has
  a `useWebSocket` (or equivalent) composable, use it.

## Anti-patterns flagged by reviewers

- `// @ts-ignore` or `any` (defeats strict TS — the whole point of the
  stack).
- Component that calls `fetch` or `axios` directly (bypasses the
  service layer).
- `localStorage.getItem('token')` from a component (auth boundary
  violation).
- Inline `style="..."` instead of Tailwind classes.
- Magic strings for events or status — should be a typed union or enum.
- A composable that creates its own reactive state instead of pulling
  from a store, when the same state is needed by multiple components.
