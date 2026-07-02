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

# --- premium banner --------------------------------------------------------

banner() {
    local d="" reset=""
    [ -t 1 ] && [ -z "${NO_COLOR:-}" ] && { d=$'\033[38;5;242m'; reset=$'\033[0m'; }
    printf '%s\n' ""
    # Kuraka shaman as terminal art: full-color ANSI (TTY+color) → ASCII fallback.
    if [ -t 1 ] && [ -z "${NO_COLOR:-}" ] && [ -f "$VAULT/assets/kuraka-banner.ans" ]; then
        cat "$VAULT/assets/kuraka-banner.ans"
    elif [ -f "$VAULT/assets/kuraka-banner.txt" ]; then
        printf '%s' "$d"; cat "$VAULT/assets/kuraka-banner.txt"; printf '%s' "$reset"
    else
        # last-resort block-letter wordmark (asset missing)
        local c=""; [ -n "$d" ] && c=$'\033[38;5;214m'
        printf '%s   ██╗  ██╗██╗   ██╗██████╗  █████╗ ██╗  ██╗ █████╗ %s\n' "$c" "$reset"
        printf '%s   █████╔╝ ██║   ██║██████╔╝███████║█████╔╝ ███████║%s\n' "$c" "$reset"
        printf '%s   ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝%s\n' "$c" "$reset"
    fi
    printf '%s        🪢  KURAKA · «el mayor» · framework multi-agente%s\n' "$d" "$reset"
    printf '%s\n' ""
}

banner
echo "   vault:  $VAULT"
echo "   target: $TARGET"
echo ""

cd "$TARGET"
mkdir -p ".claude"

# --- interactive menu (TTY only; agents/CI keep the mount-everything default) ---
# SELECTED gates which categories get synced. want() is the predicate used below.
SELECTED="agents skills commands rules artifacts"
MENU_MODE="all"
want() { case " $SELECTED " in *" $1 "*) return 0 ;; *) return 1 ;; esac; }

if [ -t 0 ]; then
    # --- estado actual: ¿ya montado? ¿hay historia guardada en el vault? ---
    if [ -d ".claude/agents" ]; then
        echo "ℹ️  Kuraka YA está montado en este proyecto → esto es un re-mount (update)."
    else
        echo "🆕 Primer montaje de Kuraka en este proyecto."
    fi
    if [ -f "$VAULT/kuraka-restore.py" ]; then
        _hist="$(python3 "$VAULT/kuraka-restore.py" "$TARGET" --check 2>/dev/null | grep 'historia en central' || true)"
        if [ -n "$_hist" ]; then
            echo "   📦 El vault guarda historia de este proyecto: ${_hist#*central: }"
            echo "      → al terminar el montaje se te preguntará si restaurarla para continuar el trabajo."
        fi
    fi
    echo ""
    echo "¿Qué querés montar?"
    echo "   [Enter] todo   ·   c) elegir categorías   ·   s) solo ver estado (sin montar)"
    printf "   > "
    read -r _choice || _choice=""
    case "$_choice" in
        c|C)
            echo "   Categorías: agents  skills  commands  rules  artifacts"
            printf "   Ingresá las que querés (separadas por espacio) [todo]: "
            read -r _sel || _sel=""
            [ -n "$_sel" ] && SELECTED="$_sel"
            echo ""
            ;;
        s|S)
            MENU_MODE="status"
            ;;
    esac
fi

# --- MCP + component detection (interactive only; single source of truth) ---
if [ -t 0 ] && [ -f "$VAULT/kuraka-init.py" ]; then
    python3 "$VAULT/kuraka-init.py" --recommend-only --target "$TARGET" 2>/dev/null || true
fi

# 'solo ver estado' → detection already shown; stop before touching anything.
if [ "$MENU_MODE" = "status" ]; then
    echo "ℹ️  Modo 'solo estado' — no se montó nada."
    exit 0
fi

# --- pre-flight: snapshot any local agent/skill/command tuning BEFORE the vault
# rsync overwrites it, so a re-mount never loses project-specific overrides.
# Best-effort; never fails the mount. Skipped on a first-ever mount (no .claude/agents).
if [ -d ".claude/agents" ] && [ -f "$VAULT/kuraka-backup.py" ]; then
    if python3 "$VAULT/kuraka-backup.py" "$TARGET" --overrides-only >/dev/null 2>&1; then
        echo "   ✓ overrides locales respaldados al store central (pre-mount)"
        echo ""
    fi
fi

# --- sync personal categories ---

SYNCED_AGENTS=0
for category in agents skills commands hooks; do
    # hooks ship together with agents; everything else maps to its own menu category
    wcat="$category"; [ "$category" = "hooks" ] && wcat="agents"
    want "$wcat" || continue
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

if want agents && [ -d "$VAULT/agents/contexts" ]; then
    mkdir -p ".claude/agents/contexts"
    rsync -a --update "$VAULT/agents/contexts/" ".claude/agents/contexts/"
    echo "   ✓ agents/contexts/"
fi

# --- sync personal rules (meta-rules of the agent system) ---

if want rules; then
mkdir -p ".claude/rules"
for rule in 16-agent-backup.md 17-kuraka-token-optimizations.md; do
    src="$VAULT/rules/$rule"
    if [ -f "$src" ]; then
        cp "$src" ".claude/rules/$rule"
        echo "   ✓ rules/$rule"
    fi
done
fi  # want rules

# --- restore Kuraka artifacts outside .claude/ (framework-level assets) ---

ARTIFACTS_SRC="$VAULT/kuraka-artifacts"
if want artifacts && [ -d "$ARTIFACTS_SRC" ]; then
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

# --- re-apply project-specific overrides on top of the fresh vault copy ---
# ALWAYS runs (TTY or not): overrides are the project's own agent/skill/command
# tunings; the vault rsync just overwrote them, so re-applying is the whole point.
# Safe + idempotent (only touches files present in the central override store).
# Decoupled from the layer/state restore prompt below, which stays TTY-gated.
if [ -f "$VAULT/kuraka-restore.py" ]; then
    python3 "$VAULT/kuraka-restore.py" "$TARGET" --overrides-only 2>/dev/null || true
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

# --- auto-register in the vault registry (best-effort; never fail the mount on this) ---
# Runs BEFORE the adoption check so the registry reflects this mount, and before
# restore so the slug is resolved consistently.
if [ -f "$VAULT/kuraka-init.py" ]; then
    if python3 "$VAULT/kuraka-init.py" --target "$TARGET" --register-only --yes >/dev/null 2>&1; then
        echo "   ✓ registrado en el registro del vault (projects/)"
        echo ""
    fi
fi

# --- offer to restore Kuraka history (branch-switch recovery) ---
# If the central store has history for this project (worked on another branch and
# not committed to the solution's git), offer to paste it back. Never overwrites
# existing files. Safe no-op when there's no history. Runs BEFORE the adoption
# check below so a successful restore (which repopulates .claude/project/) clears
# the warning instead of firing it spuriously.
if [ -f "$VAULT/kuraka-restore.py" ]; then
    if [ -t 0 ]; then
        # real terminal → interactive prompt
        python3 "$VAULT/kuraka-restore.py" "$TARGET" || true
    else
        # non-interactive (e.g. run by an agent / CI) → report only, never block
        python3 "$VAULT/kuraka-restore.py" "$TARGET" --check || true
        echo "   ℹ️  Para restaurar la historia (si la hay):"
        echo "      python3 \"$VAULT/kuraka-restore.py\" \"$TARGET\"   # pregunta antes de pegar"
    fi
    echo ""
fi

# --- auto-seed from a pre-populated migration-example layer (first-time adoption) ---
# Runs AFTER restore (the project's own accumulated history always wins) and only
# fills what is STILL missing. The seed dir is matched by the target's folder name,
# so it only ever fires for a folder literally named like its
# migration-examples/<name>-project-layer/ (today: sie_v2). NEVER overwrites — an
# existing config or .claude/project/ is left untouched, so re-runs and every other
# project are safe no-ops.
SEED_SRC="$VAULT/kuraka-artifacts/migration-examples/$(basename "$TARGET")-project-layer"
if [ -d "$SEED_SRC" ]; then
    seeded=0
    if [ ! -f "$TARGET/kuraka.config.yaml" ] && [ -f "$SEED_SRC/kuraka.config.yaml" ]; then
        cp "$SEED_SRC/kuraka.config.yaml" "$TARGET/kuraka.config.yaml"
        echo "   ✓ kuraka.config.yaml sembrado (migration-examples/$(basename "$TARGET")-project-layer → raíz)"
        seeded=1
    fi
    if [ ! -d "$TARGET/.claude/project" ]; then
        mkdir -p "$TARGET/.claude/project"
        rsync -a --exclude 'kuraka.config.yaml' --exclude 'README.md' "$SEED_SRC/" "$TARGET/.claude/project/"
        echo "   ✓ .claude/project/ sembrado (migration-examples/$(basename "$TARGET")-project-layer)"
        seeded=1
    fi
    [ "$seeded" = "1" ] && echo ""
fi

# --- pre-flight check: kuraka.config.yaml + .claude/project/ ---
# Evaluated AFTER auto-register + restore + auto-seed, so it reflects what those
# steps brought back (restore repopulating on a fresh branch, or a seed completing
# first-time adoption). Only fires when adoption is genuinely still incomplete.
HAS_CONFIG=0
HAS_PROJECT=0
[ -f "$TARGET/kuraka.config.yaml" ] && HAS_CONFIG=1
[ -d "$TARGET/.claude/project" ] && HAS_PROJECT=1

# Pre-populated layer for this project (e.g. the sie_v2 reference), matched by the
# target's folder name. When present we seed from it instead of the generic schema.
LAYER_SRC="$VAULT/kuraka-artifacts/migration-examples/$(basename "$TARGET")-project-layer"

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
    if [ -d "$LAYER_SRC" ]; then
        # this project has a pre-populated layer → seed config to ROOT, layer to .claude/project
        echo "     SRC=\"\$KURAKA_VAULT/kuraka-artifacts/migration-examples/$(basename "$TARGET")-project-layer\""
        [ "$HAS_CONFIG" = "0" ] && \
            echo "     cp \"\$SRC/kuraka.config.yaml\" ./kuraka.config.yaml   # config pre-rellenado → RAÍZ del repo"
        if [ "$HAS_PROJECT" = "0" ]; then
            echo "     mkdir -p .claude/project"
            echo "     rsync -a --exclude kuraka.config.yaml --exclude README.md \"\$SRC/.\" .claude/project/"
        fi
    else
        # no pre-populated layer → start from the generic schema, fill in by hand
        if [ "$HAS_CONFIG" = "0" ]; then
            echo "     cp \"\$KURAKA_VAULT/kuraka-artifacts/config-schema.yaml\" ./kuraka.config.yaml"
            echo "     # editá kuraka.config.yaml con los valores reales del proyecto"
        fi
        if [ "$HAS_PROJECT" = "0" ]; then
            echo "     mkdir -p .claude/project"
            echo "     # creá los archivos del layer a medida (ver kuraka-artifacts/migration-examples/README.md)"
        fi
    fi
    echo ""
fi

# --- catálogo de comandos + guía de inicio (fuente única: kuraka-export.py) ---
if [ -f "$VAULT/kuraka-export.py" ]; then
    python3 "$VAULT/kuraka-export.py" --catalog "$TARGET/.claude/commands" --env claude "$TARGET" 2>/dev/null || true
fi

echo "📋 NOTAS DEL MONTAJE:"
echo ""
echo "  • Unstage cualquier fichero personal ya indexado en git:"
echo "     git restore --staged .claude/agents/ .claude/skills/ .claude/commands/ .claude/hooks/ 2>/dev/null || true"
echo "     git restore --staged .claude/rules/16-agent-backup.md .claude/rules/17-kuraka-token-optimizations.md 2>/dev/null || true"
echo ""
if [ "$SYNCED_AGENTS" = "1" ]; then
    echo "  • ⚠️  Reinicia Claude Code (/exit + nueva sesión) para registrar los agentes"
    echo "     como subagent_type — el runtime lee .claude/agents/ solo al arrancar."
else
    echo "  • Agentes ya presentes y sincronizados. No hace falta reiniciar."
fi
echo ""
echo "  • (Recomendado) Componentes que potencian Kuraka:"
echo "     $VAULT/RECOMMENDED-COMPONENTS.md"
echo "     → RTK (ahorro 70-90% de tokens), ui-ux-pro-max, Playwright MCP..."
echo ""
