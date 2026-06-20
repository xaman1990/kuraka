# Final Audit — REQ-20260611-mvp1-registro-perito-webhook

**Mode:** Normal (8 phases) + delta re-analysis + BE-webhook re-cycle · **Date:** 2026-06-11
**Result:** Registro + cliente flow live (browser-verified) · webhook **real** contract green in 6.8 smoke (`200`, persists `PeritoAnalysis total=87.73` + 4 valuation lines, idempotent, `401` on bad `X-API-Key`) · 0 CRITICAL / 0 open HIGH security (2 MEDIUM SSRF residual, FIX-16 optional) · **Pending real e2e** (ngrok + guAI panel config).
**Scope of audit:** the full cycle as captured in `agent-telemetry/REQ-20260611-mvp1-registro-perito-webhook-telemetry.json` (39 token-bearing runs) + checkpoint `checkpoints/REQ-20260611-...-state.json`.

> The user explicitly requested honest, actionable feedback "para mejorarlo con todas las observaciones y ajustes". This retro names the agent and the line, quantifies the cost from telemetry, and proposes concrete prompt patches / project-layer files.

---

## 1) Summary

- **Total iterations: HIGH.** 39 token-bearing agent runs, ~**4.16M tokens** total. A *single MVP* (registro + perito launch + webhook) was effectively built **twice**: once against an assumed frontend flow + assumed webhook contract (Phases 1→5.5), then re-analyzed (ADDENDUM, 195K tok) and re-built across a delta-fix FE group, a series of live reactive fixes, and a full BE-webhook re-cycle (refine → architect → 5 implement rounds → 6.8 smoke → re-security).
- **Main causes of rework (ranked by cost):**
  1. **Specs not read line-by-line in Phase 1** → the whole frontend flow diverged from the prototype (login-first, inverted routing, no inline registration modal, no map pin, perito window never opened). Required the **ADDENDUM** (195K) + a 154K FE rework + ~5 reactive live-fix rounds (~330K). **Earliest catch: Phase 1 (po-analyst).**
  2. **Integration contract assumed, not obtained** → webhook (S5, 150K) was built against a fabricated contract (`X-GuAI-Signature` HMAC, a progress event, price via DOCX). The **real** guAI contract (`X-API-Key`, only `completed`/`escalated`, informe in JSON, idempotency by `recopilacionId`, evidence 24h) arrived from the user only *after* implementation, forcing a complete BE re-cycle (FIX-6..15, ~1.5M tok across implement+review). **Earliest catch: Phase 1 GATE0 (should have blocked on "obtain the real payload").**
  3. **False green on the test gate** → orchestrator piped `make … | tail`, read `tail`'s exit code as success, and advanced S3 while the suite was failing at *collection* (a pre-existing Sentry/jinja2 infra bug). **Earliest catch: the gate itself — never pipe the command whose exit code is the gate.**
  4. **Pre-existing infra bug hidden until the real stack ran** → `init_sentry` imported `Jinja2Templates`, `jinja2` was not in `requirements.txt`; the app would not boot in dev/prod and pytest could not collect. Cost S0 + two `review-setup` rounds. **Earliest catch: run the real stack (boot + 1 real request) in Phase 0/early Phase 4.**
  5. **Outgoing payload under-populated vs provider contract** → `create_claim` sent only the insured name; the user noticed cases lacked their data. Fixed in FIX-15. **Earliest catch: a "verify the outgoing payload against the provider contract" check at implementation/review time.**
- **Estimated preventable iterations: ~6–7 loops** of the ~12 distinct rework rounds. Specifically: the entire FE rework + reactive rounds (1 root cause, preventable), the webhook rebuild (1 root cause, preventable by obtaining the contract first), the false-green re-gate (preventable), the jinja2/Sentry rounds (preventable), the `create_claim` gap (preventable). Genuinely *not* preventable: the 6.8-smoke 422 catch (that is the smoke phase doing its job) and a few test-only seed/signature fixups inherent to renaming a column.

---

## 2) Timeline of Rework

| Phase | Issue | Root Cause | Preventable? | Earliest catch | Fix |
|-------|-------|-----------|--------------|----------------|-----|
| 1 (po-analyst) | Frontend flow diverged from prototype (login-first, inverted routing, no inline registration modal, no map pin, perito window never opened) | Analysis not anchored in `docs/spec-driven` (03/12/21/22) nor the React prototype line-by-line | **Yes** | Phase 1 | ADDENDUM re-analysis (195K) + FE rework S-group (154K) + ~5 reactive live-fix rounds |
| 1 / GATE0 | Webhook built on a fabricated contract (`X-GuAI-Signature` HMAC, progress event, price via DOCX) | Integration contract **assumed**, not obtained from guAI before implementing | **Yes** | Phase 1 GATE0 (should block: "no real payload → no implementation") | Full BE re-cycle: FIX-6 (`X-API-Key`), FIX-7 (drop progress), FIX-8 (real payload+idempotency), FIX-9 (informe JSON) |
| 4a (S3 gate) | **False green**: S3 advanced while suite failed at collection | Orchestrator ran `make … | tail`; gate read `tail`'s exit code, not `make`'s | **Yes** | The gate itself | Re-gate after S0 infra fix; thereafter used `make test-run` exit code (no pipe) |
| 4a (S1/S3) | App could not boot; pytest could not collect | Pre-existing infra: `init_sentry` imports `Jinja2Templates`; `jinja2` missing from `requirements.txt` | **Yes** | Phase 0 / early Phase 4 (boot the real stack) | S0 (skip Sentry in testing) + `review-setup` ×2 (add jinja2; Sentry init only in prod) |
| 4a (S4/S6) | Several "N test failures" re-gates (6 in S3, 21 in S6) | Column rename (`recopilacion_id`→`external_session_id`) + auth migration (`anon_token`→`user_id`) left stale seeds/signatures in pre-existing tests | **Partial** | Phase 3 (architect could enumerate every test fixture touching the renamed column) | test-only fixups; no prod bug — but the re-gate churn was real |
| 1-delta → 4-BE | Webhook rebuilt end-to-end (auth, events, payload, persistence, evidence, rate-limit, layering) | Consequence of cause #2 | **Yes** | (same as #2) | FIX-6..14 across 5 implement rounds + architect re-review |
| 6.8 (smoke) | `WebhookInformePayload.conclusions`/`video` typed `str`; guAI sends objects → `422` | Schema field types guessed from prose, not from a real payload sample | **No** (this is exactly what 6.8 exists to catch) | 6.8 smoke (worked as intended) | `Optional[dict]` + `_extract_conclusions_narrative`; re-smoke green |
| 4-BE (FIX-15) | `create_claim` sent only insured name; user's cases lacked user data | Outgoing payload not validated against the provider's `POST /claims` contract | **Yes** | Implementation/code-review (compare emitted payload to contract) | FIX-15: send first/last name, email, phone, address, postal, city, language |
| (process) | Reactive live-fix rounds outside the phased flow ("Soy nuevo" redirect, router guard, Google Maps, autofill, live-enable, 429) | Discipline drift: debugging in-vivo instead of re-anchoring in Kuraka phases | **Partial** | Continuous | User asked to re-anchor; BE-webhook was then re-cycled properly (refine→architect→implement→smoke→security) |

---

## 3) Agent Findings

### po-analyst (Phase 1 — 129,578 tok / 19 tools; Phase 1-delta — 195,396 tok / 41 tools)
- **What went RIGHT:** Phase-1 GATE0 *did* block on three real questions (webhook push vs poll, tracking Option A/B, field rename `recopilacion_id`→`external_session_id`). The rename decision was clean and propagated correctly. The 1-delta ADDENDUM is an excellent forensic document — root-causes the broken flow to exact files/lines (`AccesoPage.vue:28`, `PeritoConectando.vue:23-27`, `router/index.ts:26-30`) and reproduces the real guAI contract with citations.
- **What FAILED (the central lesson):**
  1. The **initial** Phase-1 analysis was **not anchored in `docs/spec-driven`** (03_IA, 12_JOURNEY, 21_USE_CASES, 22_NAVIGATION) nor in the React prototype line-by-line. The frontend was specified against an assumption, so it shipped login-first inverted, registration as a separate page (not the inline `Datos.tsx:302-380` modal), no map pin, and a perito window that never opened. This is the single most expensive miss of the cycle.
  2. GATE0 asked *whether* guAI pushes webhooks but **did not block on obtaining the real payload/header/auth scheme** before designing S5. "We will receive a webhook" was treated as enough to design against — it was not.
  3. Even the ADDENDUM admits specs `04_CONTENT_COPY`, `09_ACCEPTANCE_CRITERIA`, `23_ALERTS`, `24_REALTIME` were **not read line-by-line** (deferred to FIX-12) — the same gap, smaller.
- **Patch (see §6):** project-layer `po-analyst.md` review-check mandating (a) for any change touching the cliente flow, read the named spec-driven docs **and** the prototype routes line-by-line and produce a step-by-step prototype↔plan comparison table *before* GATE0; (b) for any external integration, GATE0 **BLOCKS** until a real captured payload + auth header + event list is in hand — never design against an assumed contract.

### story-refiner (Phase 2 — 121,006 tok / 57 tools, ~13min; Phase 2-BE — 121,229 tok / 33 tools, ~11min)
- **What went RIGHT:** The Phase-2-BE refinement is exemplary — 8 FIX stories correctly scoped, flagged schema gaps for the architect (iva_pct, informe blocks JSONB-vs-defer, expedienteId mapping), folded the 429 root cause into FIX-7, and explicitly mandated **sequential implementation + `make test` per story (Rule T6)**. That discipline is exactly what the project's own rule 17 prescribes.
- **What FAILED:** In Phase 2 (original), it inherited the PO's un-anchored flow and refined S8 (frontend) against it — so the story carried the wrong routing/registration model downstream. It also did not pre-enumerate the pre-existing tests that referenced `recopilacion_id` / `anon_token`, so the column/auth renames produced "6 failures" (S3) and "21 failures" (S6) re-gates downstream.
- **Patch:** project-layer check — when a story renames a column or changes an auth parameter, the story header must list every existing test/fixture/seed that references the old name (a `grep` inventory), so the implementer fixes them in-story rather than discovering them at the gate.

### test-engineer (Phase 2.5 plan — 111,790 tok; Phase 2.5 E2E addendum — 71,023 tok)
- **What went RIGHT:** 108 tests across S1–S8 with 3 sharp critical cases (webhook auth, idempotency, IDOR) and a Playwright E2E section with 16 `data-testid`s. The IDOR and idempotency emphasis paid off — both held through the whole cycle.
- **What FAILED:** The webhook test plan was written against the **assumed** contract (HMAC signature, progress event) — so the 108-test suite could be fully green while testing the wrong contract. The plan had no "exercise the real provider payload" step, which is why a green suite still failed the 6.8 smoke (`conclusions` dict vs str → 422).
- **Patch:** test-plan must include, for every external integration, a **"real-payload reality check"** — at least one test fixture built from a captured/real provider payload (not a hand-authored ideal), and a note that suite-green does not substitute for the 6.8 smoke against the live contract.

### architect-reviewer (Phase 3 — 152,953 tok / 35 tools, `budget_ok=false`; Phase 3-BE — 103,628 tok / 22 tools)
- **What went RIGHT (strong):** Phase 3 caught a real BLOCKER B1 (an impossible grep-gate AC on S3-AC10) and I1 (seed_demo.py), froze the `perito_sessions` schema cleanly (partial unique index, `''`→NULL backfill). Phase 3-BE caught that **FIX-7 did not actually kill the 429** (`poll.py:81` still called guAI) and forced the expansion — a genuinely valuable catch that prevented shipping a "fix" that didn't fix. The 152K over-budget was justified by deep real-code reading.
- **What FAILED:** The architect reviewed S5's webhook design against the **assumed** contract without flagging "this contract is unconfirmed — do not freeze the signature scheme until the real header is known." A schema/contract reviewer is the right place to demand the upstream contract as evidence. It also froze the schema while the renamed column's downstream test fixtures were not enumerated (contributing to the S3/S6 re-gates).
- **Patch:** architect review-check — for any story that depends on an external contract, the verdict must include a "contract provenance" line: cite the source of the contract (real doc / captured payload), or raise a BLOCKER if it is assumed.

### backend-developer (Phase 4a ×9 + Phase 4-BE ×5 + 6.8 + setup — ~1.9M tok total)
- **What went RIGHT:** Once the gate was honest, every BD story closed green via `make test-run` (exit 0, no pipe). Strong work: HMAC-then-`X-API-Key` verified **before** body parse with `compare_digest`; idempotency by `recopilacionId`; the `analysis_writer.py` and `pipeline.py` extractions that **broke a circular import** (also satisfying FIX-14d); the BackgroundTask given a **fresh `SessionLocal()`** (resolving security MEDIUM M1); SSRF host allowlist (M2 partial); and the FIX-15 defensive name-split + `None`-omission for `create_claim`. The 6.8 fix used a **real guAI payload** as the test fixture — exactly right.
- **What FAILED:** Nothing attributable to the developer as a logic defect. The cost it *absorbed* (webhook rebuild, flow rework, repeated test-fixups) originated upstream (PO/architect/contract) or from the false-green gate. Note for budget: the S5 run was ~77min / 150K and FIX-13+14 combined >180K (`budget_ok=false`) — both completed, but signal that security-critical stories should be split smaller.

### frontend-developer (delta-fix-4b — 153,988 tok + 5 reactive rounds — ~307K tok)
- **What went RIGHT:** The FE rework correctly rebuilt the cliente flow to match the prototype (login-first `/cliente`=Acceso, login→Datos, inline ≥8-char password modal, MapModal with geolocation+reverse-geocode, `window.open(signedUrl)`), **browser-verified end-to-end with Playwright**, type-check 0 + vitest green at every round. The root-cause of the "Soy nuevo → login window" bug (stale token → guard `fetchMe` 401 → `logout()` rethrow → router crash / 401-interceptor redirect) was diagnosed precisely and fixed with 5 new guard tests.
- **What FAILED:** Not the developer's fault — it was handed the wrong flow by Phase 1/2 and had to reconstruct it. The 5 reactive rounds (redirect, guard, maps, autofill, live-enable) were *outside* the phased flow (the discipline-drift the user flagged); they succeeded but at a churn cost a single correctly-scoped FE re-story would have avoided.

### code-reviewer (Phase 5 — 146,135 tok / 118 tools)
- **What went RIGHT:** APPROVED_WITH_MINOR with 4 actionable IMPORTANTs that proved real: the layer violation (`db.commit` in webhook service), two test gaps (AC15/16, AC18), and a deferred import — all later settled in FIX-14. 3 PRAISE items. Good signal-to-noise.
- **What FAILED:** Reviewed the implementation of the **assumed** contract; could not catch the contract-level wrongness (that is upstream). Did not flag that `create_claim` under-populated the outgoing payload — a code-review check comparing the emitted integration payload to the provider contract would have caught FIX-15 before the user did.
- **Patch:** code-review checklist addition — for any outbound integration call, compare the constructed payload field-by-field to the provider contract doc; flag any contract field that is silently omitted.

### migration-reviewer (Phase 5 — 73,480 tok / 24 tools)
- **What went RIGHT:** APPROVED_WITH_NOTES, 0 blockers; correctly flagged the one-shot rename needing a maintenance window, the partial index without `CONCURRENTLY` (Alembic limit, small table OK), the one-way backfill, and that downgrade is not CI-tested. Proportionate and correct for an additive+rename migration.
- **What FAILED:** Nothing material.

### security-reviewer (Phase 5.5 — 99,653 tok; Phase 5.5-BE — 91,274 tok)
- **What went RIGHT:** First pass flagged exactly the two HIGHs that mattered — **webhook header name unconfirmed** (HIGH-1) and **no rate limit** (HIGH-2) — plus the BackgroundTask-shares-request-session MEDIUM (M1) and SSRF (M2). The re-security pass confirmed HIGH-1/HIGH-2/M1 RESOLVED and M2 PARTIAL. Secret scan clean both times; IDOR verified. This agent essentially *predicted* the contract problem (HIGH-1 "header unconfirmed") — a strong signal the team should have escalated to "stop and get the contract" earlier.
- **What FAILED:** Nothing in execution. The lesson is organizational: HIGH-1 ("header unconfirmed") was raised but not treated as a hard stop — it should have triggered the contract-acquisition block.

---

## 4) Systemic Issues

1. **Specs/prototype not read to the depth the change demanded (po-analyst).** A cliente-flow change was analyzed without a line-by-line prototype↔plan diff. → Mandate the diff before GATE0 for any flow-touching change (§6 P1).
2. **Integration contract assumed instead of obtained (orchestration + po-analyst).** S5 was designed and built against a fabricated webhook contract; the real one arrived post-implementation. → GATE0 must BLOCK on a real captured payload/header/event-list before any integration story is designed (§6 P1, P3).
3. **False green: gate exit code masked by a pipe (orchestration).** `make … | tail` made the gate read `tail`'s exit code. → Never pipe the command whose exit code is the gate; assert on `make`'s own exit code (§6 P2). This is also a token-cost: `| tail` plus RTK rewriting made test output hard to read, encouraging the masking.
4. **Pre-existing infra bug surfaced only when the real stack ran (jinja2/Sentry).** The app could not boot and pytest could not collect, undetected until a real run. → Add a Phase-0 "boot the real stack + one real request" smoke before implementation (§6 P4).
5. **Green ≠ working — the 6.8 smoke caught what a green suite + green reviews did not** (`conclusions` dict vs str → 422). This is the system working *as designed*; reinforce that 6.8 is non-skippable for external-contract changes (§6 P5).
6. **Outgoing payload under-populated vs provider contract (`create_claim`).** Caught by user observation, not by review. → Code-review + implementer check: diff the emitted payload against the provider contract (§6 P6).
7. **Phase discipline drift: reactive in-vivo fixes outside Kuraka.** The FE redirect/guard/maps/autofill/live-enable rounds ran ad hoc; the user asked to re-anchor, after which the BE-webhook was re-cycled properly. → When >2 reactive fixes stack on one surface, stop and open a proper delta-story group (§6 P7).
8. **`| tail` / RTK obscured test results.** Reading the gate through a pipe (and RTK rewriting) cost tokens and hid the collection error. → Read the raw exit code; for gates, don't pipe (§6 P2).

---

## 5) Workflow Improvements (Concrete)

1. **Flow-fidelity gate (Phase 1):** for any change touching the cliente journey, the po-analyst output MUST contain a prototype↔plan step-by-step comparison table (file:line on both sides) and cite the relevant `docs/spec-driven` docs read line-by-line. No GATE0 pass without it.
2. **Contract-first gate (Phase 1 GATE0):** for any external integration, GATE0 BLOCKS until a real captured payload + auth header + event list exists. "We will receive a webhook" is not a contract.
3. **Honest gate command (orchestration):** run the gate as `make test-run` (or equivalent) with **no pipe**; assert on its exit code. If output must be trimmed, capture to a file and read the file, but never let a pipe own the exit status.
4. **Phase-0 real-stack smoke:** before Phase 4, boot the actual dev stack (`make up`) and hit one real endpoint + run `make test-run` once to surface pre-existing infra bugs (missing deps, broken init) before they masquerade as story failures.
5. **Outgoing-payload contract diff (Phase 4 + Phase 5):** every outbound integration call is checked field-by-field against the provider contract; silently omitted contract fields are flagged.
6. **Reactive-fix circuit breaker (orchestration):** after 2 ad-hoc fixes on the same surface, stop and open a delta-story group (refine → architect → implement → smoke), as was eventually done for BE-webhook.
7. **Split security-critical stories:** stories like S5 (webhook, ~77min/150K) and FIX-13+14 (>180K) should be split so each stays under budget and re-gates are cheaper.

---

## 6) Patches Proposed

> Preference: **project-layer additions** (this project's patterns are project-specific). Two patches are framework-worthy because they are universal (the false-green gate and contract-first).

### P1 — Flow-fidelity + contract-first for po-analyst (project-layer, NEW)
- **Type:** project-layer
- **Target:** `.claude/project/review-checks/po-analyst.md` (new file)
- **Change (exact text to add):**
  ```markdown
  # po-analyst project review-checks (GuaiHome)

  ## Flow-fidelity (any change touching the cliente journey)
  - BEFORE GATE0, read line-by-line: docs/spec-driven/03_INFORMATION_ARCHITECTURE_UX.md,
    12_JOURNEY_FLOW_SPEC.md, 21_USE_CASES.md, 22_NAVIGATION_MAP.md, and the React
    prototype routes under ../prototype-react/src/routes/cliente/*.
  - Produce a prototype↔plan comparison table (file:line on BOTH sides) for every
    step of the flow. No GATE0 pass without it.
  - Reference cycle: REQ-20260611 shipped login-first inverted, registration as a
    page (not the inline Datos.tsx:302-380 modal), no map pin, perito window never
    opened — because this table was skipped. Cost: ADDENDUM (195K) + FE rework (154K)
    + ~5 reactive rounds (~330K).

  ## Contract-first (any external integration)
  - GATE0 BLOCKS until a REAL captured payload + auth header + event list is in hand.
  - "We will receive a webhook" is NOT a contract. Do not design auth scheme, event
    set, or payload schema from assumption.
  - Reference cycle: S5 webhook was built on a fabricated contract (X-GuAI-Signature
    HMAC, progress event, price via DOCX); the real one (X-API-Key, completed/escalated
    only, informe JSON, idempotency by recopilacionId) arrived post-implementation and
    forced a full BE re-cycle (FIX-6..15).
  ```

### P2 — Honest gate command (framework-worthy + project-layer)
- **Type:** framework / project-layer
- **Target (framework):** the orchestration rule that runs the post-story test gate (kuraka policies); **Target (project):** append to `.claude/rules/17-kuraka-token-optimizations.md`.
- **Change (exact text to add):**
  ```markdown
  ## Rule T7 — Never pipe the command whose exit code is the gate
  When the test/typecheck result is the gate, run it WITHOUT a pipe and assert on
  its own exit code (e.g. `make test-run`, then check `$?`). NEVER `make ... | tail`
  — the shell reports the LAST command's exit code (tail's), so a failing suite reads
  as green. If output must be trimmed, redirect to a file and read the file; the gate
  still reads `make`'s exit code.
  Reference: REQ-20260611 S3 advanced on a FALSE GREEN (`make ... | tail`) while the
  suite was failing at collection (Sentry/jinja2 infra bug).
  ```

### P3 — Contract provenance line for architect-reviewer (project-layer, append)
- **Type:** project-layer
- **Target:** `.claude/agents/contexts/architect-reviewer-rules.md` (append)
- **Change (exact text to add):**
  ```markdown
  ## Contract provenance (integration stories)
  For any story that depends on an external contract (webhook, provider API), the
  verdict MUST include a "Contract provenance" line citing the source (real doc /
  captured payload). If the contract is assumed/unconfirmed, raise a BLOCKER and do
  not freeze the auth scheme, event set, or payload schema.
  Reference: REQ-20260611 froze S5 against an assumed webhook contract; the real
  contract differed on auth (X-API-Key), events (no progress), and price source (JSON).
  ```

### P4 — Phase-0 real-stack smoke (project-layer, append to lessons)
- **Type:** project-layer
- **Target:** `.claude/project/lessons-learned.md` (append, `applies_to: orchestrator, backend-developer`)
- **Change (exact text to add):**
  ```markdown
  ## Ciclo 2026-06-11 — Phase-0 real-stack smoke (boot before build)
  - Antes de Phase 4, arrancar el stack real (`make up`) y golpear UN endpoint real
    + correr `make test-run` UNA vez, para que los bugs de infra pre-existentes
    salgan ANTES de que disfracen fallos de story.
  - Bug de referencia: `init_sentry` importaba `Jinja2Templates` y `jinja2` no estaba
    en `requirements.txt` → la app no arrancaba en dev/prod y pytest no colectaba.
    Solo se vio al correr el stack real. Coste: S0 + 2 rondas review-setup.
  - Fix patrón: `init_sentry()` early-return salvo `is_prod()`; jinja2 solo necesario
    para la integración Starlette de Sentry en prod.
  ```

### P5 — Reinforce non-skippable 6.8 smoke for external contracts (project-layer, append)
- **Type:** project-layer
- **Target:** `.claude/project/lessons-learned.md` (append)
- **Change (exact text to add):**
  ```markdown
  ## Ciclo 2026-06-11 — green ≠ working (la 6.8 lo volvió a atrapar)
  - Suite verde + 3 reviews verdes, pero el contrato real fallaba: `conclusions`/`video`
    estaban tipados `str` y guAI los envía como objeto → 422. La 6.8 (smoke con payload
    REAL de guAI) lo detectó. La 6.8 es NO-SALTABLE para cambios de contrato externo.
  - Patrón: en el test-plan, al menos UN fixture construido desde un payload REAL del
    proveedor (no uno ideal escrito a mano).
  ```

### P6 — Outgoing-payload contract diff for code-reviewer (project-layer, append)
- **Type:** project-layer
- **Target:** `.claude/project/review-checklist.md` (append)
- **Change (exact text to add):**
  ```markdown
  ## Outbound integration payloads
  - For every outbound call to a provider (e.g. guAI `create_claim` / `POST /claims`),
    diff the constructed payload field-by-field against the provider contract doc.
    Flag any contract field that is silently omitted.
  - Reference: REQ-20260611 `create_claim` sent only the insured name; user-owned cases
    lacked the user's data. Fixed in FIX-15 (first/last name, email, phone, address,
    postal, city, language).
  ```

### P7 — Reactive-fix circuit breaker (project-layer, append)
- **Type:** project-layer
- **Target:** `.claude/rules/17-kuraka-token-optimizations.md` (append)
- **Change (exact text to add):**
  ```markdown
  ## Rule T8 — Reactive-fix circuit breaker
  After 2 ad-hoc "live" fixes on the same surface, STOP and open a proper delta-story
  group (refine → architect → implement → smoke → security) instead of continuing to
  debug in-vivo outside the phases.
  Reference: REQ-20260611 FE had ~5 reactive rounds (redirect, guard, maps, autofill,
  live-enable) before the user asked to re-anchor in Kuraka; the BE-webhook was then
  re-cycled properly and produced ~0 cross-story rework.
  ```

### Application record (2026-06-11 — user-approved)

| Patch | Type | Target applied | Status |
|-------|------|----------------|--------|
| P1 | project-layer | `.claude/project/review-checks/po-analyst.md` (NEW) | Applied (local-only) |
| P2 | framework | `.claude/skills/kuraka-policies.md` → new "Gate command integrity" section | Applied + synced to vault |
| P2 | project-layer | `.claude/rules/17-kuraka-token-optimizations.md` → Rule T7 | Applied (local-only) |
| P3 | project-layer | `.claude/project/review-checks/architect-reviewer.md` (NEW) | Applied (local-only) — placed in project review-checks (the loader `contexts/architect-reviewer-rules.md §3.2` reads this path), not appended to the framework contexts loader |
| P4 | project-layer | `.claude/project/lessons-learned.md` (append) | Applied (local-only) |
| P5 | project-layer | `.claude/project/lessons-learned.md` (append) | Applied (local-only) |
| P6 | project-layer | `.claude/project/review-checklist.md` (append) | Applied (local-only) |
| P7 | project-layer | `.claude/rules/17-kuraka-token-optimizations.md` → Rule T8 | Applied (local-only) |

Notes:
- `00-INDEX.md` updated to register `review-checks/` and `lessons-learned.md`.
- Vault backup mapping (`.claude/rules/16-agent-backup.md`) covers only agents/skills/commands/docs → only `kuraka-policies.md` was synced to the vault. All `.claude/project/` and `.claude/rules/` files are outside the mapping and were applied local-only.
- **Framework-repo pending (cross-project propagation):** `kuraka-policies.md` was editable locally and is applied + synced to the vault. If a separate upstream framework repo distinct from the vault is the canonical source, the P2 "Gate command integrity" change must still be re-mounted into other consumer projects (via `mount-kuraka`/`kuraka-update`) for them to inherit it. No patch required a manual edit in an external framework repo to be applied for THIS project.
- No `.claude/agents/` files were edited; `.claude/skills/kuraka-policies.md` was edited. A Claude Code restart is recommended so the updated skill is re-registered.

---

## 7) Next-Requirement Guardrails

- **Mandatory pre-implementation checks:**
  - [ ] If the change touches the cliente journey → prototype↔plan comparison table exists (P1).
  - [ ] If the change has an external integration → a real captured payload + auth header + event list is attached to the REQ before GATE0 passes (P1/P3).
  - [ ] Phase-0 real-stack smoke run (`make up` + one real request + one `make test-run`) before Phase 4 (P4).
- **Mandatory gate checks:**
  - [ ] Test gate run with NO pipe; assert on `make`'s own exit code (P2/T7).
  - [ ] 6.8 smoke against the real contract for any external-contract change; one real-payload fixture in the test plan (P5).
- **Mandatory naming/schema checks:**
  - [ ] Column rename / auth-param change → story header lists every existing test/fixture/seed referencing the old name (grep inventory).
  - [ ] Architect verdict carries a "Contract provenance" line for integration stories (P3).
- **Mandatory payload checks:**
  - [ ] Outbound integration payloads diffed field-by-field against the provider contract (P6).

---

## 8) Token & Latency Telemetry

Ranked by `total_tokens` descending. `budget_ok=false` flagged.

| Phase | Agent | Tokens | Tool uses | Duration | Produced | Notes |
|-------|-------|-------:|----------:|---------:|----------|-------|
| 4-BE | backend-developer | 221,877 | 88 | 14m47s | FIX-13 rate-limit + FIX-14 (pipeline.py extract, layer fix, AC tests) | **budget_ok=false** (combined >180K) — split next time |
| 1-delta | po-analyst | 195,396 | 41 | 5m12s | ADDENDUM (root-cause + real contract + 14 FIX stories) | Re-analysis = preventable if Phase 1 had read specs/prototype |
| 4-BE | backend-developer | 190,632 | 60 | 7m03s | FIX-10 evidence 24h BackgroundTask own session + SSRF allowlist | Covers security M1+M2; 2 test fixups |
| 3 | architect-reviewer | 152,953 | 35 | 7m30s | Arch review + SCHEMA-FROZEN perito_sessions; caught BLOCKER B1 | **budget_ok=false** — justified by deep real-code reading |
| 4-BE | backend-developer | 151,042 | 86 | 13m20s | FIX-6 X-API-Key + FIX-7 drop progress (kills 429) + FIX-8 real payload | 1 test fixup |
| 4a | backend-developer | 150,532 | 85 | 77m21s | S5 webhook (security-critical) | ~77min — split security-critical stories |
| delta-fix-4b | frontend-developer | 153,988 | 91 | 14m48s | Cliente flow rework to match prototype (browser-verified) | Rework from un-anchored Phase 1 |
| 4a | backend-developer | 162,129 | 83 | 12m43s | S6 result/status JWT owner-only + lazy-pull | 21-failure re-gate (stale anon_token tests) |
| 3-BE | (see architect 103,628) | — | — | — | — | — |
| 5 | code-reviewer | 146,135 | 118 | 7m18s | APPROVED_WITH_MINOR (4 IMPORTANT, all real) | Good S/N |
| 4a | backend-developer | 130,906 | 69 | 8m25s | S3 rename + migration | **FALSE GREEN gate** (`\| tail`) |
| 4-BE | backend-developer | 129,395 | 64 | 32m07s | FIX-9 persist valuation from informe JSON + analysis_writer extract | Breaks circular import (FIX-14d) |
| 4a | backend-developer | 125,607 | 67 | 8m49s | S4 perito/start signed_url + IDOR guard | demo-vs-live test fixup |
| 2-BE | story-refiner | 121,229 | 33 | 10m50s | 8 FIX stories (sequential + make test per T6) | Exemplary refinement |
| 2 | story-refiner | 121,006 | 57 | 13m19s | 8 stories (S1-S8) | >10min; carried un-anchored flow |
| 4a | backend-developer | 117,686 | 48 | 6m44s | S2 POST /cliente/cases JWT-gated | green |
| 4a | backend-developer | 116,520 | 51 | 7m22s | S6 test fixups (21, test-only) | re-gate churn |
| 2.5 | test-engineer | 111,790 | 27 | 5m58s | TEST-PLAN (108 tests) | written vs assumed contract |
| 4-BE | backend-developer | 103,853 | 59 | 6m43s | FIX-15 create_claim full user data | user-reported gap |
| 3-BE | architect-reviewer | 103,628 | 22 | 5m05s | Arch review BE + BLOCKER (FIX-7 didn't kill 429) | strong catch |
| 5.5 | security-reviewer | 99,653 | 26 | 2m56s | APPROVED_WITH_HIGH (HIGH-1 header unconfirmed, HIGH-2 no rate-limit) | predicted the contract problem |
| delta-fix-map | frontend-developer | 97,401 | 61 | 7m34s | MapModal interactive Google Maps | reactive round |
| 5.5-BE | security-reviewer | 91,274 | 20 | 3m43s | re-security (HIGH-1/2 + M1 RESOLVED, M2 partial) | clean |
| 6.8-BE | backend-developer | 90,952 | 32 | 5m03s | webhook informe schema fix (smoke 422→200) | green ≠ working catch |
| delta-fix-map | backend-developer | 89,214 | 41 | 4m07s | GET /me/last-address (autofill) | reactive round |
| 4a | backend-developer | 79,384 | 42 | 18m10s | S1 register/login | gate BLOCKED by jinja2 infra |
| delta-fix-map | frontend-developer | 77,171 | 50 | 5m18s | MapModal CP autofill + login autofill (live-enabled) | reactive; live e2e verified |
| 2.5 | test-engineer | 71,023 | 13 | 2m06s | E2E Playwright addendum (4 scenarios) | — |
| delta-fix-map | backend-developer | 72,075 | 30 | 3m01s | expose Google Maps browser key | reactive round |
| 5 | migration-reviewer | 73,480 | 24 | 1m20s | APPROVED_WITH_NOTES | proportionate |
| 4a | backend-developer | 64,227 | 18 | 1m44s | S4 test fixup (demo vs live) | test-only |
| 4a | backend-developer | 56,678 | 5 | 0m40s | S3 test fixups (6) | after S0 → full suite green |
| delta-fix-FE | frontend-developer | 45,626 | 19 | 1m46s | router guard stale-token root-cause fix (+5 tests) | reactive; browser-verified |
| delta-fix-FE | frontend-developer | 44,246 | 12 | 1m15s | "Soy nuevo" → /login redirect fix | reactive round |
| 4a | backend-developer | 43,766 | 5 | 0m26s | S0 infra fix (skip Sentry in testing) | unblocks collection |
| review-setup | backend-developer | 43,111 | 4 | 1m14s | Sentry init only in prod | jinja2 offline workaround |
| delta-fix-map | frontend-developer | 42,322 | 12 | 1m06s | google.maps local types (offline) | reactive round |
| review-setup | backend-developer | 41,911 | 2 | 0m17s | add jinja2 dependency | real missing dep |

**Totals:** ~**4,160,000 tokens** across **39 token-bearing runs** (~25 distinct work rounds). `budget_ok=false`: 2 runs (FIX-13+14 221K; Phase-3 architect 153K).

**Observations:**
- The cycle's cost is dominated by **rebuild, not build**: the ADDENDUM (195K) + FE rework (154K) + ~5 reactive FE rounds (~307K) + the entire BE-webhook re-cycle (FIX-6..15 implement ~896K + 6.8 91K + re-security 91K + refine 121K + architect 104K ≈ **1.4M**). Conservatively, **~2.0M of the ~4.16M (≈48%)** is attributable to the two preventable root causes (un-anchored flow + assumed contract).
- The S5 webhook run alone (77min / 150K) and the FIX-13+14 run (221K, budget_ok=false) confirm that **security-critical / multi-FIX stories should be split** to stay under budget and keep re-gates cheap.
- The Phase-3 architect over-budget (153K) was *good spend* — it caught a real BLOCKER. Not all over-budget is waste; flag, don't auto-rerun (consistent with the note in telemetry).
- Reviewers were efficient and on-point (code-review 4/4 IMPORTANTs real; security predicted the contract problem via HIGH-1). The waste was upstream of them.

**Optimization backlog (carry into next cycle):**
- [ ] Apply P2/T7 (no-pipe gate) immediately — highest ROI, zero-cost behavioral change.
- [ ] Apply P1 (flow-fidelity + contract-first) — would have removed ~2.0M tokens this cycle.
- [ ] Split security-critical stories (S5-class) and multi-FIX stories (FIX-13+14) into ≤1 concern each.
- [ ] Add Phase-0 real-stack smoke to catch infra bugs (jinja2/Sentry) before they cost story re-gates.
- [ ] If the same "assumed contract" or "specs not read" pattern appears in a future retro → escalate to `pattern-detector` (it already echoes the REQ-20260602 "fixture assumed, not inspected" finding — this is a **recurring family**: *assume instead of inspect/obtain*).

---

## 9) Final State

**Ready / done:**
- **Registro + login** (`POST /cliente/auth/register` 202 anti-enum + `/login`, JWT `sub=email` roles `[client]`).
- **Cliente flow live, prototype-faithful**, browser-verified end-to-end: `/cliente` (Acceso, login-first) → "Soy nuevo" → Datos (interactive Google Map pin + reverse-geocode + CP autofill) → inline ≥8-char password modal → account + case created → `window.open(real signed_url)` → perito procesando → resultado.
- **Webhook REAL** (`POST /api/webhooks/perito`): `X-API-Key` auth (`compare_digest` before parse, fail-close in prod), only `completed`/`escalated`, idempotency by `recopilacionId`, persists `PeritoAnalysis` + valuation lines **from the informe JSON (no DOCX)**, evidence 24h via BackgroundTask with its own session + SSRF allowlist. **6.8 smoke GREEN locally** (`200`, total=87.73, 4 lines, idempotent, `401` on bad key).
- **Status polling** reads our own DB (`service_requests.perito_*`) → 429 from guAI eliminated.
- **`create_claim`** now sends full user data (FIX-15).
- Security: 0 CRITICAL / 0 open HIGH; code-review APPROVED_WITH_MINOR (IMPORTANTs settled in FIX-14); migration APPROVED_WITH_NOTES.

**Remaining / debt:**
- **Real e2e via ngrok + guAI panel**: localhost is unreachable by guAI; need a public URL + configure that URL and `X-API-Key` in the guAI panel; shared-secret signature still TBD with GuaInsurTech (hook disabled until then).
- **Security M2 (SSRF) residual = 2 MEDIUM** → optional `FIX-16` (revalidate on `follow_redirects` + force `https` scheme).
- **Deferred informe blocks** (`meta`/`incident`/`rooms`/`photos`/`geolocation`) not yet persisted (permissive `Optional[dict]`; persist when needed).
- **Residual layer leak:** `_update_case_pricing_from_valuation` still commits inside the service (out of FIX-14 scope) → move the commit to the repository layer in a follow-up.
- **Specs `04`/`09`/`23`/`24` not yet read line-by-line** (FIX-12 deferred) — copy/AC/alerts/realtime fine-grained cotejo pending.
- No git commit made (consistent with project default; commit on user request).

---

## Confidence: HIGH

Grounded in the full telemetry (39 runs with per-run notes), the checkpoint, the ADDENDUM root-cause with file:line citations, and the 6.8 smoke evidence. The 8 mandated lessons are each verified against a specific telemetry entry. The only soft estimate is the "~48% preventable tokens" figure, which is a conservative attribution, not a measured split.
