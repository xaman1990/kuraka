# 02 — Plan de migración: de "workflow de sie_v2" a "framework adaptable"

> Documento de planificación. **No ejecutar todavía**. Revisar fase por fase con
> el usuario antes de tocar código. El objetivo es romper la dependencia
> estructural con el proyecto sie_v2 y dejar Kuraka utilizable en cualquier
> stack/proyecto, sin perder los aciertos del diseño actual.

---

## Contexto

Diagnóstico ya consensuado (ver conversación previa):

- Hoy Kuraka **dice** ser portable pero está acoplado a sie_v2 en 50+ puntos
  (paths `sie_v2/`, comandos `ruff`/`make`/`npm`, stack FastAPI+Vue+Pydantic,
  arquitectura "4-layer Endpoint→Service→Repository→DB", `tenant_id` asumido,
  referencias a incidentes LL-001/LL-002 propios del proyecto).
- El flujo "Normal" de 8 fases es razonable como modo **Compliance** opt-in,
  pero no como default para "cualquier programador".
- La estrategia de docs vía gitignore + sync bidireccional con Obsidian es
  frágil y bloquea el uso en equipo.

Decisión adoptada: **opción 2** — framework que se adapta al proyecto, no
opinionado-sobre-un-stack. Si algo del diseño actual obliga a sie_v2, se
elimina o se vuelve configurable.

---

## Principios de la migración

1. **Backwards-compatible mientras se pueda.** sie_v2 tiene ciclos en vuelo —
   no podemos romperlo de golpe. Cada fase deja el repo en estado funcional.
2. **Una fase = un PR (o un commit cohesivo).** Nada de big-bang.
3. **No tocar código sin antes haber escrito el contrato.** Cuando una fase
   introduce un concepto nuevo (`kuraka.config.yaml`, perfil de stack), el
   contrato/schema se aprueba antes de la implementación.
4. **Eliminar antes de generalizar.** Si una sección de un agente sólo aplica
   a sie_v2 y no se va a generalizar todavía, se elimina y se documenta como
   "feature pendiente", no se deja con un `# TODO`.
5. **Evals desde la fase 1.** Sin medir, no sabemos si los cambios degradan
   calidad. La fase 7 (evals) parece la última pero su esqueleto se monta
   en la fase 1.
6. **Idioma único en cada superficie.** Prompts de agentes en inglés (mejor
   resultado del modelo y mayor audiencia), documentación de usuario en
   español. No mezclar dentro del mismo archivo.

---

## Plan por fases

### Fase 0 — Decisiones a fijar antes de tocar nada

**Objetivo**: cerrar las preguntas de diseño abiertas. Sin esto, las fases
siguientes mueven el blanco.

Decisiones requeridas (responder en este mismo documento o en un anexo):

- [ ] **Nombre del producto público**: ¿Kuraka sigue siendo el nombre? Si va
      a ser un framework abierto, evaluar nombre menos críptico. *Recomendación
      provisoria: mantener "Kuraka" como marca del orquestador, pero la CLI/repo
      público puede llamarse `kuraka-framework` o equivalente.*
- [ ] **Distribución**: ¿clone + alias (status quo), git submodule, paquete
      instalable (npm/pip/brew), o tarball de releases? *Recomendación: clone
      + `kuraka.lock` en el consumidor. Migrar a paquete cuando haya >3
      consumidores reales.*
- [ ] **Versionado**: SemVer con tags `v0.1.0` etc. ¿Qué se considera breaking
      change? *Propuesta: cambios al schema de `kuraka.config.yaml`, eliminación
      de un agente, o cambio de gates obligatorios → MAJOR.*
- [ ] **Política de docs en consumidor**: ¿`docs/process/` tracked por default?
      ¿`docs/process/agent-telemetry/*.json` gitignored pero `DASHBOARD.md`
      tracked? *Recomendación: sí a ambos.*
- [ ] **Idioma**: confirmar inglés para prompts de agentes, español para
      `README.md`, `CLAUDE.md`, los 0X-*.md y `kuraka-modes.md`/`kuraka-policies.md`.
- [ ] **Modo default**: ¿qué pipeline corre cuando un usuario invoca Kuraka
      sin especificar modo? *Propuesta: `Standard` (4 fases nuevo, definido en
      Fase 5), no `Normal` (8 fases).*
- [ ] **¿sie_v2 sigue siendo consumidor del nuevo Kuraka?** Si sí, hay que
      generar el `kuraka.config.yaml` de sie_v2 antes de quitar los hardcodes
      (Fase 3 depende de esto).

**Salida**: una sección "Decisiones cerradas" añadida al final de este
documento, con fecha y versión.

**Riesgo si se salta**: las fases 2-5 producen un framework que no encaja con
las expectativas reales y hay que rehacer.

---

### Fase 1 — Stop the bleeding

**Objetivo**: arreglar lo más frágil sin cambiar comportamiento. Cero impacto
en sie_v2 en curso.

Cambios concretos:

1. **Vault path por env var**.
   - `mount-kuraka.sh:20` — reemplazar `VAULT="/Users/xmn/..."` por
     `VAULT="${KURAKA_VAULT:-$HOME/.kuraka}"`.
   - `scripts/sync-obsidian.sh` — mismo tratamiento.
   - `00-RESTAURAR-PROYECTO.md` — actualizar el one-liner.
   - `dotfiles/zshrc-alias.md` — documentar `export KURAKA_VAULT=...` si el
     usuario quiere mantener el path actual.
   - **Verificación**: `mount-kuraka.sh` corre con y sin `KURAKA_VAULT` seteado.

2. **Default de doc tracking en consumidor: invertido**.
   - `mount-kuraka.sh:119-130` — eliminar de la lista de patrones de
     `.gitignore`:
     - `docs/process/lessons-learned.md`
     - `docs/process/agent-telemetry/`
     - `tests/kuraka/`
   - Mantener gitignored sólo:
     - `.claude/agents/`, `.claude/skills/`, `.claude/commands/`, `.claude/hooks/`
       (mientras no haya versionado del framework — se quitan en Fase 6)
     - `docs/process/agent-telemetry/*.json` (telemetría per-cycle, ruido) —
       añadir patrón nuevo, no el directorio completo
   - **Verificación**: en un proyecto de prueba, tras `mount-kuraka` los REQ y
     retros aparecen como tracked en `git status`; los JSON de telemetría no.

3. **Refactor del sync-obsidian a un solo sentido (project → vault, manual)**.
   - Marcar `scripts/sync-obsidian.sh` como deprecated en su header.
   - El usuario que quiera ver Kuraka en Obsidian usa `ln -s` (documentar en
     `dotfiles/`).
   - **No borrarlo todavía** — eliminar en Fase 4 cuando se complete la
     transición a backticks-only.

4. **Esqueleto de `evals/`** (sólo el directorio + README, sin tests).
   - `evals/README.md` — explica el contrato: cada eval planta una situación
     conocida y verifica un agente.
   - `evals/fixtures/` (vacío todavía).
   - **Verificación**: ninguna; sólo se prepara el terreno.

**Riesgo**: bajo. Todos los cambios son aditivos o reversibles vía git.

**Rollback**: revertir el commit. sie_v2 sigue funcionando porque
`mount-kuraka.sh` mantiene compatibilidad si el env var no está seteado.

---

### Fase 2 — Adapter layer: `kuraka.config.yaml`

**Objetivo**: dar a cada proyecto consumidor un punto único donde declara su
stack y convenciones, para que los agentes lean de ahí en lugar de tenerlo
hardcoded en sus prompts.

Cambios concretos:

1. **Definir el schema** (`kuraka-artifacts/config-schema.yaml` o JSON Schema).
   Campos mínimos:

   ```yaml
   # kuraka.config.yaml — vive en la raíz del proyecto consumidor
   project:
     name: string
     description: string
   stack:
     backend:
       language: python | typescript | go | rust | ruby | java | ...
       framework: fastapi | django | express | gin | rails | spring | ...
       orm: sqlalchemy | prisma | gorm | activerecord | ...
       lint_cmd: string         # e.g. "ruff check ."
       test_cmd: string         # e.g. "make test"
       typecheck_cmd: string?   # opcional
     frontend:
       language: typescript | javascript | ...
       framework: vue | react | svelte | angular | ...
       state_mgmt: pinia | redux | zustand | ...
       lint_cmd: string
       test_cmd: string
       typecheck_cmd: string
     database:
       engine: postgres | mysql | sqlite | mongo | ...
       migration_tool: alembic | prisma | flyway | ...
   architecture:
     layers: [endpoint, service, repository, model]   # nombres y orden
     paths:
       backend_root: backend/
       frontend_root: frontend/
       tests_root: tests/
       migrations_root: backend/alembic/versions/
       docs_process_root: docs/process/
   conventions:
     naming_language: english        # idioma de identificadores
     null_syntax: "T | None"          # vs "Optional[T]"
     multi_tenant: true              # si requiere tenant_id en queries
     max_file_loc: 700
     max_function_loc: 50
   workflow:
     default_mode: standard | compliance | lite
     gates_require_user_approval: true
   ```

2. **Validador del config**:
   - Nuevo: `validate-config.sh` (o subcomando de `validate-kuraka.sh`).
   - Verifica: schema válido, comandos existen, paths existen.
   - **Verificación**: corre contra un `kuraka.config.yaml` de prueba y reporta
     errores claros.

3. **`kuraka-inspect.py` emite draft del config**.
   - El script ya detecta stack. Modificar para que produzca un
     `kuraka.config.yaml` candidato (en stdout o `--output`) con campos
     completados al 80% y marcadores `<TODO>` donde no pudo decidir.
   - **Verificación**: correrlo en sie_v2 produce un config que, completado
     a mano, refleja la realidad actual.

4. **Generar el `kuraka.config.yaml` de sie_v2** (caso de prueba real).
   - Documentar el resultado en `docs/migration-examples/sie_v2-config.yaml`
     dentro de este repo (a modo de ejemplo de referencia).
   - **Esto es prerequisito para Fase 3.**

**Riesgo**: medio. El schema mal diseñado obliga a re-trabajo en Fase 3.
Mitigación: validar el schema generando configs de 2-3 stacks distintos antes
de cerrar (sie_v2, un Next.js fullstack hipotético, un Go+Postgres).

**Rollback**: trivial — el config no se consume todavía. Borrar archivos.

---

### Fase 3 — Decouple agents from sie_v2 (mover, no eliminar)

**Objetivo**: que ningún `agents/*.md` ni `agents/contexts/*.md` mencione
"sie_v2", "Guai", "FastAPI", "Vue", "ruff", "make test" salvo como ejemplo
explícito dentro de un perfil de stack.

**Principio rector**: cada hardcode que sale de un agente **se mueve a algún
sitio concreto y trazable**, nunca se elimina sin destino. El conocimiento
operativo de sie_v2 (lecciones, checks específicos, convenciones de equipo)
no se pierde — se reubica en una capa nueva (Fase 3.5).

Estrategia: **tres artefactos** que componen el contexto de cada agente.

- `agents/{agent}.md` → **genérico**. Rol en el workflow, invariantes,
  output schema. Lee config + stack profile + project specialization.
- `kuraka-artifacts/stack-profiles/{stack}.md` → instrucciones que dependen
  del lenguaje/framework (ej. `python-fastapi.md`, `node-express.md`,
  `go-gin.md`, `vue-pinia.md`, `react-redux.md`). Lo que aplica a "cualquier
  proyecto FastAPI", no sólo a sie_v2.
- `<project>/.claude/project/...` → **project specialization** (Fase 3.5).
  Lo que es opinión de equipo, memoria institucional o regla de dominio
  de un proyecto concreto.

Decisión de routing por hardcode encontrado:

| Si la regla aplica a... | Va a |
|---|---|
| Cualquier proyecto que use ese lenguaje/framework | stack profile |
| Sólo a este proyecto (incidente, dominio, equipo) | project specialization |
| Cualquier proyecto sin importar stack (ej. max LOC) | agente genérico |
| Es declarativa (path, comando, flag) | `kuraka.config.yaml` |

El agente, al arrancar, lee en orden:
1. Su prompt genérico.
2. `kuraka.config.yaml` del proyecto.
3. Los stack profiles que correspondan a `stack.backend.framework` y
   `stack.frontend.framework`.
4. La capa de project specialization (Fase 3.5).

Cambios concretos por agente (los más acoplados primero):

#### 3.1 — `po-analyst.md`

- Línea 8: "Product Owner Analyst for the SIE v2 (Guai Platform) project" →
  "Product Owner Analyst. You analyze requirements for the project described
  in `kuraka.config.yaml`."
- Línea 31: hardcoded `sie_v2/docs/process/REQ-...` → usar
  `${architecture.paths.docs_process_root}/REQ-...`.
- Línea 113: `grep -rn "SYMBOL" sie_v2/` → `grep -rn "SYMBOL" .`
- Líneas 100-107 (Rules): "Files go in `api/`, `repositories/`, NOT
  `modules/`" → mover al stack profile `python-fastapi.md` **y** dejar en
  `<sie_v2>/.claude/project/conventions/06-project-structure.md` los detalles
  específicos de sie_v2 (módulos del dominio).
- Regla 4 (`str | None`) → mover a `conventions.null_syntax` del config.
- Regla 5 (tenant_id) → condicionar a `conventions.multi_tenant` **y**
  documentar el patrón concreto en
  `<sie_v2>/.claude/project/conventions/tenant-isolation.md`.
- Referencia a `[LL-001]` (mandatory grep for symbol removal) → mover el
  archivo de lección a `<sie_v2>/.claude/project/lessons-learned/LL-001-symbol-removal.md`
  con frontmatter `applies_to: [po-analyst, architect-reviewer]`. El agente
  genérico carga lessons-learned filtrando por `applies_to`.

#### 3.2 — `backend-developer.md`

- Línea 8: misma reescritura.
- Líneas 46-79: el orden Migration→Model→Schema→Repository→Service→Endpoint
  asume el stack de sie_v2. **Mover íntegro a `python-fastapi.md`**. El
  agente genérico dice: "Implement in the order specified by the stack
  profile for `${stack.backend.framework}`."
- Líneas 82, 89: `cd sie_v2 && ruff check .` y `cd sie_v2 && make test` →
  usar `${stack.backend.lint_cmd}` y `${stack.backend.test_cmd}`.
- Líneas 116-130 (Strict Rules): separar las reglas universales (max LOC,
  no commented code, all imports at top) de las específicas (`Optional[Type]`,
  `python` not `python3`, no `db.query()` in services). Las primeras quedan;
  las segundas migran al perfil.

#### 3.3 — `frontend-developer.md`, `code-reviewer.md`, `test-engineer.md`, `security-reviewer.md`, `architect-reviewer.md`, `migration-reviewer.md`

- Mismo patrón. Tres destinos por hardcode: agente genérico / stack profile /
  project specialization.
- Para `code-reviewer.md`: la sección "Cache Invalidation Checks (CRITICAL)"
  con `[LL-002]` (líneas 50-61) es 100% sie_v2-específica → mover a
  `<sie_v2>/.claude/project/review-checks/code-reviewer.md` con título
  "Cache invalidation patterns". El archivo `LL-002-cache-invalidation.md`
  vive en `<sie_v2>/.claude/project/lessons-learned/` con frontmatter
  `applies_to: [code-reviewer]`. El agente genérico carga ambos
  automáticamente vía la convención de Fase 3.5.
- Para `security-reviewer.md`: los `grep -rn "..." sie_v2/backend/` (líneas
  49-80) son patrones genéricos (secrets, tenant isolation) — el comando
  `grep` se generaliza al `${docs_process_root}` o cwd, pero los **patrones
  esperados** (qué buscar) quedan en el agente genérico. Si sie_v2 tiene
  patrones extra de auth propios, esos van a
  `<sie_v2>/.claude/project/review-checks/security-reviewer.md`.

#### 3.4 — Perfiles de stack iniciales (mínimo viable)

Crear como mínimo:
- `kuraka-artifacts/stack-profiles/python-fastapi.md` (extracto de hoy)
- `kuraka-artifacts/stack-profiles/vue-pinia.md` (extracto de hoy)
- `kuraka-artifacts/stack-profiles/_template.md` (instrucciones para
  contribuir un perfil nuevo)

**Verificación de la fase**:
- `grep -rn "sie_v2\|SIE v2\|Guai" agents/ skills/` debe devolver **0**
  resultados (ignorando ejemplos comentados explícitos).
- `grep -rn "ruff\|make test\|npm run\|FastAPI\|SQLAlchemy\|Pydantic\|Vue\|Pinia"
  agents/ skills/` debe devolver 0 resultados.
- sie_v2 sigue funcionando: corre un ciclo completo (puede ser un REQ-Lite)
  con el `kuraka.config.yaml` generado en Fase 2.

**Riesgo**: alto. Es el cambio más grande. Mitigación: hacerlo agente por
agente, no en bloque, y con un test eval (Fase 7) que se ejecute después
de cada agente refactorizado para detectar regresiones.

**Rollback por agente**: el commit anterior. La granularidad por-agente
permite revertir uno sin tocar los otros.

---

### Fase 3.5 — Project specialization layer

**Objetivo**: dar a cada proyecto consumidor un sitio formal donde vive su
conocimiento operativo (lecciones, checks, convenciones de equipo, dominio).
Esta capa es **co-requisito** de la Fase 3: cada hardcode que sale de un
agente aterriza acá. Sin esto, decoupling = pérdida de memoria institucional.

**Principio**: el framework provee genérico; el proyecto provee especialización;
los agentes componen ambos al arrancar.

#### 3.5.1 — Estructura del directorio

```
<project>/.claude/project/
├── README.md                          # qué vive acá y cómo se usa
├── conventions/                       # team conventions (las "rules 01-15")
│   ├── 01-solid-principles.md
│   ├── 04-backend-architecture.md
│   ├── 06-project-structure.md
│   ├── tenant-isolation.md           # patrones de dominio
│   └── ...
├── review-checks/                     # checklists extra por agente
│   ├── code-reviewer.md               # ej. cache invalidation pattern
│   ├── security-reviewer.md           # ej. tenant grep custom
│   └── architect-reviewer.md
├── lessons-learned/                   # memoria institucional indexada
│   ├── INDEX.md                       # tabla LL-NNN → título → applies_to
│   ├── LL-001-symbol-removal.md
│   └── LL-002-cache-invalidation.md
├── glossary.md                        # vocabulario de dominio
└── agents/                            # overrides opcionales (escape hatch)
    └── code-reviewer.append.md
```

Ningún archivo es obligatorio salvo `README.md`. Si el proyecto no tiene
lecciones todavía, el directorio `lessons-learned/` está vacío y los
agentes simplemente no cargan nada de ahí.

#### 3.5.2 — Contrato de loading en cada agente

Cada `agents/{agent}.md` genérico tiene una sección Context con orden
explícito de lectura. Ejemplo para `code-reviewer.md`:

```markdown
## Context (loaded in order, later overrides earlier)

1. <framework>/agents/contexts/code-reviewer-rules.md   (genérico)
2. <framework>/stack-profiles/${stack.backend.framework}.md
3. <project>/.claude/project/conventions/*.md
4. <project>/.claude/project/review-checks/code-reviewer.md  (si existe)
5. <project>/.claude/project/lessons-learned/*.md
   filtrar por frontmatter applies_to incluye "code-reviewer"
6. <project>/.claude/project/agents/code-reviewer.append.md  (si existe)
```

El orden importa: lo más específico (project) gana sobre lo más genérico
(framework) en caso de conflicto declarativo.

#### 3.5.3 — Schema de frontmatter para lessons-learned

```markdown
---
id: LL-002
title: Cache invalidation must cover all sub-keys in a namespace
date: 2026-03-15
incident_ref: docs/process/incidents/2026-03-15-stale-cache.md  # opcional
applies_to: [code-reviewer, backend-developer]
severity: high
tags: [redis, cache, invalidation]
---

## Contexto
[qué pasó]

## Patrón a buscar
[qué deben buscar los agentes etiquetados]

## Cómo verificar
[ejemplo de grep o check concreto]

## Referencia
[link al fix o al PR del incidente]
```

El runtime filtra: cuando se invoca el `code-reviewer`, sólo se cargan
lessons con `code-reviewer` en `applies_to`. Esto evita contaminar el
contexto del `po-analyst` con un check de cache de Redis.

#### 3.5.4 — Migración del conocimiento de sie_v2

Por cada hardcode removido en Fase 3, crear el archivo correspondiente en
el `<sie_v2>/.claude/project/`. Mapa concreto:

| Origen (hoy) | Destino (Fase 3.5) |
|---|---|
| `code-reviewer.md:50-61` (Cache Invalidation Checks) | `project/review-checks/code-reviewer.md` |
| `code-reviewer.md:61` (LL-002 reference) | `project/lessons-learned/LL-002-cache-invalidation.md` |
| `po-analyst.md:111-118` (Mandatory grep + LL-001) | `project/review-checks/po-analyst.md` + `project/lessons-learned/LL-001-symbol-removal.md` |
| `po-analyst.md` Regla 5 (tenant_id en queries) | `project/conventions/tenant-isolation.md` |
| `backend-developer.md:46-79` (Models→Schemas→Repo→Service→Endpoint, con detalles de sie_v2) | Parte genérica → `stack-profiles/python-fastapi.md`. Detalles propios del repo (módulos del dominio, naming de tablas) → `project/conventions/04-backend-architecture.md` |
| `code-reviewer.md` Architecture Checklist (líneas 37-49) | El checklist universal queda en el agente genérico. La parte sie_v2-específica (rutas, layers exactos) → `project/conventions/04-backend-architecture.md` |
| Reglas `rules/01-15.md` (hoy gitignored, viven en sie_v2) | `<sie_v2>/.claude/project/conventions/01-15-*.md` (tracked en git de sie_v2) |
| Vocabulario "providers", "Guai", "tickets de incidencia", etc. | `project/glossary.md` |
| `docs/process/lessons-learned.md` actual de sie_v2 (índice) | Partir en archivos individuales `LL-NNN-*.md` + `INDEX.md` regenerado |

#### 3.5.5 — Plantillas en el framework

El framework provee plantillas en `kuraka-artifacts/project-templates/`:

```
kuraka-artifacts/project-templates/
├── README.md                          # plantilla del README del project layer
├── conventions/_template.md
├── review-checks/_template.md
├── lessons-learned/_template.md
└── glossary-template.md
```

`kuraka init` en un proyecto nuevo crea `<project>/.claude/project/` con
el `README.md` y los directorios vacíos. El usuario va llenando a medida
que descubre patrones propios.

#### 3.5.6 — Update a `kuraka-inspect.py`

En modo Brownfield, el script ya samplea código del proyecto. Extender
para que **proponga** entradas iniciales del project layer:

- Detectar funciones/módulos con nombres recurrentes → candidatos para
  `glossary.md`.
- Detectar comentarios tipo `# HACK`, `# WORKAROUND` → candidatos para
  `lessons-learned/`.
- Detectar archivos `INCIDENT-*.md`, `POSTMORTEM-*.md` → candidatos para
  importar al `lessons-learned/`.

El `amauta` (agente brownfield) usa esas propuestas como input y le pide
al usuario que las valide antes de escribirlas.

#### 3.5.7 — Verificación

- En sie_v2: `<sie_v2>/.claude/project/lessons-learned/` contiene al menos
  LL-001 y LL-002 con `applies_to` correcto.
- En sie_v2: `<sie_v2>/.claude/project/review-checks/code-reviewer.md`
  contiene el patrón de cache invalidation.
- Eval `plant-bug-001` (cache invalidation parcial — Fase 7) **sigue
  detectándose** tras el decouple, demostrando que la lección sobrevivió
  el refactor.
- En un proyecto sin `<project>/.claude/project/`, los agentes corren igual
  (la capa es opcional, default vacía).

#### 3.5.8 — Riesgo y mitigación

**Riesgo principal**: que en la migración se "olvide" mover algún hardcode,
y un check histórico desaparezca silenciosamente. Mitigación:

- Antes de Fase 3, generar un "inventory" — un archivo
  `migration-inventory.md` que liste cada bloque sie_v2-específico encontrado
  en agents/skills, con un checkbox por destino. Fase 3 marca cada checkbox
  cuando el destino ya recibió el contenido.
- Eval suite (Fase 7) corre sobre el estado pre y post — diferencias en
  detection rate alertan que algo se perdió.

**Rollback**: trivial — el `<project>/.claude/project/` es aditivo. Si la
capa se borra o nunca se crea, los agentes corren con sólo el genérico
(menos conocimiento, mismo comportamiento estructural).

---

### Fase 4 — Estrategia de documentación

**Objetivo**: matar el sync-obsidian frágil, decidir convenciones y dejar el
modelo de docs limpio.

Cambios concretos:

1. **Convención de notación**: backticks (`` `agent-name` ``) en todo el
   source de agentes/skills/rules. Sin wikilinks.
   - `find agents/ skills/ rules/ -name "*.md" -exec sed -i ''
     's/\[\[\([a-z0-9-]*\)\]\]/`\1`/g' {} +`
   - **Costo**: el graph-view de Obsidian queda menos rico. Acepta el
     trade-off (lo discutimos en la conversación previa).

2. **Eliminar `scripts/sync-obsidian.sh`** y los arrays `AGENTS=()`/`SKILLS=()`
   hardcoded. Documentar en `README.md` la alternativa via symlink:

   ```bash
   # ejemplo en ~/.zshrc o setup manual del usuario
   ln -s ~/.kuraka ~/ObsidianVault/Frameworks/Kuraka
   ln -s /ruta/proyecto/docs/process ~/ObsidianVault/Proyectos/foo-process
   ```

3. **Eliminar conversión `[[x]]` ↔ `` `x` `` de `mount-kuraka.sh`** (si la
   tiene; verificar). Como ya no hay wikilinks, el rsync directo funciona.

4. **Modelo de docs definitivo en consumidor**:

   ```
   <project>/
   ├── kuraka.config.yaml             # tracked — declarativo (Fase 2)
   ├── kuraka.lock                    # tracked — fija versión del framework
   ├── .claude/
   │   ├── kuraka/                    # framework instalado (gitignored
   │   │                              #   o tracked, ver Fase 6)
   │   └── project/                   # tracked — project specialization (Fase 3.5)
   │       ├── README.md
   │       ├── conventions/
   │       ├── review-checks/
   │       ├── lessons-learned/
   │       ├── glossary.md
   │       └── agents/                # overrides opcionales
   ├── docs/
   │   └── process/
   │       ├── REQ-*.md               # tracked
   │       ├── stories/               # tracked
   │       ├── test-plans/            # tracked
   │       ├── schemas/               # tracked
   │       ├── retrospectives/        # tracked
   │       └── agent-telemetry/
   │           ├── *.json             # gitignored (ruido per-cycle)
   │           └── DASHBOARD.md       # tracked (consolidado)
   └── tests/
       └── kuraka/                    # tracked — eval harness estructural
   ```

   **Nota**: el `lessons-learned.md` que hoy vive en `docs/process/` se
   parte en archivos individuales bajo `.claude/project/lessons-learned/`
   con frontmatter `applies_to`. El motivo es que las lecciones son input
   del agente (deben filtrarse), no documentación pasiva del proyecto.

5. **Actualizar `mount-kuraka.sh`** (o el reemplazo `kuraka init`):
   - Crea el árbol de arriba.
   - Si `kuraka.config.yaml` no existe, ejecuta `kuraka-inspect` y propone
     generar uno.
   - Genera `.gitignore` apropiado (sólo `agent-telemetry/*.json` y
     `.claude/kuraka/` si el proyecto opta por no trackear el framework).

**Verificación**:
- `git status` en un proyecto recién montado muestra todos los docs
  necesarios como tracked.
- Borrar `scripts/sync-obsidian.sh` y correr un ciclo sin él — nada se rompe.
- Validar que un cambio en Obsidian (al símlink) se ve reflejado en el repo
  como un cambio normal de git.

**Riesgo**: medio. Si alguien dependía del sync-obsidian para preservar el
graph-view, lo va a notar. Mitigación: documentación clara del cambio en
`02-MIGRACION-FRAMEWORK.md` (este doc) y en `README.md`.

**Rollback**: difícil si ya se hizo el sed de wikilinks en 50+ archivos.
Mitigación: hacer Fase 4 en su propio commit aislado para que el revert
sea limpio.

---

### Fase 5 — Reestructura del workflow

**Objetivo**: bajar el costo del default. Modo `Standard` (4 fases) como
default. `Normal` (8 fases) sobrevive renombrado a `Compliance`.

Cambios concretos:

1. **Nuevo modo `Standard` (4 fases)** en `skills/kuraka-modes.md`:

   | Fase | Agente | Propósito |
   |------|--------|-----------|
   | S1 | `po-analyst` (mode: COMBINED) | REQ + stories + test plan en un pase |
   | S2 | `backend-developer` y/o `frontend-developer` | Implementación |
   | S3 | `code-reviewer` (mode: STANDARD) | Code review + security checklist mecánico |
   | S4 | `test-engineer` | Tests faltantes + retro corto opcional |

   Sin gates intermedios obligatorios — el usuario aprueba al final de S1
   (artefacto único) y al final de S3.

2. **Renombrar `Normal` → `Compliance`** y restringir a:
   - Cambios de schema mayor (>3 tablas o migración irreversible).
   - Cambios de auth/security críticos.
   - Cambios regulados (GDPR, HIPAA, PCI).
   - Equipos con requerimiento explícito de paper trail completo.

3. **Split del `code-reviewer`**:
   - `code-reviewer-mechanic` (haiku) — checklist mecánico: imports al top,
     no commented code, file size, function size, naming, layer skipping.
   - `code-reviewer-judgment` (sonnet) — diseño, performance, edge cases,
     coherencia con stories.
   - El primero corre siempre, el segundo sólo si el primero pasa o en
     modo Compliance.

4. **Eliminar `Retroactive` del menú principal**.
   - Mantenerlo como `tools/reconstruct-docs.md` separado, etiquetado como
     "para reconstruir documentación de código pre-existente, no parte del
     workflow".
   - Eliminar la sección de `kuraka-modes.md:237-306`.

5. **Actualizar `kuraka.md` y `kuraka-policies.md`**:
   - Tabla de modos refleja: Bootstrap, Brownfield, **Standard**, Compliance,
     Lite. Sin Retroactive.
   - Token budgets se ajustan al nuevo default.

6. **Actualizar `validate-kuraka.sh` y `tests/kuraka/`** para validar los
   nombres de modos nuevos.

**Verificación**:
- Correr el ciclo `Standard` en un proyecto de prueba pequeño y medir tokens
  vs. el ciclo `Lite` actual y el `Normal` actual.
- Confirmar que `Compliance` produce el mismo output que el `Normal` viejo.

**Riesgo**: medio. Equipos que dependen del `Normal` actual tienen que migrar
a `Compliance` (cambio de nombre, no de semántica). Mitigación: alias de
compatibilidad por una versión.

**Rollback**: revertir commit. Estado anterior es funcional.

---

### Fase 6 — Versionado y distribución

**Objetivo**: que un proyecto pueda decir "yo uso Kuraka v0.4.0" y que
upgradear sea explícito y revisable.

Cambios concretos:

1. **Tag inicial `v0.1.0`** sobre el estado **previo** al inicio de esta
   migración (commit actual del repo). Así hay un punto de retorno conocido.

2. **Tag `v0.2.0` al cierre de Fase 1** (cleanup), `v0.3.0` al cierre de
   Fase 2 (config), etc. Cada fase = tag.

3. **`kuraka.lock` en consumidor**:
   ```yaml
   # generado por `kuraka init` o `kuraka upgrade`
   version: v0.4.0
   commit: a1b2c3d
   installed_at: 2026-04-24T12:00:00Z
   ```
   - El comando `kuraka validate` falla si el `.claude/kuraka/` instalado
     no coincide con el lock.
   - El comando `kuraka upgrade <version>` re-clona, actualiza el lock y
     muestra changelog.

4. **CHANGELOG.md** en la raíz del repo. Cada fase deja una entrada con
   breaking changes destacados.

5. **`mount-kuraka.sh` deprecated → reemplazado por `kuraka init`** (script
   POSIX o un binario simple). Mantener `mount-kuraka.sh` como wrapper
   por compatibilidad durante una versión.

6. **Decisión**: ¿el directorio `.claude/kuraka/` del consumidor se trackea?
   - **A favor**: el equipo ve el framework en sus PRs, audit trail.
   - **En contra**: ruido en el repo del consumidor.
   - **Recomendación**: gitignored por default; equipos que quieran
     trackearlo lo hacen quitando la línea del `.gitignore` y commiteando.
     El `kuraka.lock` es la fuente de verdad sobre qué versión se usa.

**Verificación**:
- En un proyecto consumidor, `cat .claude/kuraka/.kuraka-version` coincide
  con `kuraka.lock`.
- `kuraka upgrade` desde v0.4.0 a v0.5.0 funciona y muestra cambios.

**Riesgo**: bajo. Es infraestructura, no toca prompts.

**Rollback**: trivial.

---

### Fase 7 — Evals reales

**Objetivo**: poder afirmar con datos que un cambio no degrada calidad.
Sin esto, las fases 3 y 5 son fe.

Cambios concretos:

1. **Estructura `evals/`**:

   ```
   evals/
   ├── README.md
   ├── runner.py                  # ejecuta los evals, mide tokens
   ├── fixtures/
   │   ├── plant-bug-001/        # bug conocido en código
   │   │   ├── before/
   │   │   ├── after/             # con bug
   │   │   ├── expected.json     # findings que el reviewer debe producir
   │   │   └── README.md
   │   ├── missing-test-001/
   │   ├── ambiguous-req-001/
   │   └── ...
   └── reports/
       └── 2026-04-24-baseline.json
   ```

2. **Evals iniciales (mínimo 5)**:
   - `plant-bug-001`: bug de cache-invalidation parcial → `code-reviewer`
     debe flaggearlo como BLOCKER.
   - `plant-bug-002`: SQL injection en raw query → `security-reviewer` debe
     flaggearlo como CRITICAL.
   - `missing-test-001`: endpoint nuevo sin tests → `test-engineer` debe
     escribirlos.
   - `ambiguous-req-001`: REQ con scope ambiguo → `po-analyst` debe pedir
     clarificación al usuario.
   - `wrong-layer-001`: lógica de negocio en endpoint → `code-reviewer` o
     `architect-reviewer` debe flaggearlo.

3. **Métricas medidas por eval**:
   - Detection rate (¿encontró lo plantado?).
   - False positive rate (¿flaggeó cosas que no estaban plantadas?).
   - Tokens consumidos.
   - Latencia.

4. **Baseline antes de Fase 3**: correr los evals contra el estado actual.
   Guardar en `evals/reports/{fecha}-baseline.json`.

5. **CI hipotético**: un GitHub Action que corre evals en cada PR y
   compara contra baseline. **Opcional** — la pieza importante es tener
   los evals corribles localmente.

**Verificación**:
- Cada eval pasa con el estado del repo previo a las modificaciones.
- Tras Fase 3 (decouple), los evals siguen pasando con el `kuraka.config.yaml`
  de sie_v2. Si bajan, el refactor introdujo regresión.

**Riesgo**: bajo, pero la inversión inicial es alta (escribir 5 fixtures
con cuidado). Vale la pena: es el único mecanismo objetivo para juzgar
las fases siguientes.

**Rollback**: N/A — los evals son aditivos.

---

## Riesgos transversales y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| sie_v2 se queda sin Kuraka funcional a mitad de migración | Media | Alto | Cada fase deja el repo funcional. sie_v2 fija una versión vía `kuraka.lock` y upgradea cuando quiera |
| El schema de `kuraka.config.yaml` queda mal y obliga a re-trabajo | Media | Alto | Validar contra 2-3 stacks distintos antes de cerrar Fase 2 |
| Refactor de prompts de agentes degrada calidad sin que se note | Alta | Alto | Evals de Fase 7 con baseline previo |
| Hardcode de sie_v2 se elimina sin moverse al project layer (pérdida silenciosa de check histórico) | Alta | Alto | "Migration inventory" en Fase 3.5.8: cada hardcode tiene checkbox de destino. Eval `plant-bug-001` valida que LL-002 sobrevivió |
| El project layer queda subutilizado y los equipos no lo llenan | Media | Medio | `kuraka-inspect` en modo Brownfield propone entradas iniciales; plantillas guían el llenado; documentar casos de éxito |
| Eliminar `Retroactive` molesta a alguien que lo usa | Baja | Bajo | Documentar en CHANGELOG; mover a `tools/` no destruir |
| Backticks-only rompe Obsidian de quien dependía del graph view | Media | Bajo | Decisión consciente, documentada |
| `kuraka init` deja consumers en estado inconsistente si falla a la mitad | Baja | Medio | El script debe ser idempotente y atómico (escribir a tmp, swap al final) |

---

## Definición de "hecho"

La migración está completa cuando se cumplen **todos**:

- [ ] `grep -rn "sie_v2\|SIE v2\|Guai" agents/ skills/ rules/` devuelve 0
      resultados (excluyendo ejemplos explícitos).
- [ ] Existe `kuraka.config.yaml` schema documentado y validado.
- [ ] Existen al menos 3 perfiles de stack (`python-fastapi`, `vue-pinia`,
      uno más distinto — Go, Node, Rails o Django).
- [ ] **Todo conocimiento sie_v2-específico está preservado en
      `<sie_v2>/.claude/project/`** y referenciable. Concretamente:
  - [ ] `project/lessons-learned/LL-001-symbol-removal.md` y
        `LL-002-cache-invalidation.md` existen con frontmatter `applies_to`.
  - [ ] `project/review-checks/code-reviewer.md` contiene el patrón de
        cache invalidation.
  - [ ] `project/conventions/` contiene las rules 01-15 del proyecto.
  - [ ] `project/glossary.md` contiene el vocabulario de dominio.
- [ ] El "migration inventory" (Fase 3.5.8) tiene **todos** los checkboxes
      de destino marcados — ningún hardcode quedó sin reubicar.
- [ ] Existen plantillas en `kuraka-artifacts/project-templates/`.
- [ ] `kuraka init` crea la estructura `.claude/project/` con README.
- [ ] sie_v2 corre con el nuevo Kuraka usando un `kuraka.config.yaml`
      generado y completa al menos un ciclo `Standard` end-to-end.
- [ ] Un proyecto **distinto a sie_v2** (de prueba, no necesariamente real)
      corre Kuraka y completa al menos un ciclo `Standard`.
- [ ] Los 5 evals iniciales pasan con el estado final. Específicamente
      `plant-bug-001` (cache invalidation) sigue detectándose, demostrando
      que la lección sobrevivió el refactor.
- [ ] `scripts/sync-obsidian.sh` eliminado, `mount-kuraka.sh` deprecated
      o reemplazado por `kuraka init`.
- [ ] `CHANGELOG.md` documenta cada fase y los breaking changes.
- [ ] `README.md` refleja el modelo nuevo (modos, distribución, config,
      project specialization layer).
- [ ] Tag `v1.0.0` aplicado al commit final.

---

## Orden recomendado y dependencias

```
Fase 0 (decisiones)
  ↓
Fase 1 (cleanup)  →  Fase 7 esqueleto (evals dir + baseline antes de F3)
  ↓
Fase 2 (config)
  ↓
Fase 3 (decouple agents)  ←→  Fase 3.5 (project layer en sie_v2)
                              [van acopladas: cada hardcode movido en F3
                               aterriza en F3.5 en el mismo PR]
  ↓
  evals corren después de cada agente refactorizado
  ↓
Fase 4 (docs strategy)    [puede ir en paralelo con F5]
  ↓
Fase 5 (workflow restructure)
  ↓
Fase 6 (versionado)       [puede empezar antes — tags se pueden poner en F1]
  ↓
Fase 7 cierre (evals completos sobre estado final)
```

Camino crítico: **0 → 1 → 2 → 3+3.5**. Las fases 4, 5, 6 pueden solaparse en
paralelo si hay capacidad.

**Nota sobre acoplamiento F3↔F3.5**: no se completa el refactor de un agente
sin haber creado los archivos de project layer correspondientes en sie_v2.
El "inventory" (Fase 3.5.8) es la herramienta de seguimiento.

---

## Estimación de esfuerzo (orden de magnitud, no commitment)

| Fase | Esfuerzo | Notas |
|------|---------:|-------|
| 0 | 0.5 día | Conversaciones de decisión, no código |
| 1 | 1 día | Cleanup mecánico |
| 2 | 2-3 días | Schema + validador + draft generator + ejemplo sie_v2 |
| 3 | 5-7 días | El más grande. Por agente: ~0.5 día + evals |
| 3.5 | 2-3 días | Estructura + plantillas + migración de conocimiento sie_v2. Acoplada con F3 |
| 4 | 1-2 días | Sed de wikilinks + symlinks + actualización docs |
| 5 | 2-3 días | Nuevo modo Standard + split de code-reviewer + tests |
| 6 | 1-2 días | Versioning, lock, init script |
| 7 | 3-4 días | Evals iniciales, runner, baseline |
| **Total** | **~17-25 días** | Asumiendo dedicación part-time |

---

## Decisiones cerradas

### D0.1 — Nombre del producto público
- Fecha: 2026-04-25
- Resolución: mantener **Kuraka** como nombre del framework y del orquestador.
- Justificación: branding e identidad cultural coherentes (quechua: kuraka, amauta, inti, arki, ayllu) ya documentados; el costo de cambiarlo no se justifica.

### D0.2 — Distribución
- Fecha: 2026-04-25
- Resolución: **git clone del repo del framework + `kuraka.lock` en cada proyecto consumidor**. Este repositorio (`kuraka`) es EL repo del framework — no se separa.
- Justificación: el producto son archivos markdown; clone+lock entrega versionado sin la fricción de submodules ni la complejidad de empaquetar (npm/pip). Patrón actual mejorado, no reemplazado.
- Revisitar si: aparecen ≥3 consumidores reales fuera del entorno actual.

### D0.3 — Versionado (SemVer estricto)
- Fecha: 2026-04-25
- Resolución:
  - **MAJOR**: breaking change al schema de `kuraka.config.yaml`, eliminación o renombre de agente, cambio de gates obligatorios, cambio de modo default.
  - **MINOR**: nuevo agente, nuevo stack profile, nuevo modo, nuevo campo opcional en config.
  - **PATCH**: fix de prompt, typo, mejora de doc, ajuste de checklist sin cambio de output schema.
- Tag `v0.1.0` se aplica sobre el commit pre-migración (último estado pre-Fase 1) como punto de retorno conocido.
- `v1.0.0` se aplica al cierre completo de la "Definición de hecho".

### D0.4 — Política de docs en consumidor
- Fecha: 2026-04-25
- Resolución:
  - Tracked: `kuraka.config.yaml`, `kuraka.lock`, `.claude/project/` (entero), `docs/process/{REQ,stories,test-plans,schemas,retrospectives}/`, `docs/process/agent-telemetry/DASHBOARD.md`, `tests/kuraka/`.
  - Gitignored: `docs/process/agent-telemetry/*.json` (ruido per-cycle), `.claude/kuraka/` (dependencia externa lockeada por hash).
- Justificación: el equipo necesita ver memoria institucional, REQs y retros en sus PRs; la telemetría per-cycle es ruido; el framework es una dependencia versionada, no source.

### D0.5 — Idioma por superficie
- Fecha: 2026-04-25
- Resolución:
  | Superficie | Idioma |
  |---|---|
  | `agents/*.md` (prompts) | **Inglés** |
  | `skills/*.md` consumidas por el modelo (incluidos `kuraka.md`, `kuraka-modes.md`, `kuraka-policies.md`) | **Inglés** |
  | Stack profiles (`kuraka-artifacts/stack-profiles/*.md`) | **Inglés** |
  | Plantillas de project layer (estructura) | **Inglés**; texto-ejemplo bilingüe |
  | `README.md`, `CLAUDE.md`, `0X-*.md`, `CHANGELOG.md` | **Español** |
  | Project layer del consumidor (`<project>/.claude/project/`) | **Idioma del equipo del proyecto** (sie_v2: español) |
- Implicación operativa: `skills/kuraka.md`, `kuraka-modes.md` y `kuraka-policies.md` (hoy en español) **se traducen a inglés** durante Fase 3.
- Justificación: mejor performance del modelo en prompts técnicos en inglés; doc de usuario en el idioma de la audiencia.

### D0.6 — Modo default
- Fecha: 2026-04-25
- Resolución: **`Standard` (4 fases)** es el nuevo modo default invocado cuando el usuario no especifica modo. `Compliance` (rebrand del actual `Normal` 8-fase) queda como opt-in explícito para cambios regulados/críticos.
- Justificación: el 8-fase es excesivo para el 80% de los cambios; reduce de 11 gates humanos a 2.

### D0.7 — sie_v2 como consumidor
- Fecha: 2026-04-25
- Resolución: **sí**, sie_v2 sigue siendo consumidor durante toda la migración y es el caso de prueba real para validar Fases 3 y 3.5.
- Nota del usuario: "sigue siendo consumidor en este momento" — la condición se reevalúa si cambia el contexto del proyecto.
- Justificación: sin un consumidor real no hay validación end-to-end del project layer; sie_v2 es la única fuente del conocimiento operativo que la Fase 3.5 preserva.
- Mitigación: cada fase deja el repo en estado funcional; sie_v2 fija versión vía `kuraka.lock` y upgradea cuando quiere.
