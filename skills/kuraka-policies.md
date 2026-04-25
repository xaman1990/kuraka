---
name: kuraka-policies
description: "Políticas transversales del Kuraka: retry, timeout, presupuesto de tokens, failure fallback, checkpointing y telemetry. Se aplica en cualquier modo."
---

# Kuraka — Policies

Políticas transversales que se aplican en cualquier modo del Kuraka
(Normal, Reducido por riesgo, Lite, Retroactive).

---

## Agent Invocation Policy

Cada llamada a `Agent` tiene políticas de retry y timeout para prevenir que
fallos silenciosos se propaguen por el workflow.

### Retry policy

- **Máximo 2 reintentos por agente** (3 intentos totales)
- **Retry triggers**:
  - Output malformado (falla el schema de [[verify-output]])
  - Agente devolvió marker `VALIDATION_FAILED`
  - Error transitorio de tool (red, rate limit)
- **NO retry en**:
  - Error que requiere input del usuario (pregunta al usuario)
  - Rechazo deliberado del agente (ej: "no puedo continuar sin X")
  - 3er fallo — escalar al usuario

### Retry protocol

En cada reintento, el orquestador inyecta feedback en el próximo prompt:

```
PREVIOUS ATTEMPT FAILED VALIDATION
Issues found:
- {specific issue 1}
- {specific issue 2}

Please re-generate addressing these issues.
```

### Timeout policy

- **Máximo 10 minutos por invocación** (`duration_ms > 600_000`)
- **Timeout escala al usuario**: "El agente {agent} lleva 10+ min. ¿Continuar, abortar o cambiar estrategia?"
- **Tareas largas legítimas**: raras. Si esperas superar 10 min, parte la tarea en unidades menores.

### Failure fallback (3 intentos fallidos)

1. Escribe checkpoint con `status: "paused"` y detalles del fallo
2. Reporta al usuario:
   - Qué agente falló
   - Qué produjeron los 3 intentos
   - Próximos pasos sugeridos (retry manual, skip, humano)
3. **ESPERA decisión del usuario** — no auto-skipeas fases críticas

### Tool use limits por agente

Para prevenir loops descontrolados:

| Categoría | Max tool uses |
|---|---|
| Research (po-analyst, explore) | 30 |
| Implementation (backend-developer, frontend-developer) | 50 |
| Review (architect-reviewer, code-reviewer, security-reviewer) | 40 |
| Audit (final-auditor, pattern-detector) | 25 |

Si un agente excede su límite sin producir output → tratar como timeout.

---

## Token Budget (recomendado)

Presupuesto nominal por fase para detectar desviaciones:

| Fase | Target | Investigar si excede |
|---|---:|---|
| 1 PO Analysis | 80–120K | 200K |
| 2 Story Refinement | 60–100K | 180K |
| 2.5 Test Planning | 60–100K | 150K |
| 3 Architect Review | 50–80K | 150K |
| 4a Backend Impl (por story M) | 100–200K | 400K |
| 4b Frontend Impl (por story M) | 100–200K | 400K |
| 5 Code Review | 70–120K | 200K |
| 5.5 Security Review | 60–100K | 180K |
| 6 Tests (por story M) | 80–150K | 300K |
| 6.5 E2E | 50–100K | 200K |
| 6.7 Deployment | 30–60K | 120K |
| 7 Final Audit | 40–80K | 150K |

**Acción si una fase excede el "investigar si excede"**:
1. Abortar la fase si aún está corriendo
2. Analizar telemetría (¿qué ficheros leyó? ¿cuántos tool_uses?)
3. Aplicar patrones T1–T5 de `rules/17-kuraka-token-optimizations.md`
4. Re-lanzar con prompt optimizado

---

## Checkpointing (OBLIGATORIO)

Después de CADA gate aprobado por el usuario, escribe el estado del workflow a:

`sie_v2/docs/process/checkpoints/{REQ-name}-state.json`

### Estructura

```json
{
  "req_name": "REQ-YYYY-MM-DD-slug",
  "mode": "normal | reduced | lite | retroactive",
  "status": "in_progress | paused | completed | abandoned",
  "current_phase": "4a",
  "phases_completed": ["1", "2", "2.5", "3"],
  "phases_pending": ["4b", "5", "5.5", "6", "7"],
  "started_at": "ISO 8601",
  "last_updated": "ISO 8601",
  "artifacts": {
    "req_path": "docs/process/REQ-...",
    "story_paths": ["docs/process/stories/..."],
    "test_plan_path": "docs/process/test-plans/...",
    "frozen_schema_path": "docs/process/schemas/..." ,
    "review_reports": {
      "phase_3": null,
      "phase_5": null,
      "phase_5_5": null
    }
  },
  "phase_4a_progress": { "total_stories": 0, "stories_done": [], "current": null },
  "phase_4b_progress": { "total_stories": 0, "stories_done": [], "current": null },
  "telemetry_path": "docs/process/agent-telemetry/..."
}
```

### Cuándo escribir

- Tras aprobación de Phase 1 → crear checkpoint inicial
- Tras CADA gate → actualizar `phases_completed`, `current_phase`, `last_updated`
- Cuando el usuario pausa sesión → `status: "paused"`
- Cuando Phase 7 completa → rename a `{REQ-name}-state.final.json`, `status: "completed"`

### Resume protocol

Si se reanuda una sesión (chat nuevo, crash recovery):

1. Leer `{REQ-name}-state.json` más reciente
2. Confirmar con usuario: "Reanudando {REQ-name} desde fase {current_phase}. ¿Continuar?"
3. Re-cargar artifacts vía paths en `artifacts.*`
4. Continuar desde `phases_pending[0]`

**Nunca saltar fases al reanudar** — si una fase dice "completed" pero el
artifact no existe, tratar el checkpoint como corrupto y preguntar al usuario.

---

## Token Telemetry (OBLIGATORIO)

Cada invocación de `Agent` devuelve un bloque `<usage>` con `total_tokens`,
`tool_uses` y `duration_ms`. DEBES apendearlo a un JSON de telemetría para
que el [[final-auditor]] (Phase 7) analice consumo por agente.

**Fichero**: `sie_v2/docs/process/agent-telemetry/{REQ-name}-telemetry.json`

### Flow

1. Tras la **primera** llamada a Agent del ciclo, crear el fichero:
   ```json
   {
     "req_name": "REQ-YYYY-MM-DD-slug",
     "mode": "normal | reduced | lite | retroactive",
     "runs": []
   }
   ```
2. Tras **cada** llamada a Agent, añadir una entrada:
   ```json
   {
     "phase": "<int | string>",
     "agent": "<agent-name>",
     "mode": "<optional identifier>",
     "total_tokens": 0,
     "tool_uses": 0,
     "duration_ms": 0,
     "produced": "<short description>",
     "budget_ok": true
   }
   ```
3. Si un agente se invoca varias veces en la misma fase, cada invocación es
   su propia entrada — usa `mode` para desambiguar.
4. Si **no** usas `Agent` para una fase (trabajo directo del orquestador),
   omite la entrada — solo se trackean invocaciones reales.
5. Marca `budget_ok: false` si la fase superó su "investigar si excede".

El [[final-auditor]] lee este JSON en Phase 7 y produce el ranking de tokens en
la retrospectiva. Falta de telemetría degrada el retro pero no lo bloquea.

---

## Model Routing (Path C)

Cada agente tiene un modelo asignado en su frontmatter según coste/juicio:

| Modelo | Agentes | Por qué |
|---|---|---|
| **opus** | [[po-analyst]], [[architect-reviewer]], [[security-reviewer]], [[final-auditor]] | Razonamiento complejo, múltiples fuentes, juicio estratégico |
| **sonnet** | [[story-refiner]], [[backend-developer]], [[frontend-developer]], [[code-reviewer]], [[test-engineer]] | Implementación y review balanceados |
| **haiku** | [[deployment-verifier]], [[pattern-detector]], [[migration-reviewer]], [[e2e-tester]] | Checks mecánicos, pattern matching, smoke tests — 5× más barato que sonnet |

Cambiar un modelo: editar `model:` en el frontmatter del agente correspondiente
y reiniciar Claude Code para que re-registre el subagente.

---

## Tooling del sistema Kuraka

Scripts del vault (`~/Documents/Agentes/AgentesTrabajos/kuraka/`)
que puedes llamar desde cualquier rama/repo:

### `mount-kuraka.sh`

Monta el sistema Kuraka personal en el repo actual (rsync desde vault,
actualiza `.gitignore`).

```bash
bash ~/Documents/Agentes/AgentesTrabajos/kuraka/mount-kuraka.sh
# o con alias en ~/.zshrc:
alias mount-kuraka='bash ~/Documents/Agentes/AgentesTrabajos/kuraka/mount-kuraka.sh'
```

### `validate-kuraka.sh`

Valida frontmatter de agentes/skills y detecta referencias huérfanas. Corre
antes de cada sesión nueva para confirmar que todo está consistente.

```bash
bash ~/Documents/Agentes/AgentesTrabajos/kuraka/validate-kuraka.sh
```

### `kuraka-inspect.py`

Detector de stack para onboarding Brownfield. Escanea un repo y produce un
JSON con backend/frontend/DB/testing/CI/containers detectados.

```bash
python3 ~/Documents/Agentes/AgentesTrabajos/kuraka/kuraka-inspect.py [dir]
# JSON a stdout, resumen humano a stderr
# Redirige a fichero si quieres persistir:
python3 ~/.../kuraka-inspect.py > inspect-report.json
```

El agente [[amauta]] lee este JSON como input principal en el modo Brownfield.

### `aggregate-telemetry.py`

Lee todos los JSON de `docs/process/agent-telemetry/` y emite un dashboard
Markdown agregado (per-cycle, per-agent, tokens/uso, flags over-budget).

```bash
python3 ~/Documents/Agentes/AgentesTrabajos/kuraka/aggregate-telemetry.py
# produce: docs/process/agent-telemetry/DASHBOARD.md
```

El [[final-auditor]] (Phase 7) DEBE correrlo antes de escribir el RETRO para
tener datos agregados, no solo los del ciclo actual.

### `tests/kuraka/`

Suite de tests estructurales del sistema. Corre tras cualquier cambio en
`.claude/agents/` o `.claude/skills/`:

```bash
cd sie_v2 && python3 -m pytest tests/kuraka/ -v
```

Valida: frontmatter, model routing, kuraka split, output-schemas cobertura,
sin referencias huérfanas a [[workflow]].

---

## Optimizaciones aplicables en cualquier modo

Ver `rules/17-kuraka-token-optimizations.md` para los patrones T1–T5:

- **T1 Context digest** — el orquestador lee ficheros de referencia una vez y los inyecta como snippets en los prompts
- **T2 End-only verification** — para restyles/mecánicos, typecheck/lint solo al final
- **T3 Phase collapse** — combinar Phase 1+2 en un solo subagente para riesgo bajo
- **T4 Mapping-table stories** — AC compactas tipo tabla para patrones de sustitución
- **T5 No auto-verify** — el orquestador verifica, el agente no

Aplicación estimada: −35% sobre baseline de un ciclo UI-only; hasta −60% si
además se aplican mejoras de infraestructura (model routing, agent registration).
