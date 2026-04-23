# Lessons Learned — Kuraka Workflow

Lecciones destiladas de retrospectivas pasadas. Referenciadas por los prompts
de agentes mediante ID corto (`[LL-NNN]`) en lugar de tener el ejemplo completo
inline (ahorra tokens en cada invocación).

> Cómo añadir una lección: cada entrada tiene ID único, REQ de origen, el
> síntoma, la causa raíz y la regla que evita la repetición. Los prompts de
> agentes citan el ID (`see LL-003`) sin duplicar el cuerpo.

---

## LL-001 — Symbol removal must grep the full repo

- **REQ origen**: REQ-2026-04-13 (guai-specialties / retiro de `MASTER_SPECIALTIES`)
- **Síntoma**: El REQ acotó "one file change". En implementación tocó 3 archivos
  (`default_prompts.py`, `analyzer.py`, `generator.py`) + 1 frontend, y requirió
  propagar un nuevo parámetro por 2 funciones de parseo.
- **Causa raíz**: Al eliminar/renombrar un símbolo, el PO no grepea el repo
  completo para enumerar todos los call sites.
- **Regla que aplica**: `po-analyst` ejecuta `grep -rn "SYMBOL" sie_v2/` en la
  fase 1 cuando el REQ contiene "eliminar", "remover", "renombrar" o
  equivalentes en inglés. Lista cada archivo y número de línea en
  "Affected Services & Repositories". El `architect-reviewer` re-verifica la
  lista antes del schema freeze.

## LL-002 — Cache invalidation must cover every subkey in the namespace

- **REQ origen**: No citado por nombre; bug sobre Redis key `CAPABILITIES`.
- **Síntoma**: Código invalidaba `CAPABILITIES` pero dejaba sobrevivir
  `CAPABILITIES:last_sync`. El test usaba
  `cache.invalidate.assert_called_once()` en lugar de verificar todos los
  targets esperados. El bug pasó Phase 4, se detectó en Phase 5 porque el
  reviewer grepeó el nombre de la constante.
- **Causa raíz**: El desarrollador asumió que invalidar la key principal basta;
  el test mock solo verificaba una llamada, no la completitud del set.
- **Regla que aplica**: `code-reviewer` verifica en Phase 5 cuando hay escritura
  a Redis:
  - Si el código invalida `KEY`, grepear `grep -rn "KEY" sie_v2/backend/` y
    exigir que TODAS las subkeys del mismo namespace (`f"{KEY}:last_sync"`,
    `f"{KEY}:meta"`, `f"{KEY}:{id}"`, etc.) se invaliden juntas
  - Preferir `cache.invalidate_pattern(f"{KEY}*")` si hay múltiples subkeys

## LL-003 — Orchestrator must not bypass the Kuraka for "small" changes

- **REQ origen**: REQ-2026-04-17 y REQ-20260420
- **Síntoma**: En ambos REQs el orchestrator editó directamente código fuente
  sin enrutar por `backend-developer` / `frontend-developer`. Produjo type
  errors y telemetría rota.
- **Causa raíz**: El orchestrator racionalizó "el cambio es trivial, hacerlo
  directo ahorra tokens" sin considerar que el bypass rompe AC verification y
  telemetry integrity.
- **Regla que aplica**: `kuraka.md` sección "Orchestrator constraint". El
  orchestrator NUNCA edita código fuente antes de Phase 4. Si aun así lo hace:
  revertir, anunciar la violación, enrutar por el agente correcto, loggear con
  `"agent": "orchestrator-direct"` en telemetry.

## LL-004 — Test plan must respect story's Out of Scope section

- **REQ origen**: REQ-20260420-clean-specialty-names
- **Síntoma**: El `test-engineer` incluyó tests Vitest de componentes
  silenciosamente, pese a que la story marcaba esos tests como out-of-scope.
  La contradicción se detectó en Phase 3 y requirió rework.
- **Causa raíz**: El agente no leyó la sección "Out of Scope" antes de generar
  test cases.
- **Regla que aplica**: `test-engineer` en modo TEST_PLANNING lee primero la
  sección "Out of Scope" de cada story, lista exclusiones como "Excluded
  Categories" en el test plan, y NO incluye test cases para lo excluido. Si el
  agente cree que una exclusión es incorrecta, crea un finding "Test Plan vs
  Story Scope Conflict" y espera resolución antes de incluir.

## LL-005 — Import path hints in stories must be verified against an existing test

- **REQ origen**: (implícito en story-refiner.md)
- **Síntoma**: Stories con import paths aproximados obligan al developer a
  inventar el path correcto y luego fallan los tests.
- **Regla que aplica**: `story-refiner` al escribir "Notes for Implementer"
  con rutas de import ejecuta:
  `grep -r "^from api\." sie_v2/backend/tests/unit/ | head -3`
  y usa el patrón confirmado. No documenta ambigüedad; resuelve en tiempo de
  escritura.

## LL-006 — TypeScript interface changes must specify exact syntax

- **REQ origen**: (genérico — varias stories de frontend)
- **Síntoma**: AC diciendo "add optional string field `nombre`" → ambiguo entre
  `nombre?: string` (propiedad opcional) y `nombre: string | null` (union).
  Semántica distinta, runtime distinto.
- **Regla que aplica**: `architect-reviewer` flaggea como MINOR cualquier AC
  que describa tipos TypeScript con lenguaje informal. La AC debe especificar
  el operador exacto (`?` vs `: T | null`).

---

## Formato para nuevas lecciones

Cuando el `final-auditor` produce un retro con una lección nueva, añade una
sección a este archivo con este formato:

```markdown
## LL-00X — Título corto (imperativo o descriptivo)

- **REQ origen**: REQ-YYYY-MM-DD-slug
- **Síntoma**: Qué pasó en producción o en review
- **Causa raíz**: Por qué pasó (proceso, no personas)
- **Regla que aplica**: Qué agente + qué checklist cambia para prevenirlo
```

Los prompts de agentes citan `[LL-00X]` en vez de copiar el cuerpo. Esto
mantiene los prompts delgados y permite actualizar las lecciones en un solo
sitio.
