# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

This is **not** an application codebase. It is the **Kuraka framework vault** — the
source-of-truth for a portable multi-agent system that mounts into any other project via
`mount-kuraka.sh`. The repo contains agent definitions, skill prompts, meta-rules,
two inspection/telemetry scripts, and a pytest-based structural eval harness.

"Kuraka" (Quechua *kuraq* = "el mayor") is the orchestrator skill (`skills/kuraka.md`)
that coordinates 16 subagents across an 8-phase dev lifecycle.

## Commands

```bash
# One-shot initializer (RECOMMENDED entry point). Runs inspect → draft config →
# project skeleton → mount → registry, in one command, from anywhere. The only manual
# step left is restarting Claude Code in the target. Interactive or flag-driven (the
# future control-plane web app wraps this). Never overwrites an existing config/layer.
python3 kuraka-init.py [target_dir]                  # or: --target ... --name ... --yes
python3 kuraka-init.py --target /path --name foo --yes --no-mount
python3 kuraka-init.py --target /path --register-only --yes   # only upsert the registry note

# Discover ALL Kuraka-mounted projects on disk and reconcile the registry (both ways:
# mounted-but-unregistered, and registered-but-not-mounted). mount-kuraka.sh now also
# auto-registers, so new mounts never drift. Read-only without --register.
python3 kuraka-discover.py [--register] [--roots ~/Desarrollos,~/work]

# Mount the vault into a consumer project (copies agents/skills/rules/artifacts into
# .claude/ and updates .gitignore of the target). Always run in the target repo root.
# (kuraka-init.py calls this for you; use directly only for a re-mount.)
bash mount-kuraka.sh [target_dir]            # default target is $PWD

# Validate frontmatter + registration readiness of a mounted .claude/
bash validate-kuraka.sh [target_dir]         # exit 1 if any agent/skill FM is invalid

# Stack detector (used by the amauta brownfield agent and ad-hoc)
python3 kuraka-inspect.py [target_dir]       # JSON to stdout, summary to stderr

# Aggregated telemetry dashboard across cycles
python3 aggregate-telemetry.py [project_root]  # writes docs/process/agent-telemetry/DASHBOARD.md

# Back up a project's FULL Kuraka state into the vault's unified store. Snapshots
# layer/ (.claude/project), state/docs-process/ (REQ, stories, schemas, checkpoints)
# and cycles/<REQ>/ (RETRO + telemetry + meta, branch-tagged). Run at Phase 7 (the
# final-auditor calls it). Idempotent. Feeds cross-project pattern-detection AND
# preserves Kuraka work outside the solution's git.
python3 kuraka-backup.py [project_root]         # writes projects/<slug>/{layer,state,cycles}/
python3 kuraka-archive.py [project_root]        # cycles-only (backward-compat wrapper)

# Restore a project's Kuraka history from the vault on branch switch / re-mount.
# mount-kuraka.sh calls this and ASKS before pasting; never overwrites without --force.
python3 kuraka-restore.py [project_root]        # central → project (layer/ + state/)

# Structural eval harness (runs from a consumer project that has mounted the artifacts)
cd <target-project> && python3 -m pytest tests/kuraka/ -v
# A single test:
python3 -m pytest tests/kuraka/test_structure.py::test_should_have_valid_frontmatter -v
```

There is no build system, linter, or package manager here. All scripts are POSIX shell
or standalone Python 3 (no dependencies).

## Architecture — what lives where, and why

### The vault layout mirrors `.claude/` in consumer projects

| Here (vault)              | Mounted to (project)              | Role                                      |
|---------------------------|-----------------------------------|-------------------------------------------|
| `agents/*.md`             | `.claude/agents/`                 | Subagent definitions (16)                 |
| `agents/contexts/*.md`    | `.claude/agents/contexts/`        | Per-agent rule bundles and output schemas |
| `skills/*.md`             | `.claude/skills/`                 | Skill prompts (phase-level)               |
| `commands/*.md`           | `.claude/commands/`               | Slash-command executable prompts          |
| `rules/16-*.md`, `17-*.md`, `18-*.md` | `.claude/rules/`           | Framework meta-rules (only these)         |
| `kuraka-artifacts/docs/process/**`    | `docs/process/**`           | lessons-learned + telemetry dashboard template |
| `kuraka-artifacts/tests/kuraka/**`    | `tests/kuraka/**`           | Structural eval harness                   |

Consumer projects pull **from** this vault (read-only for the vault during `mount-kuraka`),
but their `.claude/` may be synced **back** to the vault by the hook in
`scripts/sync-obsidian.sh`. That script has an 80%-of-vault safety guard per category:
if the consumer's `.claude/` is incomplete (e.g. just after `git switch`), it aborts
that category's sync rather than wiping the vault.

### Wikilinks vs backticks — critical when editing

The vault stores agent/skill cross-references as Obsidian wikilinks (`[[po-analyst]]`)
so the graph view works. Claude Code at runtime expects backticks (`` `po-analyst` ``).
Conversion happens in both directions:

- **Vault → project**: `mount-kuraka.sh` and `00-RESTAURAR-PROYECTO.md`'s one-liner
  convert `[[name]]` → `` `name` `` when copying into `.claude/agents|skills|rules`.
- **Project → vault**: `scripts/sync-obsidian.sh` converts `` `name` `` → `[[name]]`
  via a `sed` expression built from the hardcoded `AGENTS=()` and `SKILLS=()` arrays
  near the top of that script.

**When you edit here**: keep wikilinks in `agents/`, `agents/contexts/`, `skills/`, and
`rules/` content. `commands/*.md` is copied **verbatim** in both directions — never
use wikilinks in those files; they would break grep patterns in the executable prompts.

**When you rename or add an agent/skill**: update the `AGENTS=()` / `SKILLS=()` array
in `scripts/sync-obsidian.sh` or the reverse conversion breaks silently.

### Agent frontmatter contract

Every `agents/*.md` must have `name` + `description` + `model` (one of `opus | sonnet |
haiku`), and the frontmatter `name` must equal the filename stem. Every `skills/*.md`
needs `name` + `description`. `validate-kuraka.sh` enforces this; CI-style usage is to
run it in the target project after mounting.

Model routing convention: **opus** for judgment-heavy agents (po-analyst, code-reviewer,
security-reviewer, architect-reviewer, final-auditor), **sonnet** for
implementation/balanced work, **haiku** for mechanical tasks.

### The orchestrator workflow

`skills/kuraka.md` is the main workflow. `kuraka-modes.md` and `kuraka-policies.md`
are companions — modes (Bootstrap/Brownfield/Normal/Lite/Retroactive/Reduced),
and cross-cutting policies (retry, timeout, token budgets, checkpointing, telemetry).
Per-phase skills live in `skills/<verb>-<object>.md` (`analyze-requirement`,
`implement-story`, etc.).

Token budgets in `aggregate-telemetry.py` (the `BUDGETS` dict) must stay in sync with
`kuraka-policies.md` and `rules/17-kuraka-token-optimizations.md`. These three places
are the only authoritative source of per-agent targets.

**Hard invariant** (enforced in `skills/kuraka.md` §Orchestrator constraint): the
orchestrator never writes to `backend/`, `frontend/`, `tests/`, or `migrations/` in a
consumer project before Phase 4 — all implementation must route through
`backend-developer` or `frontend-developer`. Editing `docs/`, `.claude/agents/`,
`.claude/skills/`, `.claude/rules/` is the only legitimate exception.

## Repo-specific gotchas

### `/docs/` and `/documentacion-backend/` are gitignored mirrors

Both top-level `/docs/` and `/documentacion-backend/` are **gitignored mirrors of
sie_v2 project docs**, not part of the framework. See `.gitignore` comments. Never
edit these assuming they ship with the framework — they don't. The framework's own
docs live inside `kuraka-artifacts/docs/` (note: `kuraka-artifacts/` is tracked).

### `rules/01-*.md` through `rules/15-*.md` are also gitignored

Those are sie_v2 team conventions that live in *that* project's git, not here. Only
`rules/16-agent-backup.md`, `17-kuraka-token-optimizations.md`, and
`18-duplication-aware-refactor.md` are framework rules tracked by this repo. If you
need to edit a rule in the 01–15 range, you are in the wrong repository.

### The `VAULT=` path is hardcoded in three places

`mount-kuraka.sh`, `scripts/sync-obsidian.sh`, and the `00-RESTAURAR-PROYECTO.md`
one-liner all hardcode `/Users/xmn/Documents/Agentes/AgentesTrabajos/kuraka`. If the
vault is ever relocated, update all three (plus the alias block in
`dotfiles/zshrc-alias.md`).

### Branch switch workflow in consumer projects

`01-CAMBIO-DE-RAMA.md` is the canonical procedure. Summary: after `git switch` in the
consumer project, run `mount-kuraka` and then `/exit` + new Claude Code session —
subagents are registered at session start only.

## Docs that matter

- `README.md` — user-facing overview
- `00-RESTAURAR-PROYECTO.md` — legacy one-liner restore (alternative to `mount-kuraka.sh`)
- `01-CAMBIO-DE-RAMA.md` — branch-switch playbook for consumer projects
- `dotfiles/zshrc-alias.md` — alias/function to install in `~/.zshrc`
- `kuraka-artifacts/tests/kuraka/README.md` — what the eval harness does **not** test
  (no LLM invocation, no perf, no dynamic behavior — only structure/contracts)
