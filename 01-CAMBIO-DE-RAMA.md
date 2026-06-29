# 🔀 CAMBIO DE RAMA — Flujo completo

> Qué ejecutar cuando cambies de rama en el proyecto y necesites tener el
> Kuraka disponible (agentes, skills, rules personales, lessons-learned,
> eval harness). Copia y pega en la terminal.

---

## ⚡ TL;DR — 3 comandos

```bash
# 1. Cambia de rama
cd /Users/xmn/Documents/Trabajo/Cuidacasas/sie_integraciones
git switch <nueva-rama>

# 2. Monta el Kuraka (desde el vault al proyecto)
bash /Users/xmn/Documents/Agentes/AgentesTrabajos/kuraka/mount-kuraka.sh

# 3. En Claude Code activo:
/exit
# luego abres una nueva sesión en el proyecto — los agentes se registran
```

Con el alias configurado (ver sección al final):

```bash
git switch <nueva-rama>
mount-kuraka
/exit
```

> 💡 **Recuperar historia perdida.** Al montar, si el Kuraka central ya tiene
> historia de este proyecto (trabajaste en otra rama y no subiste lo de Kuraka a
> git), `mount-kuraka` te preguntará **«¿Restaurar la historia de <slug>? [s/N]»**
> y, si aceptás, re-pega `layer/` (`.claude/project`) y `state/docs-process/`
> (REQ, historias, schemas…) sin pisar lo que ya exista. Así no perdés el trabajo
> de Kuraka al cambiar/crear ramas, aunque viva fuera del git de la solución.
> El backup al central se hace solo al cerrar cada ciclo (Phase 7).

---

## 🗂 Qué se mueve automáticamente con `git switch`

No necesitas tocar nada de esto: viaja con la rama por estar trackeado en el git del proyecto.

| Fuente | Ejemplo |
|---|---|
| `sie_v2/docs/**` | arquitectura, base_de_datos, integraciones, seguridad… |
| `sie_v2/backend/documentacion/**` | docs específicos del backend |
| `sie_v2/.claude/rules/01-15.md` | reglas de equipo (convenciones del proyecto) |
| `sie_v2/.claude/CLAUDE.md` | índice de reglas del proyecto |
| Código fuente (`backend/`, `frontend/`) | todo lo de la rama destino |

---

## 🪢 Qué copia [[mount-kuraka]]

Desde el vault (`kuraka/`) al proyecto:

| Origen en vault | Destino en el proyecto |
|---|---|
| `agents/*.md` (16 agentes) | `.claude/agents/` |
| `agents/contexts/*.md` | `.claude/agents/contexts/` |
| `skills/*.md` ([[kuraka]] + [[kuraka-modes]] + [[kuraka-policies]] + 18 fases) | `.claude/skills/` |
| `commands/*.md` | `.claude/commands/` |
| `hooks/*.sh` | `.claude/hooks/` |
| `rules/16-agent-backup.md` | `.claude/rules/` |
| `rules/17-kuraka-token-optimizations.md` | `.claude/rules/` |
| `kuraka-artifacts/docs/process/lessons-learned.md` | `docs/process/` |
| `kuraka-artifacts/docs/process/agent-telemetry/DASHBOARD.md` | `docs/process/agent-telemetry/` |
| `kuraka-artifacts/tests/kuraka/**` | `tests/kuraka/` |

Además añade automáticamente al `.gitignore` del proyecto los patrones que excluyen estos ficheros personales del git del equipo:

```gitignore
# Personal Kuraka system — not shared with team
.claude/agents/
.claude/skills/
.claude/commands/
.claude/hooks/
.claude/rules/16-agent-backup.md
.claude/rules/17-kuraka-token-optimizations.md
docs/process/lessons-learned.md
docs/process/agent-telemetry/
tests/kuraka/
```

---

## 🔁 ¿Por qué reiniciar Claude Code?

Claude Code construye la lista de `subagent_type` invocables **al arrancar la sesión**. Si ya tienes una sesión abierta cuando haces `mount-kuraka`, los agentes nuevos existen como ficheros pero el runtime no los ha registrado. `/exit` + nueva sesión = registro automático.

Para confirmar que los 16 agentes están registrados tras el reinicio, ejecuta:

```bash
validate-kuraka
# (o sin alias: bash /Users/xmn/Documents/Agentes/AgentesTrabajos/kuraka/validate-kuraka.sh)
```

Debería terminar con `✅ validation OK` y reportar 16 agentes en disco.

---

## 🔧 Alias permanente (recomendado)

Añade a `~/.zshrc` (o copia de `dotfiles/zshrc-alias.md`):

```bash
alias mount-kuraka='bash /Users/xmn/Documents/Agentes/AgentesTrabajos/kuraka/mount-kuraka.sh'
alias validate-kuraka='bash /Users/xmn/Documents/Agentes/AgentesTrabajos/kuraka/validate-kuraka.sh'
alias kuraka-inspect='python3 /Users/xmn/Documents/Agentes/AgentesTrabajos/kuraka/kuraka-inspect.py'
alias kuraka-dashboard='python3 /Users/xmn/Documents/Agentes/AgentesTrabajos/kuraka/aggregate-telemetry.py'
```

Tras `source ~/.zshrc`, el flujo post-switch queda:

```bash
git switch <rama>
mount-kuraka
/exit
```

---

## 🌐 Escenario multi-máquina: antes de `mount-kuraka` haz `git pull`

Si editaste el framework desde otra máquina (o desde el propio repo en otra ventana del IDE) y pushearon cambios al remote:

```bash
cd /Users/xmn/Documents/Agentes/AgentesTrabajos/kuraka
git pull                      # trae cambios del remote al vault local
cd /Users/xmn/Documents/Trabajo/Cuidacasas/sie_integraciones
git switch <rama>
mount-kuraka                  # ahora copia la versión actualizada al proyecto
/exit
```

---

## ❌ Qué NO hace falta hacer

- **NO** necesitas `git stash` antes de cambiar rama — los ficheros Kuraka en la rama actual son untracked (por el `.gitignore`), sobreviven al `git switch` automáticamente. `mount-kuraka` solo garantiza consistencia.
- **NO** necesitas re-sincronizar `sie_v2/docs/` ni `sie_v2/backend/documentacion/` — viven en el git del proyecto, se mueven con la rama.
- **NO** necesitas re-instalar Claude Code — solo reiniciar la sesión.
- **NO** necesitas tocar el vault manualmente — `mount-kuraka` lo lee en read-only.

---

## 🆘 Troubleshooting

### "No veo los agentes como subagent_type después de reiniciar"

1. Ejecuta `validate-kuraka` y verifica `Agents on disk: 16`.
2. Si dice menos, faltó alguno en el mount: vuelve a correr `mount-kuraka`.
3. Si los 16 están en disco pero el `subagent_type` solo lista 1 o ninguno: a veces Claude Code cachea más agresivamente. Cierra todas las ventanas de Claude Code (no solo `/exit`) y vuelve a abrir.

### "mount-kuraka da error 'vault not found'"

El path del vault está hardcoded en `mount-kuraka.sh`. Si movieras el vault otra vez, edita esa línea. Actualmente debería ser:
```
VAULT="/Users/xmn/Documents/Agentes/AgentesTrabajos/kuraka"
```

### "Hay conflictos al hacer git switch"

Probablemente hay ficheros Kuraka **trackeados** (no gitignored) en la rama actual. Solución:

```bash
# dentro del proyecto:
git status --short .claude/ docs/process/ tests/kuraka/
# si aparecen con letra (M/A/D), están trackeados
# bórralos del index pero mantén working tree:
git rm --cached -r .claude/agents/ .claude/skills/ .claude/commands/ .claude/hooks/ \
  .claude/rules/16-agent-backup.md .claude/rules/17-kuraka-token-optimizations.md \
  docs/process/lessons-learned.md docs/process/agent-telemetry/ tests/kuraka/ 2>/dev/null
# ahora sí puedes cambiar de rama
git switch <rama>
mount-kuraka
```

### "¿Cómo compruebo que el `.gitignore` del proyecto se actualizó?"

```bash
grep -A 10 "Personal Kuraka" .gitignore
```

Si no aparecen las entradas, vuelve a correr `mount-kuraka` (es idempotente).

---

## 📚 Enlaces relacionados

- [[00-RESTAURAR-PROYECTO]] — alternativa legacy de restauración monolítica (sin `mount-kuraka.sh`)
- [[README]] — overview completo del sistema Kuraka
- [[dotfiles/zshrc-alias]] — configuración de aliases
- [[skills/kuraka]] — flujo principal del workflow
- [[skills/kuraka-modes]] — variantes Bootstrap / Brownfield / Lite / etc.
- [[skills/kuraka-policies]] — retry, timeout, telemetry, checkpoints
