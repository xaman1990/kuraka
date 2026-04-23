---
description: Rule for mirroring agents, skills, commands and project docs to the shared AgentesTrabajos Obsidian vault
alwaysApply: true
---

# Agent, Skills & Docs Backup Rule

## Backup Location

All agent definitions, skills, commands and project documentation must be
mirrored to the central Obsidian vault:

```
/Users/xmn/Documents/Agentes/AgentesTrabajos/sie_integraciones/
```

This directory is the single source of truth shared across projects and is
also the backing store for the Obsidian graph view.

## Directory Mapping

| Source (project) | Backup |
|-----------------|--------|
| `sie_v2/.claude/agents/*.md` | `AgentesTrabajos/sie_integraciones/agents/` |
| `sie_v2/.claude/skills/*.md` | `AgentesTrabajos/sie_integraciones/skills/` |
| `sie_v2/.claude/commands/*.md` | `AgentesTrabajos/sie_integraciones/commands/` |
| `sie_v2/docs/**` (recursive) | `AgentesTrabajos/sie_integraciones/docs/` |
| `sie_v2/backend/documentacion/**` (recursive) | `AgentesTrabajos/sie_integraciones/documentacion-backend/` |

The `docs/` and `documentacion-backend/` trees preserve the original folder
hierarchy so wiki-links resolve in Obsidian. Only `.md`, `.yml`/`.yaml` and
image files are synced; build artefacts (`__pycache__`, `.DS_Store`, `*.pyc`)
are excluded.

## When to Sync

**ALWAYS** sync in the same session in which the change happens (do not
defer) when:

1. Creating a new agent, skill, or command
2. Modifying an existing agent, skill, or command
3. Applying agent prompt patches from a Final Audit (Phase 7)
4. Deleting or renaming an agent/skill/command
5. Creating or modifying any file under `sie_v2/docs/`
6. Creating or modifying any file under `sie_v2/backend/documentacion/`

## How to Sync

### Single file (agents / skills / commands)

```bash
cp sie_v2/.claude/{agents,skills,commands}/changed_file.md \
   /Users/xmn/Documents/Agentes/AgentesTrabajos/sie_integraciones/{agents,skills,commands}/
```

### Docs trees (use rsync with content filter + `--delete`)

```bash
BACKUP=/Users/xmn/Documents/Agentes/AgentesTrabajos/sie_integraciones

rsync -a --delete \
  --include='*/' \
  --include='*.md' --include='*.yml' --include='*.yaml' \
  --include='*.png' --include='*.jpg' --include='*.svg' \
  --exclude='*' \
  sie_v2/docs/ "$BACKUP/docs/"

rsync -a --delete \
  --include='*/' \
  --include='*.md' --include='*.yml' --include='*.yaml' \
  --include='*.png' --include='*.jpg' --include='*.svg' \
  --exclude='*' \
  sie_v2/backend/documentacion/ "$BACKUP/documentacion-backend/"
```

`--delete` keeps the mirror in step when files are removed at source.

## Rules

- The backup is the **single source of truth** for shared tooling across
  projects.
- Never modify backup files directly — always change the project source and
  sync.
- Update `README.md` in the backup directory if the structure changes.
- Update the `Last synced` line in the backup README after every sync.
- Never commit files that live under the backup directory into the project
  repo and vice versa — they are independent storage locations.
