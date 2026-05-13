# sie_v2 — Project Specialization Layer (migration source)

This directory mirrors the structure of what `<sie_v2-repo>/.claude/project/`
should contain after the Fase 3 + 3.5 migration. It's populated incrementally
as each agent in the framework gets refactored and its sie_v2-specific
content gets extracted here.

## Status

| Agent refactor | Files added here |
|---|---|
| `po-analyst` | `lessons-learned/LL-001-symbol-removal.md`, `lessons-learned/LL-DD-896-FM-01-provider-file-coverage.md`, `review-checks/po-analyst.md`, `conventions/tenant-isolation.md` |
| `backend-developer` | (pending) |
| `code-reviewer` | (pending) |
| … | … |

See `MIGRATION-INVENTORY.md` at the vault root for the full mapping of
hardcodes → destination files.

## When the sie_v2 team is ready to consume this

```bash
# from the sie_v2 repo root
cp -r <kuraka-vault>/kuraka-artifacts/migration-examples/sie_v2-project-layer/. \
      .claude/project/
```

After copying, commit the result. The project layer is sie_v2's source of
truth from that moment on; this directory in the framework vault is just
the seed.

## Loading order (reminder)

When an agent runs in sie_v2 (after Fase 3 refactor), it reads:

1. The agent's framework prompt (`.claude/agents/{agent}.md`).
2. `kuraka.config.yaml` (project root).
3. `.claude/stack-profiles/{framework}.md` (e.g., `python-fastapi.md`).
4. `.claude/project/conventions/*.md` — all files.
5. `.claude/project/review-checks/{agent}.md` — if it exists.
6. `.claude/project/lessons-learned/*.md` — only those whose frontmatter
   `applies_to` includes the agent's name.
7. `.claude/project/agents/{agent}.append.md` — if it exists.
8. `.claude/project/glossary.md` — if it exists.

Later items in the list override earlier ones in case of conflict.
