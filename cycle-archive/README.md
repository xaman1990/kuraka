# cycle-archive/

Central, append-only archive of **every Kuraka cycle's diagnostic**, pulled back from
every consumer project. This is the cross-project memory of "where did Kuraka fail."

## What lands here

After a cycle's Final Audit (Phase 7), `final-auditor` writes in the project:
- `docs/process/agent-retrospectives/RETRO-<REQ>.md` — the retrospective + recommendations
- `docs/process/agent-telemetry/<REQ>-telemetry.json` — the cycle's telemetry

`kuraka-archive.py` copies those back here, grouped per project per cycle:

```
cycle-archive/
├── INDEX.md                      # rolling cross-project index (one row per cycle)
├── <project-slug>/
│   └── <REQ>/
│       ├── RETRO-<REQ>.md
│       ├── <REQ>-telemetry.json
│       └── meta.yaml             # project, req, archived_at, verdict, has_telemetry
```

## How it's filled

```bash
python3 kuraka-archive.py /path/to/consumer-project
# or from the project, after Phase 7 closes and syncs
```

Copies (never moves) — the project keeps its own copies. Idempotent: re-runs skip
cycles already archived (`--force` to re-copy).

## Why

This archive is the **data source for cross-project improvement**:

```
N projects' RETROs (here) → pattern-detector (cross-project)
  → cross-project RECURRING-ISSUES → RETRO Triage board → route framework|project → apply
```

A single project's RETROs only show its own recurring issues. Pooling all projects'
diagnostics here is what lets us see systemic Kuraka failures and improve the **agents**
and **bases** globally — the general improvement cycle.

Inert to `mount-kuraka.sh` / `sync-obsidian.sh` (not mounted into projects, not synced as
agents). Read by the control plane and by `pattern-detector` runs scoped to this dir.
