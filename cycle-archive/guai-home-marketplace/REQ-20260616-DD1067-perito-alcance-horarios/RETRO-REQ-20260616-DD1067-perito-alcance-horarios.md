# Final Audit — REQ-20260616-DD1067-perito-alcance-horarios

**Cycle:** Perito guAI — Alcance + Horarios views · **Mode:** Normal (read-side
reduced) · **Audited:** 2026-06-17 · **Verdict:** clean cycle, near-zero rework.

## 1) Summary

- **Total iterations: LOW.** No user-correction loops mid-implementation. The
  only "rework" was a single GATE0 re-scope at Phase 1 — which is the gate
  working as designed, not a failure.
- **Main causes of churn (all preventive, all early):**
  1. User's opening premise was wrong about the backend (assumed valuation
     persistence + a migration were still needed; they already existed on the
     branch). GATE0 caught it before any code was written.
  2. An IVA arithmetic discrepancy (lines ex-IVA 140,50 ≠ TOTAL inc-IVA 170,01)
     that would have read as a frontend bug — surfaced during analysis, resolved
     into R4 reconciliation block, never reached the user as a defect.
- **Estimated preventable iterations avoided: ~3–4 loops.** GATE0 alone
  prevented a duplicate-migration (the DD-1031 failure class) plus a likely
  "why don't the numbers add up?" round-trip.
- **Pre-existing debts surfaced (NOT caused here):** broken frontend lint gate
  (eslint not installed), live secrets in `.env.production`/`.env.staging`.

**Headline win — GATE0 ROI.** The single highest-value event in the cycle was
po-analyst's GATE0 consistency-check BLOCKING the requirement. The user asked to
"persist the valuation + add a migration"; the branch already had
`perito_valuation_lines` + `perito_work_items` + migration `20260602_1749` +
write-path repos + webhook writer. GATE0 returned 2 blockers, the scope was cut
to **read-side only**, and `migration-reviewer` was dropped. This directly
prevented the duplicate-migration class that caused real rework in DD-1031.

## 2) Timeline of Rework

| Phase | Issue | Root Cause | Preventable? | Fix | Severity |
|-------|-------|-----------|--------------|-----|----------|
| 1 (GATE0) | Requirement premise contradicted the branch: persistence + migration assumed needed, already existed | Stale mental model of branch state (DD1067 prior pass already landed write-side) | Yes — and it WAS prevented | GATE0 BLOCKED, 2 blockers, re-scoped to read-side, migration-reviewer dropped | n/a (gate success) |
| 1 (analysis) | Line amounts (ex-IVA) don't sum to displayed TOTAL (inc-IVA) → would look like a bug | Mixed IVA basis between `valuation_lines` and `analysis.total_amount` | Yes — prevented | R4: reconciliation line `Base · IVA · TOTAL` on Alcance; client never sums lines | Low |
| 5 (code review) | Function > 50 LOC; bare `=[]` mutable default | Normal implementation slips | Caught in-phase | Extracted `_resolve_or_compute_analysis` (now 44 LOC); `Field(default_factory=list)`; id-ASC tiebreak | IMPORTANT (resolved) |
| 6 (tests) | Frontend correlation/IVA logic untested | Logic lives inline in `PeritoAlcance.vue` (not extracted) → not unit-testable | Partial — deferred by design, tied to SUGGESTION#6 | Deferred to follow-up story (see §7) | Low (deferred) |

No story was re-implemented. No cross-story bug propagation (Rule T6 sequential
discipline held: S1 → make test → S2 → S3).

## 3) Agent Findings

### po-analyst (Phase 1 — two runs)
- **What worked (exemplary):** GATE0 consistency-check ran a real branch
  inspection (13 tool uses) instead of trusting the prompt, found the
  persistence + migration already present, and BLOCKED. This is the single most
  valuable action of the cycle. Also surfaced the IVA discrepancy against real
  DB data (analysis id=19) — turning a latent frontend "bug" into an explicit R4
  requirement.
- **Why it worked:** the gate is structured to verify premises against code,
  not to take the user's framing as fact.
- **Improvement:** none required. **Positive reinforcement — keep this gate
  exactly as is.** Consider citing this cycle as the canonical GATE0-ROI example
  in onboarding material.
- Severity: n/a · Preventability of the issue it caught: **Yes (prevented).**

### story-refiner (Phase 2)
- **What worked:** 3 clean stories, 59 AC, correct dependency ordering
  (S1 schema → S2 binding; S2 route → S3). Carried R2/R3/R4 decisions into the
  ACs without re-opening them.
- **Improvement:** none. Severity: n/a.

### test-engineer (Phase 2.5 + Phase 6)
- **What worked:** 16 mandatory backend TCs + 5 testability constraints up
  front; in Phase 6 confirmed 16/16 covered with 0 gaps and added
  `peritoStore.spec` (94 vitest passing).
- **What was deferred:** frontend correlation/IVA unit tests — **correctly**
  flagged as not writable because the logic is inline in `PeritoAlcance.vue`.
  test-engineer surfaced the blocker rather than writing brittle DOM-coupled
  tests. Good call.
- **Improvement (process):** when a testability constraint from 2.5 ("extract
  pure logic so it can be unit-tested") is NOT honored in implementation, the
  Phase-6 deferral should auto-emit a follow-up story stub, not just a note.
  See §6 patch.
- Severity: Low · Preventability: Partial (design choice).

### architect-reviewer (Phase 3)
- **What worked:** APPROVED with 0 blockers, froze the schema
  (`SCHEMA-FROZEN-DD1067.md`) before S2 bound to it — the contract-drift risk in
  the REQ was neutralized exactly as planned.
- **Improvement:** none. Severity: n/a.

### backend-developer (Phase 4a + Phase 5 fixes)
- **What worked:** S1 delivered read-side breakdown, subtotal exclusion, manual
  mapper, 16 tests, `make test-run` exit 0, 17/17 AC. Applied all review fixes
  cleanly and re-ran green.
- **Improvement:** the >50 LOC function should have been caught before code
  review (it's a standing project rule). Consider a self-lint of function length
  before declaring a story done. Severity: IMPORTANT (resolved in-cycle).

### frontend-developer (Phase 4b — S2 + S3)
- **What worked:** Alcance view with R2 correlation + flat fallback, R3 (no
  toggle), R4 reconciliation block, CTA wired (the actual bug fix), Horarios with
  D2 placeholder. type-check exit 0; 24/24 + 18/18 AC.
- **What worked but created debt:** put correlation + IVA logic inline in the
  `.vue` rather than a composable → blocked unit testing (SUGGESTION#6).
- **Improvement:** when implementing logic flagged by a 2.5 testability
  constraint, extract it to a `lib/` composable by default. Severity: Low.

### code-reviewer (Phase 5)
- **What worked:** thorough 6D pass (56 tool uses), 2 IMPORTANT + 3 MINOR + 3
  PRAISE; correctly deferred MINOR#4 + SUGGESTION#6 with rationale.
- **What slipped:** did NOT re-raise the broken lint gate even though it's a
  declared project gate. Reasonable (pre-existing, project-wide) but the gate
  mismatch deserves a standing note. Severity: Low (informational).

### security-reviewer (Phase 5.5)
- **What worked:** PASS, IDOR chain verified (analysis_id is server-derived from
  the ownership-guarded case, not client-supplied), parameterized ORM, no
  v-html, only `caseRef` in localStorage. Clean. Severity: n/a.

### deployment-verifier (Phase 6.7)
- **What worked:** READY-WITH-NOTES; 397 tests pass, type-check + ruff green, 0
  new migrations/env. **Correctly surfaced the two pre-existing merge-blockers**
  (secrets + eslint) instead of waving them through. Severity: n/a (notes only).

## 4) Systemic Issues

1. **Frontend lint gate is non-functional project-wide.**
   `kuraka.config.yaml` declares `npm run lint` (eslint) a gate, but eslint is
   not installed and there is no config — it fails on `main` too. Every frontend
   cycle will hit this. Saved to project memory
   `frontend-lint-gate-broken-eslint-missing`. **Recurring across cycles** → if
   it appears again, escalate to `pattern-detector`.
2. **Live secrets committed in working tree.** `backend/.env.production` +
   `.env.staging` carry live secrets, and `.gitignore` naming is inconsistent.
   Merge-blocking. Tracked in project memory `pending-secret-remediation-DD1067`.
3. **Inline frontend logic defeats Phase-2.5 testability constraints.** A
   testability constraint can be set in 2.5 but silently ignored in 4b, and the
   only consequence is a Phase-6 "deferred" note. The loop doesn't close itself.
4. **No-commit-this-cycle.** All work sits unstaged in the working tree. The
   cycle is verified (smoke PASS, 397 tests) but not preserved in git. **Risk:**
   a branch switch / reset loses a fully-audited cycle. Low probability, high
   impact. Must commit (gated on secret remediation — do not commit the live
   `.env.*` files).

## 5) Workflow Improvements (Concrete)

1. **Make the lint-gate mismatch a hard pre-flight, not a per-cycle surprise.**
   At Rule-0 pipeline planning, the orchestrator should verify each declared
   gate is actually runnable; if a gate is dead, either fix it or mark it
   `SKIPPED (broken: <reason>)` explicitly so it isn't silently relied on.
2. **Auto-emit a follow-up story when a 2.5 testability constraint is unmet.**
   Phase 6 should not be allowed to "defer" silently — emit a stub story so the
   debt is tracked, not buried in a RETRO.
3. **Self-check function length / mutable defaults before declaring a story
   done.** Both Phase-5 IMPORTANTs are mechanically detectable; catching them in
   4a saves a code-review round-trip token-wise.
4. **Keep GATE0 branch-inspection mandatory for "add persistence/migration"
   requirements.** This is the second cycle (DD-1031, now DD1067) where GATE0
   vs. a stale premise prevented duplicate DB work. It is paying for itself.

## 6) Patches Proposed

```
- Type: project-layer
- Target: .claude/project/conventions/frontend-testability.md (CREATE)
- Insertion point: new file
- Change (exact text):
    # Frontend testability convention
    Pure logic (correlation, reconciliation, IVA/price math, formatting)
    MUST live in a `lib/` composable (e.g. `useBreakdownCorrelation.ts`),
    NOT inline in a `.vue` `<script setup>`. Rationale: inline logic cannot
    be unit-tested without brittle DOM coupling. When test-engineer sets a
    Phase-2.5 testability constraint of the form "extract <X> so it is
    unit-testable", frontend-developer MUST honor it by extraction; if not
    extracted, the story is NOT done.
```

```
- Type: project-layer
- Target: .claude/project/lessons-learned/lint-gate-must-be-runnable.md (CREATE)
- Insertion point: new file (applies_to: [orchestrator, deployment-verifier])
- Change (exact text):
    # Lesson: a declared gate that cannot run is not a gate
    kuraka.config declares `npm run lint` (eslint) a frontend gate, but
    eslint is not installed / unconfigured — it fails on `main` too
    (DD1067, 2026-06-16). Until eslint is installed, treat the frontend lint
    gate as KNOWN-BROKEN: state it as "SKIPPED (broken: eslint missing)" in
    the pipeline plan rather than relying on it. Re-enable once
    `frontend-lint-gate-broken-eslint-missing` (project memory) is resolved.
```

```
- Type: framework-prompt
- Target: .claude/agents/test-engineer.md  (Phase 6 / TEST_WRITING section)
- Insertion point: end of the "deferred coverage" handling rules
- Change (exact text):
    When coverage is DEFERRED because the code-under-test was not made
    testable (e.g. logic left inline instead of extracted per a Phase-2.5
    testability constraint), do NOT merely note the gap. Emit a follow-up
    story stub at ${docs_process_root}/stories/ describing the extraction +
    the tests it unblocks, and reference it in the coverage report. A
    deferral without a tracked follow-up is not allowed.
```

Note: prefer applying the two project-layer files immediately. The framework
test-engineer patch affects all consumers — apply only via the framework repo +
vault sync (`.claude/rules/16-agent-backup.md`).

## 7) Next-Requirement Guardrails

- **Mandatory pre-implementation checks:**
  - GATE0 branch inspection for any "persist / migrate / add table" premise —
    confirm the artifact does not already exist (keep doing this).
  - At pipeline planning, verify each declared gate is runnable; mark dead gates
    `SKIPPED (broken)` explicitly.
- **Mandatory naming checks:** new routes follow `perito/*` convention (done:
  `perito/alcance`, `perito/horarios`); wire shape is camelCase via
  `alias_generator` (done).
- **Mandatory schema checks:** none new this cycle (read-side only). The
  subtotal-exclusion + TOTAL-from-`analysis.total_amount` rule must persist if a
  later cycle adds per-chapter subtotals — re-expose explicitly, never sum lines
  client-side.
- **Carry-in follow-ups (numbered, actionable):**
  1. **Extract `useBreakdownCorrelation` composable** from `PeritoAlcance.vue`
     (correlation + R4 IVA reconciliation) and add unit tests — closes
     SUGGESTION#6 + the Phase-6 deferred frontend coverage. → follow-up story.
  2. **Install + configure eslint** in `frontend/` so the declared lint gate
     actually runs (resolves `frontend-lint-gate-broken-eslint-missing`).
  3. **Secret remediation BEFORE merge:** rotate the live secrets in
     `backend/.env.production` / `.env.staging`, fix `.gitignore` naming, ensure
     they are untracked (resolves `pending-secret-remediation-DD1067`).
  4. **Commit this cycle** once (3) is done — the work is fully audited (smoke
     PASS, 397 tests, type-check + ruff green) but currently only in the working
     tree; do NOT include the live `.env.*` files in the commit.
  5. **Next cycle:** Carrito → Datos → Pago → Confirmación (explicitly deferred
     here; Horarios forward CTA is the D2 placeholder waiting on it).

## 8) Token & Latency Telemetry

Ranked by `total_tokens` descending.

| Phase | Agent | Tokens | Tool uses | Duration | Produced | Notes |
|-------|-------|-------:|----------:|---------:|----------|-------|
| 5 | code-reviewer | 131,516 | 56 | 24.0 min | APPROVED_WITH_FIXES (2 IMPORTANT, 3 MINOR, 3 PRAISE) | Highest tokens; proportionate to a 6D review across BE+FE diff |
| 4a | backend-developer | 128,431 | 69 | 7.2 min | S1 read-side + 16 tests, make test-run exit 0 | High tool-use; proportionate to repos+DTO+schema+mapper+tests |
| 3 | architect-reviewer | 102,150 | 17 | 1.8 min | APPROVED + schema freeze | Fine |
| 6 | test-engineer | 99,164 | 16 | 1.5 min | 16/16 covered, +5 store tests, vitest 94 | Fine |
| 5.5 | security-reviewer | 95,918 | 14 | 1.2 min | PASS, IDOR chain verified | Fine |
| 2.5 | test-engineer | 93,999 | 13 | 3.2 min | TEST-PLAN (16 BE + 3 FE, 5 constraints) | Fine |
| 4b | frontend-developer | 79,827 | 42 | 11.5 min | S2 Alcance + CTA + R4 + types + stub | Fine |
| 1 | po-analyst (GATE0) | 79,102 | 13 | 2.1 min | GATE0 BLOCKED, 2 blockers, no REQ | **Best ROI of the cycle** — prevented duplicate migration |
| 2 | story-refiner | 73,958 | 27 | 6.3 min | 3 stories, 59 AC | Fine |
| 6.7 | deployment-verifier | 67,933 | 41 | 4.6 min | READY-WITH-NOTES, 397 tests | Fine |
| 5 | backend-developer (fixes) | 66,740 | 21 | (wall-clock artifact) | Applied 4 review fixes, make test-run exit 0 | Duration field = 431 min wall-clock (idle gap), NOT compute; tokens/tool-uses are normal — **not over budget** |
| 4b | frontend-developer | 53,416 | 19 | 20.2 min | S3 Horarios + store slots | Fine |
| 1 | po-analyst (REQ write) | 46,800 | 2 | 1.4 min | REQ doc, 3 stories, read-side | Efficient — 2 tool uses (blockers pre-resolved) |

**Totals:** `1,118,954` tokens across `13` agent runs · `350` tool uses.

**Observations:**
- No phase is over budget (`budget_ok: true` on every run). The Phase-5
  backend-developer `duration_ms` (431 min) is a wall-clock artifact spanning an
  idle gap between review and fix-application — token count (66,740) and tool
  uses (21) are normal; **not a latency concern.**
- Splitting po-analyst into GATE0-check (79K) + REQ-write (47K) cost ~126K total
  but the GATE0 spend prevented a far larger duplicate-migration cycle. Net
  strongly positive.
- code-reviewer (131K) + backend-developer 4a (128K) are the two heaviest;
  both proportionate to their work. No optimization needed.

**Optimization backlog (carry into next cycle):**
- [ ] Extracting the Alcance logic into a composable (follow-up #1) will let
      Phase-6 frontend tests be written cheaply and shrink future review surface.
- [ ] Fix the lint gate so deployment-verifier doesn't spend tool-uses
      re-discovering it's broken each cycle.

## Confidence: HIGH

(Basis: complete telemetry, REQ, smoke test, and per-phase produced-artifacts
all present and mutually consistent; no missing inputs; rework attribution is
unambiguous.)
