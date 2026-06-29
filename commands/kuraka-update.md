---
description: "Update the mounted Kuraka framework in THIS project from the vault (new/updated agents, skills, commands, templates). Portable: resolves the vault from $KURAKA_VAULT and auto-detects the project root via .claude/. Safe: rsync --update never touches kuraka.config.yaml, .claude/project/, or docs/. Requires a Claude Code restart afterward."
---

# Task: Update Kuraka framework in this project

Re-mount the Kuraka vault into the current project so it picks up new and
updated framework files (agents, skills, commands, contexts, stack-profiles,
templates) — without touching project-specific content.

**Portability**: the vault location is NOT hardcoded. It is read from the
`KURAKA_VAULT` environment variable, falling back to the author's default
only if the variable is unset. On a different machine, set it once:
`export KURAKA_VAULT="/your/path/to/kuraka"` (put it in `~/.zshrc`).

## Steps

### 1. Pre-check for hand edits (safety)

Run:
```bash
git status --short .claude/ 2>/dev/null
```
If there are uncommitted changes inside `.claude/agents/` or `.claude/skills/`
(framework files that should normally be customized via `.claude/project/`,
not edited in place), report them to the user and ask whether to continue
before re-mounting — `rsync --update` would overwrite them if the vault copy
is newer.

### 2. Resolve the vault, find the project root, and mount

Run this block exactly. It resolves the vault from `$KURAKA_VAULT`
(portable), walks up from the current directory to find the project root
that contains `.claude/`, and mounts into it — so it works no matter which
subdirectory you launched from, and on any machine:

```bash
# --- portable vault resolution (env var first, fallback second) ---
VAULT="${KURAKA_VAULT:-/Users/xmn/Documents/Agentes/AgentesTrabajos/kuraka}"
if [ ! -d "$VAULT" ]; then
  echo "❌ Vault no encontrado en: $VAULT"
  echo "   Define la ruta correcta y reintenta:"
  echo "     export KURAKA_VAULT=\"/ruta/a/kuraka\"   # añádelo a ~/.zshrc para que persista"
  exit 1
fi

# --- find project root = nearest ancestor (incl. $PWD) containing .claude/ ---
DIR="$PWD"
while [ "$DIR" != "/" ] && [ ! -d "$DIR/.claude" ]; do DIR="$(dirname "$DIR")"; done
if [ ! -d "$DIR/.claude" ]; then
  echo "❌ No hay un proyecto con .claude/ desde: $PWD"
  echo "   Corre /kuraka-update dentro de un proyecto que ya tenga Kuraka montado."
  exit 1
fi
PROJECT_ROOT="$DIR"

echo "🪢 vault:    $VAULT"
echo "🪢 proyecto: $PROJECT_ROOT"
echo ""

# --- mount (rsync --update: only newer vault files; never touches project content) ---
bash "$VAULT/mount-kuraka.sh" "$PROJECT_ROOT"
```

This does **NOT** modify `kuraka.config.yaml`, `.claude/project/`
(conventions, lessons-learned, glossary, promoted experts), or `docs/`.

### 3. Report what changed

Summarize the script output: which categories had new/updated files
(`+ skills/`, `+ commands/`, `✓ templates/`, etc.). Call out notable
additions when present.

### 4. Validate (optional but recommended)

```bash
VAULT="${KURAKA_VAULT:-/Users/xmn/Documents/Agentes/AgentesTrabajos/kuraka}"
DIR="$PWD"; while [ "$DIR" != "/" ] && [ ! -d "$DIR/.claude" ]; do DIR="$(dirname "$DIR")"; done
bash "$VAULT/validate-kuraka.sh" "$DIR"
```
Report PASS/FAIL. If it fails, show the offending agent/skill frontmatter.

### 5. Tell the user to restart

End by reminding the user — this is MANDATORY:

> "Listo. Reinicia Claude Code (`/exit` + sesión nueva) para que se
>  registren las skills/agentes/commands nuevos — se registran solo al
>  inicio de sesión."

## Notes

- This only updates the framework. It does NOT re-run `amauta`,
  `kuraka-inspect`, or regenerate `kuraka.config.yaml`.
- The vault path is portable via `$KURAKA_VAULT`. If the script reports the
  vault is not found, export `KURAKA_VAULT` to the right path (and add it to
  `~/.zshrc`). The same variable is honored by `mount-kuraka.sh` and the
  shell alias, so set it once per machine.
