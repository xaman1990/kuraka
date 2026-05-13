# sie_v2 — Project Specialization Layer (migration source)

This directory mirrors the structure of what `<sie_v2-repo>/.claude/project/`
should contain after the Fase 3 + 3.5 migration. It's populated as agents
in the framework get refactored and their sie_v2-specific content is
extracted here.

---

## Status

Complete. All 15 sie_v2 conventions (`rules/01-15.md` in the legacy
layout) are migrated to this layer, with two exceptions:

- `08-testing.md` → replaced by `conventions/test-fixtures.md` (fixture
  catalog) + the stack profile's "Test patterns" section in
  `python-fastapi.md`.
- `10-code-review.md` → replaced by the `code-reviewer` agent's 6D
  framework + project-specific `review-checks/code-reviewer.md`.

---

## Contents

### Top-level

- `kuraka.config.yaml` — pre-filled project config (placed at the sie_v2
  repo root, NOT inside `.claude/project/`). Values verified against
  the codebase on 2026-05-13: multi_tenant true, paths relative to
  sie_v2/, pip + ruff + make test on backend, npm + vue-tsc on frontend.

### `conventions/` (15 files)

| File | Replaces (old rule) | Loaded by agents |
|---|---|---|
| `solid-principles.md` | 01 | All implementers + reviewers |
| `clean-code.md` | 02 | All implementers + reviewers |
| `file-organization.md` | 03 | `backend-developer`, `frontend-developer`, `code-reviewer`, `architect-reviewer` |
| `backend-architecture.md` | 04 | `backend-developer`, `code-reviewer`, `architect-reviewer` |
| `backend-conventions.md` | 05 | `backend-developer`, `code-reviewer`, `architect-reviewer`, `story-refiner` |
| `project-structure.md` | 06 | All agents (defines the monorepo tree) |
| `providers.md` | 07 | `backend-developer`, `code-reviewer`, `architect-reviewer`, `po-analyst` |
| `tenant-isolation.md` | — (synthesized from 04 + 05) | `backend-developer`, `code-reviewer`, `security-reviewer`, `architect-reviewer`, `story-refiner` |
| `frontend-standards.md` | 09 | `frontend-developer`, `code-reviewer`, `e2e-tester` |
| `frontend-branding.md` | — (extracted from 09) | `frontend-developer`, `code-reviewer` |
| `test-fixtures.md` | 08 (partial) | `test-engineer`, `backend-developer` (Phase 6) |
| `security-audit.md` | 11 | `security-reviewer` |
| `insurance-api-connector.md` | 12 | `backend-developer`, `architect-reviewer`, `po-analyst`, `migration-reviewer` |
| `db-migrations.md` | 13 | `migration-reviewer`, `backend-developer`, `architect-reviewer` |
| `incident-integration.md` | 14 | Operations / on-call (reference doc, not loaded by agents) |
| `data-mapping-specs.md` | 15 | `backend-developer`, `architect-reviewer`, `po-analyst` (when mappings are in scope) |

### `review-checks/` (5 files)

| File | Loaded by |
|---|---|
| `po-analyst.md` | `po-analyst` agent |
| `code-reviewer.md` | `code-reviewer` agent |
| `architect-reviewer.md` | `architect-reviewer` agent |
| `security-reviewer.md` | `security-reviewer` agent |
| `migration-reviewer.md` | `migration-reviewer` agent |

### `lessons-learned/` (4 files)

| File | `applies_to` |
|---|---|
| `LL-001-symbol-removal.md` | `po-analyst`, `architect-reviewer` |
| `LL-002-cache-invalidation.md` | `code-reviewer`, `backend-developer` |
| `LL-004-out-of-scope-respect.md` | `test-engineer` |
| `LL-DD-896-FM-01-provider-file-coverage.md` | `po-analyst` |
| `LL-DD-896-FM-02-alembic-vs-seeds.md` | `architect-reviewer`, `migration-reviewer` |

---

## How sie_v2 consumes this (adoption sequence)

```bash
# 1. Export the vault path. Required by every cp/cp -r below.
#    The mount script has a hardcoded fallback, but the user-run
#    commands below would expand to /kuraka-artifacts/... without this.
export KURAKA_VAULT=/Users/xmn/Documents/Agentes/AgentesTrabajos/kuraka

# 2. From the sie_v2 repo root, on a branch isolated from in-flight work.
#    sie_v2 uses `main` as the trunk (no `develop`).
cd /Users/xmn/Documents/Trabajo/Cuidacasas/sie_integraciones/sie_v2
git checkout main && git pull
git checkout -b kuraka-v0.3.x

# 3. Copy the pre-filled kuraka.config.yaml for sie_v2.
#    This file already has the correct values verified from the codebase
#    (multi_tenant: true, paths relative to sie_v2/, etc.). Review it
#    before committing in case there are project preferences to tweak.
cp "$KURAKA_VAULT/kuraka-artifacts/migration-examples/sie_v2-project-layer/kuraka.config.yaml" ./kuraka.config.yaml

# 4. Populate the project specialization layer from this directory.
#    Excludes kuraka.config.yaml (already at root from step 3).
mkdir -p .claude/project
rsync -a --exclude='kuraka.config.yaml' \
  "$KURAKA_VAULT/kuraka-artifacts/migration-examples/sie_v2-project-layer/" \
  .claude/project/

# 5. Mount the framework (agents + skills + stack profiles + meta-rules).
bash "$KURAKA_VAULT/mount-kuraka.sh"

# 6. Restart Claude Code so subagents register at session start.
#    (This is a Claude Code slash command, not a shell command.)
/exit
```

**Note**: if you started from a feature branch and forgot, your new
`kuraka-v0.3.x` branch will carry that branch's changes. Verify with
`git log --oneline main..HEAD` before committing the mount.

After step 6, in a new Claude Code session, the agents will:

1. Read `kuraka.config.yaml` at the project root.
2. Read the relevant stack profile from `.claude/stack-profiles/python-fastapi.md`.
3. Read this project layer from `.claude/project/`.
4. For each invocation, load the conventions, review-checks, and
   lessons-learned that apply to that agent.

---

## Loading order recap (per agent invocation)

1. The agent's framework prompt (`.claude/agents/{agent}.md`).
2. `kuraka.config.yaml` (project root).
3. `.claude/stack-profiles/{stack.backend.framework}.md` (and frontend
   if applicable).
4. `.claude/project/conventions/*.md` — all files.
5. `.claude/project/review-checks/{agent}.md` — if it exists.
6. `.claude/project/lessons-learned/*.md` — only those whose frontmatter
   `applies_to` includes the agent's name.
7. `.claude/project/agents/{agent}.append.md` — if it exists (escape
   hatch for project-specific prompt overrides).

Later sources override earlier ones in case of conflict
(most-specific wins). If a conflict touches security or correctness,
the agent flags it instead of silently picking.

---

## Verifying the adoption

After mounting, run a smoke test:

```bash
# In a new Claude Code session, invoke a simple agent and verify it
# reads from the right places. Example:

> "po-analyst: analyze the requirement 'add a status field to expedientes'"

# In its output, the agent should:
# - Reference kuraka.config.yaml (config-driven paths/commands).
# - Reference the stack profile's idiomatic file paths.
# - Apply tenant-isolation.md (since conventions.multi_tenant: true).
# - Cite project-structure.md for the monorepo layout.
# - Generate the REQ under architecture.paths.docs_process_root.
```

If anything in the output looks like generic framework content (no
project specifics), the project layer isn't loading — verify
`.claude/project/` was populated correctly and the file paths in
`kuraka.config.yaml` are right.

---

## Maintenance

Once adopted, the sie_v2 team owns this layer in their repo. Updates
flow forward (sie_v2 modifies its `.claude/project/`), not back. This
directory in the framework vault remains as the **initial seed only**.

If the team wants to contribute a generic version of a convention back
to the framework (e.g., for other projects to inherit), they propose it
via the framework's PR process — the framework agents' prompts can be
patched, or new stack profiles can be added.
