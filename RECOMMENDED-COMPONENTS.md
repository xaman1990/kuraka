# Kuraka — Componentes recomendados

Kuraka funciona sin estos componentes, pero varios agentes/skills rinden mucho
mejor (o mucho más barato en tokens) con ellos instalados. `kuraka-init.py`
muestra esta lista al final del onboarding y detecta cuáles ya están presentes.
Ninguno se instala automáticamente — son herramientas externas y la instalación
debe ser una decisión explícita del usuario.

Leyenda de prioridad:
- 🔴 **strong** — alto impacto transversal; instalalo salvo que tengas una razón.
- 🟡 **recommended** — claro beneficio para cierto tipo de proyecto.
- ⚪ **optional** — útil en casos puntuales.

| Componente | Prioridad | Qué agente/skill de Kuraka lo usa | Para qué |
|------------|:---------:|-----------------------------------|----------|
| **RTK** (rtk-ai/rtk) | 🔴 strong | TODOS los agentes (bash/test/grep/git) | Proxy CLI que filtra la salida de comandos antes de que entre al contexto. Ahorro 70–90% en operaciones de dev. |
| **ui-ux-pro-max** | 🟡 recommended | `frontend-developer`, `impeccable` | Inteligencia de diseño UI/UX (estilos, paletas, tipografías, guías UX, charts). |
| **Playwright MCP** | 🟡 recommended | `e2e-tester` (Phase 6.5), `checkmarx-remediation` | Tests de navegador end-to-end y captura en vivo (login Checkmarx). |
| **impeccable** (skill) | ⚪ optional | revisión/pulido de UI del `frontend-developer` | Auditoría y refinamiento visual de interfaces. |
| **magic / 21st MCP** | ⚪ optional | `frontend-developer` (scaffolding) | Generación/refinamiento de componentes UI. |
| **Jira/MCP de tickets** | ⚪ optional | `po-analyst` (Phase 1) | Traer el ticket real en vez de pegar la descripción. |

---

## RTK — instalación y por qué es la #1

RTK ("Rust Token Killer") es un binario único en Rust (<10 ms de overhead) que
intercepta la salida de 100+ comandos y la comprime antes de que llegue al LLM:
filtrado de ruido, agrupación, truncado preservando contexto, y deduplicación de
líneas repetidas.

**Instalación:**
```bash
brew install rtk            # o: cargo install --git https://github.com/rtk-ai/rtk
rtk init -g                 # instala el hook auto-rewrite (Claude Code, etc.)
rtk --version               # verificar
```

**Verificación:** `rtk gain` (analítica de ahorro). ⚠️ colisión de nombre: si
`rtk gain` falla, tenés instalado otro `rtk` (Rust Type Kit), no este.

**Ahorros publicados (sesión de 30 min de Claude Code):**

| Operación | Reducción |
|-----------|:---------:|
| `ls` / `tree` | 80% |
| `cat` / `read` | 70% |
| `grep` / `rg` | 80% |
| `git` (status/log/diff) | 75–92% |
| test runners (pytest, vitest, cargo, go) | 90% |
| **Total típico** | **~118k → ~23.9k tokens (-80%)** |

**Por qué encaja con Kuraka:** los ciclos de Kuraka son intensivos en exactamente
estas operaciones — `code-reviewer` hace grep + lee muchos archivos, los
developers corren `make test`, `deployment-verifier` lee logs de CI, `e2e-tester`
corre Playwright. RTK ataca el **costo de cada lectura**; las reglas de
`rules/17` atacan **cuántas veces leés** (digest T1, typecheck al final, no
auto-verify). Son **complementarios, no se solapan** → el ahorro se multiplica.

---

## ui-ux-pro-max — para proyectos con frontend

Skill de inteligencia UI/UX (50+ estilos, 161 paletas, 57 pares de tipografías,
guías UX, 25 tipos de charts, integración shadcn/ui MCP). El `frontend-developer`
la consulta al implementar/revisar UI (ver `agents/frontend-developer.md` →
"Recursos de diseño"). Recomendado para cualquier proyecto con superficie visual.

---

## Notas

- Skills (ui-ux-pro-max, impeccable) se instalan vía el marketplace de plugins de
  Claude Code y **no** son detectables desde el CLI — se imprime la recomendación.
- **Los MCP sí se detectan.** `kuraka-init.py` / `kuraka mount` leen los servidores
  configurados en `~/.claude.json` (y `.mcp.json` del proyecto, si existe) bajo
  `mcpServers`, y marcan cada componente con `mcp` como `✓ instalado (MCP)` o
  `— falta`. Hoy detecta: Playwright (`playwright`), magic/21st (`magic`),
  Jira/ticket (`jira`). RTK se detecta por CLI (`which rtk`).
- Ver la detección en vivo sin montar nada:
  `python3 kuraka-init.py --recommend-only [dir]`. El `kuraka mount` interactivo
  también la imprime (menú de categorías + estado de MCP).
- Mantené esta tabla en sync con `kuraka-init.py` (`RECOMMENDED_COMPONENTS`): la
  clave `detect` es un binario (`which`), `mcp` es una key de `mcpServers`.
