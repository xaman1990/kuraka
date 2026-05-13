---
name: gap-analysis
description: "Produce a pre-REQ gap analysis document that bridges a source codebase (current state) and a target architecture (desired state). Use this skill WHENEVER the user mentions migration, refactor, port, rewrite, modernization, or version upgrade between two explicit codebases — including phrases like 'migrar X de v1 a v2', 'analizar provider existente para refactor', 'comparar módulo A contra módulo B', 'gap analysis', 'feasibility study', 'pre-REQ research'. Output is a structured document with Parts A (origin analysis), B (target patterns), C (bridge mapping), D (next-phase recommendations) that feeds into Kuraka Phase 1. Invokable by po-analyst, amauta, or architect-reviewer. Always prefer this skill over writing a formal REQ when the input is a migration/refactor ticket — the formal REQ comes AFTER the gap analysis."
---

# Gap Analysis — Pre-REQ Bridge Document

> Skill para producir el **documento-puente** entre "lo que existe" y "lo que debe existir" ANTES de escribir un REQ formal. No reemplaza al REQ; lo alimenta.

Kuraka encaja un formal REQ (Phase 1) con stories implementables. Pero cuando la entrada es una **migración/refactor entre dos bases de código**, el PO necesita primero entender qué hay hoy, qué patrones existen en destino, y cómo unirlos. Ese entendimiento es el gap analysis.

---

## 1. Cuándo usar este skill

Usa este skill si **cualquiera** de estas condiciones se cumple:

- El ticket/usuario menciona "migración", "migration", "port", "rewrite", "refactor", "modernización", "upgrade" con dos codebases explícitos
- Hay versiones distintas del mismo sistema como origen y destino (v1 → v2, legacy → modern, JS → Python, etc.)
- Se pide analizar código existente como **input para un REQ futuro**, no como REQ directo
- Eres `po-analyst` / `amauta` / `architect-reviewer` y el ticket que recibes es una migración — aplica este skill antes del REQ formal

**NO uses este skill cuando:**

- Es un feature greenfield sin origen existente → usa `analyze-requirement`
- Es onboarding de proyecto completo sin Kuraka → usa `amauta` con su flujo brownfield
- Ya existe el análisis y toca producir el REQ formal → usa `analyze-requirement` tomando el GAP doc como input

---

## 2. Inputs requeridos

Antes de leer código, confirma con el usuario (o extrae del contexto) los 4 inputs siguientes. Si alguno falta o es ambiguo, **pregunta antes de proceder**:

| Input | Qué es | Ejemplo |
|---|---|---|
| **Source context** | Path(s) absoluto(s) + docs disponibles del origen | `sie_integraciones/backend/src/providers/lineadirecta/` |
| **Target context** | Path(s) absoluto(s) + ≥2 implementaciones de referencia en destino | `sie_v2/backend/api/services/providers/` + `generali/` + `asitur/` |
| **Ticket reference** (opcional) | Jira key o referencia para trazabilidad | DD-896 |
| **Scope boundary** | Qué está dentro y fuera del scope (outbound, data migration, UX, auth, etc.) | "Sólo inbound; outbound queda fuera" |

No asumas. Preguntar 30s ahora evita un documento de 500 líneas desalineado.

---

## 3. Output: ubicación y formato

Crea el documento en:

```
{project_root}/docs/process/GAP-{YYYYMMDD}-{ticket-or-slug}.md
```

Prefijo **`GAP-`** (no `REQ-`) — señala que es pre-REQ. El REQ formal derivado tendrá su propio fichero `REQ-` en Phase 1 de Kuraka.

### Plantilla obligatoria (Partes A / B / C / D)

```markdown
# Gap Analysis — {Ticket} {Title}

## 0. Metadata
- Ticket: {key + link}
- Fecha: {YYYY-MM-DD}
- Origen: {path + 1-line description}
- Destino: {path + 1-line description}
- Scope: {in / out}
- Este documento NO es el REQ formal. Alimenta Phase 1 Kuraka (analyze-requirement).

## Parte A — Análisis del origen (estado actual)

### A.1 Inventario de archivos
Tabla: archivo | LOC | propósito 1-línea

### A.2 Tipo de integración / arquitectura
Protocolo(s), librerías, autenticación, endpoints externos, dependencias internas.

### A.3 Flujos principales
Para cada flujo relevante (inbound/outbound/sync):
- Trigger
- Tipos de evento/mensaje soportados
- Parseo/transformación (citar archivo:línea, marcar fragilidades)
- Efectos laterales (BD, emails, llamadas externas)

### A.4 Hardcodeos detectados
Tabla completa: archivo:línea | valor | categoría | observaciones

### A.5 Problemas evidentes
Checklist con archivo:línea concretos:
- Contract codes hardcodeados
- Parseo frágil
- Sin transacciones / consistencia débil
- Error handling silencioso
- Sin logging estructurado
- Sin tipado
- Imports dentro de funciones
- Sin tests

### A.6 Dependencias
Internas (módulos del mismo repo) + externas (librerías, APIs).

### A.7 Complejidad y tamaño
LOC total + por archivo, funciones largas, archivos que superan límites.

## Parte B — Arquitectura destino (patrones disponibles)

### B.1 Clases base / primitivas
Para cada una: archivo, contrato (métodos clave), cuándo extenderla.

### B.2 Componentes compartidos
Factories, registries, servicios de reglas, utilidades transversales.

### B.3 Implementaciones de referencia (≥2)
Analiza ≥2 módulos ya implementados en destino:
- Estructura de archivos
- Cómo extienden las base classes
- Patrones que replican (ejemplos con archivo:línea)
- Schemas / tipos usados

### B.4 Discrepancias ticket vs realidad
Si el ticket menciona referencias que no existen (ej: un módulo que ya fue renombrado o nunca se creó), documéntalo aquí como GAP bloqueante.

### B.5 Pre-conclusión de base class aplicable
Dado el tipo de integración del origen (A.2), ¿qué base class del destino aplica? (justificado)

## Parte C — Puente origen → destino

### C.1 Mapeo hardcodeo → destino
Para cada valor de A.4, indica dónde debe vivir en destino (BD / config / enum / eliminado).

### C.2 Flujos origen → clases destino
Tabla: flujo origen | clase destino equivalente | cambios necesarios

### C.3 Estructura propuesta
Árbol de archivos propuesto en destino, con justificación por archivo.

### C.4 Riesgos identificados (≥5)
Tabla: riesgo | impacto (H/M/L) | mitigación

### C.5 Dependencias aguas arriba
Qué debe existir antes de poder empezar la implementación (migraciones BD, seeds, configuración, decisiones de negocio).

### C.6 Preguntas abiertas para el equipo
Lista numerada de ambigüedades que requieren decisión humana. Bloqueantes al frente.

## Parte D — Recomendaciones para próximos pasos

### D.1 Fase inmediata siguiente
Acciones concretas (BD, schema, seeds, rotaciones de credenciales, etc.) para poder avanzar al REQ formal.

### D.2 Contenido esperado del REQ formal
Qué secciones debe tener el REQ cuando se escriba, específicas a este caso.

### D.3 Advertencias para la implementación
Puntos sensibles (secrets, data migration, retrocompatibilidad) que deben aparecer en la story/implementation.
```

---

## 4. Proceso recomendado (orden)

1. **Context digest** (Rule T1 de `rules/17-kuraka-token-optimizations.md`): lista ficheros y `wc -l` en ambos codebases antes de leer contenido. Embebe el digest al inicio del prompt si vas a invocar subagentes.

2. **Skim amplio**: lee estructura (árboles, `__init__.py`, `index.js`, nombres de funciones) antes que detalles.

3. **Parte A primero, luego B**: no mezcles. Completar A entera antes de entrar a B reduce re-lecturas.

4. **Parte C al final de A+B**: el mapping depende de ambos.

5. **Parte D deriva de C**: no la improvises — cada recomendación debe trazar a una línea de C.

6. **Validación externa** (Rule T5): no ejecutes verificaciones repetidas dentro del skill. El orquestador valida al terminar.

---

## 5. Reglas de redacción

- **Cada aserción cita `archivo:línea`** — si no puedes citar, no es aserción, es hipótesis (márcala como tal).
- **No modifiques ningún archivo fuente** — solo creas el documento en `docs/process/`.
- **No inventes convenciones** — si no las ves en el código real, márcalas como TODO.
- **LOC con `wc -l`**, no a ojo.
- **Contradicciones ticket vs código real** → documéntalas explícitamente en B.4, no las silencies.
- **Idioma**: documento en español (si la organización lo permite en docs); código e identificadores siempre en inglés.

---

## 6. Criterios de completitud

El GAP doc está listo para pasarse a Phase 1 Kuraka cuando:

- Partes A, B, C, D completas (no placeholders)
- A.4 lista **≥10 hardcodeos** concretos con archivo:línea
- B.3 analiza **≥2 implementaciones** de referencia
- C.1 tiene mapping completo para cada hardcodeo
- C.4 lista **≥5 riesgos** identificados
- C.6 enumera las preguntas abiertas, con las bloqueantes separadas visualmente

---

## 7. Composición con agentes Kuraka

| Agente que invoca | Cuándo |
|---|---|
| `po-analyst` | Input es un ticket de migración/refactor; antes de `analyze-requirement` |
| `amauta` | Adaptando un provider/módulo legacy que no pasó por Kuraka |
| `architect-reviewer` | Congelando schema de destino y necesita gap doc para validar diseño |

**Output feed:**

- Feed principal: `analyze-requirement` usa GAP doc como fuente para escribir `REQ-...md`
- Feed secundario: `schema-freeze` consulta C.1 y C.5 para decidir schema destino

**No reemplaza a:**

- `analyze-requirement` (producir REQ con stories) — GAP doc es su input
- `refine-stories` (producir AC verificables) — viene después
- `schema-freeze` (congelar schema BD) — viene después

---

## 8. Ejemplo de output existente

Referencia trabajada sobre DD-896 Linea Directa:

```
sie_v2/docs/process/REQ-20260423-DD-897-898-analisis-migracion-linea-directa.md
```

(Nota: ese fichero precede a la adopción de este skill y usa prefijo `REQ-`. A partir de ahora, usar prefijo `GAP-`.)

---

## 9. Duplication-Aware Refactor Proposals (regla 18)

Al comparar el origen con las implementaciones de referencia del destino
(Parte B), aplica la regla `sie_v2/.claude/rules/18-duplication-aware-refactor.md`:

- Si una función/método que el origen necesita ya existe idéntico (o casi
  idéntico) en ≥2 implementaciones de referencia del destino → propón su
  extracción a `utils/`, base class o módulo compartido según el tipo.
- Formato del finding: ver regla 18 sección 3.
- Incluye estos findings en **Parte D "Recomendaciones"** del documento,
  bajo un subapartado propio "D.4 Refactors propuestos (regla 18)".
- **NO** ejecutes el refactor en este documento — solo propón.

Razón: la migración siempre expone la duplicación cross-provider mejor
que ningún otro momento. Esta es la ocasión natural para detectarla.

---

## 10. Checklist final antes de entregar

- [ ] Todos los inputs confirmados con el usuario antes de empezar
- [ ] Documento en `docs/process/GAP-{YYYYMMDD}-{slug}.md`
- [ ] Partes A/B/C/D completas con contenido real
- [ ] ≥10 hardcodeos, ≥2 referencias, ≥5 riesgos
- [ ] Preguntas abiertas listadas en C.6 con las bloqueantes marcadas
- [ ] Recomendaciones por fase siguiente en D.1/D.2/D.3
- [ ] Refactors propuestos (regla 18) en D.4 si detectaste duplicación
- [ ] Ningún archivo fuente modificado
- [ ] Discrepancias ticket vs realidad documentadas
