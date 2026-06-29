---
description: "Snapshot THIS project's full Kuraka state into the central vault store (unified scheme: projects/<slug>/{layer,state,cycles}). Run it after /kuraka-update to accommodate the project into the new scheme, and any time you want to preserve Kuraka work outside the solution's git. Portable via $KURAKA_VAULT. Idempotent; copies only (never moves)."
---

# Task: Back up this project's Kuraka state into the central store

Snapshot everything Kuraka has produced in THIS project into the vault's unified
store, so it (a) survives solution branch switches (it lives outside the solution's
git) and (b) feeds cross-project pattern-detection.

This is the **"accommodate into the new scheme"** step: run it once right after
`/kuraka-update` to migrate the project into the unified layout, and routinely
thereafter (Phase 7's final-auditor also runs it automatically at cycle close).

What it snapshots into `<vault>/projects/<slug>/`:
- `layer/` — the project's `.claude/project/` specialization (conventions,
  lessons-learned, review-checks, agent appends),
- `state/docs-process/` — `docs/process/**` (REQ, stories, test-plans, schemas,
  checkpoints — the in-flight Kuraka work),
- `cycles/<REQ>/` — closed-cycle diagnostics (RETRO + telemetry + meta, branch-tagged),
and appends new cycles to `projects/INDEX.md`. The slug is the project's
`kuraka.config.yaml` `project.name` (one canonical slug everywhere).

## Steps

### 1. Resolve the vault, find the project root, and back up

Run this block exactly. It resolves the vault from `$KURAKA_VAULT` (portable),
walks up from the current directory to the project root that contains `.claude/`,
and snapshots it into the store:

```bash
# --- portable vault resolution (env var first, fallback second) ---
VAULT="${KURAKA_VAULT:-/Users/xmn/Documents/Agentes/AgentesTrabajos/kuraka}"
if [ ! -d "$VAULT" ]; then
  echo "❌ Vault no encontrado en: $VAULT"
  echo "     export KURAKA_VAULT=\"/ruta/a/kuraka\"   # añádelo a ~/.zshrc"
  exit 1
fi

# --- find project root = nearest ancestor (incl. $PWD) containing .claude/ ---
DIR="$PWD"
while [ "$DIR" != "/" ] && [ ! -d "$DIR/.claude" ]; do DIR="$(dirname "$DIR")"; done
if [ ! -d "$DIR/.claude" ]; then
  echo "❌ No hay un proyecto con .claude/ desde: $PWD"
  exit 1
fi
PROJECT_ROOT="$DIR"

echo "🪢 vault:    $VAULT"
echo "🪢 proyecto: $PROJECT_ROOT"
echo ""

# --- snapshot the project's full Kuraka state into the unified central store ---
python3 "$VAULT/kuraka-backup.py" "$PROJECT_ROOT"
```

### 2. Report what landed

Summarize the script output: how many files in `layer/` and `state/`, how many
cycles archived, and the branch it was tagged with. Confirm the destination
`projects/<slug>/` and that the command exited 0.

### 3. (Optional) Confirm the store

```bash
VAULT="${KURAKA_VAULT:-/Users/xmn/Documents/Agentes/AgentesTrabajos/kuraka}"
# replace <slug> with the project.name reported above
ls -R "$VAULT/projects/<slug>" | head -40
```

## Notes

- **Idempotent**: cycles already archived are skipped (`--force` re-copies); layer/
  state are re-snapshotted (overwrite with the current project content).
- **Inverse op**: `kuraka-restore.py` (run automatically by `mount-kuraka.sh` on
  branch switch) pastes `layer/` + `state/` back into the project, asking first and
  never overwriting existing files without `--force`.
- **Git policy**: the central store is filesystem-only (gitignored in the vault);
  it is not pushed with the vault. Its job is to survive solution branch switches.
- The vault path is portable via `$KURAKA_VAULT` — set it once per machine.
