# RETRO — Sesión 2026-06-07 (clinicaDental2026)

> Retrospectiva de proceso (no de un ciclo único). Cubre los ciclos de UI de la sesión
> (toggle Habilitar/Deshabilitar+Eliminar en listados, validadores/placeholders del form de
> clientes, bloqueo de entrada + select de Género, favicon/título ZYNVET) y, sobre todo, las
> **lecciones de proceso** que el usuario exigió que queden registradas para que Kuraka las tome
> en cuenta a futuro.

## 1. Resumen

La parte de implementación funcionó (subagentes `frontend-developer` entregaron y `ng build`
quedó verde en cada paso). El problema fue de **proceso del orquestador**: (a) declarar "hecho"
con evidencia débil, y (b) saltarse el gate de techlead en cambios chicos. El usuario tuvo que
**repetir pedidos** (caso favicon). Además se detectó un **hueco estructural**: faltaba el
stack-profile de Angular, por lo que las convenciones llegaban a los subagentes solo vía
`.claude/project/conventions/*` + inyección manual del orquestador (frágil).

## 2. Timeline de retrabajo

| # | Pedido | Qué pasó | Retrabajo |
|---|--------|----------|-----------|
| 1 | Favicon = logo de la solución | Cambié `<title>` y favicon, pero apunté a `images/logo/logo.svg` (asset **heredado de Fuse**) y di "hecho" verificando solo `200` + href, sin mirar la imagen. | El usuario reportó "sigo viendo el logo viejo" → 2ª pasada: usar `logo-zynvet-128.png` + `?v=2`. |
| 2 | Validadores del form de clientes | Implementé validadores que **muestran error** pero no **bloquean** el tecleo. | El usuario aclaró que quería bloqueo → 2ª pasada: directiva `appInputFilter` + fix master_id de Género. |

## 3. Causa raíz

1. **Verificación con proxies, no con el resultado real.** Cerré tareas de UI mirando `HTTP 200`,
   `ng build` verde o el `href` del `<link>`, en lugar del **resultado visible** (la imagen del
   favicon, el comportamiento del input). Es justo el principio de Kuraka "tests verdes ≠ feature
   funcionando" no aplicado al plano **visual**.
2. **Gate de techlead omitido en cambios chicos.** Los cambios de 1 agente (validadores,
   bloqueo+Género, favicon) NO pasaron por `code-reviewer`. El review existe precisamente para
   cazar estos errores (lo demostró el review de `angular.md`, que encontró 1 BLOCKER real).
3. **Hueco estructural: faltaba `.claude/stack-profiles/angular.md`.** Los agentes
   (`frontend-developer`, `code-reviewer`) están programados para cargar
   `.claude/stack-profiles/${stack.frontend.framework}.md` = `angular.md`, que **no existía**
   (solo había `python-fastapi.md` y `vue-pinia.md`). Las convenciones llegaban solo por
   `.claude/project/conventions/*` + lo que el orquestador inyectaba a mano en cada prompt →
   dependiente del orquestador, no del sistema.

> Nota sobre docs/CLAUDE.md: el `CLAUDE.md` y `docs/spec/*` se auto-cargan en el contexto del
> **orquestador**, pero los **subagentes NO los heredan** automáticamente (contexto separado).
> Reciben la spec vía `kuraka.config.yaml` + el stack-profile + `.claude/project/conventions/*`.
> Por eso el stack-profile de Angular es la pieza que faltaba.

## 4. Acciones tomadas en esta sesión (ya aplicadas)

- **Creado `.claude/stack-profiles/angular.md`** (Profile v1, stable), derivado de `docs/spec/*`
  + el código real. Cubre: orden de implementación, paths idiomáticos, invariantes de
  arquitectura (standalone/lazy, `IApiResponse`, 200-con-error, identidad por `*_hash`, borrado
  lógico con `StateUtil`, multi-tenant `company_hash`, `*appCanAccess` con etiquetas reales del
  `X-Acc`, i18n total, sprite Lucide), test patterns, naming bilingüe, command surface,
  pitfalls y anti-patrones.
- **Validado por techlead (`architect-reviewer`)**: verdicto **APPROVED-WITH-FIXES**. Encontró y
  se corrigieron: BLOCKER (el sprite usa `<svg id>`, no `<symbol>`); IMPORTANT (`master-list` NO
  tiene `backendError()` → la referencia canónica es `list-profile`/`master-argu-list`); 2 MINOR
  (`zv-table` es clase CSS no componente; registro como set namespaced).
- **Reglas de proceso registradas** en memoria de proyecto (`memory/kuraka-process-rules.md`).

## 5. Lecciones / mejoras para Kuraka (que debe tomar en cuenta a futuro)

### L1 — Gate de techlead OBLIGATORIO tras cada cambio (incluso 1 agente)
Pipeline mínimo por defecto en este proyecto:
`implementar (dev agent) → code-reviewer (techlead valida requerimiento + constitución +
conventions + stack-profile) → orquestador verifica el resultado VISIBLE real → "hecho"`.
No saltarlo por "es trivial". (Exigido por el usuario 2026-06-07.)

### L2 — Prohibido cerrar con proxies
No declarar "hecho" con `200` / `ng build` verde / href correcto. En UI: abrir la pantalla,
ejecutar la acción y **observar el resultado**; al usar un asset (logo/icono), **abrir la imagen**
y confirmar que es el correcto antes de cerrar.

### L3 — Mantener los stack-profiles en sincronía con el framework detectado
Cuando el stack detectado no tenga su `.claude/stack-profiles/<framework>.md`, crearlo (o avisar)
ANTES de correr ciclos — es el canal por el que la spec llega a los subagentes. (Sugerencia:
`amauta`/`pattern-detector` deberían chequear su existencia.)

### Propuesta de adición al project-layer (para que los reviewers lo enforced)
- `.claude/project/review-checks/code-reviewer.md`: añadir checks "200-con-`error`→error state",
  "etiqueta de permiso existe en X-Acc", "icono existe como `<svg id>` en el sprite".
- `.claude/project/lessons-learned/`: registrar L1/L2 con `applies_to: [code-reviewer, frontend-developer]`.

## 6. Telemetría (esta tanda de proceso)

| Fase | Agente | tokens | tool_uses | duration_ms | Resultado |
|------|--------|-------:|----------:|------------:|-----------|
| stack-profile review | architect-reviewer | 99_542 | 14 | 186_323 | APPROVED-WITH-FIXES (1 BLOCKER + 1 IMPORTANT detectados y corregidos) |

Telemetría de los ciclos de UI en
`docs/process/agent-telemetry/REQ-20260607-*.json`.

## 7. Estado

- `angular.md`: creado, validado, fixes aplicados. ✅
- Reglas de proceso: adoptadas + en memoria. ✅
- **Pendiente:** pasar por el techlead (`code-reviewer`) los 3 cambios de UI que se hicieron sin
  gate (validadores, bloqueo+Género, favicon) para dejarlos validados como corresponde; y el
  commit de la sesión.
