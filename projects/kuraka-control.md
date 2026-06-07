---
name: kuraka-control
path: /Users/xmn/Desarrollos/kuraka-control
repo_url: ""
stack: "node-express + react-vite-zustand (control plane web app)"
kuraka_version: 0.3.4
has_project_layer: false
default_mode: normal
focus_scope: ""
status: onboarding
last_mount: 2026-06-06
last_sync: ""
tags: [kuraka-project, control-plane]
---

# kuraka-control

The **Kuraka Control Plane** web app — Phase 1 of `CONTROL-PLANE.md`. Local single-user
dashboard to govern Kuraka across projects (observe + act).

Greenfield project, **built with Kuraka itself** (dogfood) via Bootstrap mode
(`inti` → `arki` → Normal). It is the first new project in the registry and validates
the hub-and-spoke model end to end.

## Stack (target, to be confirmed by arki)
- **Backend:** Node + Express (FS access + wraps vault scripts)
- **Frontend:** React + Vite + Zustand
- Reads the vault at `KURAKA_VAULT`; mutations go through existing scripts + direct
  writes to `retro-triage/` and patch targets.

## Onboarding notes
- Discovery brief: `docs/discovery/brief.md` (fed to inti/arki).
- Architecture constraints: see brief §"Constraints de arquitectura".
- Does NOT wrap `sync-obsidian.sh` (deprecated).
- Pending: inti (vision/requirements) → arki (config + scaffold) in a session rooted in
  the repo, then `/kuraka <feature>` per dashboard feature.
