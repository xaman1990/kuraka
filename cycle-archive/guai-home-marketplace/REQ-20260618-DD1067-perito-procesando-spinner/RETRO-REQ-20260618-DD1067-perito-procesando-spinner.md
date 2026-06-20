# Final Audit — REQ-20260618-DD1067-perito-procesando-spinner

**Date:** 2026-06-18 · **Mode:** Reduced-by-risk (UI-only) · **Result:** clean cycle, all gates green.
**Surface:** single `.vue` file (`frontend/src/views/cliente/PeritoProcesando.vue`), `<template>` + CSS class + copy + dead-code removal. No backend / DB / contract / auth / realtime change.

## 1) Summary
- Total iterations: **low** — zero rework loops. One in-cycle post-review fix (expected, not rework).
- Main causes of the one fix cycle: a brand/WCAG contrast bug (`text-lime` spinner on cream) + a stale comment — both caught by the code-reviewer and fixed in a single 33.5K-token pass.
- Estimated preventable iterations: **0 loops** for this cycle. The contrast fix was *not* preventable here because its source is a **pre-existing latent bug in the codebase** that was reused as a precedent (see §4). It could only have been avoided if the digest/story had been skeptical of the precedent.
- Pipeline was correctly scaled (Rule 0): ran 1+2 (LITE_COMBINED) → 3 → 4b → 5 → 6.8 smoke → 7; skipped 2.5/5.5/6/6.5/6.7 with valid justification (no backend, no test runner for FE).

## 2) Timeline of Rework

| Phase | Issue | Root Cause | Preventable? | Fix |
|-------|-------|-----------|--------------|-----|
| 1+2 (story) | Story's "Snippets to use" embedded a `text-lime` spinner copied verbatim from `PagoConfirmacionPage.vue:114` | Reuse of an existing precedent that is itself a latent brand/WCAG violation (lime #CCFF00 on cream #FAF9F6 ≈ 1.08:1) | Partial | n/a in story; surfaced at Phase 5 |
| 4b (impl) | Implementer faithfully shipped `text-lime` spinner as instructed | Implementer trusted the snippet (correct behavior given the prompt) | Partial | Fixed in 5-fix |
| 5 (review) | code-reviewer flagged IMPORTANT spinner contrast + MINOR stale comment | — (this is the gate working as designed) | — | `text-lime` → `text-ink`; comment corrected; type-check+lint green |

No user-correction loops occurred. The single fix cycle is the normal review→fix path, not rework.

## 3) Agent Findings

### po-analyst (Phase 1+2, LITE_COMBINED)
- **What went RIGHT:** Excellent scope locking. The REQ explicitly verified preserve-untouched symbols (`poll`, `applyBackoff`, `awaitingInforme`, `stopPolling`, `RATE_LIMIT_BACKOFF_MS`, `POLL_INTERVAL_MS`) against the real file at GATE0. The mapping-table story (17 AC, T4 format) was compact and unambiguous. This is the template for low-risk UI cycles.
- **What slipped:** The "Snippets to use" block reused `PagoConfirmacionPage.vue:114` verbatim — a precedent that is itself a contrast violation. The story even labeled it "reuse repo precedent" as a *positive*, laundering a latent bug into the implementer prompt.
- **Instruction update (project-layer, see §6):** add a design-system note that lime is **background-only on light surfaces**; story-refiner should not cite a precedent as authoritative without a one-line brand/a11y sanity check.

### frontend-developer (Phase 4b + 5-fix)
- **What went RIGHT:** 17/17 AC, type-check + lint green both passes, respected T2 (end-only verification) and T5 (no self-verify). Clean dead-code removal (`PROCESS_STEPS`, `activeIdx`, `scheduleStepAdvance`, `stepTimerId`) without touching polling/202/429 lifecycle.
- **What slipped:** Shipped the `text-lime` spinner — correct given the prompt, but no independent brand check. Not a fault; the gate caught it.

### architect-reviewer (Phase 3)
- **What went RIGHT:** APPROVED with HIGH confidence, correctly mapped AC11–AC14 (preserve-untouched) and declared schema-freeze N/A. Did not over-engineer a UI restyle.
- **What slipped:** Did not flag the `text-lime`-on-cream contrast in the proposed snippet (arguably out of architect scope; it's a brand/a11y concern, caught at Phase 5 as intended).

### code-reviewer (Phase 5) — STAR OF THE CYCLE
- **What went RIGHT:** Caught the IMPORTANT contrast bug **and** correctly diagnosed that it came from a flawed precedent rather than a fresh mistake. This is exactly the kind of "don't trust the precedent" skepticism the rest of the pipeline lacked. Also caught the stale comment. Tight, correct, no false positives.

## 4) Systemic Issues

**S1 — "Reuse precedent" can propagate latent bugs.** The cycle's contrast bug did not originate in this cycle; it was copied from `PagoConfirmacionPage.vue:114`, which has had a lime-on-cream spinner (~1.08:1, fails WCAG 1.4.3) since before DD1067. The story cited it as a *good* reuse target. A grep confirms the latent bug is broader than the brief stated:
- `PagoConfirmacionPage.vue:114` — `Loader2 ... text-lime` on cream (loading state)
- `PagoConfirmacionPage.vue:125` — `Loader2 ... text-lime` on cream (confirming state)
- `PagoConfirmacionPage.vue:170` — `CheckCircle2 ... text-lime` on cream (success icon) **← additional instance not in the brief**
- (`:174` is `text-lime` on `bg-ink` — correct usage; `:233` needs a surface check)

**S2 — The orchestrator's context digest (Rule T1) can launder a latent bug.** The pre-cooked digest embedded the bad precedent snippet verbatim, presented as a trusted reference. The digest is an amplifier: a single flawed snippet is copied into every downstream prompt. The architect/reviewer caught it this time, but the digest should be **skeptical of precedents** — especially color/contrast on light surfaces — rather than treating "it exists in the repo" as "it is correct."

**S3 — No automated guard for lime-on-light.** The brand rule "lime is the only accent, never as text/foreground on light surfaces" (CLAUDE.md §20, MASTER §6 anti-patterns) is enforced only by human review. A grep/eslint guard would have caught all four instances pre-review.

## 5) Workflow Improvements (Concrete)
1. **Skeptical digest:** when the orchestrator pre-cooks a Rule-T1 digest containing a color/spacing/contrast snippet, annotate it with a one-line brand check (or mark it "verify against MASTER §6") rather than presenting it as canonical.
2. **Precedent ≠ proof:** story-refiner should not phrase precedent reuse as a positive AC unless the precedent has been brand/a11y-sanity-checked. Cite the precedent for *structure* (markup, sizing, motion), not necessarily *color*.
3. **Lime-on-light grep guard:** add a cheap repo guard (grep or eslint) that flags `text-lime` / lime-as-foreground outside `bg-ink`/dark contexts.
4. **Follow-up the latent bug now:** fix `PagoConfirmacionPage.vue:114`, `:125`, and `:170` (`text-lime` → `text-ink`) — the spinner/icon should be ink on cream, matching the corrected `PeritoProcesando.vue`.

## 6) Patches Proposed

Kept proportional — this was a clean, low-risk cycle. All suggestions are **project-layer** (the lesson is GuaiHome-brand-specific, not a universal framework defect).

```
- Type: project-layer
- Target: .claude/project/conventions/brand-lime-on-light.md (new)
- Change: "Lime (#CCFF00) is background-only on light surfaces (paper #FAF9F6).
  Never use `text-lime` (or lime as icon/stroke foreground) on cream/light backgrounds —
  contrast ≈ 1.08:1, fails WCAG 1.4.3. On light surfaces, spinners/icons/accent text must be
  `text-ink`; lime appears only as `bg-lime` (with `text-ink` on top) for marker highlights.
  Lime-as-foreground is valid ONLY on dark surfaces (`bg-ink` / dark cards).
  Reviewers and story-refiner: do not cite a repo precedent that violates this as a reuse target.
  Known latent offenders to remediate: PagoConfirmacionPage.vue:114, :125, :170."
```

```
- Type: project-layer
- Target: .claude/project/lessons-learned/digest-precedent-skepticism.md (new; applies_to: kuraka, story-refiner, frontend-developer, final-auditor)
- Change: "When pre-cooking a Rule-T1 context digest or citing a 'reuse repo precedent' snippet,
  do NOT treat 'it exists in the repo' as 'it is correct'. Color/contrast/spacing snippets must be
  sanity-checked against design-system MASTER §6 before being embedded. DD1067 propagated a
  lime-on-cream contrast bug from PagoConfirmacionPage.vue into a new file via the digest; only the
  Phase-5 code-reviewer's skepticism caught it. Mark digest color snippets 'verify vs MASTER §6'."
```

No framework patches proposed — the pipeline behaved correctly; the gap is a project-specific brand convention plus a digest-hygiene habit.

## 7) Next-Requirement Guardrails
- **Mandatory pre-implementation checks:** any story that introduces or reuses an accent color on a light/cream surface must cite MASTER §6 and confirm the color is `bg-` not `text-`/foreground.
- **Mandatory naming checks:** n/a (no new identifiers/tables/endpoints this cycle).
- **Mandatory schema checks:** n/a (no DB).
- **Digest hygiene:** color snippets in any Rule-T1 digest carry a "verify vs MASTER §6" annotation.

## 8) Token & Latency Telemetry

Ranked by `total_tokens` descending.

| Phase | Agent | Tokens | Tool uses | Duration | Produced | Notes |
|-------|-------|-------:|----------:|---------:|----------|-------|
| 3 | architect-reviewer | 49,957 | 3 | 44.2 s | APPROVED, HIGH confidence | Highest spend for a UI-only restyle; slightly heavy vs task |
| 1+2 | po-analyst (LITE_COMBINED) | 49,654 | 3 | 434.4 s | REQ + 17-AC mapping story; GATE0 clean | Longest wall-clock (7.2 min); thorough scope-lock justifies it |
| 4b | frontend-developer | 43,439 | 15 | 92.5 s | restyle, 17/17 AC, gates green | Tool-use count reasonable for edit+verify |
| 5 | code-reviewer | 39,385 | 9 | 70.0 s | APPROVED_WITH_MINOR (1 IMPORTANT + 1 MINOR) | Best value-per-token of the cycle — caught the latent bug |
| 5-fix | frontend-developer | 33,559 | 4 | 29.9 s | applied fixes, gates green | Lean, focused |

**Totals:** `215,994` tokens across `5` agent runs.

**Observations:**
- Total ~216K for a single-file UI restyle is acceptable but the two review/analysis phases (architect 50K, po-analyst 50K) dominate at ~46% combined. For a one-file cosmetic change, the architect phase is the weakest-justified spend — consider folding architect into a lighter checkpoint for pure restyles (it added little here beyond confirming the preserve-untouched mapping the story already locked).
- po-analyst wall-clock (434s) is 5–10× any other phase; tokens are normal, so the time is reasoning/think latency, not context bloat. Acceptable for a combined Phase 1+2 with a real-file GATE0 verification.
- code-reviewer was the highest-leverage spend: 39K tokens prevented a brand/WCAG bug from shipping (and surfaced a broader latent-bug class).

**Optimization backlog** (carry into next cycle):
- [ ] For pure-restyle surfaces, evaluate skipping or de-weighting Phase 3 (architect) when the story already locks preserve-untouched symbols at GATE0 — could save ~50K.
- [ ] Embed the lime-on-light grep guard so the contrast class never reaches review (shifts the catch left, frees reviewer tokens).
- [ ] Annotate Rule-T1 digest color snippets with "verify vs MASTER §6" to avoid laundering latent bugs (zero token cost, prevents a fix cycle).
