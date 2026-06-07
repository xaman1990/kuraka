---
project: <name>          # must match a projects/<name>.md
source: <RECURRING-ISSUES or RETRO-id>
date: <YYYY-MM-DD>
decision: pending        # pending | applied | rejected | deferred
applied: false
tags: [retro-triage]
---

# Triage — <project> — <date>

Source: [[RECURRING-ISSUES]] (or the specific RETRO).

For each finding, decide **routing** and record it. The routing rule: a finding is
**framework** if it would recur in ANY stack; **project** if it depends on this
project's conventions/oracle/schema. When in doubt → project (scoped, reversible).

| # | Finding | Routing | Target file | Severity | Status |
|---|---------|---------|-------------|----------|--------|
| 1 | <short description> | framework / project | `agents/<x>.md` or `<proj>/.claude/project/...` | HIGH/MED | applied / pending |
| 2 | | | | | |

## Decisions & rationale
- **#1** — <why framework vs project; what changed; expected prevention>

## Follow-up
- [ ] Apply patch(es)
- [ ] Bump version (framework changes only)
- [ ] Sync project layer back to vault (`sync-obsidian` / re-run adoption rsync)
- [ ] Update `projects/<name>.md` `last_sync`
- [ ] Re-run pattern-detector next cycle to confirm prevention
