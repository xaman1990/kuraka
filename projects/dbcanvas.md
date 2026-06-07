---
name: dbcanvas
path: /Users/xmn/Desarrollos/PlugginSQLAgent
repo_url: ""
stack: "typescript+express / react"
kuraka_version: 0.3.4
has_project_layer: true
default_mode: normal
focus_scope: ""
status: onboarding
last_mount: 2026-06-06
last_sync: ""
tags: [kuraka-project]
---

# dbcanvas

Electron desktop app (`dbcanvas`) — npm-workspaces monorepo with 5 packages:
`core`, `desktop`, `mcp-server`, `platform`, `website`.

## Stack (from kuraka-inspect, confidence 0.83)
- **Language:** TypeScript (88%), JS (10%)
- **Backend:** Express + Knex (`knex-migrations`) — inside workspace packages
- **Frontend:** React + Vite + Zustand, Vitest
- **Desktop:** Electron 34.1.1
- **CI:** GitHub Actions

## Root commands
- `test` → `npm test` (core + mcp-server)
- `format` → `prettier --write 'packages/*/src/**/*.{ts,tsx}'`
- no `lint` at root (eslint is per-package); `build` is per-workspace

## Onboarding notes
- ⚠️ kuraka-inspect reported `single-package` — **wrong**, it's a workspace monorepo.
- Pending: `amauta` to generate `kuraka.config.yaml` + `.claude/project/`.
- Decision pending: model the whole monorepo or target one package (`focus_scope`).
- Branch at mount: `CanvasSoftware`.
