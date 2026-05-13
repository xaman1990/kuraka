---
name: kuraka-modes
description: "Kuraka workflow variants (Bootstrap, Brownfield, Lite, Retroactive, Reduced-by-risk). Defines when to use each based on project type or change surface."
---

# Kuraka — Modes

This file describes the variants of the main flow (`kuraka.md`). The
default for incremental changes in an existing project is **Normal**
(8 phases). The **Bootstrap** and **Brownfield** modes are entry points:
used **once** at the start of a new project or when integrating Kuraka
into a pre-existing codebase.

| Mode | When | Phases / agents |
|---|---|---|
| **Bootstrap** (Greenfield) | Project with no code yet (just an idea) | `inti` → `arki` → Normal Kuraka |
| **Brownfield** | Existing project without Kuraka | `kuraka-inspect` → `amauta` → Normal Kuraka |
| **Normal** | Change in a project with Kuraka already integrated | 8 phases (see `kuraka.md`) |
| **Reduced by risk** | Narrow change of low complexity | 3–5 phases |
| **Lite** | Trivial change (9 strict criteria) | 3 phases |
| **Retroactive** | Code already implemented without Kuraka (anti-pattern) | 4 phases |

---

## Mode: Bootstrap (Greenfield — new project)

**When**: starting a project with no code yet. The user only has an idea,
a product brief, or a Figma. No stack chosen, no repo structure, no rules.

**Phase map**:

| Phase | Agent | Skill | Output | Gate |
|---|---|---|---|---|
| B1 | `inti` | (interview-driven) | `docs/discovery/vision.md` + `docs/discovery/requirements.md` | User approves discovery |
| B2 | `arki` | (stack proposal + bootstrap) | `kuraka.config.yaml` + `docs/arquitectura/` + `.claude/project/` skeleton + source skeletons + project root files | User approves stack + scaffolding |

After B2, the project is ready for **Normal** mode with `po-analyst` as
the first phase of the first REQ.

**How to start**:

```bash
# from the empty directory of the new project
bash ${KURAKA_VAULT}/mount-kuraka.sh    # mount agents + skills + stack-profiles
/exit                                    # restart Claude Code to register agents
# new session:
# invoke inti: "I want to start a new project: {description}"
```

**When NOT to use Bootstrap**:
- Code already exists in the directory → use Brownfield.
- A `kuraka.config.yaml` already exists → use Normal directly.

**Expected saving**: Bootstrap replaces ~2 weeks of "thinking architecture
from scratch" with a structured 2-phase flow. It's not a shortcut — it's
rigor applied from day 0.

---

## Mode: Brownfield (existing project without Kuraka)

**When**: the repo already has mature code but Kuraka has never been
used there. You need to generate `kuraka.config.yaml`, `.claude/project/`,
and `docs/` without inventing conventions — extracting them from real
code.

**Phase map**:

| Phase | Tool / Agent | Output | Gate |
|---|---|---|---|
| W0 | `kuraka-inspect.py` (script, not an agent) | `inspect-report.json` | User reviews the report |
| W1 | `amauta` | `kuraka.config.yaml` + `.claude/project/` skeleton + `docs/` skeleton + convention matrix with low-confidence findings flagged | User approves the generated rules |

After W1, the project is ready for **Normal** mode in its next REQ.

**How to start**:

```bash
# from the root of the existing repo
python3 ${KURAKA_VAULT}/kuraka-inspect.py > inspect-report.json
bash ${KURAKA_VAULT}/mount-kuraka.sh    # mount agents + skills + stack-profiles
/exit                                    # restart Claude Code
# new session:
# invoke amauta: "I just mounted Kuraka in this existing project.
#                 Read inspect-report.json and generate config + project layer."
```

**When NOT to use Brownfield**:
- No code yet → use Bootstrap.
- `kuraka.config.yaml` already exists → only sync agents, don't regenerate.

**Amauta's golden rule**: never invent conventions. If you didn't see it
in code, marking it as TODO is better than fabricating it.

---

## Mode: Reduced by risk (recommended for small structural changes)

**When:** the change surface is narrow and doesn't touch critical logic.

**How to choose**:

| Surface | Minimum pipeline | Omit (with reason) |
|---|---|---|
| UI-only restyle (CSS / classes, no logic) | 1 + 2 + 4b | 2.5, 3, 5, 5.5, 6, 6.5, 6.7, 7 (no new logic) |
| Type tightening (no logic) | 1 + 4b + 5 | 2.5, 3, 5.5, 6, 6.5, 6.7, 7 (review detects magic strings) |
| Mechanical rename (identifier / file) | 1 (combined with 2) + 4b + 5 | 2.5, 3, 5.5, 6.5, 6.7, 7 |
| Config edit (env var, docker-compose) | 1 + 4 + 6.7 | 2, 2.5, 3, 5.5, 6, 6.5, 7 |

**Rule**: propose the pipeline to the user with a table justifying each
omitted phase. Don't assume; ask before invoking agents.

**Do NOT use this mode** for changes that touch business logic, API
contracts, DB, auth, or integrations — Normal is mandatory there.

See also `rules/17-kuraka-token-optimizations.md` for patterns T1–T5
applicable in any mode.

---

## Mode: Lite (trivial changes, strict criteria)

> ⚠️ EXCLUSIVE mode for trivial changes that meet ALL 9 criteria below.
> If any fails → use Normal or Reduced-by-risk. Do not use Lite to save
> time on normal changes.

### MANDATORY criteria

- [ ] **≤ 3 source files affected**
- [ ] **0 DB migrations**
- [ ] **0 new endpoints** (only modifies existing or doesn't touch endpoints)
- [ ] **0 SQL schema changes**
- [ ] **0 API contract changes** (request/response stable)
- [ ] **No impact on auth or permissions**
- [ ] **No changes to security code** (auth, encryption, tokens)
- [ ] **No changes to integrations**
- [ ] **Complexity S — ≤ 50 LOC total**

If ANY fails → **NOT Lite**.

### Cases that NEVER qualify

- Add / remove a DB column (even 1 line in the model).
- New endpoint, however trivial.
- Change in integration / provider code.
- Change to auth / JWT / tokens / CORS.
- Change to logging of sensitive data.
- Migration or seeding of production data.
- Change to shared frontend state stores.

### Phase Map Lite (3 agents vs 8)

| Lite Phase | Agents | Replaces |
|------------|--------|----------|
| L1 | `po-analyst` (mode: LITE_COMBINED) | Phase 1 + 2 + 2.5 |
| L2 | `backend-developer` / `frontend-developer` | Phase 4 |
| L3 | `code-reviewer` + writes tests | Phase 3 + 5 + 6 + 7 |

**Phases omitted** (justification inherent to the mode):
- Phase 3 (Architect) — L3 review covers it.
- Phase 5.5 (Security) — Lite doesn't allow security changes.
- Phase 6.5 (E2E) — Lite doesn't allow flow changes.
- Phase 6.7 (Deployment) — Lite doesn't allow config changes.
- Phase 7 (Final Audit) — replaced by a light note in L3.

### L1 — Combined PO + Stories + Test Plan

Agent: `po-analyst` (mode: LITE_COMBINED).

Output:
`${architecture.paths.docs_process_root}/REQ-LITE-{YYYYMMDD}-{slug}.md`
all-in-one with:
- Scope + 9 Lite criteria verified.
- List of affected files.
- 1–3 stories embedded with AC.
- Minimum test plan embedded.
- Confidence.

Gate: user approves the REQ-LITE.

### L2 — Implementation

Agent: `backend-developer` or `frontend-developer` (whichever applies).

Implements stories sequentially. If there's backend + frontend, both are
invoked (backend first if there's a contract). Each runs its checks.

Gate: files modified + tests passing.

### L3 — Review + Audit

Agent: `code-reviewer` (mode: LITE_FINAL). A single invocation does:
1. 6D code review.
2. Generate tests if the developer didn't write them.
3. Short RETRO only if there's a preventable lesson.

Output: review report with verdict + short RETRO (optional).

Gate: findings resolved.

### Lite Workflow Status Template

```markdown
## Workflow Status (Lite)
- [x] Lite Criteria: 9/9 VERIFIED ✓
- [ ] L1: REQ-LITE + Stories + Test Plan
- [ ] L2: Implementation
- [ ] L3: Review + Tests + Audit
```

### Expected saving (historical data)

Typical Lite cycle: ~70% token reduction vs Normal, ~3× faster duration,
fewer approval gates (3 vs 8).

### Golden rule

**If you doubt whether it qualifies as Lite → it does NOT qualify.** Use
Normal or Reduced-by-risk. An "expensive" workflow well-applied costs
less than a Lite badly-applied.

### Mid-cycle escalation

If during L2 / L3 you discover that the change is more complex than
expected (e.g., requires a new column):

1. **STOP immediately.**
2. Notify the user: "This change no longer qualifies as Lite. It needs
   to escalate. Proceed?"
3. Revert if necessary.
4. Re-start at Phase 1 of Normal with the known context.

---

## Mode: Retroactive (code already implemented)

**Trigger**: the user says the implementation is already done, or you
detect that the modified files already contain the described changes.

**Anti-pattern**: avoid it when possible. The existence of this mode
implies the workflow was skipped — it is NOT a valid default. It exists
to reconstruct documentation retroactively, not to justify systematic
bypass.

### Phase Map Retroactive

| Retro Phase | Replaces | Agent | Function |
|------------|----------|-------|----------|
| R1 | Phase 1 + 2 + 2.5 | `po-analyst` | Generate REQ + stories + test plan in one pass by reading existing code |
| R2 | Phase 3 + 5 | `code-reviewer` | Joint review of stories, test plan, and implementation |
| R3 | Phase 6 | (skip if tests exist) | Validate existing tests, write missing ones |
| R4 | Phase 7 | `final-auditor` | Retrospective |

### R1 — Combined PO + Stories + Test Plan

Agent: `po-analyst` in a single pass. Reads the implemented code and
existing tests to extract function names, paths, and **real** test
cases (not fabricated).

Output: REQ + stories + test plan (same locations as Normal mode).

Gate: user approves everything before R2.

### R2 — Combined Review

Agent: `code-reviewer`. A single invocation reviews stories AND code
together (the code already exists; separate story review adds no
additional value).

Output: single review report covering story fidelity + code quality.

Gate: BLOCKER and IMPORTANT resolved.

### R3 — Test Validation

```bash
${stack.backend.lint_cmd}
${stack.backend.test_cmd}
```

If tests are missing, `test-engineer` writes them.

### R4 — Final Audit

Same as Phase 7 Normal. The `final-auditor` produces the RETRO with
special attention to why the workflow was skipped (to prevent
repetition).

### Retroactive Workflow Status Template

```markdown
## Workflow Status (Retroactive)
- [ ] R1: PO + Stories + Test Plan
- [ ] R2: Combined Review
- [ ] R3: Test Validation
- [ ] R4: Final Audit
```

### Estimated saving

Retroactive uses 2–3 agents vs 5–6 of Normal → −40 to −60% of tokens.
The savings come from:
- No separate story-refiner (merged into PO).
- No separate REVIEW_STORIES pass (merged into REVIEW_IMPLEMENTATION).
- Phase 4 entirely skipped (already implemented).
- Phase 6 reduced to validation, not writing.
