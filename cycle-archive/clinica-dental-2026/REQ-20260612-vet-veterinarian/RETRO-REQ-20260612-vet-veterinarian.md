# Final Audit - REQ-20260612-vet-veterinarian

> Module: **Veterinarios (Veterinarian)** Cycle 1 · Project: `clinicaDental2026`
> Mode: **Normal-reduced** · Phases run: 1, 2, 3, 4b, 5, 6.8, 7 · Phases skipped (Rule 0): 2.5, 6, 6.5, 6.7

## 1) Summary
- **Total iterations:** LOW (effectively zero rework). One forward-only MINOR-fix pass after Phase 5 (commit 9667f57), no correction loops.
- **Main causes of the (minimal) extra work:** advisory MINORs from Phase 5 review (#6/#1/#2/#4), all cosmetic/defensive; no defect re-opened a prior phase.
- **Estimated preventable iterations:** 0 loops. The cycle was clean end to end.
- **Highlight:** the component **mounted clean in vivo with NO NG0203 injection-context error**, in direct contrast to the Pets module (F17) which shipped that exact BLOCKER. The frozen-schema + mirror-precedent discipline paid off.

## 2) Timeline of Rework

| Phase | Issue | Root Cause | Preventable? | Fix |
|-------|-------|-----------|--------------|-----|
| 1 Analysis | `requirement-consistency-check` skill not installed | Tooling gap in env | No (env) | Inline manual GATE0 against verbatim contract + binding spec — handled correctly |
| 3 Architect | 4 MINOR advisory (no BLOCKER) | Normal advisory polish | N/A | Folded into stories; schema frozen |
| 5 Review | 6 MINOR + 2 SUGGESTION (0 BLOCKER, 0 IMPORTANT) | Defensive/cosmetic polish | N/A (not rework) | MINOR #6/#1/#2/#4 applied in commit 9667f57 |
| 5 Review | **101 tool_uses (cap 40) + ~15 min (policy 10 min)** | Reviewer over-explored a wide 18-file surface | Partial | See §3 code-reviewer + §4 |
| 6.8 Smoke | Table/modal not render-verified live | Backend 404 + missing X-Acc accesses | No (external dep) | Accepted risk; F27 + F28 raised |

## 3) Agent Findings

### po-analyst — GOOD
- **What went right:** Produced a correctly split Cycle1/Cycle2 REQ, recognized the env-missing consistency skill and ran an inline GATE0 instead of blocking, and correctly classified all known-unknowns (master_ids, collation, X-Acc) as Risks/Assumptions per established repo precedent rather than hard blockers. 113K tokens / 13 tools — proportionate.
- **No patch needed.**

### story-refiner — GOOD
- **What went right:** 8 well-scoped Cycle-1 stories mirroring the `pet-modal` nested-FormArray precedent (S6/S7/S8 sub-forms), with the edit-mode "hide credentials + nested collections so nothing is silently swallowed" rule carried verbatim from `pet-modal` AC-9b. Longest phase (350s) but justified by the 8-story fan-out.
- **No patch needed.**

### architect-reviewer — GOOD
- APPROVED_WITH_MINOR with a clean schema freeze (`persna_hash` verbatim spelling preserved, Spanish field names kept per Constitution Art. VI). The freeze held — implementation required no Phase-3 re-open.
- **No patch needed.**

### frontend-developer — GOOD
- 18 files (15 new + 3 altered), `ng build` EXIT=0 (orchestrator-verified), lazy chunk emitted. 67 tool_uses for 18 files is reasonable. Most notable outcome: **no NG0203** at runtime — the injection-context discipline from the Pets retro was internalized.
- **No patch needed.**

### code-reviewer — NEEDS ATTENTION (process, not output)
- **What went right:** Output was valid and high-quality — 0 BLOCKER, 0 IMPORTANT, security dimension folded and audited clean (multi-tenant `company_hash` scoping + credential handling).
- **What failed:** **101 tool_uses (over the 40 review cap) and ~900s (~15 min, over the 10-min policy).** Tokens (129K) stayed within budget, so it never tripped a hard stop, but the tool-use/latency caps exist to bound exactly this kind of wide-surface drift.
- **Why:** the 18-file surface (component + modal + 3 sub-forms + 3 interface files + service + constants) invited file-by-file re-reading. With Phase 5.5 folded in, the reviewer also did the security pass in the same run.
- **Instruction update (project-layer, preferred):**
  - **Project layer:** new entry in `.claude/project/lessons-learned/` with `applies_to: [code-reviewer]` — "For `vet/*` and `cfg/*` CRUD modules that mirror an approved precedent (`customer`, `pets`, `plan`), review **by diff against the precedent**, not by full re-read of every file. Budget: ≤40 tool_uses / ≤10 min. When folding Phase 5.5, scope the security pass to tenant-scoping + credential handling only — the rest is covered by the mirrored pattern."

## 4) Systemic Issues
- **Review tool-use/latency cap is soft.** Phase 5 breached both the 40-tool-use cap and the 10-min policy without any guardrail firing, because only the token budget is enforced. The caps are advisory-only today. (Recurs theme: large-surface CRUD reviews drift.)
- **Backend lag is now a standing pattern.** Every `vet/*` and `cfg/plan` frontend module ships ahead of its backend (Customer F11, Pets F18/F19, Plan F24, now Veterinarian F27/F28). The frontend is correct but cannot be render-verified live. This is accepted, but it means smoke is structurally "partial" for this whole family of modules.
- **`requirement-consistency-check` skill missing in env** — GATE0 fell back to a manual inline check (handled well, but undocumented as a standing env gap).

## 5) Workflow Improvements (Concrete)
1. Make the review **40-tool-use / 10-min cap enforced** (soft warning at 40, hard checkpoint at 60) instead of advisory — or explicitly grant a higher cap for ≥15-file mirror modules so the policy matches reality.
2. Add a project-layer note instructing reviewers of mirror-precedent CRUD modules to review **by diff against the precedent module**, cutting re-read cost.
3. Track the recurring "frontend ships before backend" pattern as a known program condition so future smoke verdicts pre-declare the partial-render acceptance instead of re-deriving it each cycle.

## 6) Patches Proposed

- Type: project-layer
- Target: `.claude/project/lessons-learned/review-mirror-crud.md` (new) — `applies_to: [code-reviewer]`
- Change: "When reviewing a CRUD module that mirrors an APPROVED precedent (`vet/customer`, `vet/pets`, `cfg/plan`), review by **diff against the precedent**, not by full re-read of all N files. Hard budget: ≤40 tool_uses, ≤10 min. When Phase 5.5 is folded in, scope the security pass to (a) `company_hash` tenant-scoping and (b) credential handling; the remaining surface is covered by the mirrored, already-reviewed pattern."

- Type: framework (defer — only if the pattern recurs in another project)
- Target: `agents/code-reviewer.md`
- Change: convert the 40-tool-use / 10-min review caps from advisory to a soft-warn-at-cap + hard-checkpoint policy, with an explicit higher allowance for ≥15-file mirror modules. **Reserve until pattern-detector confirms recurrence across projects** — do not patch the framework on a single occurrence.

## 7) Next-Requirement Guardrails
- **Mandatory pre-implementation checks:** confirm the mirror-precedent module before refining stories (here: `pet-modal` for nested arrays, `customer` for the single-page CRUD shell). Freeze the schema with verbatim backend spellings (`persna_hash`) before Phase 4.
- **Mandatory naming checks:** verbatim endpoint casing (`vet/list-veterinarian`, `vet/update-state-veterinarian`, `vet/upd-veterinarian`) and Spanish field names — keep exact (Constitution Art. VI), do not "normalize".
- **Mandatory schema checks:** every nested array in the create payload must have a matching standalone endpoint deferred to Cycle 2; `upd-*` must omit credentials/perfil/rol/access/arrays (no silent swallow — `pet-modal` AC-9b).
- **Permissions:** all controls under `*appCanAccess="'/vet/veterinarian'"`; expect them hidden until backend X-Acc config (F28).

## 8) Token & Latency Telemetry

Ranked by `total_tokens` descending.

| Phase | Agent | Tokens | Tool uses | Duration | Produced | Notes |
|-------|-------|-------:|----------:|---------:|----------|-------|
| 4b | frontend-developer | 161,600 | 67 | ~10.3 min | S1–S8, 18 files, ng build PASS | Proportionate to 18-file surface |
| 3 | architect-reviewer | 130,963 | 17 | ~2.4 min | APPROVED_WITH_MINOR + schema freeze | Efficient |
| 5 | code-reviewer | 129,010 | **101** | **~15.0 min** | APPROVED_WITH_MINOR, security folded | ⚠️ tool_uses over 40 cap; duration over 10-min policy; tokens OK |
| 1 | po-analyst | 113,767 | 13 | ~2.6 min | REQ, GATE0 not blocked, 9 stories | Efficient |
| 2 | story-refiner | 98,012 | 13 | ~5.8 min | 8 Cycle-1 stories | Longest non-impl phase; justified fan-out |

**Totals:** `633,352` tokens across `5` agent runs (6.8 smoke + 7 audit not metered here).

**Observations:**
- frontend-developer (impl) is correctly the heaviest at 161K — normal for an 18-file module.
- **code-reviewer is the only flagged outlier:** despite 3rd in tokens (129K, within budget), it consumed **101 tool_uses (2.5× the 40 cap) and ~15 min (1.5× the 10-min policy)** — wide-surface re-read drift on a mirror module. Tokens stayed bounded, so no hard stop fired.
- No phase exceeded its token budget; `budget_ok: true` on all metered runs.

**Optimization backlog (carry into next cycle):**
- [ ] Enforce (or raise + match) the review tool-use/latency caps for ≥15-file mirror modules.
- [ ] Add the "review-by-diff-against-precedent" project-layer note for code-reviewer.
- [ ] Pre-declare partial-render smoke acceptance for the `vet/*` + `cfg/*` family (frontend-ahead-of-backend).

## 9) Accepted-risk note — partial smoke
The live smoke (6.8) is **PASS — partial**, accepted as a documented limitation identical to the Customer (F12), Pets (F18/F19) and Plan (F24) precedents:
- **Backend 404** — `POST /vet/list-veterinarian` returns HTTP 404 (endpoints not deployed; plain 404, **not** the F10 collation 500). → backend task **F27**.
- **Missing X-Acc accesses** — `/vet/veterinarian` has no accesses in the dynamic menu, so `*appCanAccess` correctly suppresses every gated control (table, toolbar, "Nuevo", row actions, hence modal + sub-forms are unreachable at runtime). → backend task **F28**.
Frontend Cycle 1 is correct and complete: route registered + AuthGuard + return-URL round-trip verified, component mounts clean (no NG0203), and the real `vet/list-veterinarian` contract is called with Bearer + tenant `company_hash`. The end-to-end visual is blocked **exclusively** by backend dependencies.
