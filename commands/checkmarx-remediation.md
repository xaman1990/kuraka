---
description: "Ejecuta el flujo completo de remediación Checkmarx para un scan: extrae los tickets (SAST + SCA + API Security) vía las APIs internas, los cruza con el código real, diseña la solución, detalla tareas, estima el esfuerzo por hallazgo y entrega un informe HTML + un checklist .md. Reutilizable para cada nuevo requerimiento/scan."
---

# Task: Remediación Checkmarx (informe HTML + checklist .md)

Lanza el agente **`checkmarx-remediation`** para producir el plan de remediación de un scan de
Checkmarx One. Es el mismo flujo con el que se hizo el análisis inicial, ahora repetible.

## Entradas
Pide al usuario (si no vienen en los argumentos):
- **URL / projectId / scanId** del scan en `ast.checkmarx.net`.
- **Alcance de severidad** (default: todas; permite excluir Low u otras).
- **Parámetros de estimación** si difieren de los defaults (repetición 40% · SQLi 20% · API excluido ·
  SCA por upgrade de paquete · overhead 10 h).

## Pasos
1. **Lee la memoria** `checkmarx-api-extraction` (endpoints + truco de token + mapeos).
2. **Invoca el agente `checkmarx-remediation`** pasándole projectId/scanId, alcance y parámetros.
   El agente ejecuta sus 6 fases:
   - Fase 0: abre Checkmarx con Playwright → **el usuario inicia sesión** → captura el Bearer en vivo.
   - Fase 1: extrae SAST (`/api/sast-results`), SCA (`/api/sca/graphql`), API Security
     (`/api/apisec/.../risks`), descripciones de query y `scan-summary`; guarda los JSON crudos.
   - Fase 2: cruza cada hallazgo con el **código real** del repo (file:línea) y mapea módulos/vistas.
   - Fase 3: diseña el fix antes/después, validado contra la guía oficial del query.
   - Fase 4: estima por hallazgo (descuento por similitud) agrupado por criticidad.
   - Fase 5: genera los entregables en `docs/process/checkmarx/`.
3. **Verifica** el HTML sirviéndolo con `python3 -m http.server` (no `file://`) y revisa 2-3 slides.
4. **Espeja** el agente, este command y los `docs/` cambiados al vault Obsidian
   (`.claude/rules/16-agent-backup.md`).

## Entregables (en `docs/process/checkmarx/`)
- `remediacion-checkmarx.html` — informe/presentación autocontenido (sin auto-avance; links de la
  estimación a la slide de la solución).
- `checklist-remediacion.md` — **checklist de tareas** (`- [ ]`) por PR/criticidad con esfuerzo,
  `archivo:línea`, módulo afectado y link a la solución.
- `remediacion-checkmarx.md`, `estimacion-detallada.md`, `inventario-completo.md` + JSON crudos.

> Recordatorio: API Security ⊂ SAST (no duplicar esfuerzo); CWE y líneas vienen de la API/código (no
> inventar); build/verificación de fixes es Windows/IIS.
