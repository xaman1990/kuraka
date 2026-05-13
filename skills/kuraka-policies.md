---
name: kuraka-policies
description: "Cross-cutting Kuraka policies: retry, timeout, token budget, failure fallback, checkpointing, and telemetry. Applies in any mode."
---

# Kuraka — Policies

Cross-cutting policies that apply in any Kuraka mode (Normal,
Reduced-by-risk, Lite, Retroactive).

---

## Agent Invocation Policy

Every `Agent` call has retry and timeout policies to prevent silent
failures from propagating through the workflow.

### Retry policy

- **Max 2 retries per agent** (3 total attempts).
- **Retry triggers**:
  - Malformed output (fails the `verify-output` schema).
  - Agent returned `VALIDATION_FAILED` marker.
  - Transient tool error (network, rate limit).
- **NO retry on**:
  - Error requiring user input (ask the user).
  - Deliberate agent rejection (e.g., "I can't proceed without X").
  - 3rd failure — escalate to the user.

### Retry protocol

On each retry, the orchestrator injects feedback into the next prompt:

```
PREVIOUS ATTEMPT FAILED VALIDATION
Issues found:
- {specific issue 1}
- {specific issue 2}

Please re-generate addressing these issues.
```

### Timeout policy

- **Max 10 minutes per invocation** (`duration_ms > 600_000`).
- **Timeout escalates to the user**: "Agent {agent} has been running 10+
  min. Continue, abort, or change strategy?"
- **Legitimate long tasks**: rare. If you expect to exceed 10 min, split
  the task into smaller units.

### Failure fallback (3 failed attempts)

1. Write checkpoint with `status: "paused"` and failure details.
2. Report to the user:
   - Which agent failed.
   - What the 3 attempts produced.
   - Suggested next steps (manual retry, skip, human).
3. **WAIT for user decision** — don't auto-skip critical phases.

### Tool use limits per agent

To prevent runaway loops:

| Category | Max tool uses |
|---|---|
| Research (`po-analyst`, exploration) | 30 |
| Implementation (`backend-developer`, `frontend-developer`) | 50 |
| Review (`architect-reviewer`, `code-reviewer`, `security-reviewer`) | 40 |
| Audit (`final-auditor`, `pattern-detector`) | 25 |

If an agent exceeds its limit without producing output → treat as timeout.

### Rate-limit policy during Phase 4

The orchestrator **MUST NOT** write implementation code under any
circumstances. If the implementer subagent (`backend-developer`,
`frontend-developer`, `test-engineer`) is rate-limited:

1. **First option** — `ScheduleWakeup` with delay based on estimated
   rate-limit duration:
   - Message "rate limited, retry in N minutes" →
     `ScheduleWakeup(delaySeconds=N*60+30, ...)` with a prompt that
     resumes the exact story.
2. **Second option** — degrade to an alternative agent: if the block is
   specific to one model, try `simplify` or a lower-cost agent for
   mechanical tasks (reduce scope to copy-paste with exact citations).
3. **Documented exception** — the orchestrator may write SOLELY in these
   cases, announcing first to the user:
   - Edits ≤ 5 LOC for a precise fix of a post-review IMPORTANT.
   - Mechanical refactor of an already-written migration (pattern change
     with no new logic).
   - **NEVER** a new file of > 50 LOC.

If the orchestrator writes code outside the exceptions, it must:
- Announce the violation to the user first.
- Request explicit approval.
- Trigger a mandatory re-review by the corresponding agent (same role,
  in a different invocation once the rate limit has passed).
- Document the violation in the Phase 7 RETRO.

**Why**: an orchestrator that implements directly normalizes a
role-isolation breakage that's hard to walk back from. Re-review can
mitigate the risk per case, but the pattern is dangerous if it becomes
routine.

---

## Token Budget (recommended)

Nominal budget per phase to detect deviations:

| Phase | Target | Investigate if exceeds |
|---|---:|---|
| 1 PO Analysis | 80–120K | 200K |
| 2 Story Refinement | 60–100K | 180K |
| 2.5 Test Planning | 60–100K | 150K |
| 3 Architect Review | 50–80K | 150K |
| 4a Backend Impl (per story M) | 100–200K | 400K |
| 4b Frontend Impl (per story M) | 100–200K | 400K |
| 5 Code Review | 70–120K | 200K |
| 5.5 Security Review | 60–100K | 180K |
| 6 Tests (per story M) | 80–150K | 300K |
| 6.5 E2E | 50–100K | 200K |
| 6.7 Deployment | 30–60K | 120K |
| 7 Final Audit | 40–80K | 150K |

**Action if a phase exceeds "investigate if exceeds"**:
1. Abort the phase if still running.
2. Analyze telemetry (which files were read? how many tool_uses?).
3. Apply patterns T1–T5 from `rules/17-kuraka-token-optimizations.md`.
4. Re-launch with an optimized prompt.

---

## Checkpointing (MANDATORY)

After EACH gate approved by the user, write the workflow state to:

`${architecture.paths.docs_process_root}/checkpoints/{REQ-name}-state.json`

### Structure

```json
{
  "req_name": "REQ-YYYY-MM-DD-slug",
  "mode": "normal | reduced | lite | retroactive",
  "status": "in_progress | paused | completed | abandoned",
  "current_phase": "4a",
  "phases_completed": ["1", "2", "2.5", "3"],
  "phases_pending": ["4b", "5", "5.5", "6", "7"],
  "started_at": "ISO 8601",
  "last_updated": "ISO 8601",
  "artifacts": {
    "req_path": "docs/process/REQ-...",
    "story_paths": ["docs/process/stories/..."],
    "test_plan_path": "docs/process/test-plans/...",
    "frozen_schema_path": "docs/process/schemas/...",
    "review_reports": {
      "phase_3": null,
      "phase_5": null,
      "phase_5_5": null
    }
  },
  "phase_4a_progress": { "total_stories": 0, "stories_done": [], "current": null },
  "phase_4b_progress": { "total_stories": 0, "stories_done": [], "current": null },
  "telemetry_path": "docs/process/agent-telemetry/..."
}
```

### When to write

- After approval of Phase 1 → create initial checkpoint.
- After EACH gate → update `phases_completed`, `current_phase`, `last_updated`.
- When the user pauses the session → `status: "paused"`.
- When Phase 7 completes → rename to `{REQ-name}-state.final.json`,
  `status: "completed"`.

### Resume protocol

If a session is resumed (new chat, crash recovery):

1. Read the most recent `{REQ-name}-state.json`.
2. Confirm with user: "Resuming {REQ-name} from phase {current_phase}. Continue?"
3. Reload artifacts via paths in `artifacts.*`.
4. Continue from `phases_pending[0]`.

**Never skip phases when resuming** — if a phase says "completed" but
the artifact doesn't exist, treat the checkpoint as corrupt and ask the
user.

---

## Token Telemetry (MANDATORY)

Every `Agent` invocation returns a `<usage>` block with `total_tokens`,
`tool_uses`, and `duration_ms`. You MUST append it to a telemetry JSON
so the `final-auditor` (Phase 7) can analyze consumption by agent.

**File**:
`${architecture.paths.docs_process_root}/agent-telemetry/{REQ-name}-telemetry.json`

### Flow

1. After the **first** Agent call in the cycle, create the file:
   ```json
   {
     "req_name": "REQ-YYYY-MM-DD-slug",
     "mode": "normal | reduced | lite | retroactive",
     "runs": []
   }
   ```
2. After **each** Agent call, add an entry:
   ```json
   {
     "phase": "<int | string>",
     "agent": "<agent-name>",
     "mode": "<optional identifier>",
     "total_tokens": 0,
     "tool_uses": 0,
     "duration_ms": 0,
     "produced": "<short description>",
     "budget_ok": true
   }
   ```
3. If an agent is invoked multiple times in the same phase, each
   invocation is its own entry — use `mode` to disambiguate.
4. If you do **not** use `Agent` for a phase (direct orchestrator work),
   omit the entry — only track real invocations.
5. Mark `budget_ok: false` if the phase exceeded its "investigate if
   exceeds" threshold.

The `final-auditor` reads this JSON in Phase 7 and produces the token
ranking in the retro. Missing telemetry degrades the retro but doesn't
block it.

---

## Model Routing

Each agent has a model assigned in its frontmatter according to cost / judgment:

| Model | Agents | Why |
|---|---|---|
| **opus** | `po-analyst`, `architect-reviewer`, `security-reviewer`, `final-auditor` | Complex reasoning, multiple sources, strategic judgment |
| **sonnet** | `story-refiner`, `backend-developer`, `frontend-developer`, `code-reviewer`, `test-engineer` | Balanced implementation and review |
| **haiku** | `deployment-verifier`, `pattern-detector`, `migration-reviewer`, `e2e-tester` | Mechanical checks, pattern matching, smoke tests — much cheaper than sonnet |

Changing a model: edit `model:` in the corresponding agent's frontmatter
and restart Claude Code so it re-registers the subagent.

---

## Kuraka system tooling

Scripts from the framework vault (`${KURAKA_VAULT}`) callable from any
branch / repo:

### `mount-kuraka.sh`

Mounts the Kuraka system into the current repo (rsync from vault,
updates `.gitignore`).

```bash
bash ${KURAKA_VAULT}/mount-kuraka.sh
# or with an alias in ~/.zshrc:
alias mount-kuraka='bash ${KURAKA_VAULT}/mount-kuraka.sh'
```

### `validate-kuraka.sh`

Validates frontmatter of agents / skills and detects orphan references.
Run before each new session to confirm everything is consistent.

```bash
bash ${KURAKA_VAULT}/validate-kuraka.sh
```

### `kuraka-inspect.py`

Stack detector for Brownfield onboarding. Scans a repo and produces a
JSON with backend / frontend / DB / testing / CI / containers detected.

```bash
python3 ${KURAKA_VAULT}/kuraka-inspect.py [dir]
# JSON to stdout, human summary to stderr
# Redirect to file to persist:
python3 ${KURAKA_VAULT}/kuraka-inspect.py > inspect-report.json
```

The `amauta` agent reads this JSON as its main input in Brownfield mode.

### `aggregate-telemetry.py`

Reads all JSONs from
`${architecture.paths.docs_process_root}/agent-telemetry/` and emits an
aggregated Markdown dashboard (per-cycle, per-agent, tokens / usage,
over-budget flags).

```bash
python3 ${KURAKA_VAULT}/aggregate-telemetry.py
# produces: ${architecture.paths.docs_process_root}/agent-telemetry/DASHBOARD.md
```

The `final-auditor` (Phase 7) MUST run it before writing the RETRO to
have aggregated data, not just from the current cycle.

### `tests/kuraka/`

Structural test suite for the system. Run after any change in
`.claude/agents/` or `.claude/skills/`:

```bash
python3 -m pytest tests/kuraka/ -v
```

Validates: frontmatter, model routing, kuraka split, output-schemas
coverage, no orphan references.

---

## Optimizations applicable in any mode

See `rules/17-kuraka-token-optimizations.md` for patterns T1–T5:

- **T1 Context digest** — the orchestrator reads reference files once
  and injects them as snippets in prompts.
- **T2 End-only verification** — for restyles / mechanical changes,
  typecheck / lint only at the end.
- **T3 Phase collapse** — combine Phase 1+2 into a single subagent for
  low-risk changes.
- **T4 Mapping-table stories** — compact AC as tables for substitution
  patterns.
- **T5 No auto-verify** — the orchestrator verifies, the agent doesn't.

Estimated impact: −35% on baseline for a UI-only cycle; up to −60% if
combined with infrastructure improvements (model routing, agent
registration).
