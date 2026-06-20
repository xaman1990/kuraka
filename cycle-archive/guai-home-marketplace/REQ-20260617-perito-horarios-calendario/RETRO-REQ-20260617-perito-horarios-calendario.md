# Final Audit — REQ-20260617-perito-horarios-calendario

> **Mode:** Reduced-by-risk (frontend-only). Phases run: 1+2 (LITE_COMBINED), 4b (S1→S2 sequential), 5 (code review + apply-fixes), 6 (folded into 4b+5), 6.8 (smoke via Playwright MCP). Skipped: 2.5, 3, 5.5, 6.5, 6.7, 7.
> **Verdict:** Clean cycle. Zero preventable rework loops. All gates green, smoke PASS.

## 1) Summary
- **Total iterations:** low. No user-correction loops; the only "rework" was the planned Phase 5 review-fix pass (3 IMPORTANT + 2 MINOR + 2 test hardenings), all caught internally before any user gate.
- **Main causes of in-cycle fixes:** UTC off-by-one in `slot.iso`, incomplete focus trap, missing recap-card AC20 — all standard review catches, none escaped the pipeline.
- **Estimated preventable iterations:** 0. The pipeline scaled correctly to the risk and the review caught what it should.

## 2) Timeline of Rework

| Phase | Issue | Root Cause | Preventable earlier? | Fix |
|-------|-------|-----------|----------------------|-----|
| 5 (review) | `slot.iso` UTC off-by-one (label could show wrong weekday) | `.toISOString()` shifts to UTC; date built from local parts | Partial — risk §8 flagged it; the unit tests injected `today` but the label path wasn't covered | Switched to local ISO + exported `toLocalDateString`; test hardened |
| 5 (review) | Incomplete focus trap in SlotModal | a11y AC16 partially implemented | No — exactly what review is for | Focus trap completed (trap + Esc + return focus) |
| 5 (review) | Recap card AC20 not honored | Missed in S2 template pass | No — caught one phase later, no user impact | Recap card restored |
| 5 (review) | 44px touch target, past-month nav guard (MINOR) | polish gaps | No | Both fixed |
| 6.8 (smoke) | Apparent "3 slots from 1 add" | TEST artifact — `e26`-targeted snapshot hid the still-open sibling dialog | N/A — not a product bug | Cleared via clean full-snapshot repro; no code change |

## 3) Agent Findings

### po-analyst (Phase 1+2, LITE_COMBINED) — WORKED WELL
- Produced a tight, frozen-decision REQ + 2 well-sized stories (S compose+tests, M wiring) in one pass with mapping-table ACs (Rule T4). GATE0 spot-checked against live code.
- The risk table pre-flagged BOTH issues review later caught (store-shape consumers, UTC off-by-one) — good foresight. No update needed.

### frontend-developer (4b S1) — WORKED WELL
- Pure composable with **injectable `today`** + 33 deterministic unit tests. This is the testability convention from RETRO-DD1067 applied for the FIRST time — see §4(a). No update needed.

### frontend-developer (4b S2 / apply-fixes) — minor
- S2 missed AC20 (recap card) and shipped a partial focus trap + UTC-tied label; all caught in Phase 5. These are normal review-surface items, not a systemic gap. No prompt patch warranted.

### code-reviewer (Phase 5) — WORKED WELL
- 6D review caught the UTC off-by-one in the label path that the S1 unit tests didn't reach, plus the a11y and AC20 gaps. Highest-token agent (80K, 67 tool uses) but proportionate to a full-surface review of a new component + composable + store change.

## 4) What Worked (positive reinforcement)
- **(a) Testability convention ROI confirmed.** The "pure logic → `lib/` composable" rule added in the prior cycle's RETRO (DD1067) was applied here for the first time and paid off directly: 33 deterministic unit tests AND it gave the code reviewer a clean seam to spot the UTC off-by-one. The convention works — keep it.
- **Pipeline scaling (Rule 0) was correct.** Skipping 3/5.5/6.5/6.7 for a frontend-only, no-contract, no-auth change was justified and lost nothing; folding 6.5 into 6.8 via Playwright MCP was the right call with no harness present.
- **Sequential S1→S2** (Rule T6 spirit) meant the store-shape change landed on top of tested pure logic — no cross-story debugging storm.

## 5) Improvements (concrete)
1. **Smoke-via-MCP snapshot hygiene** — see §6 lessons-learned patch (b). Take FULL snapshots (or assert the dialog node explicitly) when verifying modal/overlay state; subtree-targeted snapshots can hide sibling overlays and fabricate anomalies.
2. **Label-path coverage for date logic** — when a composable is pure+injectable, also unit-test the *consumer's* formatted output (the label), not just the predicate functions, so UTC/local bugs are caught in 4b instead of 5.

## 6) Patches Proposed

```
- Type: project-layer
- Target: .claude/project/lessons-learned.md
- Change: append a "Smoke-via-Playwright-MCP: snapshot scope" note —
  "When verifying modal/overlay or any state where a dialog stays open,
   take a FULL page snapshot or assert the dialog node directly. A
   subtree-targeted snapshot (e.g. an `e26` node) can exclude a sibling
   open dialog and surface false anomalies (observed in
   REQ-20260617-perito-horarios: an apparent '3 slots from 1 add' was a
   snapshot-scope artifact, not a product bug)."
```

No framework patches. The two findings are project/tooling-specific, not universal agent-prompt gaps.

## 7) Next-Requirement Guardrails
- **Pre-implementation:** keep the `lib/` pure-composable convention for any date/calendar/business logic; require a label/consumer test alongside predicate tests.
- **Naming/schema:** none (no DB/contract this cycle).
- **Smoke:** full snapshots for modal/overlay verification.

## 8) Token & Latency Telemetry

Ranked by `total_tokens` descending.

| Phase | Agent | Tokens | Tool uses | Duration | Produced | Notes |
|-------|-------|-------:|----------:|---------:|----------|-------|
| 5 | code-reviewer | 80,038 | 67 | 306.6s | APPROVED_WITH_FIXES (3 IMPORTANT, 2 MINOR, 2 test-hardening, 4 PRAISE) | Highest, but proportionate to new component+composable+store review |
| 4b | frontend-developer (S2) | 71,643 | 19 | 170.3s | SlotModal + Horarios rework + store shape change | Largest implementation surface |
| 5 | frontend-developer (apply-fixes) | 61,891 | 31 | 158.0s | All 7 findings fixed; vitest 131 passed | — |
| 1+2 | po-analyst (LITE_COMBINED) | 60,603 | 5 | 125.7s | REQ + 2 stories, GATE0 passed | Combined phase = efficient |
| 4b | frontend-developer (S1) | 53,587 | 19 | 310.5s | Pure composable + 33 unit tests | Longest duration (test authoring) |

**Totals:** `327,762` tokens across `5` agent runs.

**Observations:**
- No single agent is disproportionate. The two frontend-developer runs that touched the most files (S2, apply-fixes) and the full 6D review are the top three — expected.
- LITE_COMBINED kept Phase 1+2 at 60.6K with only 5 tool uses — combining the phases (Rule T3) clearly paid off.
- Total 327K for a 5-run cycle that delivered a new composable, a new component, a store refactor, 131 tests, and a live smoke is healthy for a reduced-by-risk frontend cycle.

**Optimization backlog (carry into next cycle):**
- [ ] When stories are mechanical/template-heavy, consider giving the apply-fixes pass the reviewer's exact line refs as a digest (T1-style) to trim its 31 tool uses.

## 9) Systemic Note
- **Accumulating uncommitted work is the standing risk.** This cycle and the prior one (DD1067) both ended uncommitted; live secrets remain in the working tree with a broken `.gitignore` (MEMORY: pending-secret-remediation-DD1067). The longer the tree stays uncommitted, the higher the chance of conflict/loss. See follow-ups.

## Follow-ups (numbered)
1. **Holiday source = debt.** `NATIONAL_HOLIDAYS_2026` is a hardcoded list tagged "⚠️ VALIDAR vs BOE", national-only. Recurring "calendario laboral real" TODO (also in the prototype). Move to a backend/config source per CCAA/municipio when an API exists. Until then, validate the 2026 list (esp. movable Viernes Santo 2026-04-03) against the official BOE before merge.
2. **Commit the accumulated work** (DD1067 + this cycle) once the secret remediation is done — rotate live secrets, fix `.gitignore`, then commit. Do not commit while secrets are tracked.
3. **eslint install still pending** in the frontend container — the lint gate is known-broken and was skipped this cycle. Install eslint so the lint gate is real again next cycle.
