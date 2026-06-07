---
name: sie_v2
path: /Users/xmn/Documents/Trabajo/Cuidacasas/sie_integraciones/sie_v2
repo_url: ""
stack: "fastapi+sqlalchemy / vue (multi-tenant)"
kuraka_version: 0.3.4
has_project_layer: true
default_mode: normal
focus_scope: ""
status: active
last_mount: ""
last_sync: ""
tags: [kuraka-project]
---

# sie_v2

The reference consumer project. Its project layer is pre-populated in
`kuraka-artifacts/migration-examples/sie_v2-project-layer/` and is the source of the
DD-1031 continuous-improvement work.

## Stack
- **Backend:** Python / FastAPI + SQLAlchemy (multi-tenant, `tenant_id`)
- **Frontend:** Vue + Pinia
- **DB:** migrations via Alembic

## Improvement history
- Active feature branch: `feature/DD-1031_MutuaMadrileña_v2`
- 7 RETROs analyzed → `RECURRING-ISSUES` → patches P1–P6 applied to project layer
  (`sie_v2-project-layer/agents/*.append.md`, `review-checks/code-reviewer.md`) and
  framework Rule T6 (`rules/17`). Applied 2026-06-06.
- Pending: re-run adoption rsync in the sie_v2 repo so `.claude/project/agents/`
  picks up the new append files; restart Claude Code there.
