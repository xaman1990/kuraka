#!/bin/bash
# mount-kuraka.sh — Mount personal Kuraka agent system from Obsidian vault into current repo.
#
# Usage (from any repo root):
#   bash /path/to/vault/mount-kuraka.sh [target_dir]
#   # or with alias:
#   mount-kuraka [target_dir]
#
# If no target_dir given, uses $PWD.
#
# What it does:
#   1. Detects/creates .claude/ in the target
#   2. Rsyncs personal categories (agents, skills, commands, hooks, personal rules)
#      from the Obsidian vault
#   3. Ensures .gitignore excludes the personal dirs (so they never get committed)
#   4. Prints next steps (reinicio de Claude Code necesario)

set -euo pipefail

VAULT="${KURAKA_VAULT:-/Users/xmn/Documents/Agentes/AgentesTrabajos/kuraka}"
TARGET="${1:-$PWD}"

# --- sanity checks ---

if [ ! -d "$VAULT" ]; then
    echo "❌ ERROR: vault no encontrado en $VAULT" >&2
    exit 1
fi

if [ ! -d "$TARGET" ]; then
    echo "❌ ERROR: target no existe: $TARGET" >&2
    exit 1
fi

echo "🪢 Kuraka — montando desde vault"
echo "   vault:  $VAULT"
echo "   target: $TARGET"
echo ""

cd "$TARGET"
mkdir -p ".claude"

# --- sync personal categories ---

SYNCED_AGENTS=0
for category in agents skills commands hooks; do
    src="$VAULT/$category"
    dst=".claude/$category"
    if [ -d "$src" ]; then
        mkdir -p "$dst"
        count_before=$(find "$dst" -maxdepth 1 -name "*.md" -o -name "*.sh" 2>/dev/null | wc -l | tr -d ' ')
        # *.append.md are project-layer rule fragments (e.g. sie_v2 DD-1031), not
        # framework agents — they have no frontmatter and must never be mounted as agents.
        rsync -a --update --exclude='*.append.md' "$src/" "$dst/"
        count_after=$(find "$dst" -maxdepth 1 -name "*.md" -o -name "*.sh" 2>/dev/null | wc -l | tr -d ' ')
        delta=$((count_after - count_before))
        if [ "$delta" -gt 0 ]; then
            echo "   + $category/  ($delta new, $count_after total)"
            [ "$category" = "agents" ] && SYNCED_AGENTS=1
        else
            echo "   ✓ $category/  (up to date, $count_after total)"
        fi
    fi
done

# --- sync contexts sub-directory ---

if [ -d "$VAULT/agents/contexts" ]; then
    mkdir -p ".claude/agents/contexts"
    rsync -a --update "$VAULT/agents/contexts/" ".claude/agents/contexts/"
    echo "   ✓ agents/contexts/"
fi

# --- sync personal rules (meta-rules of the agent system) ---

mkdir -p ".claude/rules"
for rule in 16-agent-backup.md 17-kuraka-token-optimizations.md; do
    src="$VAULT/rules/$rule"
    if [ -f "$src" ]; then
        cp "$src" ".claude/rules/$rule"
        echo "   ✓ rules/$rule"
    fi
done

# --- restore Kuraka artifacts outside .claude/ (framework-level assets) ---

ARTIFACTS_SRC="$VAULT/kuraka-artifacts"
if [ -d "$ARTIFACTS_SRC" ]; then
    echo ""
    echo "[mount-kuraka] restoring Kuraka artifacts..."

    # docs/process/lessons-learned.md
    if [ -f "$ARTIFACTS_SRC/docs/process/lessons-learned.md" ]; then
        mkdir -p "docs/process"
        cp "$ARTIFACTS_SRC/docs/process/lessons-learned.md" "docs/process/"
        echo "   ✓ docs/process/lessons-learned.md"
    fi

    # docs/process/agent-telemetry/DASHBOARD.md (template; per-cycle JSONs stay project-local)
    if [ -f "$ARTIFACTS_SRC/docs/process/agent-telemetry/DASHBOARD.md" ]; then
        mkdir -p "docs/process/agent-telemetry"
        cp "$ARTIFACTS_SRC/docs/process/agent-telemetry/DASHBOARD.md" "docs/process/agent-telemetry/"
        echo "   ✓ docs/process/agent-telemetry/DASHBOARD.md"
    fi

    # tests/kuraka/ — the eval harness
    if [ -d "$ARTIFACTS_SRC/tests/kuraka" ]; then
        mkdir -p "tests/kuraka"
        rsync -a --update \
            --exclude='.pytest_cache' --exclude='__pycache__' \
            "$ARTIFACTS_SRC/tests/kuraka/" "tests/kuraka/"
        echo "   ✓ tests/kuraka/"
    fi

    # stack-profiles/ — framework-supplied per-stack guidance (read by agents)
    if [ -d "$ARTIFACTS_SRC/stack-profiles" ]; then
        mkdir -p ".claude/stack-profiles"
        rsync -a --update "$ARTIFACTS_SRC/stack-profiles/" ".claude/stack-profiles/"
        echo "   ✓ stack-profiles/"
    fi

    # templates/ — framework-supplied templates (e.g. design-brief,
    # domain-expert for the Discovery/Tinkuy flow; read by the orchestrator)
    if [ -d "$ARTIFACTS_SRC/templates" ]; then
        mkdir -p ".claude/templates"
        rsync -a --update "$ARTIFACTS_SRC/templates/" ".claude/templates/"
        echo "   ✓ templates/"
    fi
fi

# --- ensure .gitignore excludes personal content ---

GITIGNORE=".gitignore"
touch "$GITIGNORE"

PATTERNS=(
    "# Kuraka framework files (versioned externally; not source of this repo)"
    ".claude/agents/"
    ".claude/skills/"
    ".claude/commands/"
    ".claude/hooks/"
    ".claude/rules/16-agent-backup.md"
    ".claude/rules/17-kuraka-token-optimizations.md"
    "# Per-cycle telemetry JSONs (noise; the consolidated DASHBOARD.md is tracked)"
    "docs/process/agent-telemetry/*.json"
)

ADDED=0
NEEDS_HEADER=0
for pattern in "${PATTERNS[@]}"; do
    if ! grep -Fqx "$pattern" "$GITIGNORE" 2>/dev/null; then
        if [ "$NEEDS_HEADER" = "0" ] && [[ "$pattern" != \#* ]]; then
            NEEDS_HEADER=1
        fi
        echo "$pattern" >> "$GITIGNORE"
        ADDED=$((ADDED + 1))
    fi
done

if [ "$ADDED" -gt 0 ]; then
    echo ""
    echo "   + $ADDED entradas añadidas a .gitignore"
fi

# --- final summary + instructions ---

echo ""
echo "✅ Kuraka montado en $TARGET/.claude/"
echo ""

# --- pre-flight check: kuraka.config.yaml + .claude/project/ ---
HAS_CONFIG=0
HAS_PROJECT=0
[ -f "$TARGET/kuraka.config.yaml" ] && HAS_CONFIG=1
[ -d "$TARGET/.claude/project" ] && HAS_PROJECT=1

if [ "$HAS_CONFIG" = "0" ] || [ "$HAS_PROJECT" = "0" ]; then
    echo "⚠️  ATENCIÓN — ADOPCIÓN INCOMPLETA"
    echo ""
    [ "$HAS_CONFIG" = "0" ] && \
        echo "   ❌ kuraka.config.yaml NO existe en el proyecto."
    [ "$HAS_PROJECT" = "0" ] && \
        echo "   ❌ .claude/project/ NO existe en el proyecto."
    echo ""
    echo "   Los agentes refactorizados (v0.3+) leen kuraka.config.yaml para"
    echo "   paths y comandos, y .claude/project/ para convenciones y lecciones."
    echo "   Sin esos dos artefactos, los agentes van a fallar o degradar a"
    echo "   guidance genérico."
    echo ""
    echo "   Para completar la adopción:"
    echo ""
    echo "     export KURAKA_VAULT=\"$VAULT\""
    if [ "$HAS_CONFIG" = "0" ]; then
        echo "     cp \"\$KURAKA_VAULT/kuraka-artifacts/config-schema.yaml\" ./kuraka.config.yaml"
        echo "     # editar kuraka.config.yaml con valores reales del proyecto"
    fi
    if [ "$HAS_PROJECT" = "0" ]; then
        echo "     mkdir -p .claude/project"
        echo "     # si este proyecto es sie_v2, copiar el layer pre-poblado:"
        echo "     cp -r \"\$KURAKA_VAULT/kuraka-artifacts/migration-examples/sie_v2-project-layer/.\" .claude/project/"
        echo "     # si es otro proyecto, crear archivos a medida (ver README de migration-examples)"
    fi
    echo ""
fi

echo "📋 PASOS SIGUIENTES:"
echo ""
echo "  1. Unstage cualquier fichero personal ya indexado en git:"
echo "     git restore --staged .claude/agents/ .claude/skills/ .claude/commands/ .claude/hooks/ 2>/dev/null || true"
echo "     git restore --staged .claude/rules/16-agent-backup.md .claude/rules/17-kuraka-token-optimizations.md 2>/dev/null || true"
echo ""

if [ "$SYNCED_AGENTS" = "1" ]; then
    echo "  2. ⚠️  Reinicia Claude Code (/exit + nueva sesión) para que registre los"
    echo "     agentes como subagent_type. El runtime solo lee .claude/agents/ al"
    echo "     arrancar la sesión."
else
    echo "  2. Agentes ya presentes y sincronizados. No hace falta reiniciar."
fi
echo ""
echo "  3. Invoca el Kuraka cuando empieces un requerimiento:"
echo "     /kuraka o referencia skills/kuraka.md en el chat"
echo ""
