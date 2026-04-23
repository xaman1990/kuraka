---
description: "Migrate agents/skills/contexts/rules/commands + sync-obsidian.sh from the Obsidian vault to the local project. Use when switching branches and files are missing."
---

# Task: Sync from Obsidian vault to local project

## Context

My multi-agent system lives in two places:
1. **Source of truth (central backup):** `/Users/xmn/Documents/Agentes/AgentesTrabajos/kuraka/`
2. **Working copy (per branch):** `{current working directory}/.claude/` and `{cwd}/scripts/`

When I switch git branches, these files may be missing because I don't always
commit agent definitions (they're for my local development only). This task
migrates the central backup INTO the local project so I can use the agents
and hooks on any branch.

## Pre-check (run FIRST)

Before starting, run:
```bash
git status --short .claude/ scripts/sync-obsidian.sh
```

If there are uncommitted changes in `.claude/` or `scripts/sync-obsidian.sh`,
report them to me and ask if I want to stash them before the migration. This
prevents losing local edits.

## Directory mapping (copy FROM → TO)

| From (Obsidian vault) | To (local project) |
|-----------------------|---------------------|
| `agents/*.md` | `.claude/agents/` |
| `agents/contexts/*.md` | `.claude/agents/contexts/` |
| `skills/*.md` | `.claude/skills/` |
| `commands/*.md` | `.claude/commands/` |
| `rules/*.md` | `.claude/rules/` |
| `scripts/sync-obsidian.sh` | `scripts/sync-obsidian.sh` (then `chmod +x`) |

Vault root: `/Users/xmn/Documents/Agentes/AgentesTrabajos/kuraka/`

## Execution steps (in order)

### 1. Detect what's missing

Compare source vs destination. For each file in the source:
- If destination file does NOT exist → mark as MISSING (will copy)
- If destination file exists and is IDENTICAL → mark as SKIP
- If destination file exists but DIFFERS → mark as CONFLICT (ask user)

Report the 3 groups to me BEFORE copying anything.

Use `diff -rq` or equivalent to detect differences.

### 2. Handle conflicts safely

For each CONFLICT file:
- Show me a brief diff (first 20 lines of difference)
- Ask: "Overwrite local `{path}` with vault version? (yes/no/diff/skip)"
- Options:
  - `yes` → overwrite
  - `no` → keep local, log the decision
  - `diff` → show full diff, then ask again
  - `skip` → same as no

NEVER overwrite without explicit approval per file.

### 3. Create missing directories

If `.claude/agents/contexts/` doesn't exist, create it.
If `.claude/skills/` doesn't exist, create it.
If `.claude/commands/` doesn't exist, create it.
If `.claude/rules/` doesn't exist, create it.
If `scripts/` doesn't exist, create it.
Use `mkdir -p` (idempotent).

### 4. Copy missing files

For each MISSING file: copy from vault to local.
Preserve filename and relative path within each category.
Use `cp -p` to preserve permissions and timestamps.

**Special: sync-obsidian.sh**
- Copy `vault/scripts/sync-obsidian.sh` to `scripts/sync-obsidian.sh`
- Run `chmod +x scripts/sync-obsidian.sh` afterward (git may not preserve exec bit)

### 4b. Convert wikilinks back to backticks (CRITICAL)

The vault uses `[[name]]` wikilinks for Obsidian's graph view, but Claude Code
expects `` `name` `` backticks. After copying, convert in these directories ONLY:

- `.claude/agents/` (all .md files)
- `.claude/agents/contexts/` (all .md files)
- `.claude/skills/` (all .md files)
- `.claude/rules/` (all .md files)

**Do NOT convert** `.claude/commands/*.md` — commands are executable prompts
where backticks are intentional (grep patterns, code samples).

Conversion command (macOS sed):
```bash
for dir in .claude/agents .claude/agents/contexts .claude/skills .claude/rules; do
  for file in "$dir"/*.md; do
    [ -f "$file" ] || continue
    sed -i '' 's/\[\[\([a-z][a-z0-9-]*\)\]\]/`\1`/g' "$file"
  done
done
```

If you see `[[name]]` still present in local files after the migration, the
conversion was skipped — run it manually.

### 5. Verify the migration

After copying and converting, run these checks:
- Count files per directory (agents, agents/contexts, skills, commands, rules) in vault vs local — local must be `>=` vault count
- Grep for `tech-lead` in local `.claude/` — must return 0 results (legacy name, should not exist)
- Grep for `architect-reviewer` and `code-reviewer` (with backticks) in local `.claude/` — must exist
- Grep for `[[` in local `.claude/agents/`, `.claude/skills/`, `.claude/rules/` — must return 0 (wikilinks were converted)
- Confirm these critical files are present:
  - `.claude/skills/kuraka.md`
  - `.claude/skills/verify-output.md`
  - `.claude/agents/contexts/output-schemas.md`
  - `scripts/sync-obsidian.sh` (executable)

### 6. Report

Show me a final summary:

```
## Migration Report

**Source:** /Users/xmn/Documents/Agentes/AgentesTrabajos/kuraka/
**Destination:** {cwd}/

### Files copied (MISSING → created)
- .claude/agents/X.md
- scripts/sync-obsidian.sh
- ...

### Files overwritten (CONFLICT → resolved with yes)
- .claude/skills/Y.md
- ...

### Files skipped
- .claude/agents/Z.md (identical, no change needed)
- .claude/skills/W.md (user said no to overwrite)

### Verification
- Agents count: N vault / M local ✅
- No `tech-lead` references: ✅
- `architect-reviewer` + `code-reviewer` present: ✅
- Core files (workflow, output-schemas, verify-output) present: ✅
- sync-obsidian.sh is executable: ✅

### Next steps
- Review any files you kept local (listed above)
- Your branch now has access to all {N} agents and {M} skills
- Auto-sync hook to vault is operational via scripts/sync-obsidian.sh
```

## Rules

1. **Never force overwrite** — always confirm conflicts per file
2. **Use git to protect work** — if `.claude/` or `scripts/sync-obsidian.sh` has uncommitted changes, warn before overwriting
3. **Only copy `.md` files for .claude/** — skip anything else (images, JSON, etc.)
4. **For sync-obsidian.sh, always restore executable bit** with `chmod +x`
5. **Do not touch other directories** — only `.claude/*` subdirs and `scripts/sync-obsidian.sh`
6. **Preserve permissions and timestamps** — use `cp -p`
7. **Idempotent by default** — running twice should produce no changes if vault and local are in sync
8. **Stop on first error** — if a copy fails, report and halt (don't continue silently)
