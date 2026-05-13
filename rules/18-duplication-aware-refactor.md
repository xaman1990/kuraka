---
description: When analyzing, designing or reviewing, detect duplicated/near-duplicated logic across providers or modules and PROPOSE (don't execute) its extraction to a shared location. Preventive DRY at the architecture level — catch duplication before it spreads, but without triggering premature abstraction.
alwaysApply: false
appliedBy:
  - po-analyst
  - architect-reviewer
  - code-reviewer
  - gap-analysis
---

# Duplication-Aware Refactor Proposals

Cuando al analizar, diseñar o revisar código detectes una función/método que
ya existe en OTRO provider/módulo y podría reutilizarse (idéntica o con
adaptación mínima), **propón su extracción** — NO la ejecutes en el mismo ticket.

Esta regla es **preventiva**: detecta duplicación antes de que se acople a N
providers, pero con guardas contra el DRY prematuro (YAGNI).

---

## 1. Dónde proponer que vaya (por tipo de lógica)

| Tipo de lógica | Destino propuesto |
|---|---|
| Utilidad pura sin contexto de provider (dates, phones, strings, parsing genérico) | `utils/` (ej: `utils/date_utils.py`) |
| Provider-related pero genérico (touches contracts, credentials, auth flows, token lifecycle) | Base class (`base_api.py`, `base_email.py`, `base_outbound.py`, `base_processor.py`) — solo si la firma encaja en el template method existente |
| No encaja en base class pero ≥2 providers la necesitan | Nuevo módulo hermano en `api/services/providers/` (patrón `rule_resolver.py`, `case_builder.py`) |

**Regla de oro**: elige el destino **más específico** que cumpla el caso.
No subas a `utils/` lo que es claramente lógica de provider; no bajes a
base class lo que es utilidad pura.

---

## 2. Umbral (cuándo proponer, cuándo callar)

### Propón SI:
- **2+ consumidores actuales** que necesitan la misma lógica idéntica o ~idéntica, O
- **1 consumidor actual + 1 en pipeline conocido** (ej: migración de un provider nuevo a punto de añadir el segundo consumidor)

### NO propongas SI:
- **Único consumidor** sin plan de más (YAGNI — premature abstraction cuesta más que duplicación)
- **<10 LOC trivialmente reescribible** (coste del refactor > beneficio)
- **Signos de divergencia**: la lógica depende de reglas de negocio que evolucionan independientemente por provider (extracción crea acoplamiento dañino)
- El método es **específico del dominio de un provider** aunque su shape parezca genérico (ej: parseo con labels propios de una aseguradora)

---

## 3. Cómo proponer (formato estándar)

En el documento o review correspondiente, incluye un bloque con estos campos:

```markdown
**Refactor propuesto**: {nombre de la función/clase}

- **Ubicación actual**: `{archivo:línea}` en {provider A}
- **Ubicación propuesta**: {utils/ | base_X.py | nuevo módulo `providers/{name}.py`}
- **Firma sugerida**: `def nombre_funcion(...) -> ...:`
- **Consumidores**: provider A (actual) + provider B (este ticket) + [otros previstos]
- **Complejidad extracción**: S (<1h) / M (1-4h) / L (>4h)
- **Riesgo divergencia**: bajo / medio / alto
- **Acción**: crear subtask Jira (NO incluir en este ticket)
```

---

## 4. Principio fundamental: propón, NO refactorices

La extracción real **nunca** se hace en el ticket que la descubre. Va a
subtask propia por 3 razones:

1. **Coordinación de consumidores**: todos los providers afectados deben
   actualizarse a la vez para no dejar copias divergentes.
2. **Tests de paridad antes/después**: necesitas tests que demuestren que
   el refactor no cambia comportamiento (especialmente crítico cross-provider).
3. **Respeto al orchestrator Kuraka**: el REQ en curso tiene un scope
   aprobado. Expandir scope mid-ticket viola el gate del usuario.

**Excepción**: si eres el `backend-developer` implementando desde cero una
función que vas a necesitar EN ESTE MISMO TICKET para 2+ providers nuevos,
puedes colocarla directamente en el destino compartido — sin pasar por
subtask. Esto NO es un refactor (no hay código previo), es decisión de
ubicación inicial.

---

## 5. Quién aplica esta regla y cuándo

| Agente / Skill | Fase | Output del finding |
|---|---|---|
| `po-analyst` | Phase 1 (PO Analysis) | Bloque en sección "Dependencies" del REQ |
| `architect-reviewer` | Phase 3 (Architect Review) | Finding severidad SUGGESTION en el review |
| `code-reviewer` | Phase 5 (Code Review) | Finding severidad MAINTAINABILITY (6D framework) |
| Skill `gap-analysis` | Pre-REQ research | Bloque en Parte D "Recomendaciones" |

El `backend-developer` y `frontend-developer` **no aplican esta regla**
durante Phase 4 — su trabajo es implementar la story tal como está
definida, no expandir scope. Si detectan duplicación obvia durante
implementación, lo reportan como nota al final del commit para que el
`code-reviewer` lo convierta en finding.

---

## 6. Ejemplo real (referencia histórica)

Durante el análisis de DD-896 (Linea Directa v1 → v2), el anexo de
patrones Q2 observó que `set_active_contract()` + `_authenticate()` +
`_store_token()` están casi idénticos en asitur (`provider.py:64-130`) y
generali (`provider.py:58-116`).

**Con esta regla activa**, el `po-analyst` de LD habría producido:

> **Refactor propuesto**: `_authenticate()` + token lifecycle (`_store_token()`, `set_active_contract()`)
> - **Ubicación actual**: `asitur/provider.py:64-130` + `generali/provider.py:58-116`
> - **Ubicación propuesta**: `base_api.py` como template method con hooks virtuales para la llamada HTTP específica
> - **Firma sugerida**: `async def authenticate(self) -> None` en `BaseAPIProvider`, override de `_build_auth_request(self, contract) -> dict`
> - **Consumidores**: asitur (actual), generali (actual), linea_directa (este ticket = 3er consumidor)
> - **Complejidad**: M (1-4h)
> - **Riesgo divergencia**: bajo (los 3 providers usan OAuth2 password grant o equivalente)
> - **Acción**: crear subtask DD-XXX — no incluir en DD-901

El resultado: DD-896 implementa LD con copy-paste temporal (pero
consciente y documentado), y una subtask aparte sube el patrón a base
class con tests de paridad para los 3 providers.

---

## 7. Anti-patrones a evitar

- ❌ **Extraer "por si acaso"**: si solo hay 1 consumidor real, NO propongas.
- ❌ **Forzar encaje en base class**: si la firma no cuadra limpiamente con el
  template method, propón módulo hermano — no contamines la base class.
- ❌ **Refactor y scope creep en el mismo ticket**: si descubres duplicación
  durante la implementación, abre subtask y sigue con el scope aprobado.
- ❌ **Extraer sin tests de paridad**: la subtask de refactor DEBE incluir
  tests antes/después que prueben equivalencia comportamental.
