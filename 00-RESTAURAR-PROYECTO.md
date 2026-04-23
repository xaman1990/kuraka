# 🔄 RESTAURAR PROYECTO — EJECUTAR PRIMERO

> Este es el PRIMER paso cuando abres un proyecto y faltan agentes, skills, commands, rules o el script de sync.
> Copia el comando de abajo, pégalo en la terminal (en la raíz del proyecto) y listo.

---

## ⚡ Comando de restauración (copiar y pegar)

```bash
VAULT=/Users/xmn/Documents/Agentes/AgentesTrabajos/sie_integraciones && \
mkdir -p .claude/agents/contexts .claude/skills .claude/commands .claude/rules scripts && \
REVERT_WIKILINKS() { for dir in "$@"; do for file in "$dir"/*.md; do [ -f "$file" ] || continue; sed -i.bak 's/\[\[\([a-z][a-z0-9-]*\)\]\]/`\1`/g' "$file" && rm "${file}.bak"; done; done; } && \
cp "$VAULT"/agents/*.md .claude/agents/ 2>/dev/null; \
cp "$VAULT"/agents/contexts/*.md .claude/agents/contexts/ 2>/dev/null; \
cp "$VAULT"/skills/*.md .claude/skills/ 2>/dev/null; \
cp "$VAULT"/commands/*.md .claude/commands/ 2>/dev/null; \
cp "$VAULT"/rules/*.md .claude/rules/ 2>/dev/null; \
cp "$VAULT"/scripts/sync-obsidian.sh scripts/ 2>/dev/null && chmod +x scripts/sync-obsidian.sh; \
REVERT_WIKILINKS .claude/agents .claude/agents/contexts .claude/skills .claude/rules; \
echo "Restaurado: $(ls .claude/agents/*.md 2>/dev/null | wc -l) agentes, $(ls .claude/skills/*.md 2>/dev/null | wc -l) skills, $(ls .claude/commands/*.md 2>/dev/null | wc -l) commands, $(ls .claude/rules/*.md 2>/dev/null | wc -l) rules, $([ -x scripts/sync-obsidian.sh ] && echo 'sync-obsidian.sh ✓' || echo 'sync-obsidian.sh ✗')"
```

---

## 📋 Cómo usarlo

1. Abre el proyecto en tu editor
2. Abre la terminal **en la raíz del proyecto** (donde está `.git/`)
3. Pega el comando de arriba y Enter
4. Verás cuántos archivos se restauraron

### Salida esperada

```
Restaurado: 13 agentes, 21 skills, 4 commands, 16 rules, sync-obsidian.sh ✓
```

---

## 🔧 Opcional — Alias permanente

Si quieres escribir solo `claude-sync` en vez de pegar el comando entero,
ver `dotfiles/zshrc-alias.md` en este vault para la configuración del `.zshrc`.

---

## 🗂 Qué restaura

| Carpeta/Archivo local | Origen en el vault | Conversión |
|-----------------------|-------------------|-----------|
| `.claude/agents/*.md` | `agents/` | `[[name]]` → `` `name` `` |
| `.claude/agents/contexts/*.md` | `agents/contexts/` | `[[name]]` → `` `name` `` |
| `.claude/skills/*.md` | `skills/` | `[[name]]` → `` `name` `` |
| `.claude/commands/*.md` | `commands/` | Verbatim (sin conversión) |
| `.claude/rules/*.md` | `rules/` | `[[name]]` → `` `name` `` |
| `scripts/sync-obsidian.sh` | `scripts/` | Verbatim + `chmod +x` |

---

## ⚠️ Notas

- **El vault usa wikilinks `[[name]]` para el graph view de Obsidian**. Al restaurar, se convierten a backticks `` `name` `` porque es lo que Claude Code espera
- Los archivos en `commands/` NO se convierten — son prompts ejecutables y la conversión rompería sus greps
- El comando **NO sobrescribe** archivos en el baúl — solo copia desde el vault hacia tu proyecto local
- Si hay conflictos (archivo diferente en local), **sí los sobrescribe** — por eso ejecutarlo solo cuando quieras restaurar al estado del vault
- Es seguro ejecutarlo múltiples veces (idempotente si el vault no cambió)
- El `chmod +x` al script es necesario porque los permisos de ejecución se pierden al copiar en algunos casos
- **Importante:** El script `sync-obsidian.sh` tiene safety guards — si tu `.claude/` está vacío, el hook no pisará el vault. Siempre restaura ANTES de editar archivos

---

## 🆘 Si el comando falla

- Verifica que el path del vault existe: `ls /Users/xmn/Documents/Agentes/AgentesTrabajos/sie_integraciones/`
- Verifica que estás en la raíz del proyecto: `ls` debería mostrar carpetas como `backend/`, `frontend/`, etc.
- Si cambió el path del vault, edita la línea `VAULT=...` del comando
- Si el script no queda ejecutable: `chmod +x scripts/sync-obsidian.sh`
- Si ves wikilinks `[[name]]` en archivos locales tras restaurar, corre: `find .claude/agents .claude/skills .claude/rules -name "*.md" -exec sed -i '' 's/\[\[\([a-z][a-z0-9-]*\)\]\]/\`\1\`/g' {} +`
