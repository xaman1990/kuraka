# Final Audit - REQ-20260613-permission-route-normalize

## 1) Summary
- Total iterations: **low** (1 review loop: APPROVED_WITH_MINOR → 1 IMPORTANT fix → PASS).
- Main causes: a **latent defect from the prior cycle** (REQ-20260612-vet-veterinarian) where
  `PermissionService` matched `X-Acc` menu links verbatim, assuming a leading slash that the
  backend does not always send (`vet/veterinarian` vs `/vet/veterinarian`). The frontend did not
  tolerate the backend data inconsistency, so all `*appCanAccess` controls were hidden.
- Estimated preventable iterations: **0 within this cycle** (clean, minimal-loop fix). The
  *defect itself* (1 extra full cycle) was preventable upstream — see Systemic Issues.

## 2) Timeline of Rework

| Phase | Issue | Root Cause | Preventable? | Fix |
|-------|-------|-----------|--------------|-----|
| (Prior cycle) | Veterinarian controls hidden after smoke | `buildPermissionsMap`/`findPermissionRoute` matched route strings verbatim; no slash normalization | Yes (upstream) | This entire cycle |
| Analysis (1) | — | — | — | Combined REQ+story produced precise root cause + zero-regression AC table; no rework |
| Implementation (4b) | — | — | — | `normalizePath` helper + 2 call-site edits; `ng build` PASS first try (commit 108bc87) |
| Review (5) | `normalizePath('')` returned `''` instead of `'/'` | Edge case for empty input not handled | Partial | 1 IMPORTANT raised by reviewer, fixed in commit 9db9eea |
| Smoke (6.8) | — | — | — | Live PASS: vet controls visible, list error contained, customer regression OK (commit e8405eb) |

## 3) Agent Findings

### po-analyst (combined REQ+story)
- What went RIGHT: The combined-mode REQ pinned the root cause to exact file/line, documented the
  decoded `X-Acc` evidence, and ships an **idempotency + edge-case AC table** (including `/` and
  `''`) that pre-empted most of the review surface. Strong zero-regression framing (S1-AC4).
- Minor gap: AC-1 documented `''` → `/` as "documented; no key collision expected" but did **not**
  flag it as a *must-implement* line — the reviewer had to catch that the implementation returned
  `''`. Tightening: when an AC table lists an edge case, mark which rows are normative vs
  illustrative so the implementer cannot treat them as optional.

### frontend-developer
- What went RIGHT: Minimal additive change (one private pure helper + two call sites), no public
  signature change, build green first pass. Respected the "no substring matching" constraint.
- The `''` edge case slipped through — covered by the review gate, so no escape to smoke.

### code-reviewer (+ security folded)
- What went RIGHT: Correctly folded security (auth-wide blast radius) into one pass with zero
  escalation, and caught the one real edge-case bug (`normalizePath('')` must return `'/'`) before
  smoke. This is exactly the value of the mandatory Phase 5 on an auth-path change.

## 4) Systemic Issues
- **The prior cycle's smoke could not exercise permission matching.** At smoke time of
  REQ-20260612-vet-veterinarian, `/vet/veterinarian` had **zero `X-Acc` accesses** configured, so
  "all controls hidden" looked like the expected no-access state (F28) rather than a matching bug.
  The matching defect only became observable once the backend node *did* carry accesses (with the
  malformed slash). A smoke that observes "all controls hidden" is **ambiguous**: it can mean
  (a) no access granted, or (b) a matching bug. The prior cycle closed on interpretation (a).
- **The frontend trusted backend data hygiene.** `Menu.link` is an *external* string; the code
  assumed a leading slash invariant that the backend does not guarantee.
- Telemetry file present and well-formed (no gap to note).

## 5) Workflow Improvements (Concrete)
1. **Disambiguate "all controls hidden" in any `*appCanAccess` smoke.** When a smoke observes a
   gated screen rendering nothing, the smoke MUST decode the live `X-Acc` and state explicitly
   whether the route has zero accesses (expected) or has accesses that fail to match (bug). Do not
   close a cycle on "hidden = no access" without that check.
2. **Treat external route strings as untrusted at the boundary.** Any code that matches/keys on a
   backend-provided route (`Menu.link`, `url` in modcat) normalizes leading/trailing slash before
   comparison. Codify as a project-layer convention (section 6).
3. **Mark normative vs illustrative rows in AC edge-case tables** so implementers don't skip them.

## 6) Patches Proposed

- Type: **project-layer**
- Target: `.claude/project/conventions/permission-route-matching.md` (new)
- Change:
  ```markdown
  # Convention — Permission / route matching must normalize slashes

  Backend `X-Acc` menu links are NOT slash-consistent: some nodes arrive as
  `/vet/customer` (leading slash) and others as `vet/veterinarian` (none).
  Angular's `router.url` ALWAYS carries a leading slash.

  Rule: any code that builds keys from, or matches against, a backend-provided
  route string (e.g. `Menu.link`, modcat `url`) MUST normalize it first:
  exactly one leading `/`, no trailing `/`, root `/` preserved, `''` → `/`.
  Reference impl: `PermissionService.normalizePath` (commit 9db9eea).
  Do NOT loosen matching to substring/contains — keep exact + `route + '/'`
  prefix semantics.

  Smoke rule: when a gated screen renders no controls, DECODE the live `X-Acc`
  and record whether the cause is "zero accesses" (expected) or "accesses
  present but not matching" (bug). Never close a cycle on the ambiguity.
  ```

- Type: **project-layer**
- Target: `.claude/project/lessons-learned/smoke-disambiguate-no-access.md` (new; `applies_to:
  [e2e-tester, final-auditor, frontend-developer]`)
- Change: Capture the systemic lesson from §4 so a future `*appCanAccess` cycle does not re-close
  on "hidden = no access" without decoding `X-Acc`.

## 7) Next-Requirement Guardrails
- **Pre-implementation:** for any change in the authorization match path, keep Phase 5
  (security-folded) + Phase 6.8 live smoke non-skippable (this cycle confirmed their value).
- **Naming:** none new.
- **Schema:** none.
- **Smoke:** for `*appCanAccess` screens, decode live `X-Acc` and classify hidden-controls cause.

## 8) Token & Latency Telemetry

Ranked by `total_tokens` descending.

| Phase | Agent | Tokens | Tool uses | Duration | Produced | Notes |
|-------|-------|-------:|----------:|---------:|----------|-------|
| 1 | po-analyst (combined REQ+story) | 89,051 | 2 | 63.7s | REQ + S1 story, zero-regression AC | Highest cost; justified — combined mode + precise root-cause evidence |
| 5 | code-reviewer (+security folded) | 74,027 | 6 | 62.0s | APPROVED_WITH_MINOR, 1 IMPORTANT | Folded security into one pass; caught the `''` edge case |
| 4b | frontend-developer | 69,214 | 4 | 30.6s | normalizePath + 2 edits, build PASS, 108bc87 | Tight, fastest phase |

**Totals:** `232,292` tokens across `3` agent runs.

**Observations:**
- Cost is well-distributed and modest for an auth-path fix; no agent is disproportionate. The
  combined REQ+story (Rule T3) avoided a separate story-refiner run.
- No phase looks bloated relative to its output. Reduced-by-risk pipeline (4 active phases of ~13)
  was the correct scaling for a single-file additive normalization with auth blast radius.

**Optimization backlog** (carry into next cycle):
- [ ] When the AC table fully specifies a pure helper, the implementer prompt can forbid
      re-reading the REQ beyond the embedded story (the story already carries the table) — small
      Phase 4b savings.
