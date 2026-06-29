# Kuraka Control Plane — design & definition

**Status:** draft v1 · **Owner:** Carlos · **Created:** 2026-06-06

This document defines how Kuraka manages **multiple consumer projects** and how the
**continuous-improvement loop** (RETRO feedback → agent改进) is governed from this
vault. It is the source-of-truth for the registry, the governance model, and the
front-end roadmap.

---

## 1. Core principle: develop ≠ govern

Two planes, deliberately separated:

| Plane | Where it lives | What happens there |
|-------|----------------|--------------------|
| **Data plane** (develop) | **Inside each consumer project** | Agents run, read `kuraka.config.yaml` + `.claude/project/`, write code through `backend-developer`/`frontend-developer`, produce RETROs + telemetry. |
| **Control plane** (govern) | **This vault** | Project registry, framework agents (source of truth), RETRO triage, cross-project telemetry, the front. |

> You **develop inside each project** and **govern from the vault**. This is the
> hub-and-spoke model. It is NOT "develop all projects from the vault" — see §2.

### Why not "develop everything from the vault" (rejected Option A)

| # | Blocker | Detail |
|---|---------|--------|
| 1 | Config is per-cwd | Agents read `kuraka.config.yaml` + `.claude/project/` relative to the working directory. One cwd = one config; can't honor dbcanvas's monorepo paths and sie_v2's FastAPI paths simultaneously. |
| 2 | Subagents register per-session/project | Claude Code reads `./.claude/agents/` at session start. Vault `agents/*.md` are *source* (wikilinks), not runtime; `mount-kuraka.sh` converts them. |
| 3 | Git isolation | Each project = own repo, branch, `.gitignore`. Nesting repos under the vault → submodule/ignore chaos, cross-repo commits. |
| 4 | Orchestrator write-invariant | "No writes to `backend/` before Phase 4" is evaluated against the project root; mixing roots muddies it. |
| 5 | Context/token cost | All projects in one window degrades agent focus and wastes tokens. |
| 6 | Vault must stay clean | It is the bidirectionally-synced source of truth; doing dev *in* it pollutes the framework. |

---

## 2. The three pieces we are building

### 2.1 Project registry  (Phase 0)

One markdown note per consumer project under `projects/<name>.md`, with frontmatter.

- **Single source of truth**, Obsidian-native (Dataview-queryable, graph-linkable,
  hand-editable) AND machine-readable (the web front parses the same frontmatter).
- `mount-kuraka.sh` upserts the note on each mount (planned enhancement — see §5).
- Schema (frontmatter):

```yaml
---
name: dbcanvas                 # slug, == filename stem
path: /abs/path/to/project     # project root on this machine
repo_url: ""                   # optional
stack: "electron+react+express+knex (monorepo)"
kuraka_version: 0.3.4          # version mounted
has_project_layer: true        # .claude/project/ exists & populated
default_mode: normal           # kuraka workflow default
focus_scope: ""                # for monorepos: which package(s) Kuraka targets
status: active                 # active | paused | onboarding | archived
last_mount: 2026-06-06
last_sync: 2026-06-06
tags: [kuraka-project]
---
```

### 2.2 Governance model

| Layer | Who edits | How it reaches a project | Editable from front? |
|-------|-----------|--------------------------|----------------------|
| **Framework agents** (`agents/*.md`) | **ONLY the vault** | `mount-kuraka.sh` copies read-only + gitignored | Yes — guarded (this is "adjust the main agent during improvement") |
| **Project layer** (`.claude/project/`) | Each project | synced back to vault as backup | Yes — per project |

The boundary the user asked for ("agentes principales solo se modifican por esta
solución") = the vault owns `agents/*.md`; projects only ever get read-only copies.

### 2.3 The improvement loop  (the reason this exists)

This systematizes the manual P1–P6 exercise done on 2026-06-06 (see `RECURRING-ISSUES`).

**Cross-project data source — `projects/<slug>/`:** at every cycle's Final Audit (Phase 7),
`final-auditor` runs `kuraka-backup.py <project>`, which snapshots that project's full
Kuraka state back into the vault's unified store: `projects/<slug>/cycles/<REQ>/` (RETRO +
telemetry + meta, branch-tagged), plus `layer/` and `state/`, and appends to
`projects/INDEX.md`. This is the central memory of "where did Kuraka fail" across ALL
projects — what lets `pattern-detector` find SYSTEMIC failures (not just per-project ones)
and drive a general improvement of the agents and bases — and it also preserves Kuraka work
outside the solution's git (restored by `kuraka-restore.py` on branch switch).

```
RETRO in project  →  kuraka-backup.py  →  projects/<slug>/{cycles,layer,state} (vault)
                  →  pattern-detector (cross-project)  →  RECURRING-ISSUES report
   →  [ TRIAGE in the front ]  →  routing decision per finding:
          framework fix?  → edit vault agent  (affects ALL projects)
          project fix?    → edit that project's project-layer (scoped)
   →  apply  →  version bump  →  sync
```

**Routing rule of thumb:** a finding is *framework* if it would recur in ANY stack;
it is *project* if it depends on this project's conventions, oracle, or schema. When
in doubt, prefer **project layer** (reversible, scoped) over framework (global blast
radius). The DD-1031 patches were all project-layer for exactly this reason.

Each triage produces a record under `retro-triage/<date>-<project>.md` (template
in §6) so decisions are auditable.

---

## 3. The front — roadmap (phased)

**Decision:** Obsidian-native first (observe), then a local web dashboard (act).
v1 scope = **observe + act**.

### Phase 0 — Obsidian-native (observe)  ← building now
- `projects/*.md` registry notes.
- `dashboards/Kuraka-Control.md` — Dataview views: projects table, agent catalog
  with framework/project governance badges, RETRO/RECURRING-ISSUES feed.
- Zero new infra. Editing an agent = editing its `.md` (graph view already works).

### Phase 1 — Local web dashboard (act)
A small **React + Vite** app (stack the user already runs in dbcanvas) that reads the
vault filesystem and adds the governance *actions* Obsidian can't do:
- **RETRO triage board**: drag a finding → choose framework vs project routing →
  it writes the patch to the vault agent or the project layer.
- **Apply / sync** buttons (wrap `mount-kuraka.sh`, `sync-obsidian.sh`,
  `aggregate-telemetry.py`).
- **Telemetry charts** (cross-project, from `*-telemetry.json` via the registry).
- **Agent governance badges**: which agents are framework (edit here) vs which
  projects override them in their project layer.

> Rejected: extending dbcanvas itself. The control plane must be project-agnostic and
> live with the vault; coupling it to a *consumer* project is backwards.

### Phase 1 data sources (all already in the vault)
| Data | Source |
|------|--------|
| Projects | `projects/*.md` frontmatter |
| Agents | `agents/*.md` frontmatter (name/description/model) |
| Project overrides | each project's `.claude/project/` (read via registry `path`) |
| RETROs / patterns | `RECURRING-ISSUES`, project `docs/process/**` |
| Telemetry | `<project>/docs/process/agent-telemetry/*-telemetry.json` |

---

## 4. Design decisions (locked 2026-06-06)
- **Lives in** sibling repo `kuraka-control` at `/Users/xmn/Desarrollos/kuraka-control`
  (bootstrapped, mounted). Built **with Kuraka** (Bootstrap: inti → arki → Normal).
- **Backend** = Node + Express; **frontend** = React + Vite + Zustand.
- **Reads each consumer project LIVE** (fs access to every registered `path`), not just
  the registry mirror — enables a real version-drift indicator. Implies fs-watch/poll of
  N external repos.
- **Live agent state via a watcher**: the "Quipu en vivo" stays the dominant hero, fed by
  a NEW real-time mechanism (file-watcher/IPC) that emits "agent X in phase Y now". This
  is added scope vs. post-cycle telemetry — must be built, not assumed.
- **Mutations wrap existing scripts** (`kuraka-init.py`, `mount`, `validate`, `inspect`)
  + direct writes only to `retro-triage/*.md` and patch targets. Single local user, no auth.

### UX conventions adopted (from the po-analyst review)
- **Framework-vs-project two-color system** everywhere: gold = framework override,
  jade = project-native (applied in Project Detail tree/badges).
- Quipu carries a **legend**; KPIs disambiguate catalog (16) vs running-now (4); nav in
  one language (Spanish), Quechua only as proper nouns.

### Mockups (in `pencil-new.pen`) — full concept, 5 screens
1. **Resumen / Monitor** — KPIs, Quipu en vivo (hero + legend), Projects, RETRO Triage, Telemetry, Quick actions.
2. **Project Detail** — header + drift, tabs (Config · Capa de proyecto · RETRO & Triage ·
   Telemetría · Ciclos · Agentes), Project Layer file-tree + content preview.
3. **RETRO Triage board** — kanban (Sin triar → Enrutado → Aplicado → Sincronizado),
   per-finding framework-vs-project routing actions, the loop bar.
4. **Agentes** — catalog of the 16 (real colors + models) + agent detail with the
   governance banner (framework = editable only here), per-project overrides, budget, activity.
5. **Onboard wizard** — modal wrapping `kuraka-init` (Ruta → Inspect → Config → Mount →
   Registrar), draft-config review + the one manual-step reminder.

## 5. Onboarding wizard — `kuraka-init.py` (done)
The friction of the old multi-step adoption (inspect → mount → config → skeleton →
register) is collapsed into one command: **`kuraka-init.py`**. It runs from anywhere,
interactive or flag-driven (`--target --name --yes`), and:
- runs `kuraka-inspect` → drafts a `kuraka.config.yaml` (with `# TODO`s) → creates the
  `.claude/project/` skeleton → runs `mount-kuraka.sh` → upserts `projects/<name>.md`.
- **never overwrites** an existing config or a populated project layer (idempotent).
- leaves exactly ONE manual step: restart Claude Code in the target (subagent
  registration is a runtime behavior; no script can do it), then run `amauta` to fill
  the TODOs from real code.

**The control-plane web app's "onboard/mount" action wraps this script** (Phase 1,
§3) — the wizard backend is already built.

### Registry auto-discovery (done)
The registry was manual, so projects mounted with the old `mount-kuraka.sh` flow drifted
out of view. Fixed:
- `mount-kuraka.sh` now **auto-registers** every mount (`kuraka-init.py --register-only`).
- `kuraka-discover.py` scans the filesystem for the Kuraka marker and **reconciles** the
  registry both ways: mounted-but-unregistered (fix with `--register`) and
  registered-but-not-mounted (drift, reported only).

### Still-planned script enhancements
- `aggregate-telemetry.py`: optional `--registry` mode to iterate `projects/*.md`
  and build a **cross-project** dashboard instead of single-project.

## 6. RETRO-triage record template
See `retro-triage/_TEMPLATE.md`.
