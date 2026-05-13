# Migration Inventory — sie_v2 hardcodes en el framework

> Artefacto de tracking para Fase 3 + Fase 3.5 del plan de migración
> (`02-MIGRACION-FRAMEWORK.md`).
>
> Lista **todo** hardcode/coupling con sie_v2 encontrado en agents/, skills/,
> rules/, commands/ y contexts/. Cada item tiene un destino concreto y un
> checkbox. La Fase 3 está hecha cuando todos los checkboxes están marcados.
>
> Generado: 2026-05-12 vía grep + revisión manual del estado post-sync
> (commit `f2fab30`, tag `v0.2.1`).

---

## Cómo se lee

Cada item tiene la forma:

```
- [ ] `path/file.md:LINEA` — descripción del hardcode → DESTINO
```

**Destinos posibles** (códigos):

| Código | Destino | Significa |
|---|---|---|
| `CFG` | `kuraka.config.yaml` | Declarativo. Se mueve a un campo del config y los agentes lo leen de ahí. |
| `SP-PY` | `kuraka-artifacts/stack-profiles/python-fastapi.md` | Específico de Python/FastAPI. Aplica a cualquier proyecto en ese stack. |
| `SP-VUE` | `kuraka-artifacts/stack-profiles/vue-pinia.md` | Específico de Vue 3/Pinia. |
| `SP-GO`, `SP-NODE`, etc. | otros stack profiles | Para futuras adiciones. No bloqueante en Fase 3. |
| `PL-CONV` | `<sie_v2>/.claude/project/conventions/*.md` | Convención de equipo / dominio sie_v2. |
| `PL-RC` | `<sie_v2>/.claude/project/review-checks/*.md` | Checklist específico que ejecuta un agente. |
| `PL-LL` | `<sie_v2>/.claude/project/lessons-learned/LL-NNN-*.md` | Lección institucional con frontmatter `applies_to`. |
| `PL-GLO` | `<sie_v2>/.claude/project/glossary.md` | Vocabulario de dominio (provider, tenant, contract…). |
| `GEN-KEEP` | agente genérico | Ya es genérico o lo será con cambio cosmético (saca "SIE v2" del texto). |
| `GEN-REWORD` | agente genérico | Aplica a cualquier proyecto pero hay que reformular en términos parametrizados. |
| `DELETE` | nada | Específico de sie_v2 y no aporta al framework. Se elimina del vault. |

---

## Quick stats

| Categoría | Items |
|---|---:|
| Agentes con coupling | 14 / 16 |
| `agents/contexts/*-rules.md` 100% sie_v2-path-referenced | 15 / 15 |
| Skills con coupling | 17 / ~25 |
| Rules con coupling | 3 / 3 |
| Commands hard-coded a sie_v2 | 3 / 4 |
| Archivos nuevos del sync a relocar | 1 (`CROSS-PROVIDER-CONVENTIONS.md`) |
| **Total estimado de items de inventario** | **~180** |

---

## Inventario por destino

### A. → `kuraka.config.yaml` (CFG)

Items que se vuelven campos declarativos del config. **Una vez en CFG, los agentes leen la variable; nunca repiten el valor literal.**

| # | Fuente | Hardcode | Campo CFG |
|---|---|---|---|
| A1 | múltiples agentes/skills | `ruff check .` | `stack.backend.lint_cmd` |
| A2 | múltiples | `make test` | `stack.backend.test_cmd` |
| A3 | `frontend-developer.md:74-81`, `kuraka.md` | `npm run lint`, `npm run typecheck`, `npm run test` | `stack.frontend.{lint,typecheck,test}_cmd` |
| A4 | `implement-story.md:32` | `python -m alembic upgrade head` | derivable de `stack.database.migration_tool` |
| A5 | `verify-deployment.md:26` | `docker compose config` | (genérico — queda como check estándar) |
| A6 | varias rutas hardcoded `sie_v2/docs/process/...` | path | `architecture.paths.docs_process_root` |
| A7 | varias rutas hardcoded `sie_v2/backend/...` | path | `architecture.paths.backend_root` |
| A8 | `frontend-developer.md` rutas `frontend/src/...` | path | `architecture.paths.frontend_root` |
| A9 | `sie_v2/backend/alembic/versions/...` | path | `architecture.paths.migrations_root` |
| A10 | múltiples `tenant_id` mentions | tenant column | `conventions.multi_tenant`, `conventions.tenant_column_name` |
| A11 | múltiples `str \| None` vs `Optional[T]` | null syntax | `conventions.null_syntax` |
| A12 | `agents/backend-developer.md:117`, `arki.md` | max 700 LOC | `conventions.max_file_loc` |
| A13 | `agents/backend-developer.md:118` | max 50 LOC | `conventions.max_function_loc` |
| A14 | `frontend-developer.md` (max 400 LOC components) | max frontend LOC | `conventions.max_frontend_file_loc` |
| A15 | múltiples "all names in English" | naming language | `conventions.naming_language` |
| A16 | múltiples "Enums for states, no magic strings" | enum convention | `conventions.enums_for_states` |

---

### B. → Stack profiles

#### B.1 `kuraka-artifacts/stack-profiles/python-fastapi.md` (SP-PY)

Contenido a extraer/migrar:

- [ ] **Implementation order** (de `backend-developer.md:46-79`): Models (SQLAlchemy) → Schemas (Pydantic) → Repository → Service → Endpoint → Migration.
- [ ] **Layers nomenclatura** (de `code-reviewer.md:41`): "Endpoint → Service → Repository → DB". Los nombres exactos vienen de `architecture.layers` en CFG; el profile explica qué responsabilidad tiene cada uno.
- [ ] **Architecture rules específicas Python**:
  - No try/except in endpoints (middleware handles errors)
  - No `db.query()` in services (use repositories)
  - No logic in endpoints
  - No logic in repositories
- [ ] **Path structure típica FastAPI**: `api/models/{module}/`, `api/schemas/{module}/`, `api/services/{module}/`, `api/endpoints/{module}/`, `repositories/{module}/`. (Esto sale de `story-refiner.md:82-86,102-106`, `backend-developer.md:47-70`, `implement-story.md:36-66`, `write-tests.md:24-26`.)
- [ ] **Test patterns Python/FastAPI**: `pytest` + AAA pattern, `TestClient` para endpoints, `conftest.py` para fixtures. (De `test-engineer.md:84,95,188-189`, `generate-endpoint-tests.md:35-36`, `write-tests.md:32,98`.)
- [ ] **Python-specific rules**: `python` not `python3`; no commented-out code; imports at file top. (Algunas son genéricas — distinguir.)
- [ ] **Alembic migration patterns**: naming convention `{YYYYMMDD}_{NNNN}_{description}.py`, `alembic upgrade head` checks. (De `backend-developer.md:76-79`, `deployment-verifier.md:63`.)

#### B.2 `kuraka-artifacts/stack-profiles/vue-pinia.md` (SP-VUE)

Contenido a extraer:

- [ ] **Frontend implementation order** (de `frontend-developer.md:34-65`): Types → Services → Stores → Composables → Components.
- [ ] **Path structure típica Vue**: `frontend/src/types/`, `frontend/src/services/`, `frontend/src/stores/`, `frontend/src/composables/`, `frontend/src/components/{domain}/`.
- [ ] **Stack-specific rules**: All TypeScript (no `.js`, no `// @ts-ignore`, no `any`); Pinia para state global; Tailwind para styling; scoped styles; reactive WebSocket updates.
- [ ] **TypeScript syntax precision** (de `architect-reviewer.md:43,113`): `nombre?: string` vs `nombre: string | null` tienen semántica diferente, exigir AC explícito.
- [ ] **Match backend schemas** (de `frontend-developer.md:43`): types deben matchear Pydantic schemas. (Esto es un patrón cross-stack; generalizar como "match backend types".)

#### B.3 Stack profiles futuros (placeholder)

No bloqueantes para Fase 3. Cuando alguien intente Kuraka en otros stacks:
- `node-express.md`, `nestjs.md`
- `go-gin.md`, `go-echo.md`
- `rails.md`, `django.md`
- `react-redux.md`, `react-zustand.md`, `svelte.md`

Template general en `kuraka-artifacts/stack-profiles/_template.md`.

---

### C. → Project specialization layer (PL-*)

Todo lo que se va al `<sie_v2>/.claude/project/`. Acá se preserva la memoria operativa del proyecto sin contaminar el framework.

#### C.1 `<sie_v2>/.claude/project/conventions/` (PL-CONV)

- [ ] **C1.1** `architecture.md` — la "4-layer Endpoint→Service→Repository→DB" en su versión sie_v2-opinionada (nombres exactos, responsabilidades, antipatrones documentados). Fuente: `agents/contexts/*-rules.md` referencias a `04-backend-architecture.md`.
- [x] **C1.2** `tenant-isolation.md` ✅ — creado en `migration-examples/sie_v2-project-layer/conventions/tenant-isolation.md`. Patrón completo: repository/service/endpoint, anti-patterns, detection commands. (Refactor po-analyst.)
- [ ] **C1.3** `project-structure.md` — la estructura monorepo sie_v2 (backend/, frontend/, etc.). Fuente: contexts referencias a `06-project-structure.md`.
- [ ] **C1.4** `naming-conventions.md` — "All names in English", `T | None` vs `Optional[T]` con casos específicos. Fuente: múltiples agentes.
- [ ] **C1.5** `frontend-standards.md` — Vue 3 + TS strict, WebSocket, Pinia, **Guai branding** (`#CCFF00`, `#0A0A0A`, `#B7FF1E`). Fuente: `frontend-developer.md:95`, contexts referencias a `09-frontend-standards.md`.
- [ ] **C1.6** `cross-provider-conventions.md` — relocación de `CROSS-PROVIDER-CONVENTIONS.md` (raíz del vault) — mailbox naming, `scheduling_tasks` dual-dispatch, seeds vs alembic. Este archivo dice "vive en raíz del vault para que esté disponible a TODOS los proyectos" pero su contenido es 100% sie_v2 — relocar acá y agregar `_template.md` en `kuraka-artifacts/project-templates/conventions/` mostrando cómo crear el propio.
- [ ] **C1.7** `providers.md` — convenciones cross-provider (asitur, generali, caser, linea_directa). Fuente: contexts referencias a `07-providers.md`, `12-insurance-api-connector.md`.
- [ ] **C1.8** `migrations.md` — convenciones de migrations Alembic + SQL seeds (la regla "data va en seeds, no en alembic"). Fuente: `migration-reviewer.md:47-49`, `architect-reviewer.md:122-126`.
- [ ] **C1.9** `db-migrations-naming.md` — naming convention `{YYYYMMDD}_{NNNN}_{description}.py`. Fuente: contexts referencias a `13-db-migrations.md`.

#### C.2 `<sie_v2>/.claude/project/review-checks/` (PL-RC)

Checklists ejecutables por agente, project-specific.

- [x] **C2.1** `code-reviewer.md` ✅ — creado en `migration-examples/sie_v2-project-layer/review-checks/code-reviewer.md`. 2 checks: cache invalidation namespace coverage + audit log presence. (Refactor code-reviewer.)
- [x] **C2.2** `po-analyst.md` ✅ — creado en `migration-examples/sie_v2-project-layer/review-checks/po-analyst.md`. 3 checks: provider directory full file coverage, mailbox/contract convention validation, tenant strategy explicit per table. (Refactor po-analyst.)
- [x] **C2.3** `security-reviewer.md` ✅ — creado en `migration-examples/sie_v2-project-layer/review-checks/security-reviewer.md`. 6 checks: secret scanning con paths sie_v2 (backend/, frontend/src/, providers/), tenant isolation audit, FastAPI route auth grep, PII inventory cross-check, provider webhook signature verification, encrypted-at-rest columns. (Refactor security-reviewer.)
- [x] **C2.4** `architect-reviewer.md` ✅ — creado en `migration-examples/sie_v2-project-layer/review-checks/architect-reviewer.md`. 2 checks: pattern parity (4 sub-checks: migrations with data, seed files, directory structure, executable command) + cross-provider naming/ID conventions. Con BLOCKER text en español preservado. (Refactor architect-reviewer.)
- [ ] **C2.5** `migration-reviewer.md` — el check de SQL seeds vs alembic data (line 47-49).
- [ ] **C2.6** `test-engineer.md` — verify tenant isolation tests (line 144).

#### C.3 `<sie_v2>/.claude/project/lessons-learned/` (PL-LL)

Cada lección en su archivo con frontmatter `applies_to`.

- [x] **C3.1** `LL-001-symbol-removal.md` ✅ — creado en `migration-examples/sie_v2-project-layer/lessons-learned/`. Frontmatter `applies_to: [po-analyst, architect-reviewer]`. (Refactor po-analyst.)
- [x] **C3.2** `LL-002-cache-invalidation.md` ✅ — creado en `migration-examples/sie_v2-project-layer/lessons-learned/`. Frontmatter `applies_to: [code-reviewer, backend-developer]`. (Refactor code-reviewer.)
- [ ] **C3.3** `LL-004-test-engineer-rule.md` — referenciada en `test-engineer.md:57`. `applies_to: [test-engineer]`.
- [x] **C3.4** `LL-DD-896-FM-01-provider-file-coverage.md` ✅ — creado en `migration-examples/sie_v2-project-layer/lessons-learned/`. Frontmatter `applies_to: [po-analyst]`. (Refactor po-analyst.)
- [x] **C3.5** `LL-DD-896-FM-02-alembic-vs-seeds.md` ✅ — creado en `migration-examples/sie_v2-project-layer/lessons-learned/`. Frontmatter `applies_to: [architect-reviewer, migration-reviewer]`. (Refactor architect-reviewer.)
- [ ] **C3.6** `LL-DD-896-FM-04-orchestrator-bypass.md` — referenciada en `kuraka-policies.md:89`. `applies_to: [orchestrator, kuraka]`.
- [ ] **C3.7** `LL-DD-896-IS-05-smoke-test.md` — referenciada en `kuraka.md:190,232`. La **regla derivada** (smoke test antes de cerrar ciclo) es genérica y queda en `kuraka.md`; la **referencia al incidente** va acá.
- [ ] **C3.8** `LL-DD-896-S1-bug-detection.md` — referenciada en `rules/17:200`. `applies_to: [code-reviewer, test-engineer]`.
- [ ] **C3.9** `INDEX.md` — tabla LL-NNN → título → applies_to → tags.

#### C.4 `<sie_v2>/.claude/project/glossary.md` (PL-GLO)

- [ ] **C4.1** Vocabulario del dominio: `tenant`, `provider`, `contract`, `mailbox`, `case`, `Guai Platform`, "incident integration", `cuidacasa`, `guainsurtech`, etc.
- [ ] **C4.2** Nombres de providers conocidos: asitur, generali, caser, ima, santander, kutxa, linea_directa.
- [ ] **C4.3** Tickets/branches naming: `DD-XXX`, `LD-XXX` patterns.

---

### D. Generic-keep / Generic-reword (GEN-KEEP, GEN-REWORD)

Items que YA aplican a cualquier proyecto y solo necesitan despegar el "SIE v2 (Guai Platform)" o reformular en términos parametrizados:

- [ ] **D1** Identidad de cada agente: "You are a {Role} for the SIE v2 (Guai Platform) project" → "You are a {Role}. You operate on the project described by `kuraka.config.yaml`." (16 agentes afectados.)
- [ ] **D2** Phase 6.8 "Smoke test obligatorio antes de cerrar ciclo" (`kuraka.md:165,190,232`) — el principio es universal, queda en `kuraka.md`. Solo se quita la referencia explícita "DD-896 IS-05" (que va a lessons-learned).
- [ ] **D3** Rate limit handling para el orchestrator (`kuraka-policies.md:89`) — principio universal (no implementar bypassing developer), queda en policies. La referencia a "DD-896 FM-04" va a lessons-learned.
- [ ] **D4** Constraint "el orquestador no toca código antes de Phase 4" (`kuraka.md:219`) — universal, queda. La referencia "REQ-2026-04-17 y REQ-20260420" → lessons-learned como nota.
- [ ] **D5** "Lite mode" 9 criterios (`kuraka-modes.md`) — universal. Las referencias a REQs específicos (`REQ-20260420-clean-specialty-names` y `REQ-2026-04-17-excel-parallel-generation`) se reemplazan por descripciones genéricas o se mueven a lessons-learned como ejemplos.
- [ ] **D6** `kuraka-modes.md:148` "Cambio en stores de Pinia compartidos" → reword "Changes to shared frontend state stores".
- [ ] **D7** `kuraka-modes.md:144` "Cambio en `backend/api/services/providers/`" → reword genérico ("Changes to provider/integration layer").

---

### E. Delete from framework (DELETE)

Items que no tienen sentido en el framework agnostico — se borran del vault y, si el equipo de sie_v2 los necesita, los re-crea en su `<sie_v2>/.claude/commands/` o `<sie_v2>/.claude/project/`.

- [ ] **E1** `commands/clean-cases.md` — `cd sie_v2 && make clean-cases`. 100% sie_v2.
- [ ] **E2** `commands/lint.md` — `cd sie_v2 && ruff check .`. Redundante con el lint_cmd del config; el agente lo invoca, no hace falta comando dedicado.
- [ ] **E3** `commands/run-tests.md` — `cd sie_v2 && make test`. Mismo argumento que E2.
- [ ] **E4** `skills/evals/gap-analysis.json` — fixture con datos 100% sie_v2 (LD, DD-896, asitur, generali). Se mueve a `<sie_v2>/.claude/project/evals/` o se borra del vault.
- [ ] **E5** `rules/16-agent-backup.md` — define rutas de backup `sie_v2/.claude/agents/* → AgentesTrabajos/kuraka/agents/`. Cuando Fase 4 mate el sync-obsidian, esta regla pierde sentido. Marcar como deprecated en Fase 3; eliminar en Fase 4.

---

### F. Keep but generic-reword (los `agents/contexts/*-rules.md`)

Los 15 archivos en `agents/contexts/` listan paths sie_v2 (`sie_v2/.claude/rules/04-backend-architecture.md`). Hay que retemplatearlos para que apunten al **project layer del consumidor**.

Patrón actual:
```markdown
1. `sie_v2/.claude/CLAUDE.md` - Project conventions
2. `sie_v2/.claude/rules/04-backend-architecture.md` - 4-layer architecture
3. ...
```

Patrón nuevo (mismo archivo, retemplateado):
```markdown
## Context (loaded in order, later overrides earlier)

1. `<framework>/agents/contexts/{agent}-rules.md` (this file, generic guidance)
2. `<framework>/stack-profiles/${stack.backend.framework}.md`
3. `<project>/.claude/project/conventions/*.md`
4. `<project>/.claude/project/review-checks/{agent}.md` (if exists)
5. `<project>/.claude/project/lessons-learned/*.md` filtered by applies_to includes "{agent}"
6. `<project>/.claude/project/agents/{agent}.append.md` (if exists)
```

Items:

- [x] **F1** `agents/contexts/po-analyst-rules.md` ✅ — retemplatado con loading order (config → stack profile → project layer → output schema). 0 referencias a sie_v2. (Refactor po-analyst.)
- [x] **F2** `agents/contexts/backend-developer-rules.md` ✅ — retemplatado con loading order de 5 secciones (config + stack profile required + project layer + story file + output schema). 0 referencias a sie_v2. (Refactor backend-developer.)
- [ ] **F3** `agents/contexts/frontend-developer-rules.md` — retemplatear (9 líneas)
- [x] **F4** `agents/contexts/code-reviewer-rules.md` ✅ — retemplatado. 0 sie_v2. (Refactor code-reviewer.)
- [x] **F5** `agents/contexts/security-reviewer-rules.md` ✅ — retemplatado. 0 sie_v2. (Refactor security-reviewer.)
- [x] **F6** `agents/contexts/architect-reviewer-rules.md` ✅ — retemplatado. 0 sie_v2. (Refactor architect-reviewer.)
- [ ] **F7** `agents/contexts/test-engineer-rules.md` — retemplatear (12 líneas)
- [ ] **F8** `agents/contexts/e2e-tester-rules.md` — retemplatear (7 líneas)
- [ ] **F9** `agents/contexts/deployment-verifier-rules.md` — retemplatear (7 líneas)
- [ ] **F10** `agents/contexts/pattern-detector-rules.md` — retemplatear (6 líneas)
- [ ] **F11** `agents/contexts/final-auditor-rules.md` — retemplatear (6 líneas)
- [ ] **F12** `agents/contexts/migration-reviewer-rules.md` — retemplatear (6 líneas)
- [ ] **F13** `agents/contexts/story-refiner-rules.md` — retemplatear (9 líneas)
- [ ] **F14** `agents/contexts/output-schemas.md` — paths sie_v2 en líneas 19,44,68,104,174 → reemplazar por `${architecture.paths.docs_process_root}/...`
- [ ] **F15** (eventual `amauta-rules.md` y `inti-rules.md` y `arki-rules.md` si existen)

---

## Per-agent worklist (orden propuesto de refactor)

Orden por dependencia, no por dificultad. Cada agente = un commit aislado en Fase 3.

### 1. `po-analyst.md` ✅ COMPLETADO (commit pendiente)

- [x] Línea 8 — identidad → GEN-KEEP (reword). Ahora: "for the project described in `kuraka.config.yaml`".
- [x] Línea 31 — path REQ → CFG (A6). Ahora: `${architecture.paths.docs_process_root}/REQ-...`.
- [x] Líneas 77-78 — ejemplos `api/services/`, `repositories/` → SP-PY (python-fastapi.md, sección "Idiomatic file paths"). Reemplazados por placeholders `<service-or-handler-file>`.
- [x] Línea 102 — regla 3 "files go in api/, repositories/" → SP-PY + reword ("follow the stack profile's path conventions").
- [x] Línea 103 — regla 4 `str | None` → CFG (A11). Ahora referencia `conventions.null_syntax`.
- [x] Línea 104 — regla 5 `tenant_id` → CFG (A10) + PL-CONV (C1.2). Ahora referencia `conventions.multi_tenant` + `.claude/project/conventions/tenant-isolation.md`.
- [x] Línea 113 — `grep -rn SYMBOL sie_v2/` → GEN-REWORD. Ahora `grep -rn SYMBOL .`.
- [x] Línea 118 — `[LL-001]` reference → PL-LL (C3.1). Reemplazado por "auto-loaded from `.claude/project/lessons-learned/`".
- [x] Líneas 122-136 — "Reglas de inventario para migraciones de provider" + referencia DD-896 FM-01 → movido íntegro a `migration-examples/sie_v2-project-layer/review-checks/po-analyst.md` (PL-RC C2.2) y `lessons-learned/LL-DD-896-FM-01-provider-file-coverage.md` (PL-LL C3.4).
- [x] Sección Context actualizada con loading order: config → stack profile → project layer.
- [x] Nueva regla 9 añadida: "Project-specific checks — execute every check in `.claude/project/review-checks/po-analyst.md`".
- [ ] Commit: "Refactor po-analyst: decouple from sie_v2" (pending user instruction).

### 2. `backend-developer.md` ✅ COMPLETADO (commit pendiente)

- [x] Línea 3 — description: "4-layer architecture" → GEN-REWORD. Ahora: "following the project's architecture (defined in kuraka.config.yaml and the matching stack profile)".
- [x] Línea 8 — identidad → GEN-KEEP. Ahora: "for the project described in `kuraka.config.yaml`".
- [x] Líneas 18, 24 — `ruff check .` + `make test` → CFG (A1, A2). Ahora: `${stack.backend.lint_cmd}` y `${stack.backend.test_cmd}` en gates.
- [x] Líneas 46-79 — implementation order completo → SP-PY (python-fastapi.md, sección "Implementation order"). Agente ahora delega: "follow the implementation order specified in the stack profile for `${stack.backend.framework}`".
- [x] Líneas 47-70 — paths concretos → SP-PY (sección "Idiomatic file paths"). Eliminados del agente.
- [x] Líneas 76-79 — Alembic migration naming → SP-PY (sección "Idiomatic file paths" + "Reference command surface"). Sie_v2-specific overrides van a `.claude/project/conventions/migrations.md` si los hay (no creado todavía; no hay convención sie_v2-specific identificada).
- [x] Líneas 82, 89 — `cd sie_v2 && ...` → CFG (A1, A2). Ahora invoca `${stack.backend.lint_cmd}` y `${stack.backend.test_cmd}` desde project root sin cd.
- [x] Línea 48 — `tenant_id` → CFG (A10). Ahora referencia `conventions.multi_tenant` + `conventions.tenant_column_name` + project layer `tenant-isolation.md`.
- [x] Línea 54 — `str | None` → CFG (A11). Ahora referencia `conventions.null_syntax`.
- [x] Líneas 116-130 — Strict rules separadas:
  - Universales (max LOC, no hardcoded, no imports inside funcs, no commented code) → quedan en agente, referencian CFG cuando aplica.
  - Stack-specific (no try/except in endpoints/services, no db.query in services, Optional[Type] vs T|None, `python` not `python3`) → SP-PY (ya estaban + se añadió "no try/except in services either").
  - "No magic strings" / "All names in English" → referencian CFG (`enums_for_states`, `naming_language`).
- [x] Línea 128 — "No `any` in TypeScript" → ELIMINADO del agente backend-developer (no aplica). Va a SP-VUE/SP-TS cuando se refactorice frontend-developer.
- [x] Línea 13 (en Pre-Implementation Checks) — "Tech Lead" → renombrado a `architect-reviewer` para alinear con nombres actuales de agentes.
- [x] Sección Context actualizada con loading order de 4 capas (config → stack profile → project layer → story file).
- [ ] Commit: "Refactor backend-developer: extract Python/FastAPI to stack profile" (pending user instruction).

**SP-PY extension** (subproducto del refactor): se añadieron 2 items nuevos a `python-fastapi.md`:
- En "Architecture invariants": "No try/except in services either" (rationale separado del de endpoints).
- En "Anti-patterns flagged by reviewers": "Renaming an entity without updating string-based references" (Alembic data migrations, scripts, JSON/YAML configs).

### 3. `code-reviewer.md` ✅ COMPLETADO (commit pendiente)

- [x] Línea 8 — identidad → GEN-KEEP. Ahora: "for the project described in `kuraka.config.yaml`".
- [x] Líneas 37-49 — Architecture checklist separado en (a) Universal (queda en agente con referencias a CFG: `max_file_loc`, `max_function_loc`, `null_syntax`, `enums_for_states`, `naming_language`, `${stack.backend.lint_cmd}`, `${stack.backend.test_cmd}`) y (b) Stack-specific delegado a "Stack-specific architecture checks" que cita el stack profile.
- [x] Línea 41 — "Layers not skipped" → instrucción ahora dice "Apply every architecture invariant from the stack profile for `${stack.backend.framework}`", que enforza `architecture.layers` del config.
- [x] Línea 46 — `Type | None` vs `Optional[Type]` → CFG (A11). Ahora referencia `conventions.null_syntax`.
- [x] Líneas 47-48 — `ruff check .` / `make test` → CFG (A1, A2). Ahora `${stack.backend.lint_cmd}` / `test_cmd`.
- [x] Líneas 50-60 — "Cache Invalidation Checks (CRITICAL)" → ELIMINADO del agente. Movido íntegro a `review-checks/code-reviewer.md` (PL-RC C2.1) + `lessons-learned/LL-002-cache-invalidation.md` (PL-LL C3.2).
- [x] Output Format example: ejemplos con paths concretos `service.py:42 — db.query() used directly` reemplazados por placeholders `<file>:<line>`.
- [ ] Considerar split en `code-reviewer-mechanic` (haiku) + `code-reviewer-judgment` (sonnet) según Fase 5 — diferido a Fase 5.
- [x] Sección Context actualizada con loading order de 4 capas (config → stack profile → project layer → artifacts under review).
- [ ] Commit: "Refactor code-reviewer + architect-reviewer + security-reviewer" (pending user instruction).

### 4. `frontend-developer.md`

- [ ] Líneas 3, 8 — identidad + descripción → GEN-KEEP + SP-VUE para "Vue 3 + TypeScript strict"
- [ ] Líneas 27-65 — implementation order Types→Services→Stores→Composables→Components → SP-VUE
- [ ] Líneas 40-62 — paths `frontend/src/...` → SP-VUE (+ CFG A8 para el root)
- [ ] Línea 43 — "Match backend Pydantic schemas" → reword generic ("match backend schemas")
- [ ] Líneas 50, 70 — Pinia → SP-VUE
- [ ] Líneas 65, 94 — Tailwind → SP-VUE
- [ ] Líneas 74, 81 — `cd sie_v2/frontend && npm run ...` → CFG (A3)
- [ ] Líneas 86-95 — Strict rules: separar TypeScript-universales de Vue-específicas
- [ ] Línea 95 — **Guai branding** → PL-CONV (C1.5)
- [ ] Líneas 116-117 — `ruff check` → `npm run lint` mapping → ya cubierto por CFG (A1 vs A3)
- [ ] Commit: "Refactor frontend-developer: extract Vue/Pinia to stack profile, Guai branding to project layer"

### 5. `architect-reviewer.md` ✅ COMPLETADO (commit pendiente)

- [x] Línea 8 — identidad → GEN-KEEP. Ahora: "for the project described in `kuraka.config.yaml`".
- [x] Línea 12 — "Phase 3 (Tech Lead Review — Stories + Test Plan)" → "Phase 3 (Architect Review — Stories + Test Plan)".
- [x] Líneas 32-36, 77 — Story checklist: todos los items con tenant_id, Optional[Type], paths reescritos para referenciar CFG (`conventions.multi_tenant`, `conventions.tenant_column_name`, `conventions.null_syntax`, `architecture.paths.*`) + stack profile.
- [x] Línea 35 — "File paths match project structure" → ahora dice "match the stack profile's idiomatic layout and `architecture.paths.*`".
- [x] Línea 41 — "Migration naming follows convention" → referencia stack profile + `stack.database.migration_tool`.
- [x] Líneas 43, 113 — TypeScript precision rule mantenida en el agente pero etiquetada como "stack profile (TypeScript)" en la columna Source.
- [x] Líneas 115-126 — Sección "Verificación de paridad con convenciones del proyecto" (4 checks sie_v2: migrations vs seeds, seed files, directory structure, executable command) → ELIMINADA del agente. Movida íntegro a `review-checks/architect-reviewer.md` (PL-RC C2.4) + `lessons-learned/LL-DD-896-FM-02-alembic-vs-seeds.md` (PL-LL C3.5).
- [x] Schema freeze path → `${architecture.paths.docs_process_root}/schemas/...`
- [x] Sección Context actualizada con loading order de 4 capas.
- [ ] Commit: "Refactor code-reviewer + architect-reviewer + security-reviewer" (pending).

### 6. `test-engineer.md`

- [ ] Línea 8 — identidad → GEN-KEEP
- [ ] Línea 24 — `ruff check .` / `make test` → CFG
- [ ] Líneas 33, 37 — paths `sie_v2/.claude/rules/...`, `sie_v2/backend/tests/conftest.py` → retemplatear (referenciar project layer + config paths)
- [ ] Línea 57 — `[LL-004]` → PL-LL (C3.3)
- [ ] Línea 77 — `sie_v2/docs/process/test-plans/...` → CFG (A6)
- [ ] Líneas 84, 95, 188-189 — TestClient FastAPI, SQLAlchemy → SP-PY
- [ ] Línea 144 — verify tenant isolation → CFG (A10) + PL-CONV (C1.2)
- [ ] Commit

### 7. `security-reviewer.md` ✅ COMPLETADO (commit pendiente)

- [x] Línea 8 — identidad → GEN-KEEP. Ahora: "for the project described in `kuraka.config.yaml`".
- [x] Línea 34 — A01 entry con `tenant_id` → reword genérico ("tenant scoping enforced on queries") + reference a CFG (`conventions.multi_tenant`) + project layer.
- [x] Líneas 49-53 — Secret scanning greps `sie_v2/backend/` → reescritos para correr desde project root (usa `.` por default + reference a `--include` por language del CFG). Las versiones sie_v2-específicas con paths `backend/`, `frontend/src/` y provider configs → movidas a `review-checks/security-reviewer.md` (PL-RC C2.3).
- [x] Líneas 61-64, 68 — Tenant Isolation Audit reescrito: condicionado a `conventions.multi_tenant: true`, usa `conventions.tenant_column_name`, referencia `.claude/project/conventions/tenant-isolation.md`.
- [x] Línea 80 — grep `@router.*` → GEN-REWORD ("the framework's auth dependency mechanism — see the stack profile"). Comando exacto sie_v2 va a PL-RC C2.3.
- [x] Línea 86 — SQLAlchemy column types → reword "ORM column types or framework equivalent" (delegado al stack profile).
- [x] Línea 112 — finding example → placeholders `<file>:<line>`.
- [x] GDPR section reescrita: referencia `.claude/project/conventions/pii-inventory.md` (project layer) en lugar de asumir formato sie_v2.
- [x] Sección Context actualizada con loading order de 4 capas.
- [x] Rules 3 — "Tenant isolation is non-negotiable" → condicionado a `conventions.multi_tenant: true`.
- [ ] Commit: "Refactor code-reviewer + architect-reviewer + security-reviewer" (pending).

### 8. `migration-reviewer.md`

- [ ] Línea 8 — identidad → GEN-KEEP
- [ ] Líneas 47-49 — SQL seeds vs alembic check → PL-RC (C2.5) + PL-LL (C3.5)
- [ ] Commit

### 9. `story-refiner.md`

- [ ] Línea 8 — identidad → GEN-KEEP
- [ ] Línea 30 — path `sie_v2/docs/process/stories/...` → CFG (A6)
- [ ] Líneas 57, 100, 107 — tenant_id, `str | None`, tenant strategy → CFG
- [ ] Líneas 82-86, 102-106 — paths SQLAlchemy/Pydantic/api/* → SP-PY
- [ ] Línea 117 — grep `sie_v2/backend/tests/` → GEN-REWORD
- [ ] Commit

### 10. `e2e-tester.md`

- [ ] Línea 8 — identidad → GEN-KEEP
- [ ] Línea 33 — "Outbound integrations — Guai webhook → SIE → aseguradora" → PL-GLO (C4) + reword genérico
- [ ] Commit

### 11. `deployment-verifier.md`

- [ ] Línea 8 — identidad → GEN-KEEP
- [ ] Línea 57 — "CI runs `ruff check` and `make test`" → CFG (A1, A2)
- [ ] Línea 63 — `alembic upgrade head` → CFG (A4)
- [ ] Commit

### 12. `pattern-detector.md`

- [ ] Línea 8 — identidad → GEN-KEEP
- [ ] Línea 42 — ejemplo "Missing tenant_id" → CFG (A10) + reword
- [ ] Commit

### 13. `final-auditor.md`

- [ ] Línea 8 — identidad → GEN-KEEP
- [ ] Líneas 33, 66 — paths `sie_v2/docs/process/...` → CFG (A6)
- [ ] Commit

### 14. `arki.md` (bootstrap, greenfield)

- [ ] Línea 98 — "04-backend-architecture.md ... FastAPI 4-layer, Django apps, Rails MVC" → ya es genérico (es un agente que ELIGE stack). Validar que use el campo `stack.*` del config que va a generar.
- [ ] Líneas 114, 117, 119-120, 127 — FastAPI bootstrap example → marcar como ejemplo SP-PY explícito (este agente PROPONE stacks, así que tener un ejemplo es OK). Agregar también ejemplo Node/Go.
- [ ] Commit

### 15. `inti.md` (bootstrap, greenfield discovery)

- [ ] Bajo coupling. Revisar cualquier asunción de stack y eliminar. (No detecté hits sie_v2 directos en grep #1.)
- [ ] Commit (probablemente trivial)

### 16. `amauta.md` (brownfield onboarding)

- [ ] Líneas 69 — ejemplo "TypeScript ref<T>" → marcar como ejemplo, no asunción
- [ ] Líneas 107-108 — "Adapted rules — use the stack's real vocabulary, not SIE v2's. E.g., for Django: ..." → YA ES GENÉRICO. Validar.
- [ ] Línea 205 — "Never force SIE v2's patterns" → YA ES GENÉRICO. Validar.
- [ ] Actualizar para consumir el `kuraka-inspect` mejorado de Fase 2 (cuando emita draft de config)
- [ ] Commit

---

## Skills worklist (post-agentes)

Aplicar en bloque tras agents 1-9. Items ya cubiertos por las tablas A-F arriba. Una pasada por skill:

- [ ] `analyze-requirement.md` (líneas 10, 23-25, 39)
- [ ] `refine-stories.md` (líneas 10, 20, 36, 54, 56, 68)
- [ ] `plan-tests.md` (líneas 27, 96)
- [ ] `review-stories.md` (líneas 14, 20, 29, 33, 43)
- [ ] `review-implementation.md` (líneas 22, 37, 76, 81-82)
- [ ] `schema-freeze.md` (líneas 46, 48)
- [ ] `implement-story.md` (líneas 14, 32, 34, 36, 38, 42, 44, 47, 51, 54, 58, 66, 74, 79, 96-97)
- [ ] `security-audit.md` (líneas 30-32, 40-41)
- [ ] `analyze-testability.md` (líneas 14, 77)
- [ ] `generate-unit-tests.md` (líneas 24, 39, 45, 72, 110, 120, 133-135)
- [ ] `generate-endpoint-tests.md` (líneas 3, 10, 14, 35-36, 47)
- [ ] `generate-e2e-tests.md` (línea 23)
- [ ] `validate-coverage.md` (líneas 3, 17, 26, 29, 38-39, 64-66)
- [ ] `write-tests.md` (líneas 3, 24-26, 32, 63, 87, 90, 98, 105, 111)
- [ ] `verify-deployment.md` (líneas 26, 44)
- [ ] `verify-output.md` (referencia indirecta — auditar)
- [ ] `run-audit.md` (líneas 27-29, 73)
- [ ] `detect-patterns.md` (línea 14)
- [ ] `compact-context.md` (línea 57)
- [ ] `kuraka.md` (líneas 24, 61-62, 90, 111-112, 116-117, 138, 165, 190, 219, 232)
- [ ] `kuraka-modes.md` (líneas 144, 148, 150, 153, 216, 278)
- [ ] `kuraka-policies.md` (líneas 89, 124, 182, 291)
- [ ] `gap-analysis.md` (líneas 37-39, 222, 225, 235) — **considerar si la skill entera es portable o si va al project layer de sie_v2**

---

## Rules worklist

- [ ] `rules/16-agent-backup.md` — marcar deprecated en Fase 3 header; eliminar en Fase 4 (cuando muera sync-obsidian.sh)
- [ ] `rules/17-kuraka-token-optimizations.md` — línea 200 referencia DD-896 → PL-LL (C3.8); resto del archivo es genérico, validar
- [ ] `rules/18-duplication-aware-refactor.md` — todo el ejemplo trabajado de líneas 107-123 es sobre DD-896/asitur/generali → mover ejemplo a PL-LL como caso de estudio o reformular genéricamente; el resto de la regla es portable

---

## Commands worklist

- [ ] `commands/clean-cases.md` → DELETE (E1)
- [ ] `commands/lint.md` → DELETE (E2)
- [ ] `commands/run-tests.md` → DELETE (E3)
- [ ] `commands/sync-from-vault.md` → mantener; revisar wikilink/backtick logic en Fase 4

---

## Progress log

| Fecha | Agente refactorizado | Items cerrados | Commit |
|---|---|---|---|
| 2026-05-12 | `po-analyst` + infra (stack-profiles, project-templates skeleton, migration-examples) | po-analyst worklist (11), C1.2, C2.2, C3.1, C3.4, F1, primer SP-PY | pending |
| 2026-05-12 | `backend-developer` + extensión SP-PY | backend-developer worklist (12), F2; SP-PY +2 items (no try/except in services, rename anti-pattern) | pending |
| 2026-05-12 | `code-reviewer` + `architect-reviewer` + `security-reviewer` (3 reviewers en bloque) | worklists 3 + 5 + 7, F4 + F5 + F6, C2.1 + C2.3 + C2.4, C3.2 + C3.5 | pending |

Infraestructura nueva creada en este turno (no estaba prevista como item individual del inventario pero queda registrada):

- `kuraka-artifacts/stack-profiles/{README.md, _template.md, python-fastapi.md}`
- `kuraka-artifacts/migration-examples/README.md`
- `kuraka-artifacts/migration-examples/sie_v2-project-layer/README.md`
- `mount-kuraka.sh` — añadida sección de mount para `stack-profiles/` → `.claude/stack-profiles/`

---

## Notas operativas

- **Mantener este archivo actualizado durante Fase 3**: cada checkbox marcado tras el commit correspondiente. El commit message del refactor de cada agente debe citar los IDs aquí (ej. "implements [A1, A2, C1.2, C3.2, F4]").
- **Eval de regresión sin evals automatizados**: la red de seguridad acordada es (a) cada commit aislado por agente (revertible), (b) revisión manual del prompt resultante, (c) sie_v2 como detector tardío. Si en algún commit el agente queda más débil de lo esperado, se revierte y se rehace.
- **CROSS-PROVIDER-CONVENTIONS.md** y `skills/evals/gap-analysis.json` son los dos artefactos nuevos del sync más sie_v2-coupled. Tratarlos como casos especiales (no son patrón estable del framework).
- **Idioma de salida**: per D0.5, los archivos refactorizados se escriben en **inglés** (agents/, skills/). Esto significa que el refactor también traduce los bloques en español que aún existen en `kuraka.md`, `kuraka-modes.md`, `kuraka-policies.md`. Se hace en el mismo commit que el decouple para no duplicar churn.
