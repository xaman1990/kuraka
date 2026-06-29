# Reporte de Optimización de Kuraka — Análisis Cross-Project de Retrospectivas

> **Fecha:** 2026-06-27
> **Alcance analizado:** 38 retrospectivas de ciclo, 6 parches de agente (`*.append.md`),
> 8 lessons-learned (clinica-dental) + 14 LL (kuraka-control), `RECURRING-ISSUES.md`,
> 3 review-checks, y 8 perfiles de proyecto.
> **Proyectos fuente:** `guai-home-marketplace` (23 ciclos), `clinica-dental-2026` (6 ciclos),
> `kuraka-control` (8 ciclos), + perfiles de sie_v2, dbcanvas, wacertificadonodeudor, etc.
> **Objetivo:** Identificar qué tuvo que ajustarse a mano en cada proyecto, extraer lo
> **común** entre proyectos, y convertirlo en mejoras al **vault base** de Kuraka para
> que esos parches dejen de ser necesarios.

---

## Parte 1 — Resumen ejecutivo

El hallazgo central: **los proyectos no fallan por bugs aislados de dominio, fallan por
las mismas ~14 lagunas estructurales del framework, una y otra vez.** Casi todos los
parches `*.append.md` y lessons-learned son instancias locales de un patrón generalizable.

Los 5 problemas más caros y recurrentes (aparecen en **2 o 3 de los proyectos**):

1. **El contrato se "recuerda/describe" en vez de observarse** — congelar esquemas desde
   Swagger/memoria en lugar de un *probe* en vivo o de payloads verbatim. (clinica-dental 4
   ciclos, guai 7 ciclos, kuraka-control enum-guess). Costó rescates de **~318–346K tokens**
   por ciclo en clinica-dental y **~48% de un ciclo de 4.16M tokens** en guai.

2. **"Verde" ≠ correcto** — `build`/`vitest` en verde tratado como Definition of Done,
   mientras el typecheck, el runtime real o el estado vacío esconden el bug. (los 3 proyectos).

3. **El loop de mejora no se cierra** — las retros proponen parches que nunca se aplican;
   `pattern-detector` se difiere ~6 ciclos; `RECURRING-ISSUES.md` queda obsoleto. El
   framework *captura* lecciones pero no las *aplica ni verifica*. (los 3 proyectos).

4. **Las correcciones triviales cuestan como features** — un fix de 2 líneas costó
   **154K tokens** porque el agente recarga toda la superficie; el digest de contexto
   (Rule T1) nunca se implementó en 8 ciclos. (los 3 proyectos).

5. **Los límites (latencia, tool-uses, LOC) son advisory** — `budget_ok: true` siempre,
   aunque se exceda el presupuesto 8×; los LOC se detectan tarde en Phase 5, nunca en
   freeze. (guai 4–7 ciclos, kuraka-control, clinica-dental).

**Recomendación estratégica:** priorizar las mejoras *meta* (cerrar el loop de retro,
auto-disparar pattern-detector, hacer typecheck parte de "verde", aplicar el digest T1)
antes que las mejoras por-agente, porque el loop meta es lo que hace que todas las demás
mejoras se mantengan aplicadas en lugar de re-descubrirse cada ciclo.

---

## Parte 2 — Cuadro tabular de hallazgos COMUNES (cross-project)

Ordenado por nº de proyectos donde aparece y severidad. "Proyectos" = en cuántos de los 3
proyectos con retros aparece; "Ciclos" = total de ciclos distintos que lo mencionan.

| # | Hallazgo común | Proyectos | Ciclos | Severidad | Elemento(s) Kuraka objetivo |
|---|----------------|:---------:|:------:|:---------:|------------------------------|
| C1 | **Contrato recordado/desde-docs en vez de observado** (Swagger miente, enum adivinado, esquema desde memoria) | 3/3 | ~14 | 🔴 Crítica | `po-analyst`, `architect-reviewer`, `schema-freeze`, `analyze-requirement` |
| C2 | **"Verde" ≠ correcto** (typecheck saltado, runtime-only crash, estado vacío mal leído, gate que no puede fallar) | 3/3 | ~12 | 🔴 Crítica | `verify-output`, `verify-deployment`, `kuraka` (Phase 4/6), `kuraka-policies`, `deployment-verifier` |
| C3 | **Loop de mejora no se cierra** (retro→parche no aplicado; pattern-detector diferido; RECURRING obsoleto) | 3/3 | ~10 | 🔴 Crítica | `final-auditor`, `run-audit`, `pattern-detector`, `detect-patterns`, `kuraka-archive.py` |
| C4 | **Fix barato = run caro** (recarga toda la superficie; digest T1 nunca aplicado; reviewer relee todo) | 3/3 | ~8 | 🟠 Alta | `kuraka-policies`, `rules/17`, `compact-context`, `code-reviewer`, orquestador |
| C5 | **Límites advisory** (`budget_ok` siempre true; latencia=wall-clock; tool-use caps no aplican) | 3/3 | ~9 | 🟠 Alta | `kuraka-policies`, `rules/17`, `aggregate-telemetry.py` |
| C6 | **LOC de función/archivo detectado tarde** (en Phase 5, nunca en plan/freeze) | 2/3 | ~6 | 🟡 Media | `architect-reviewer`, `story-refiner`, `implement-story`, `backend/frontend-developer` |
| C7 | **Mecanismo ambiguo en la historia** (parse/compare/serialize dejado como prosa-hedge, >1 implementación válida) | 2/3 | ~5 | 🟠 Alta | `story-refiner`, `po-analyst`, `architect-reviewer`, `refine-stories` |
| C8 | **Prosa no obliga al implementador** (pitfall como "Technical Note" → dev re-rompe; deviations silenciosas) | 2/3 | ~3 | 🟡 Media | `story-refiner`, `architect-reviewer`, `refine-stories`, `implement-story` |
| C9 | **Campos nullable/edge en seams de seguridad/escritura** (null entra a scope de token, fail-open, IDOR) | 2/3 | ~4 | 🟠 Alta | `architect-reviewer`, `story-refiner`, `security-reviewer` |
| C10 | **Smoke ambiguo / snapshot parcial** (hidden=no-access vs bug; subtree snapshot fabrica anomalía) | 2/3 | ~3 | 🟡 Media | `e2e-tester`, `verify-output`, `final-auditor` |
| C11 | **Detector de stack falla / faltan stack-profiles** (monorepo mal detectado; falta angular/express/react.md) | 2/3 | ~4 | 🟡 Media | `kuraka-inspect.py`, `amauta`, `mount-kuraka.sh` |
| C12 | **Deuda acarreada sin libro mayor** (follow-ups triviales re-flagged 8 ciclos sin cerrarse) | 2/3 | ~6 | 🟡 Media | `pattern-detector`, `final-auditor`, `rules/18` |
| C13 | **Freeze empírico adversarial** (POSITIVO — correr el path sospechoso antes de congelar; 3 catches MAJOR pre-código) | 2/3 | ~6 | 🟢 Reforzar | `architect-reviewer`, `schema-freeze` |
| C14 | **Tests/fixtures no exercitan el path real** (108 tests verdes sobre contrato falso; cliente vivo nunca ejecutado) | 2/3 | ~7 | 🔴 Crítica | `test-engineer`, `plan-tests`, `write-tests`, `validate-coverage` |

Hallazgos **mono-proyecto** notables (no comunes aún, pero alto valor — vigilar para 2ª aparición):
state-machine traps en flujos de pago (guai), telemetría no escrita (guai), docs/process
path-drift (guai), commit hygiene en repo sucio (guai), fail-open mock default en prod (guai),
VERSION file frágil del vault (kuraka-control), `:5174` port collision (kuraka-control).

---

## Parte 3 — Reporte detallado de hallazgos (por tema)

### C1 · El contrato se recuerda, no se observa  🔴
**Evidencia:** clinica-dental `LL-006-swagger-unreliable-live-probe`, `po-analyst.append.md`,
`architect-reviewer.append.md` (probe in-vivo, 4 ciclos: vet-pets, appointments, plan, +F27);
guai `mvp1-registro-perito-webhook` (webhook construido 2× contra contrato fabricado),
`payment-capture-mode` (columnas asertadas de memoria, mal en 3 fases), `case-reference-scheme`;
kuraka-control `arki` (enum `status` adivinado → GATE0 BLOCKER, LL-007/008).

**Causa raíz:** Ni `po-analyst` (Phase 1) ni `architect-reviewer` (Phase 3) diferencian
fidelidad-a-lo-conocido de descubrimiento-de-lo-desconocido. Cuando el usuario da bytes
exactos (Postman, payloads) o cuando hay un backend vivo, se modela "de memoria" y la
divergencia fluye aguas abajo hasta el lugar más caro (code review).

**Qué hacer:** Probe en vivo obligatorio + tabla de fidelidad verbatim **antes** del freeze.
(Ver Parte 4 → `schema-freeze`, `po-analyst`, `architect-reviewer`, `analyze-requirement`).

### C2 · "Verde" ≠ correcto  🔴
**Evidencia:** clinica-dental `LL-002-ng0203` (crash runtime invisible a `ng build`), favicon
cerrado por HTTP 200; guai gates que no pueden fallar (`make … | tail` devuelve exit de tail;
`make test-run` sin `--exit-code-from`), `vue-tsc` saltado → TS error en prod; kuraka-control
`LL-014` (cast inválido sobrevivió ~3 ciclos porque el gate corría vitest sin `tsc --noEmit`),
write-surface no exercitado en Phase 4.

**Qué hacer:** Redefinir "verde" = lint + **typecheck** + test; smoke en vivo obligatorio para
clases de fallo solo-runtime (DI, reactividad, lazy-load) y para toda superficie de escritura;
nunca pipear el comando cuyo exit-code es el gate; desambiguar estado-vacío de estado-roto.

### C3 · El loop de mejora no se cierra  🔴
**Evidencia:** clinica-dental "el hallazgo de proceso más importante de esta auditoría":
LL-004/005 + el probe de `tooling.md` propuestos en un ciclo y **nunca aplicados**, por eso el
mismo fallo de Swagger reapareció; guai `pattern-detector` diferido "~6º ciclo, no diferir de
nuevo", RETROs dispersos en 3 directorios; kuraka-control `RECURRING-ISSUES.md` obsoleto
(cubre S12→S4, faltan LL-013/014 y 3 retros), sin mecanismo para cerrar deuda trivial.

**Qué hacer:** `final-auditor`/`run-audit` debe, al inicio de cada auditoría, enumerar los
parches propuestos por la retro anterior y **verificar que se aplicaron**, reportando fugas como
hallazgo sistémico. `pattern-detector` debe **auto-dispararse** tras N retros (no ser opcional).
Consolidar RETROs a un único directorio canónico (en `kuraka-archive.py`).

### C4 · Fix barato = run caro  🟠
**Evidencia:** clinica-dental fix de 2 líneas = **154,177 tokens** (más que la implementación
completa); guai Rule-T1 no aplicado en 3 ciclos, plan Phase-2.5 re-derivado en Phase-6
(~30–50K perdidos); kuraka-control code-reviewer 25–58 min en 4/8 ciclos releyendo todo.

**Qué hacer:** Para runs de "aplicar N MINOR fixes" y para el code-reviewer, pasar un **digest
pre-extraído** (archivos + rangos de línea + texto del finding + esquema congelado + invariantes)
para que el agente no recargue toda la superficie. Ahorro estimado ~40–80K por run.

### C5 · Límites advisory  🟠
**Evidencia:** guai 7 ciclos con `budget_ok: true` mientras po-analyst corría 31–86 min (cap
10 min); clinica-dental code-reviewer 101 tool-uses vs cap 40, sin guardrail; la métrica mezcla
wall-clock (espera de DB/contenedor) con compute.

**Qué hacer:** Separar wall-clock de compute en telemetría; re-baseline por clase de fase;
hacer que `budget_ok` refleje realmente el umbral (soft-gate: avisa + requiere ack del
orquestador). Dejar de emitir `budget_ok: true` sin chequear.

### C6–C14
(Resumidos en la tabla de Parte 2; el detalle accionable está en la Parte 4 por elemento).

---

## Parte 4 — Plan de mejora por elemento

> Convención: cada ítem dice **[Cx]** el hallazgo común que lo origina, y **(gen/esp)** si es
> mejora generalizable al vault base o un patrón a documentar. Editar manteniendo wikilinks
> `[[...]]` en `agents/`, `agents/contexts/`, `skills/`, `rules/` (NO en `commands/`).

### AGENTES

#### `po-analyst` (+ `contexts/po-analyst-rules.md`)
- **[C1] Pase de fidelidad-verbatim** distinto del gap-finding: si el usuario aporta payloads
  exactos, construir tabla `campo · tipo · id-vs-hash/opaco · endpoint` y diferenciarla contra
  cada interfaz generada **antes** del freeze. (gen)
- **[C1] GATE0 contract-first:** bloquear toda historia de integración externa hasta tener
  payload real capturado + header de auth + lista de eventos. El veredicto lleva línea
  "Contract provenance". (gen)
- **[C9] Config-classification gate:** REQUIRED solo para secretos/conexiones sin default
  seguro; DEFAULTED para constantes operativas. "Cada entorno debe añadir N vars nuevas" =
  smell que requiere sign-off. (gen)
- **Modo deletion-cycle:** entrar por prueba, no por creencia; grep-verificar que no hay
  consumidor vivo antes de borrar. (gen)

#### `architect-reviewer` (+ `contexts/architect-reviewer-rules.md`)
- **[C13] Checklist de freeze empírico-adversarial** (la mejora de mayor leverage, validada 3×):
  (a) **correr** la mutación/contención propuesta contra el store vivo antes de congelar;
  (b) tratar cada `z.string().nullable()` de propiedad externa como input adversarial — declarar
  manejo de null/blank, nunca bindear null a un token-scope o clave de conflicto;
  (c) congelar invariantes nombrados + tabla de ataque con columna "where". (gen) **[C9]**
- **[C1] Probe in-vivo como precondición de Phase 3** para endpoints nuevos/re-cableados; citar
  el probe (no Swagger) como fuente de verdad. (gen)
- **[C6] LOC en freeze:** `LOC_actual + delta_estimado ≤ cap` para cada archivo/función ALTERado;
  BLOCKER con plan de extracción de helper nombrado. (gen)
- **[C8] Pitfalls estructurales como snippet copy-this** en la AC, nunca como prosa. (gen)
- **State-machine / migraciones** (esp→gen): transiciones multi-hop = intentos independientes;
  sanar filas envenenadas in-place; resolver decisión `CREATE INDEX CONCURRENTLY` en la AC
  (nunca dentro de Alembic transaccional).

#### `story-refiner` (+ `contexts/story-refiner-rules.md`)
- **[C7] Nombrar el mecanismo:** para cualquier paso parse/compare/curate/serialize con >1
  implementación razonable, la AC declara el mecanismo *resuelto* en una línea — nunca un hedge.
  (Colapsar LL-011/012/013 en una lección-paraguas). (gen)
- **[C8] Snippets vinculantes:** pitfall estructural (routing, DI/provider scope, lazy-load,
  module wiring) embebido como bloque corregido copy-this en la AC del story dueño. (gen)
- **[C8/AC] Filas de AC marcadas normativa-vs-ilustrativa** para que el dev no salte edge-cases
  obligatorios. (gen)
- **[C6] Header del story** registra LOC actual de cada archivo/función ALTERado. (gen)
- **Rename stories** incluyen inventario grep de tests/fixtures/seeds que referencian el nombre
  viejo (evoluciona en sitio, no crea `*_rename.py`). (gen)

#### `code-reviewer` (+ `contexts/code-reviewer-rules.md`)
- **[C1] Cross-check de contrato dirigido por defecto** (no esperar instrucción per-cycle):
  cuerpos implementados vs esquema congelado + payloads verbatim, en nombre/tipo/id-vs-hash/casing.
  (gen) — *este es literalmente el `code-reviewer.append.md` de clinica-dental.*
- **[C2] Check normalize-before-compare:** todo string externo usado como clave de mapa/match
  debe normalizarse idempotentemente antes. (gen)
- **Double-submit check:** formularios/acciones mutantes con exactamente un trigger de submit +
  guard `submitting` (2ª ocurrencia en clinica-dental → merece check estándar). (gen)
- **[C5] Niveles de severidad `DEFERRED`/`INFO`** para gaps que pertenecen a una fase posterior
  planificada; reservar BLOCKER para must-fix-antes-de-este-gate. (gen)
- **Sibling-guard parity** y **design-token-defined** (`var(--x)` debe existir en tokens) y
  **React namespace types** (`React.X` en posición de tipo → MINOR) como checks mecánicos. (gen)
- **[C4] No releer toda la superficie** — consumir el digest pre-extraído. (gen)

#### `backend-developer` (+ rules)
- **[C6] Self-lint de longitud de función** antes de declarar done. (gen)
- **[C8] Flag de deviation:** cualquier desviación de instrucción explícita se reporta con
  rationale + camino de vuelta al estado instruido (no substituir en silencio). (gen)
- **Heal-in-place** (≤1 registro activo por clave lógica) y **verify-or-self-heal** para IDs
  externos persistidos re-jugados (bounded: 1 try/except/retry). (esp→gen)
- **Promover Rule-T6** (secuencial-por-story + `make test`) de regla de proyecto a default. (gen)

#### `frontend-developer` (+ rules)
- **[C2] Phase 6 corre type-check** (`vue-tsc`/`tsc --noEmit`), no solo vitest. (gen)
- **[C2] Smoke runtime en vivo** para módulos con primitivas creadas dinámicamente. (gen)
- Double-submit guard; **render de fecha externa verbatim** (nunca `new Date(...)` para mostrar
  un `YYYY-MM-DD`); extraer lógica pura a `lib/`/composable por defecto. (gen)

#### `final-auditor` (+ `contexts/final-auditor-rules.md`)
- **[C3] Verificar aplicación de la retro anterior** al inicio de la auditoría; reportar fugas
  como hallazgo sistémico/escalante. (gen) — *es el `final-auditor.append.md` de clinica-dental.*
- **[C3] Telemetría como gate de Phase 7:** bloquear si falta `{REQ}-telemetry.json`; añadir
  campo `status: ok|session_limit|interrupted`. (gen)
- **[C12] Libro mayor de deuda acarreada:** ítem flagged en N ciclos consecutivos se agenda. (gen)
- **Ciclo auditado-pero-no-commiteado** = ítem bloqueante/diferimiento explícito. (gen)
- **[C10] Veredicto "front-ready/backend-pending" de primera clase** (no re-derivar cada ciclo). (gen)

#### `security-reviewer` (+ rules)
- **[C9] Fail-open mock default:** toda factory mock/live cuyo path mock salte un control de
  seguridad debe lanzar en `is_prod()`. (gen)
- Cambio random→secuencial de identificador = evento de seguridad (enumerar endpoints keyed por
  el id para confirmar authz; un control basado en inadivinabilidad puede volverse IDOR). (gen)
- Aristas con `requires_role` no-null deben enforcarse (no advisory). (gen)

#### `deployment-verifier` (+ rules)
- **[C2] Re-derivar todo número** (test/edge/table counts) del output del run actual; nunca
  asertar un flag de config sin citar la línea literal. (gen)
- **Integridad del gate:** verificar que cada gate declarado realmente puede fallar. (gen)

#### `e2e-tester`
- **[C10] Snapshots de página completa** al verificar estado de modal/overlay (subtree fabrica
  anomalías). (gen)
- **[C10] Desambiguar empty-vs-broken** antes de cerrar (inspeccionar datos/headers
  subyacentes). (gen)

#### `pattern-detector` (+ `detect-patterns`)
- **[C3] Auto-trigger tras N retros** (no recomendación opcional del auditor). (gen)
- **[C3] Leer corpus consolidado** (un solo directorio de RETRO). (gen)
- **[C12] Mantener el libro mayor de deuda acarreada** cross-cycle. (gen)

#### `amauta`
- **[C11] Verificar que existe stack-profile** para el framework detectado; crearlo/flaggearlo
  antes de correr ciclos. (gen)
- **[C11] Validar el veredicto de `kuraka-inspect`** contra `package.json` workspaces antes de
  draftear config (corrige misdetección de monorepo). (gen)

#### `migration-reviewer`
- Guard `alembic heads == 1` cuando existe migración no-trackeada; `down -v` programado al
  borrar/renumerar revisión. (esp→gen)

### SKILLS

| Skill | Mejoras |
|-------|---------|
| `schema-freeze` | **[C1]** Probe in-vivo obligatorio (422/multipart), citar probe no docs; **incluir formato de serialización** (datetime/number/null), no solo nombre/tipo; **[C13]** verificar round-trip `serialize(parse(raw))===raw` empíricamente antes de congelar escrituras. |
| `analyze-requirement` | **[C1]** Tabla de fidelidad verbatim + "contract provenance"; **[C9]** clasificación de config required-vs-defaulted. |
| `requirement-consistency-check` | Detectar contradicciones spec↔código (constitución dice "strict TS" pero tsconfig lo tiene off) como hallazgo explícito; **asegurar que la skill se monta** (gap de entorno en clinica-dental). |
| `review-implementation` | **[C1]** Cross-check de contrato por defecto; **[C2]** normalize-before-compare; double-submit; **[C5]** niveles DEFERRED/INFO. |
| `verify-output` / `verify-deployment` | **[C2]** "build verde ≠ runtime"; smoke en vivo para clases solo-runtime; **[C10]** desambiguar empty-vs-broken; **template de smoke en temp-vault** para superficies de escritura (ejercer mutación → asertar store real intacto → borrar). |
| `refine-stories` / `review-stories` | **[C7]** nombrar mecanismo; **[C8]** snippets copy-this + filas AC normativas; **[C6]** LOC en header. |
| `kuraka-policies` | **[C5]** latencia wall-clock vs compute; **[C2]** typecheck en definición de "verde"; **[C4]** digest T1; soft-gate de caps; circuit-breaker de fixes reactivos (tras 2 fixes ad-hoc en la misma superficie → abrir delta-story). |
| `run-audit` | **[C3]** check de aplicación de retro previa; gate de telemetría; **[C12]** deuda acarreada. |
| `detect-patterns` | **[C3]** auto-trigger; consolidación de directorios. |
| `kuraka-modes` | Modo **deletion-cycle**; modo **partial-smoke** (front-ready/backend-pending); modo **reduced/incremental** (abrir REQ ligero aun para trabajo en goteo); **split read/write** como respuesta estándar a nueva clase de riesgo. |
| `compact-context` | **[C4]** digest para fix-runs y reviewer; anotar snippets de reuse ("verificar vs design-system"; citar precedentes por estructura, no por color). |
| `plan-tests`/`write-tests`/`validate-coverage` | **[C14]** asertar el contrato de retorno COMPLETO (cada campo usado por consumidores, esp. secretos/tokens); ≥1 test que ejercita el cliente vivo (httpx-mock); fixtures desde payload real capturado; assertions delta/`>=` en DB compartida (nunca conteos absolutos); strip comments antes de meta-tests de token-scan; **[C2]** incluir typecheck. |

### WORKFLOW — orquestador `skills/kuraka.md` (lifecycle 8 fases)

- **Phase 0:** smoke de stack real (boot + 1 endpoint + `make test-run`) para que un import
  faltante no se disfrace de fallo de story. **[C2]**
- **Phase 3:** precondición de probe de contrato in-vivo. **[C1]**
- **Phase 4:** "done" = lint + **typecheck** + test; para superficies de escritura, **live-verify
  obligatorio en temp-vault** (happy + idempotencia + store-real-intacto) antes de Phase 5. **[C2][C14]**
- **Phase 5:** review **no-skippable** aun para cambios de un solo agente "triviales". **[C2]**
- **Phase 7:** gate de telemetría + verificación de aplicación de retro previa + commit hygiene
  (scope `git add` a archivos del story tras revisar `git diff --cached`) + libro de deuda. **[C3][C12]**
- **Transversal:** integridad de gates (nunca pipear el comando del exit-code); resolución de
  paths de `docs/process` desde `kuraka.config` anclado a repo-root. **[C2]**
- **Rule-0 scaling:** de-pesar/saltar Phase 3 en ciclos de puro restyle de un archivo.

### RULES (framework)

- **`rules/17-kuraka-token-optimizations.md`:** aplicar digest T1 (enforce), añadir T7
  "gate command integrity", T8 "circuit-breaker de fixes reactivos", y modelo de latencia
  wall-clock-vs-compute. **[C4][C2][C5]**
- **`rules/16-agent-backup.md`:** commit scoping por story; protección de ciclo no-commiteado. **[C12]**
- **`rules/18-duplication-aware-refactor.md`:** libro mayor de deuda acarreada; sibling-guard parity. **[C12]**

### HERRAMIENTAS (scripts del vault)

| Herramienta | Mejora |
|-------------|--------|
| `kuraka-inspect.py` | **[C11]** detección de workspaces/monorepo (npm/pnpm/yarn, `packages/*`); corrige misdetección single-package. |
| `aggregate-telemetry.py` | **[C5]** separar wall-clock de compute; campo `status`; re-baseline `BUDGETS` por clase de fase (mantener en sync con `kuraka-policies` y `rules/17`). |
| `kuraka-archive.py` | **[C3]** consolidar RETROs a un directorio canónico + único `RETRO-LATEST`; sembrar `RECURRING-ISSUES.md`. |
| `kuraka-init.py` | Crear `VERSION` canónico en raíz del vault (hoy se regex-scrapea `DEFAULT_VERSION`). |
| `validate-kuraka.sh` | Flaggear skills/stack-profiles ausentes en el consumidor (gap de `requirement-consistency-check` en clinica-dental). |
| **Nuevos stack-profiles** | `angular.md`, `express.md`, `react-vite.md` (faltan; conventions llegaban por inyección manual frágil). **[C11]** |

---

## Parte 5 — Roadmap priorizado

**Ola 1 — Meta-loop (hace que todo lo demás se mantenga aplicado).** ~mayor ROI.
✅ **IMPLEMENTADA 2026-06-27** (commit pendiente).
1. ✅ `final-auditor` + `run-audit`: sección 0 "Prior-Retro Application Check" al
   inicio de la auditoría. **[C3]**
2. ✅ `pattern-detector` + `detect-patterns`: auto-trigger cada 5 retros + umbral
   cross-project (2+ proyectos distintos = patrón) + consolidar corpus de RETROs. **[C3]**
   *(Pendiente: consolidación física de directorios en `kuraka-archive.py` — Ola 4.)*
3. ✅ `kuraka-policies` ("Definition of green") + `kuraka.md` (Phase 4a typecheck +
   Gate 4): "green" = lint + typecheck + test. **[C2]**
4. ✅ `rules/17` (nueva Rule T7 gate-integrity + T8 digest) + `compact-context`
   (modo digest para fix-runs y reviewer). **[C4]**

**Ola 2 — Correctitud de contrato (lo más caro históricamente).**
✅ **IMPLEMENTADA 2026-06-27** (commit pendiente).
5. ✅ `schema-freeze` (paso 1b + provenance) + `po-analyst` (Contract-first GATE +
   reglas 10/11) + `analyze-requirement` (paso 4b): probe in-vivo + fidelidad
   verbatim + clasificación de config. **[C1]**
6. ✅ `architect-reviewer`: Empirical Freeze Checklist (E1–E6) + filas 14/15 +
   reglas 8/9 (correr el path, nullable-as-adversarial, fail-open, state-machine,
   migraciones, LOC en freeze). **[C13][C9][C6]**
7. ✅ `test-engineer` (full contract + live path + green-test integrity) +
   `plan-tests` (reglas 7/8/9). **[C14]**

**Ola 3 — Calidad de historias y reviews.**
✅ **IMPLEMENTADA 2026-06-27** (commit pendiente).
8. ✅ `story-refiner` (reglas 15–18) + `refine-stories` (pasos 7–9): nombrar
   mecanismo + snippets copy-this vinculantes + AC normativa-vs-ilustrativa +
   inventario de rename. **[C7][C8]**
9. ✅ `code-reviewer` (Directed checks + severidad DEFERRED/INFO + reglas 6–8) +
   `review-implementation` (paso 5.5): cross-check de contrato por defecto,
   normalize-before-compare, single-submit, design-token, namespace-types,
   sibling-guard, silent-deviation, re-derive numbers. **[C1][C5]**
10. ✅ LOC en freeze ya cubierto en Ola 2 (architect E6) + story-refiner regla 14. **[C6]**

**Ola 4 — Telemetría, modos y herramientas.**
✅ **IMPLEMENTADA 2026-06-27** (commit pendiente).
11. ✅ `aggregate-telemetry.py` (status field + wall-clock labeling + over-budget
    solo por tokens) + `kuraka-policies` (budget=tokens, duration no es gate,
    `budget_ok` real, `status` en telemetría). **[C5]**
12. ✅ `kuraka-modes`: modos deletion-cycle / partial-smoke / incremental (tabla + secciones).
13. ✅ `kuraka-inspect.py` (detección npm/yarn-workspaces + packages/apps, testeada) +
    `amauta` (verificar veredicto de structure + existencia de stack-profile) +
    nuevos stack-profiles `angular.md` / `express.md` / `react.md` + README. **[C11]**
14. ✅ `e2e-tester` + `generate-e2e-tests`: full-page snapshot + empty-vs-broken. **[C2][C10]**

---

## ✅ Las 4 olas implementadas (2026-06-27). Pendiente de commit.

Quedan como trabajo opcional fuera de las 4 olas: `validate-kuraka.sh` flaggear
skills/stack-profiles ausentes, `kuraka-init.py` archivo `VERSION` canónico, y la
expansión de los 3 stack-profiles nuevos (hoy en estado `draft`).

---

## Apéndice — Patrones POSITIVOS a endurecer como default

No todo es a corregir; estos comportamientos emergentes funcionaron y conviene promoverlos
de regla-de-proyecto a default del vault:

- **GATE0 inspección de rama vs premisa stale del usuario** (guai) — el de mayor ROI; previno
  migraciones duplicadas, 4 contradicciones de contrato, 2 trampas de sobre-borrado.
- **Freeze empírico-adversarial** (kuraka-control) — 3 catches MAJOR pre-código, 0 rework.
- **Rule-T6 secuencial-por-story + `make test`** (guai) — ~0 rework cross-story.
- **Split read/write + sub-split** (kuraka-control) — aísla la primera clase de riesgo de mutación.
- **Smoke en temp-vault desechable** para superficies de escritura (kuraka-control).
- **Review-check mecánico** (React namespace §8) — mató una recurrencia al primer deploy.
