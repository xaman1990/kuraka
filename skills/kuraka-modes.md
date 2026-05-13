---
name: kuraka-modes
description: "Variantes del Kuraka (Bootstrap, Brownfield, Lite, Retroactive, Reducido por riesgo). Define cuándo usar cada modo según el tipo de proyecto o cambio."
---

# Kuraka — Modes

Este fichero describe las variantes del flujo principal (`kuraka.md`). El default
para cambios incrementales en un proyecto existente es **Normal** (8 fases). Los
modos **Bootstrap** y **Brownfield** son puntas de lanza: se usan **una sola vez**
al inicio de un proyecto nuevo o al integrar Kuraka en un codebase preexistente.

| Modo | Cuándo | Fases/agentes |
|---|---|---|
| **Bootstrap** (Greenfield) | Proyecto sin código todavía (solo una idea) | `inti` → `arki` → normal Kuraka |
| **Brownfield** | Proyecto existente sin Kuraka todavía | `kuraka-inspect` → `amauta` → normal Kuraka |
| **Normal** | Cambio en proyecto con Kuraka ya integrado | 8 fases (ver `kuraka.md`) |
| **Reducido por riesgo** | Cambio estrecho de baja complejidad | 3–5 fases |
| **Lite** | Cambio trivial (9 criterios estrictos) | 3 fases |
| **Retroactive** | Código ya implementado sin pasar por Kuraka (anti-pattern) | 4 fases |

---

## Modo: Bootstrap (Greenfield — proyecto nuevo)

**Cuándo**: arrancas un proyecto que no tiene código aún. El usuario solo
tiene una idea, un brief de producto o un Figma. No hay stack elegido, no hay
estructura de repo, no hay rules.

**Phase map**:

| Phase | Agent | Skill | Output | Gate |
|---|---|---|---|---|
| B1 | `inti` | (interview-driven) | `docs/discovery/vision.md` + `docs/discovery/requirements.md` | Usuario aprueba discovery |
| B2 | `arki` | (stack proposal + bootstrap) | `docs/arquitectura/` + `.claude/rules/` + `kipus/` + source skeletons + project root files | Usuario aprueba stack + scaffolding |

Tras B2, el proyecto está listo para el modo **Normal** con po-analyst como
primera fase del primer REQ.

**Cómo arrancar**:

```bash
# desde el directorio vacío del proyecto nuevo
bash ~/.kuraka/mount-kuraka.sh    # monta agentes + rules básicas
/exit                              # reinicia Claude Code para registrar agentes
# nueva sesión:
# invocar inti: "Quiero arrancar un proyecto nuevo: {descripción}"
```

**Cuándo NO usar Bootstrap**:
- Ya existe código en el directorio → usa Brownfield
- Ya existe `.claude/rules/` propio del proyecto → usa Normal directamente

**Ahorro esperado**: Bootstrap reemplaza ~2 semanas de "pensar la arquitectura
desde cero" con un flujo estructurado de 2 fases. No es un atajo — es rigor
aplicado desde el día 0.

---

## Modo: Brownfield (proyecto existente sin Kuraka)

**Cuándo**: el repo ya tiene código maduro pero Kuraka nunca se ha usado ahí.
Necesitas generar `rules/`, `docs/` y `kipus/` sin inventar convenciones —
extrayéndolas del código real.

**Phase map**:

| Phase | Tool/Agent | Output | Gate |
|---|---|---|---|
| W0 | `kuraka-inspect.py` (script, no agente) | `inspect-report.json` | Usuario revisa el reporte |
| W1 | `amauta` | `.claude/rules/` + `docs/` skeleton + `kipus/` + convention matrix con findings dudosos marcados | Usuario aprueba las reglas generadas |

Tras W1, el proyecto está listo para modo **Normal** en su próximo REQ.

**Cómo arrancar**:

```bash
# desde la raíz del repo existente
python3 ~/.kuraka/kuraka-inspect.py > inspect-report.json
bash ~/.kuraka/mount-kuraka.sh    # monta agentes
/exit                              # reinicia Claude Code
# nueva sesión:
# invocar amauta: "Acabo de montar Kuraka en este proyecto existente.
#                  Lee inspect-report.json y genera rules + docs."
```

**Cuándo NO usar Brownfield**:
- Proyecto sin código aún → usa Bootstrap
- Ya hay `.claude/rules/` propio → solo falta sync de agentes, no rehacer reglas

**Regla dorada del amauta**: nunca inventes convenciones. Si no las viste en
código, marcarlas como TODO es mejor que fabricarlas.

---

## Modo: Reducido por riesgo (recomendado para cambios pequeños estructurales)

**Cuándo:** la superficie del cambio es estrecha y no toca lógica crítica.

**Cómo elegir**:

| Superficie | Pipeline mínimo | Omite (con razón) |
|---|---|---|
| UI-only restyle (CSS/clases, sin lógica) | 1 + 2 + 4b | 2.5, 3, 5, 5.5, 6, 6.5, 6.7, 7 (no hay lógica nueva) |
| Type tightening (sin lógica) | 1 + 4b + 5 | 2.5, 3, 5.5, 6, 6.5, 6.7, 7 (review detecta magic strings) |
| Rename mecánico (identifier / file) | 1 (combinado con 2) + 4b + 5 | 2.5, 3, 5.5, 6.5, 6.7, 7 |
| Config edit (env var, docker-compose) | 1 + 4 + 6.7 | 2, 2.5, 3, 5.5, 6, 6.5, 7 |

**Regla**: propone el pipeline al usuario con tabla justificando cada fase
omitida. No asumas; pregunta antes de invocar agentes.

**No uses este modo** para cambios que toquen lógica de negocio, contratos API,
BD, auth o providers — ahí Normal es obligatorio.

Ver también `rules/17-kuraka-token-optimizations.md` para los patrones T1–T5
aplicables en cualquier modo.

---

## Modo: Lite (cambios triviales, criterio estricto)

> ⚠️ Modo EXCLUSIVO para cambios triviales que cumplen TODOS los 9 criterios
> abajo. Si alguno falla → usa Normal o Reducido por riesgo. No uses Lite para
> ahorrar tiempo en cambios normales.

### Criterios OBLIGATORIOS

- [ ] **≤ 3 archivos fuente afectados**
- [ ] **0 migraciones Alembic**
- [ ] **0 endpoints nuevos** (solo modifica existentes o no toca endpoints)
- [ ] **0 cambios de schema SQL**
- [ ] **0 cambios de contrato API** (request/response estables)
- [ ] **Sin impacto en auth ni permisos**
- [ ] **Sin cambios en código de seguridad** (auth, encryption, tokens)
- [ ] **Sin cambios en providers**
- [ ] **Complejidad S — ≤ 50 LOC totales**

Si CUALQUIERA falla → **NO es Lite**.

### Casos que NUNCA califican

- Agregar/quitar columna de BD (aunque sea 1 línea en el modelo)
- Nuevo endpoint, aunque sea trivial
- Cambio en `backend/api/services/providers/`
- Cambio en auth / JWT / tokens / CORS
- Cambio en logging de datos sensibles
- Migración o seeding de datos de producción
- Cambio en stores de Pinia compartidos

### Ejemplo SÍ: REQ-20260420-clean-specialty-names
2 archivos, 0 migraciones, cambio puramente de display (UI fallback), complejidad S.

### Ejemplo NO: REQ-2026-04-17-excel-parallel-generation
1 archivo pero +150 LOC con cambio de algoritmo (semáforo, parallel async).

### Phase Map Lite (3 agentes vs 8)

| Lite Phase | Agentes | Reemplaza |
|------------|---------|-----------|
| L1 | [[po-analyst]] (mode: LITE_COMBINED) | Phase 1 + 2 + 2.5 |
| L2 | [[backend-developer]] / [[frontend-developer]] | Phase 4 |
| L3 | [[code-reviewer]] + escribe tests | Phase 3 + 5 + 6 + 7 |

**Fases omitidas** (justificación inherente al modo):
- Phase 3 (Architect) — L3 review lo cubre
- Phase 5.5 (Security) — Lite no permite cambios de seguridad
- Phase 6.5 (E2E) — Lite no permite cambios de flujo
- Phase 6.7 (Deployment) — Lite no permite cambios de config
- Phase 7 (Final Audit) — reemplazado por nota ligera en L3

### L1 — Combined PO + Stories + Test Plan

Agent: [[po-analyst]] (mode: LITE_COMBINED)

Output: `docs/process/REQ-LITE-{YYYYMMDD}-{slug}.md` todo-en-uno con:
- Scope + 9 criterios Lite verificados
- Lista de archivos afectados
- 1–3 stories embebidas con AC
- Test plan mínimo embebido
- Confidence

Gate: usuario aprueba el REQ-LITE.

### L2 — Implementation

Agent: [[backend-developer]] o [[frontend-developer]] (según corresponda).

Implementa stories secuencialmente. Si hay backend + frontend, se invocan
ambos (backend primero si hay contrato). Cada uno corre sus checks.

Gate: archivos modificados + tests pasando.

### L3 — Review + Audit

Agent: [[code-reviewer]] (mode: LITE_FINAL). Una sola invocación hace:
1. Code review 6D
2. Genera tests si el developer no los escribió
3. RETRO corto solo si hay lección preventible

Output: review report con verdict + RETRO corto (opcional).

Gate: findings resueltos.

### Template Workflow Status (Lite)

```markdown
## Workflow Status (Lite)
- [x] Lite Criteria: 9/9 VERIFICADOS ✓
- [ ] L1: REQ-LITE + Stories + Test Plan
- [ ] L2: Implementation
- [ ] L3: Review + Tests + Audit
```

### Ahorro esperado (datos históricos)

- REQ-20260420 tipo: ~706K → ~200K tokens (−71%)
- Duración: ~12 min → ~4 min
- Gates de aprobación: 8 → 3

### Regla de oro

**Si dudas si califica como Lite → NO califica.** Usa Normal o Reducido por
riesgo. Un workflow "caro" bien hecho cuesta menos que un Lite mal aplicado.

### Escalamiento mid-cycle

Si durante L2/L3 descubres que el cambio es más complejo de lo esperado (p.ej.
requiere columna nueva):

1. **STOP inmediato**
2. Notifica al usuario: "Este cambio ya no califica como Lite. Requiere escalar. ¿Procedo?"
3. Revierte si es necesario
4. Re-arranca en Phase 1 de Normal con el contexto ya conocido

---

## Modo: Retroactive (código ya implementado)

**Trigger**: el usuario dice que la implementación ya está hecha, o detectas que
los archivos modificados ya contienen los cambios descritos.

**Anti-pattern**: evítalo cuando sea posible. La existencia de este modo
implica que se saltó el workflow — no es una alternativa válida "por defecto".
Existe para reconstruir documentación retroactivamente, no para justificar
bypass sistemático.

### Phase Map Retroactive

| Retro Phase | Reemplaza | Agent | Función |
|------------|-----------|-------|---------|
| R1 | Phase 1 + 2 + 2.5 | [[po-analyst]] | Genera REQ + stories + test plan en un pase leyendo el código existente |
| R2 | Phase 3 + 5 | [[code-reviewer]] | Review conjunto de stories, test plan e implementación |
| R3 | Phase 6 | (skip si tests existen) | Valida tests existentes, escribe los que falten |
| R4 | Phase 7 | [[final-auditor]] | Retrospectiva |

### R1 — Combined PO + Stories + Test Plan

Agent: [[po-analyst]] en un solo pase. Lee el código implementado y los tests
existentes para extraer nombres de funciones, paths, y test cases **reales**
(no inventados).

Output: REQ + stories + test plan (mismas ubicaciones que modo Normal).

Gate: usuario aprueba todo antes de R2.

### R2 — Combined Review

Agent: [[code-reviewer]]. Una sola invocación revisa stories Y código juntos
(el código ya existe, review de stories separado no aporta valor adicional).

Output: review report único cubriendo fidelidad de stories + calidad de código.

Gate: BLOCKER e IMPORTANT resueltos.

### R3 — Test Validation

```bash
cd sie_v2 && ruff check . && make test
```

Si faltan tests, [[test-engineer]] los escribe.

### R4 — Final Audit

Igual que Phase 7 Normal. El [[final-auditor]] produce el RETRO con especial
atención al motivo por el que se saltó el workflow (para prevenir repetición).

### Template Workflow Status (Retroactive)

```markdown
## Workflow Status (Retroactive)
- [ ] R1: PO + Stories + Test Plan
- [ ] R2: Combined Review
- [ ] R3: Test Validation
- [ ] R4: Final Audit
```

### Ahorro estimado

Retroactive usa 2–3 agentes vs 5–6 de Normal → −40–60% de tokens. Las
economías vienen de:
- Sin story-refiner separado (merged en PO)
- Sin pass de REVIEW_STORIES separado (merged en REVIEW_IMPLEMENTATION)
- Phase 4 totalmente saltada (ya implementado)
- Phase 6 reducida a validación, no escritura
