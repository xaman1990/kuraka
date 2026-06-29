---
description: "Map an existing (brownfield) project: run kuraka-inspect if needed, then invoke the amauta agent to generate kuraka.config.yaml + the .claude/project/ layer by extracting conventions from the real code (never inventing). Use once, after mounting Kuraka into a project that has code but no config."
---

# Task: Map this brownfield project with amauta

Onboard Kuraka into an **existing** codebase by generating the two
artifacts the agents need — `kuraka.config.yaml` and `.claude/project/` —
extracted from the real code, not invented.

**Portability**: vault is read from `$KURAKA_VAULT` (fallback to the
author's default). Project root is auto-detected via `.claude/`.

## Step 1 — Ensure the inspect report exists

Run this block. It resolves the vault, finds the project root, and runs
`kuraka-inspect.py` only if `inspect-report.json` is missing:

```bash
VAULT="${KURAKA_VAULT:-/Users/xmn/Documents/Agentes/AgentesTrabajos/kuraka}"
if [ ! -d "$VAULT" ]; then
  echo "❌ Vault no encontrado en: $VAULT — export KURAKA_VAULT=\"/ruta/a/kuraka\""; exit 1
fi
DIR="$PWD"; while [ "$DIR" != "/" ] && [ ! -d "$DIR/.claude" ]; do DIR="$(dirname "$DIR")"; done
if [ ! -d "$DIR/.claude" ]; then
  echo "❌ No hay un proyecto con .claude/ desde: $PWD — monta Kuraka primero (/kuraka-update o mount-kuraka.sh)"; exit 1
fi
PROJECT_ROOT="$DIR"
echo "🪢 vault:    $VAULT"
echo "🪢 proyecto: $PROJECT_ROOT"
if [ -f "$PROJECT_ROOT/inspect-report.json" ]; then
  echo "✓ inspect-report.json ya existe — se reutiliza"
else
  echo "→ generando inspect-report.json…"
  python3 "$VAULT/kuraka-inspect.py" "$PROJECT_ROOT" > "$PROJECT_ROOT/inspect-report.json"
  echo "✓ inspect-report.json generado"
fi
```

If `kuraka.config.yaml` ALREADY exists in the project root, STOP and tell
the user — this project is already mapped; re-running amauta would
regenerate config. Ask before overwriting.

## Step 2 — Invoke the amauta agent

Invoke the **`amauta`** subagent (Task tool, `subagent_type: amauta`) with
these instructions:

> Read `inspect-report.json` at the project root and sample the real code.
> Generate `kuraka.config.yaml` + the `.claude/project/` specialization
> layer + the `docs/` skeleton, extracting conventions from the codebase.
> Golden rule: **never invent conventions** — if you didn't see it in the
> code, mark it `<TODO: confirm with team>`. Present the convention matrix
> and the list of TODOs for my approval before finalizing.

If the Task call fails because `amauta` is not a known subagent, the
agents aren't registered yet: tell the user to restart Claude Code
(`/exit` + new session) and run `/amauta` again — subagents register only
at session start.

## Step 3 — Relay amauta's report

Present amauta's summary (stack detected, files created, convention
confidence, TODOs, anti-patterns) and the approval question. Do NOT mark
the project ready until the user resolves the `<TODO>` markers.

## Notes

- Run this **once per project**. For incremental work afterward, use
  `/kuraka` (Normal mode) or Discovery for a fuzzy new idea.
- This does not write business code — only config, project layer, docs.
