---
name: kuraka
description: "Development orchestrator (kuraka, del Quechua *kuraq* — 'el mayor'). Multi-agent workflow for end-to-end requirements: PO analysis → Story refinement → Test planning → Architect review → Implementation → Code review → Security → Tests → E2E → Deployment → Final audit. Scale the pipeline to the change's risk — see `kuraka-modes`."
---

# Kuraka — Development Orchestrator

> *Kuraka* (también "curaca") — del Quechua `kuraq` = "el mayor". Era el líder
> local que coordinaba a los *ayllus* (grupos especialistas) bajo un plan mayor.
> En este sistema, el Kuraka es el orquestador que dirige a los agentes
> especializados a través de las fases del ciclo de desarrollo.

Este skill define el **flujo principal**. Dos ficheros complementan:

- `kuraka-modes.md` — variantes del flujo (Lite, Retroactive, reducido por riesgo) y cuándo usarlas
- `kuraka-policies.md` — políticas transversales (retry, timeout, telemetry, checkpoints)

---

## Pre-requisitos

Antes de arrancar necesitas:

1. Un REQ (documento) o ticket de Jira (p.ej. DD-755)
2. Descripción del requerimiento (de Jira, markdown o input del usuario)

Si el usuario no lo ha dado, pídelo antes de proceder.

---

## Decisión inicial: modo y pipeline

**ANTES de invocar cualquier agente** evalúa la superficie del cambio y decide:

1. **¿Qué capas toca?** UI-only / types-only / service / repository / schema / provider / auth
2. **¿Cuántos archivos y LOC estimados?**
3. **¿Hay lógica nueva? ¿Cambio de contrato? ¿PII/security? ¿Migración?**

Con eso elige modo:

| Modo | Fases | Cuándo |
|------|:----:|--------|
| **Normal** (default) | 8 | Cambios con lógica, DB, contratos API o providers |
| **Reducido por riesgo** | 3–5 | UI-only, types-only, renames mecánicos — ver `kuraka-modes.md` y `rules/17-kuraka-token-optimizations.md` |
| **Lite** | 3 | Cambios triviales que cumplen 9 criterios estrictos — ver `kuraka-modes.md` |
| **Retroactive** | 4 | Código ya implementado sin workflow (anti-pattern, evítalo) |

**Default es Normal.** Justifica y presenta el pipeline propuesto al usuario
**antes** de invocar cualquier agente — él aprueba qué fases correr.

---

## Phase-Agent-Skill Map (modo Normal — 8 fases)

| Phase | Agent | Skill | Gate |
|-------|-------|-------|------|
| 1. PO Analysis | [[po-analyst]] | [[analyze-requirement]] | User aprueba REQ |
| 2. Story Refinement | [[story-refiner]] | [[refine-stories]] | User aprueba stories |
| 2.5. Test Planning | [[test-engineer]] (mode: TEST_PLANNING) | [[plan-tests]] | User aprueba test plan |
| 3. Architect Review | [[architect-reviewer]] | [[review-stories]] + [[schema-freeze]] | Sin BLOCKERS; schema congelado |
| 4a. Backend Impl | [[backend-developer]] | [[implement-story]] | `ruff check .` + `make test` OK |
| 4b. Frontend Impl | [[frontend-developer]] | [[implement-story]] | `npm run lint` + `typecheck` + `test` OK |
| 5. Code Review | [[code-reviewer]] | [[review-implementation]] | Sin BLOCKERS ni IMPORTANT |
| 5.5. Security Review | [[security-reviewer]] | [[security-audit]] | Sin CRITICAL |
| 6. Tests | [[test-engineer]] (mode: TEST_WRITING) | [[analyze-testability]] + [[generate-unit-tests]] + [[generate-endpoint-tests]] + [[validate-coverage]] | Tests pasan |
| 6.5. E2E | [[e2e-tester]] | [[generate-e2e-tests]] | Playwright pasa |
| 6.7. Deployment | [[deployment-verifier]] | [[verify-deployment]] | Docker/env/nginx/CI válidos |
| 7. Final Audit | [[final-auditor]] | [[run-audit]] | Retro creado |

### Agentes condicionales

| Phase | Agent | Condición |
|-------|-------|-----------|
| 5 (sub) | [[migration-reviewer]] | Solo si hay ficheros en `backend/alembic/versions/` |

---

## Fases

### Phase 1 — PO Analysis
- Agent: [[po-analyst]] | Skill: [[analyze-requirement]]
- Output: `docs/process/REQ-{YYYYMMDD}-{ticket}-{slug}.md`
- Contenido: scope IN/OUT, tablas, endpoints, dependencias, riesgos, stories propuestas
- Gate: user aprueba REQ

### Phase 2 — Story Refinement
- Agent: [[story-refiner]] | Skill: [[refine-stories]]
- Output: `docs/process/stories/{ticket}-S{N}.md` (uno por story)
- Contenido: descripción, AC verificables, schema changes (si aplica), API contract, files
- Reglas: todo nombre en inglés; `T | None`; ruta exacta según estructura monorepo; `tenant_id` en queries
- Gate: user aprueba stories

### Phase 2.5 — Test Planning
- Agent: [[test-engineer]] (mode TEST_PLANNING) | Skill: [[plan-tests]]
- Output: `docs/process/test-plans/TEST-PLAN-{ticket}.md`
- Contenido: testability constraints, test cases por story, fixtures, riesgos, estimación de tests
- Por qué: contrato para el developer — el código debe ser testeable según este plan
- Gate: user aprueba test plan

### Phase 3 — Architect Review + Schema Freeze
- Agent: [[architect-reviewer]] | Skills: [[review-stories]] + [[schema-freeze]]
- Valida stories y test plan; congela schema antes de implementación
- Output: reporte con verdict + `docs/process/schemas/SCHEMA-FROZEN-{ticket}.md`
- Gate: todos los BLOCKER resueltos + schema congelado

### Phase 4 — Implementation
Dos sub-fases que pueden correr en paralelo si las stories son independientes:

- **4a Backend** — Agent: [[backend-developer]] | Skill: [[implement-story]]
  - Orden: Migration → Model → Schema → Repository → Service → Endpoint
  - Check tras cada archivo: `ruff check .`
  - Check tras cada story: `make test`

- **4b Frontend** — Agent: [[frontend-developer]] | Skill: [[implement-story]]
  - Orden: Types → Services → Stores → Composables → Components
  - Check tras cada archivo: `npm run lint && npm run typecheck`
  - Check tras cada story: `npm run test`

Reglas compartidas: max 700 LOC/fichero (400 en Vue), max 50 LOC/función, sin hardcoded values, sin magic strings, imports al top, sin código comentado.

Gate 4: todas las stories implementadas + checks en verde.

### Phase 5 — Code Review
- Agent: [[code-reviewer]] | Skill: [[review-implementation]]
- Framework 6D: correctness, security, performance, maintainability, readability, tests
- Output: reporte con tabla de findings por severidad (BLOCKER/IMPORTANT/MINOR/SUGGESTION/PRAISE)
- Gate: BLOCKER e IMPORTANT resueltos

### Phase 5.5 — Security Review
- Agent: [[security-reviewer]] | Skill: [[security-audit]]
- Scope: OWASP Top 10, secret scan, tenant isolation, auth por endpoint, GDPR
- Vocabulario: CRITICAL / HIGH / MEDIUM / LOW / INFO
- Gate: sin CRITICAL; HIGH aceptados explícitamente por el usuario

### Phase 6 — Tests
- Agent: [[test-engineer]] (mode TEST_WRITING) | Skills: [[analyze-testability]], [[generate-unit-tests]], [[generate-endpoint-tests]], [[validate-coverage]]
- Escribe tests según el plan de Phase 2.5 (AAA pattern, `test_should_{action}_when_{condition}`)
- Run: `make test` + `ruff check .`
- Gate: todos los tests pasan

### Phase 6.5 — E2E
- Agent: [[e2e-tester]] | Skill: [[generate-e2e-tests]]
- Scope: solo golden path de flujos cambiados (auth, tool flows, outbound)
- Skip legítimo: REQ pure-backend sin cambios user-facing
- Gate: Playwright en verde

### Phase 6.7 — Deployment Verification
- Agent: [[deployment-verifier]] | Skill: [[verify-deployment]]
- Valida: `docker-compose config`, env vars documentadas en `.env.example`, nginx, CI, migraciones aplican, smoke test de build
- Gate: sin BLOCKER

### Phase 6.8 — Smoke test runtime (OBLIGATORIO en TODO ciclo Kuraka)

**Aplica SIEMPRE.** Esta fase no es opcional ni condicional al tipo de cambio. Todo ciclo Kuraka — independientemente del provider, del scope, del modo (Normal/Lite/Retroactive) — debe ejercitar el flujo end-to-end antes de declarar el ciclo cerrado. El principio rector es **«tests verdes + reviews aprobadas ≠ feature funcional»**.

**El orquestador NO puede invocar Phase 7 (Final Audit / RETRO)** sin haber completado o justificado explícitamente esta fase. Si lo intenta, debe revertir y completar 6.8 primero.

**Pasos obligatorios:**

1. **Identificar el flujo end-to-end principal** del cambio. Para CUALQUIER cambio, articular en una frase: «el resultado de este ciclo es que el sistema ahora puede X cuando Y». Si no se puede articular, el alcance del ciclo está mal definido y hay que volver a Phase 1.
   - Ejemplos por tipo de cambio:
     - **Provider/integración**: «email entrante → case persistido en BD → sync a servicio externo».
     - **Endpoint nuevo**: «request HTTP autenticado → validación → service → repository → respuesta verificada».
     - **Refactor**: «el comportamiento observable antes y después del refactor es idéntico para los 2-3 flujos críticos que toca».
     - **UI/Frontend**: «el usuario navega a la página, ejecuta la acción principal, ve el resultado esperado». Dev server + browser, no solo `npm run build`.
     - **Schema/migration**: «la migration aplica sobre un dump real (o snapshot), las queries afectadas siguen funcionando, el rollback es seguro».
     - **Bug fix**: «el escenario que reproducía el bug ahora produce el comportamiento correcto».
2. **Diseñar UN escenario smoke test runtime** que ejercite ese flujo con:
   - Input realista (datos reales anonimizados o fixture lo más cercana posible a producción). **NO** mock sintético trivial generado por el agente.
   - Dependencias reales o mocks de alta fidelidad (httpx_mock con responses verificadas, base de datos real con seeds aplicados, no `MagicMock()` genérico).
   - Verificación de que TODOS los componentes encajan: contratos de datos, shapes esperados, side effects, persistencia, llamadas externas, manejo de errores cuando aplica.
3. **Ejecutar el escenario** end-to-end, no las piezas por separado.
4. **Documentar el resultado** en `docs/process/smoke-tests/SMOKE-{ticket}.md`:
   - Comando exacto ejecutado
   - Output verificado (con cita literal o screenshot si es UI)
   - Componentes ejercitados (lista cerrada)
   - Componentes NO ejercitados y por qué — cualquier componente del flujo no ejercitado debe tener justificación explícita («stub aceptado por scope DD-XXX», «requiere credenciales prod que no tenemos en dev», etc.)
5. **Si el smoke test falla**, abrir bug-fix story en Phase 4 antes de avanzar a Phase 7. **No cerrar el ciclo con flujo end-to-end roto.**

**Skip request** (no skip automático): el orquestador puede PEDIR al usuario saltar 6.8 SÓLO en estos casos, y sólo con aprobación explícita:

- **Documentación pura**: el ciclo no modifica código ejecutable.
- **Refactor verificable estáticamente** sin cambio de comportamiento (rename, mover archivos sin tocar lógica, tipado más estricto sin cambio runtime).
- **Imposibilidad técnica documentada** (ej. requiere infraestructura no disponible en dev). En este caso, abrir IMP/subtask para añadir el smoke test cuando la infraestructura esté disponible.

Si el usuario aprueba el skip, **documentarlo en el RETRO Phase 7** como riesgo aceptado con la justificación textual.

**Gate**: `docs/process/smoke-tests/SMOKE-{ticket}.md` existe y verde, O justificación de skip aprobada por el usuario y documentada en el RETRO.

**Por qué**: lección DD-896 IS-05 generalizada — `make test` verde + reviews aprobadas + RETRO cerrado NO garantiza que las piezas funcionen juntas. La regla del CLAUDE.md global ya lo dice para UI («Type checking and test suites verify code correctness, not feature correctness»); este gate extiende ese principio a TODO ciclo Kuraka, no solo a providers o integraciones. **Sin esta fase, cualquier ciclo puede cerrarse con tests verdes y feature rota — el coste oculto se traslada a post-cierre y no aparece en métricas formales.**

### Phase 7 — Final Audit
- Agent: [[final-auditor]] | Skill: [[run-audit]]
- Output: `docs/process/agent-retrospectives/RETRO-{REQ-name}.md` con:
  - Resumen + timeline de rework
  - Findings por agente + prompt patches concretos
  - Issues sistémicos + improvements
  - Telemetría de tokens/latencia

---

## Orchestrator constraint (NO tocar código directamente)

El orchestrator (Claude que ejecuta el Kuraka) **NUNCA** crea o modifica ficheros
fuente (`backend/`, `frontend/`, `tests/`, `migrations/`) antes de Phase 4.
Toda implementación va por [[backend-developer]] o [[frontend-developer]], sin
excepciones por "el cambio es trivial".

**Excepción legítima**: el orchestrator puede editar `docs/` (REQ, stories,
test plans, retros) y los ficheros del sistema Kuraka (`.claude/skills/`,
`.claude/agents/`, `.claude/rules/`).

**Protocolo si se viola**:
1. Revertir el cambio
2. Anunciar la violación al usuario
3. Enrutar por el agente correcto
4. Loggear el bypass en telemetría con `"agent": "orchestrator-direct"`

Este constraint fue añadido tras las retros de REQ-2026-04-17 y REQ-20260420
donde el bypass produjo type errors y telemetría rota.

---

## Reglas generales del Kuraka

- **Nunca saltar fases** cuando el pipeline las incluye — cada gate existe por una razón
- **Aprobación del usuario entre fases** — el orchestrator no auto-avanza
- **Schema freeze antes de Phase 4** — no DB changes durante implementación
- **Refrescar stories obsoletas** si el usuario hace correcciones entre fases
- **Una story a la vez en Phase 4** — baby steps
- **Optimización de tokens**: aplicar `rules/17-kuraka-token-optimizations.md` (context digest, end-only typecheck, combined phases, mapping-table stories, no auto-verify)
- **Tests verdes ≠ feature funcional** (principio rector universal): TODO ciclo Kuraka, sin excepción de tipo de cambio o provider, debe ejercitar el flujo end-to-end antes de cerrarse (ver Phase 6.8). `make test` verde + reviews aprobadas son condición necesaria pero NUNCA suficiente para declarar un ciclo terminado. Si el smoke test runtime no es viable, justificarlo explícitamente y registrarlo como riesgo aceptado en el RETRO. **Esta regla aplica a CUALQUIER cambio**: backend, frontend, refactor, bug fix, migration, integración o cosmético — no solo a providers o flujos de datos. Lección DD-896 IS-05.

---

## Templates de Workflow Status

Para modo Normal, añade al inicio del REQ:

```markdown
## Workflow Status
- [ ] Phase 1: PO Analysis
- [ ] Phase 2: Story Refinement
- [ ] Phase 2.5: Test Planning
- [ ] Phase 3: Architect Review + Schema Freeze
- [ ] Phase 4a: Backend Implementation
- [ ] Phase 4b: Frontend Implementation
- [ ] Phase 5: Code Review
- [ ] Phase 5.5: Security Review
- [ ] Phase 6: Tests
- [ ] Phase 6.5: E2E Tests
- [ ] Phase 6.7: Deployment Verification
- [ ] Phase 6.8: Smoke test runtime (OBLIGATORIO en todo ciclo — skip solo con justificación explícita)
- [ ] Phase 7: Final Audit
```

Para modos Lite / Retroactive / reducido, ver templates en `kuraka-modes.md`.
