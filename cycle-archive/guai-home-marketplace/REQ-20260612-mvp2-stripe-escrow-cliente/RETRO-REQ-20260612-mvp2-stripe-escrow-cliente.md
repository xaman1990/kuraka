# Final Audit — REQ-20260612-mvp2-stripe-escrow-cliente

**Mode:** Normal (full 8 phases + mandatory 5.5) + delta-fix + Phase-5 re-review · **Date:** 2026-06-12 · **Closed:** 2026-06-14
**Result:** **CYCLE COMPLETE — feature delivered in mock mode; live code implemented; live smoke (6.8) DEFERRED pending real Stripe keys.** MVP-2 client-side Stripe **escrow authorization**: `PaymentIntent` (`capture_method=manual`) → `Payment(authorized)` → verified Stripe webhook → case `payment_authorized` → confirmation. 6 stories S1–S6, all gated with explicit user approvals. **Deliberately narrow scope:** capture/release, payouts/Connect, disputes/refunds, price-adjustment payments DEFERRED. Final suites: backend `make test-run` **353 passed** (idempotent); frontend type-check clean + vitest **72 passed**. Reviews: code-review **APPROVED** (after delta-fix; 2 BLOCKERs + 4 IMPORTANTs closed with file:line evidence), security **APPROVED_WITH_NOTES** (0 CRITICAL, 2 HIGH — one fixed, one accepted operational), migration **APPROVED**.
**Scope of audit:** the full cycle as captured in `checkpoints/REQ-20260612-mvp2-stripe-escrow-cliente-state.json` + the three review reports + the test-infra lesson already written to `.claude/project/lessons-learned.md` (2026-06-13 block, referenced not duplicated here).

> **Telemetry note:** no `agent-telemetry/REQ-20260612-...-telemetry.json` was written for this cycle (the last telemetry file on disk is REQ-20260611). This is itself a systemic finding (§4.6) — the §8 table is reconstructed from the checkpoint's per-phase narrative, not from token measurements. Numbers below are phase outcomes, not token counts.

---

## 1) Summary

- **Total iterations: LOW–MEDIUM.** The feature was built **once**, cleanly, story-by-story (S1→S6 sequential, `make test-run` per story per Rule T6). There was **no rebuild** — in stark contrast to REQ-20260611 (built twice, ~4.16M tok). The rework that did occur was: (a) one cross-cutting **test-infra root fix** discovered mid-cycle (the headline), (b) one **CONCURRENTLY-in-Alembic** correction caught at the per-story gate, and (c) a single **delta-fix round** closing Phase-5's 2 BLOCKERs + 4 IMPORTANTs and Phase-5.5's HIGH#1, which then **re-reviewed APPROVED on the first pass**.
- **Main causes of rework (ranked):**
  1. **Test-DB was not idempotent** — `conftest` managed the schema via ORM (`Base.metadata.create_all/drop_all`) while the container ran `alembic upgrade head` over a **persistent volume** → divergent schemas, state-dependent pass/fail. Surfaced only when S2's migration + unique-index test exercised the drift (`payments does not exist`, perito FK without `ON DELETE CASCADE`, missing unique index). Root-fixed (user-approved) by making conftest the **single alembic source**. **Earliest catch: a Phase-0 infra-smoke asserting test-DB idempotency before any migration cycle.**
  2. **"green ≠ working" recurred (4th tier)** — Phase 5 found 2 BLOCKERs a fully-green suite missed: B1 (reuse path returned the bare `pi_id` as `client_secret`; the reuse test **omitted** the `client_secret` assertion) and B2 (`LiveStripeClient` had no customer creation → silently falls to `MOCK_CUSTOMER_ID`; mock-only tests never exercised the live client). **Earliest catch: test plan must assert the FULL return contract (every field, esp. secrets) + live clients need per-Protocol-method httpx-mocked tests.**
  3. **`CREATE UNIQUE INDEX CONCURRENTLY` inside Alembic** — the story AC prescribed CONCURRENTLY; it cannot run inside Alembic's transactional DDL (`InvalidRequestError`). Caught at the S2 `make test-run` gate. **Earliest catch: architect/story should never prescribe CONCURRENTLY for a transactional Alembic migration on a new/empty table.**
  4. **Insecure default in production** — `STRIPE_CLIENT` defaults to `"mock"`, and mock `construct_event` skips signature verification → a prod deploy with the default would accept forged webhooks. Caught by Phase 5.5 (HIGH#1), fixed (factory raises on `is_prod()` + mock). **Earliest catch: a "secure-default / fail-safe in prod" check for any mock/live integration factory.**
- **Estimated preventable iterations: ~2–3 loops.** The test-infra fix (1 loop, preventable by a Phase-0 idempotency smoke), the CONCURRENTLY correction (1 loop, preventable by the architect not prescribing it), and the B1/B2 BLOCKER round (1 loop, partially preventable — the live-client gap is exactly what code-review exists to catch, but a fuller test plan would have caught B1 earlier). **Genuinely not preventable:** the delta-fix itself was Phase 5 doing its job; the 6.8 live-smoke deferral is a keys-availability constraint, not a process miss.

---

## 2) Timeline of Rework

| Phase | Issue | Root Cause | Preventable? | Earliest catch | Fix |
|-------|-------|-----------|--------------|----------------|-----|
| 4 / S2 gate | `make test-run` NOT idempotent (pass/fail depended on volume state: `payments does not exist`, perito FK without ON DELETE CASCADE, missing unique index) | conftest used ORM `create_all/drop_all` while the container ran `alembic upgrade head` over a **persistent** volume → two divergent schema sources | **Yes** | Phase 0 (assert test-DB idempotency before a migration cycle) | conftest `setup_database` → `DROP SCHEMA public CASCADE` + programmatic `alembic upgrade head`; removed `create_all/drop_all`; `Config()` **without** the `.ini` (avoids `fileConfig` disabling app loggers / `caplog`). Alembic = single schema source. Already documented in lessons-learned (2026-06-13). |
| 4 (collateral) | 2 pre-existing perito tests "passed for the wrong reason" on the broken schema | The divergent ORM schema masked a child-first teardown bug and a 202-path test that relied on the drift | **Partial** | Same as above (correct schema exposes them) | (a) teardown deletes tasks→analysis→session child-first; (b) 202-path test uses a `_NotReadyPeritoClient` to force a genuine 202 |
| 4 / S2 gate | `CREATE UNIQUE INDEX CONCURRENTLY` raised `InvalidRequestError` | Story AC prescribed CONCURRENTLY; Alembic wraps each migration in a transaction (transactional DDL) — CONCURRENTLY needs autocommit | **Yes** | Phase 3 (architect should not prescribe CONCURRENTLY for a transactional migration on a new/empty table) | Removed CONCURRENTLY → plain `CREATE UNIQUE INDEX` (payments table new/empty → no lock concern). Migration-reviewer confirmed plain index correct for context. |
| 5 (code-review) | **BLOCKER B1** — reuse path returned the bare `pi_id` as `client_secret`; Stripe.js rejects a PI id | The reuse test (`test_payment_intent_service.py:366`) deliberately **omitted** the `client_secret` assertion → bug invisible to green suite | **Yes** | 2.5 test-plan (assert the FULL return contract — every field, esp. `client_secret`) | Added `retrieve_payment_intent` to Protocol + Live + Mock; `_retrieve_client_secret` on reuse; test now asserts `result.client_secret == expected_secret` |
| 5 (code-review) | **BLOCKER B2** — `LiveStripeClient` had no customer creation → falls to `MOCK_CUSTOMER_ID` → "No such customer" in prod | Mock-only tests never exercised the live client's customer path; the duck-typing `hasattr` fallthrough returned the mock constant | **Yes** | 2.5/5 (live client needs per-Protocol-method httpx-mocked tests, not mock-only coverage) | Added `get_or_create_customer` to `LiveStripeClient` (Protocol-declared); removed `MOCK_CUSTOMER_ID` import from the production service entirely |
| 5 (code-review) | 4 IMPORTANTs: I3 service `db.commit`, I4 dropped `failed` field, I5 status `idle` vs frozen `pending`, I6 `PagoConfirmacion` trusts `redirect_status` | Layering leak + schema drift from the frozen contract + a 3DS redirect path never gated on real status | **Partial** | 5 (working as designed) | I3→`UserRepository.update_stripe_customer_id`; I4→`failed: Optional[bool]`; I5→return `PAYMENT_STATUS_PENDING`; I6→`PagoConfirmacion` gates on `getStatus`, never trusts `redirect_status` |
| 5.5 (security) | **HIGH#1** — `STRIPE_CLIENT` default=`mock` + mock skips signature verify → prod with default accepts forged webhooks | No "secure default / fail-safe in prod" guard on the integration factory | **Yes** | 5.5 (working as designed; a factory fail-safe checklist would pre-empt it) | `factory._assert_not_production_mock()` raises on `is_prod()` + mock; `LiveStripeClient` moved to module-top import (also closes code-review #7 lazy-import) |
| (infra noise) | Docker base-image pull DNS timeout; one agent API ConnectionRefused (S5 still completed) | Transient environment / network | **No** | n/a (not a process failure) | Retried; S5 was complete despite the ConnectionRefused. Noted only for honesty. |

---

## 3) Agent Findings

> No telemetry → no token attribution per agent. Findings below are grounded in the checkpoint narrative and the three review artifacts.

### po-analyst (Phase 1) + GATE0/GATE1
- **What went RIGHT (strong):** GATE0 correctly negotiated **scope down to client-escrow-authorization only** (option A) — capture/release, payouts/Connect, disputes/refunds explicitly deferred. This narrow framing is the single biggest reason the cycle did not balloon. GATE1 resolved four real design questions cleanly (EVT-018 defer, schema D1/D2 defer, **read-or-create `User.stripe_customer_id`**, reprice-collision policy: update PI if not authorized / cancel+recreate if authorized). The pre-Phase-1 discovery (3 Explore agents) correctly confirmed the payments data model already honored the specs and that the **only** real gap was the Stripe service layer + the unique index — preventing a wasteful "build the schema" detour.
- **What FAILED:** Nothing material attributable to analysis. The mock/live factory split was specified up-front (gate0_resolved), which is exactly right for "user has test keys but they aren't in `.env` yet."
- **Note:** P1 (flow-fidelity) and P3/P10 (contract-provenance, downstream-generated values) from the prior cycle's applied project-layer checks were respected here — the Stripe contract is a well-documented first-party API, so contract-provenance was not a risk this cycle.

### story-refiner (Phase 2) + architect-reviewer (Phase 3)
- **What went RIGHT:** The frozen schema + 7 architect amendments (F1–F7) were exemplary and **overrode stale story text where they conflicted** (esp. F1: read-or-create `stripe_customer_id`; F5: catch `ErrInvalidStateTransition` specifically, not parent `ErrValidation`; F6: bad signature → 401 consistently; F7: `amount` typed string because backend serializes Decimal→JSON string). T6 (sequential + `make test-run` per story) was mandated and honored. The architect correctly froze the migration as a **plain** index for a new/empty table.
- **What FAILED (the one architect miss):** the S2 story AC **prescribed `CREATE UNIQUE INDEX CONCURRENTLY`**, which cannot run inside Alembic's transactional DDL. The implementer followed the AC over the orchestrator's note → caught only at `make test-run`. The architect (Phase 3) is the earliest place this should have been corrected: for a transactional Alembic migration on a new/empty table, CONCURRENTLY is both unnecessary (no lock concern) and impossible (transaction-wrapped). → **P13.**
- **Cross-reference:** the prior cycle's migration-reviewer already flagged "partial index without CONCURRENTLY (Alembic limit, small table OK)" — the **architect/story** didn't carry that lesson forward into the AC. The reviewer caught it after; the cost is the per-story re-gate.

### backend-developer (Phase 4, S1–S6)
- **What went RIGHT (strong):** Replicated the proven perito factory/Protocol + webhook-security skeleton faithfully. Webhook order is textbook (rate-limit → 413 body cap → signature on **raw bytes before parse** → parse → delegate), idempotency is a defense-in-depth triple (UNIQUE index + `authorized_at` short-circuit + `ErrInvalidStateTransition` catch), EUR→cents is Decimal `ROUND_HALF_UP` throughout (never a float), IDOR is enforced in the **service** layer on both endpoints. Applied the **real-payload webhook fixture** (P8 from last cycle) for S5. Sequential build + per-story `make test-run` (T6) held — **~0 cross-story rework**, exactly the discipline the prior retros prescribed.
- **What FAILED:** Two live-mode gaps shipped green (B1 reuse `client_secret`, B2 live customer creation) — both **only exercised in live mode**, masked by mock-only tests. This is the "green ≠ working" family again: the developer wrote the live client but did **not** write per-Protocol-method httpx-mocked tests for it (the perito `test_guai_client.py` pattern existed as a model and was not applied to the Stripe live client). → **P14, P15.** Also followed the CONCURRENTLY AC literally rather than escalating the orchestrator's note (a discipline call — AC vs note conflict should be raised, not silently resolved either way).

### code-reviewer (Phase 5 + re-review)
- **What went RIGHT (very strong):** This is the agent that earned its keep this cycle. Phase 5 traced the exact live-mode code paths and caught **both** BLOCKERs that the green suite + mock tests missed, with precise file:line + the **root cause of why the suite was green** ("the test deliberately omits an assertion on `result.client_secret`"). 4 actionable IMPORTANTs (all real), 5 MINORs, plus 9 specific PRAISE items. The re-review closed every BLOCKER/IMPORTANT with file:line evidence and flagged the residual dead `PAYMENT_STATUS_IDLE` constant honestly. High signal-to-noise.
- **What FAILED:** Nothing. The review **is** the safety net that the test plan should have made redundant — i.e., the lesson is upstream (test plan / live-client coverage), not in the reviewer.

### migration-reviewer (Phase 6.5)
- **What went RIGHT:** APPROVED. Correctly reasoned that the plain index is production-safe **because the payments table is new/empty** (no CONCURRENTLY needed), validated NULL-distinct semantics, linear single-head chain, correct downgrade, and explicitly confirmed the **conftest alembic-single-source change was sound**. Proportionate and correct. It also documented the autocommit-CONCURRENTLY pattern (for the large-table case) — useful provenance for P13.
- **What FAILED:** Nothing material.

### security-reviewer (Phase 5.5)
- **What went RIGHT:** APPROVED_WITH_NOTES, 0 CRITICAL. Flagged exactly the two HIGHs that mattered: HIGH#1 (mock default in prod skips signature verify — the **fail-open default**) and HIGH#2 (rate-limiter fails open on Redis down). Verified amount integrity (no client-supplied amount path), IDOR on both endpoints, secret hygiene (only the publishable key crosses to the SPA, webhook logs `bool(sig_header)` only), and that the conftest infra change disables **no** security control. Secret scan clean.
- **What FAILED:** Nothing in execution. HIGH#1 is the kind of finding that a **factory fail-safe checklist** (P16) should pre-empt before Phase 5.5 even runs.

### orchestrator (process)
- **What went RIGHT:** Honored every gate with explicit user approval. Ran the test-infra root fix **as a user-approved decision**, not silently. Kept the delta-fix tight (one round, re-review APPROVED first pass). Correctly **deferred** the 6.8 live smoke rather than faking it without real keys.
- **What FAILED:** (a) **No telemetry JSON was written** for this cycle (the checklist in rule 17 says "Telemetry JSON is written after every Agent invocation") — §4.6. (b) The cross-cutting **test-infra fix bled into a feature cycle**; it was the right fix but the wrong time to discover it — a Phase-0 infra-smoke would have surfaced it before S1. It cost significant orchestration time mid-cycle. → **P12.**

---

## 4) Systemic Issues

1. **Test-DB schema had two sources of truth (ORM vs Alembic) over a persistent volume → non-idempotent suite.** The defining infra bug of the cycle. Already root-fixed and documented in `.claude/project/lessons-learned.md` (2026-06-13 block, "test-infra: alembic como única fuente del esquema de test"). The **process** lesson is that this should have been caught by a **Phase-0 idempotency smoke** before a migration-bearing cycle, not mid-S2. → P12.
2. **Cross-cutting infra fix bled into a feature cycle.** Fixing test-infra while implementing escrow is scope-bleed: correct fix, wrong moment. It exposed 2 perito tests "green for the wrong reason" — good outcome, but the discovery cost mid-cycle orchestration time. → P12 (a Phase-0 gate that asserts idempotency keeps the infra fix out of the feature cycle).
3. **"green ≠ working" recurred a FOURTH time** (after the 6.8 `conclusions` 422, the FIX-18 202-as-success, and the idealized-smoke-payload misses of REQ-20260611). Here: B1's reuse test **omitted the `client_secret` assertion**, and the live client had **mock-only coverage**. The common root across all four: **tests assert the happy/partial contract, not the FULL contract, and the live path is never exercised.** → P14, P15, and escalate the family to `pattern-detector` (now spanning 3+ cycles).
4. **An external-integration factory shipped with an insecure default (`mock`) that is also a no-signature-verification path.** Fail-open-in-prod by default. → P16 (a generic "integration factories must fail-safe in production" check).
5. **A story AC prescribed an operation incompatible with the migration tool** (CONCURRENTLY inside transactional Alembic). The architect is the earliest place to strip it. → P13.
6. **Telemetry was not captured for this cycle.** No `REQ-20260612-...-telemetry.json` exists, so token/latency cost is unmeasurable and the §8 table is reconstructed from prose. The orchestrator's own checklist (rule 17) mandates writing it after every `Agent` invocation. → P17.

**Positive systemic notes:**
- **T6 (sequential + per-story make-test-run) delivered ~0 cross-story rework** — the exact opposite of REQ-20260611's parallel-batch debugging storm. The rule works; keep it mandatory for provider/migration cycles.
- **Scope discipline held.** GATE0's narrow framing (authorization only, mock/live split) is the primary reason this cycle was LOW–MEDIUM, not HIGH.
- **P8 (real-payload webhook fixture) was applied** — the S5 webhook used a real-payload fixture, carrying forward the prior cycle's hardest-won lesson.

---

## 5) Workflow Improvements (Concrete)

1. **Phase-0 test-DB idempotency smoke (any migration-bearing cycle):** before Phase 4, run `make test-run` **twice** (clean volume + dirty volume) and assert identical pass counts; assert the test schema comes from `alembic upgrade head`, never from `Base.metadata.create_all`. This keeps infra fixes OUT of feature cycles.
2. **Architect strips CONCURRENTLY from transactional Alembic migrations:** for a new/empty table, mandate a plain index; for a large existing table, mandate a **separate autocommit migration** (`op.execute` after committing the transaction). Document the decision in the story AC, not just a note.
3. **Test plan asserts the FULL return contract:** every field of every returned DTO — especially secrets/tokens (`client_secret`), not just ids/amounts. No "reuse behaviour" test may omit the field the consumer actually uses.
4. **Live integration clients require per-Protocol-method httpx-mocked tests:** mirror `test_guai_client.py`. Mock-only coverage is insufficient for any client with a live counterpart; each Protocol method needs at least one httpx-mocked test against the live client.
5. **Integration factories must fail-safe in production:** no `mock` (or any signature-skipping) default reachable when `is_prod()`. The factory raises.
6. **Always write telemetry:** the orchestrator writes `agent-telemetry/{REQ}-telemetry.json` after every `Agent` invocation (already in rule 17's checklist — enforce it).

---

## 6) Patches Proposed (P12–P17, continuing P1–P11)

> Preference (same as prior retros): **project-layer** unless truly universal. P16 (fail-safe-in-prod factory) is framework-worthy. **PROPOSED only — not applied; user approves application separately.**

### P12 — Test-DB must be alembic-single-source + a Phase-0 idempotency smoke before any migration cycle (project-layer, append)
- **Type:** project-layer
- **Target:** `.claude/project/lessons-learned.md` already carries the *fix* (2026-06-13 block). This patch adds the **process guardrail** to `.claude/rules/17-kuraka-token-optimizations.md` (new Rule T9) so it runs as Phase-0, not as mid-cycle discovery.
- **Change (exact text to add):**
  ```markdown
  ## Rule T9 — Phase-0 test-DB idempotency smoke (any migration-bearing cycle)
  Before Phase 4 of ANY cycle that adds/edits an Alembic migration or a SQLAlchemy
  model, run a Phase-0 smoke that asserts:
    (1) the test schema is built ONLY by `alembic upgrade head` (conftest does
        `DROP SCHEMA public CASCADE` + alembic; NEVER `Base.metadata.create_all`);
    (2) `make test-run` yields the SAME pass count on a clean volume and a dirty
        volume (idempotent).
  If either fails, FIX THE INFRA IN A SEPARATE CYCLE before starting the feature —
  do not let a cross-cutting infra fix bleed into a feature cycle.
  Reference: REQ-20260612 — conftest used ORM create_all/drop_all while the
  container ran alembic over a PERSISTENT volume → divergent schemas, state-dependent
  pass/fail (payments-missing, perito FK without ON DELETE CASCADE, missing unique
  index), discovered mid-S2. Root fix in lessons-learned 2026-06-13.
  ```

### P13 — Never prescribe `CONCURRENTLY` inside a transactional Alembic migration (project-layer, append)
- **Type:** project-layer
- **Target:** `.claude/project/review-checks/architect-reviewer.md` (append)
- **Change (exact text to add):**
  ```markdown
  ## Alembic unique/index migrations — CONCURRENTLY decision
  - NEW or EMPTY table → prescribe a PLAIN `CREATE UNIQUE INDEX` / `op.create_index`.
    Do NOT prescribe CONCURRENTLY: Alembic wraps each migration in a transaction
    (transactional DDL), and `CREATE INDEX CONCURRENTLY` raises InvalidRequestError
    inside a transaction. There is no lock concern on an empty table.
  - LARGE EXISTING table where the lock matters → prescribe a SEPARATE autocommit
    migration (commit the transaction, then `op.execute("CREATE UNIQUE INDEX
    CONCURRENTLY ...")` in autocommit mode). State this explicitly in the story AC,
    not as a side note.
  - The architect verdict for any index/unique migration MUST state which of the two
    applies, so the story AC carries a buildable instruction.
  - Reference: REQ-20260612 S2 — story AC said CONCURRENTLY on a new/empty payments
    table; the implementer followed the AC → InvalidRequestError at make test-run.
    Fixed to a plain index (migration-reviewer confirmed correct for context).
  ```

### P14 — Test plan must assert the FULL return contract (every field, esp. secrets/tokens) (project-layer, append)
- **Type:** project-layer
- **Target:** `.claude/project/review-checklist.md` (append, applies to test-engineer + code-reviewer)
- **Change (exact text to add):**
  ```markdown
  ## Return-contract completeness (test plan + code-review)
  - Every test that exercises a function returning a DTO MUST assert EVERY field the
    CONSUMER uses — not only ids/amounts. In particular: assert any secret/token field
    (client_secret, access_token, signed_url) has the REAL expected value/shape, never
    skip it "because the test only checks reuse behaviour."
  - A reuse / cache-hit / second-call test is exactly where a sentinel/placeholder
    sneaks through — assert the returned value is the SAME shape the first call gives.
  - Reference: REQ-20260612 B1 — `_derive_client_secret` returned the bare `pi_id` as a
    sentinel on the reuse path (Stripe.js rejects a PI id); the reuse test deliberately
    OMITTED the `client_secret` assertion → green suite, broken reuse. Fix: assert
    `result.client_secret == MOCK_CLIENT_SECRET`.
  ```

### P15 — Live integration clients need per-Protocol-method httpx-mocked tests, not mock-only coverage (project-layer, append)
- **Type:** project-layer
- **Target:** `.claude/project/lessons-learned.md` (append, applies_to: backend-developer, test-engineer, code-reviewer)
- **Change (exact text to add):**
  ```markdown
  ## Ciclo 2026-06-12 — el cliente LIVE necesita tests httpx-mocked por método (no solo mock)
  - Un cliente de integración con contraparte LIVE (LiveStripeClient, GuaiPeritoClient)
    DEBE tener al menos UN test httpx-mocked por cada método del Protocol — el patrón
    de `test_guai_client.py`. La cobertura SOLO-mock deja el path live sin ejercitar.
  - Reference: REQ-20260612 B2 — `LiveStripeClient` no tenía creación de customer →
    `_get_or_create_customer_via_client` caía a `MOCK_CUSTOMER_ID` → `PaymentIntent.create
    (customer="cus_mock_...")` daría "No such customer" en prod. Invisible en mock.
    Fix: `get_or_create_customer` en el cliente live (declarado en el Protocol) +
    eliminado el import de `MOCK_CUSTOMER_ID` del servicio de producción.
  - REGLA: cualquier rama `if is_testing()` / `hasattr(...)` que devuelva una constante
    mock NO debe ser alcanzable en modo live; protégela con `if is_testing()` estricto
    o, mejor, satisface el Protocol en el cliente live.
  ```

### P16 — Integration factories must fail-safe in production (framework-worthy + project-layer)
- **Type:** framework / project-layer
- **Target (project):** `.claude/project/review-checks/architect-reviewer.md` + `.claude/project/review-checklist.md` (append, applies to security-reviewer); **Target (framework):** the security-review checklist (universal mock/live factory trap).
- **Change (exact text to add):**
  ```markdown
  ## Integration factory — fail-safe in production
  - Any factory selecting between a MOCK and a LIVE client (Stripe, perito, payments)
    where the MOCK path SKIPS a security control (signature verification, auth) MUST
    raise when `is_prod()` and the selected mode is mock. The insecure mode must be
    UNREACHABLE in production — never the silent default.
  - Verify: the default value of the selector env var, and that `is_prod() + mock`
    raises (a unit test asserting the raise).
  - Reference: REQ-20260612 sec-HIGH#1 — `STRIPE_CLIENT` defaulted to "mock" and the
    mock `construct_event` does zero signature verification → a prod deploy with the
    default would accept forged webhooks and authorize escrow. Fix:
    `factory._assert_not_production_mock()` raises on `is_prod()` + mock.
  ```

### P17 — Always write per-cycle telemetry (project-layer, append)
- **Type:** project-layer
- **Target:** `.claude/rules/17-kuraka-token-optimizations.md` (the existing checklist already lists "Telemetry JSON is written after every Agent invocation" — this adds a Phase-7 enforcement note)
- **Change (exact text to add):**
  ```markdown
  ## Telemetry enforcement (Phase 7 gate)
  - The orchestrator writes `docs/process/agent-telemetry/{REQ}-telemetry.json` after
    EVERY `Agent` invocation (one entry per run: phase, agent, total_tokens, tool_uses,
    duration_ms, produced).
  - Phase 7 (final-auditor) checks the file exists. If missing, the RETRO's §8 cannot
    be produced from measurements and the cost of the cycle is unknowable.
  - Reference: REQ-20260612 wrote NO telemetry file → the RETRO §8 had to be
    reconstructed from the checkpoint prose; token/latency optimisation backlog for
    this cycle is unmeasured.
  ```

### Application record
**PROPOSED only — none applied.** User approves application separately (project-layer can apply immediately; the framework half of P16 contributes back to the shared vault per `.claude/rules/16-agent-backup.md`).

---

## 7) Next-Requirement Guardrails

- **Mandatory pre-implementation checks:**
  - [ ] If the cycle adds/edits a migration or SQLAlchemy model → Phase-0 test-DB idempotency smoke passed (P12/T9): schema from alembic only, identical pass count clean vs dirty volume.
  - [ ] Architect verdict states the CONCURRENTLY decision for any index migration (new/empty → plain; large → separate autocommit migration) (P13).
  - [ ] Integration factory fail-safe-in-prod verified before Phase 5.5 (P16).
- **Mandatory test checks:**
  - [ ] Every returned-DTO test asserts the FULL contract, incl. secret/token fields; no reuse/cache test omits the consumer-used field (P14).
  - [ ] Each live integration client has ≥1 httpx-mocked test per Protocol method; no `is_testing()`/`hasattr` mock-constant branch reachable in live mode (P15).
- **Mandatory process checks:**
  - [ ] Telemetry JSON written after every `Agent` invocation; Phase 7 verifies it exists (P17).
  - [ ] T6 (sequential + per-story `make test-run`) for any provider/migration cycle (held this cycle — keep).
  - [ ] Cross-cutting infra fixes go in a SEPARATE cycle, not bled into a feature cycle (P12).

---

## 8) Token & Latency Telemetry

> **No telemetry file was written for this cycle** (`agent-telemetry/REQ-20260612-...-telemetry.json` does not exist). The table below is a **qualitative reconstruction** from the checkpoint's per-phase narrative — there are no token/duration measurements. This is itself a finding (§4.6, P17).

| Phase | Agent | Tokens | Tool uses | Duration | Produced | Notes |
|-------|-------|-------:|----------:|---------:|----------|-------|
| 1 + GATE0/1 | po-analyst | n/a | n/a | n/a | REQ + scope-down + 4 GATE1 resolutions | Scope discipline = the cheapest decision of the cycle |
| 2 + 3 | story-refiner + architect-reviewer | n/a | n/a | n/a | Frozen schema + F1–F7 amendments + 6 stories | F1–F7 overrode stale story text correctly; one miss (CONCURRENTLY AC) |
| 2.5 | test-engineer | n/a | n/a | n/a | Test plan | Missed FULL-contract assertion on `client_secret` (→ B1 slipped) |
| 4 (S1–S6 + infra fix) | backend-developer | n/a | n/a | n/a | 6 stories + test-infra root fix + real-payload fixture | T6 sequential; ~0 cross-story rework. Infra fix cost mid-cycle orchestration time (unmeasured) |
| 5 + re-review | code-reviewer | n/a | n/a | n/a | 2 BLOCKERs + 4 IMPORTANTs + 5 MINORs; re-review APPROVED | Highest-value agent this cycle; caught both live-mode BLOCKERs the green suite missed |
| 5.5 | security-reviewer | n/a | n/a | n/a | APPROVED_WITH_NOTES, 0 CRITICAL, 2 HIGH | Caught the fail-open mock default (HIGH#1) |
| 6.5 | migration-reviewer | n/a | n/a | n/a | APPROVED | Confirmed plain index + conftest alembic-single-source sound |
| delta-fix | backend + frontend developer | n/a | n/a | n/a | Closed B1/B2/I3/I4/I5/I6 + sec-HIGH#1 | One round; re-review APPROVED first pass |

**Totals:** unmeasured (no telemetry file). **Verified suite numbers:** backend `make test-run` **353 passed** (idempotent); frontend type-check clean + vitest **72 passed**.

**Observations (qualitative):**
- The cycle's cost was dominated by **build + one root infra fix + one delta-fix**, NOT by rebuild — the healthy profile T6 + scope discipline are meant to produce. Compared to REQ-20260611 (~4.16M tok, built twice), this cycle is structurally far cheaper, but the **exact savings are unmeasurable** because telemetry was not captured.
- The test-infra fix was the single largest unplanned cost; a Phase-0 idempotency smoke (P12) would have moved it out of the feature cycle.
- Reviewers were high-value and on-point (code-review caught both BLOCKERs; security caught the fail-open default). The waste was upstream (test plan didn't assert the full contract; architect carried CONCURRENTLY into the AC).

**Optimization backlog (carry into next cycle):**
- [ ] **Apply P17 immediately** — write telemetry every cycle; without it the optimisation loop is blind (this cycle is unmeasurable).
- [ ] Apply P12/T9 (Phase-0 idempotency smoke) — keeps cross-cutting infra fixes out of feature cycles.
- [ ] Apply P14 + P15 — close the "green ≠ working" family at the test-plan + live-client-coverage level.
- [ ] Apply P16 (factory fail-safe-in-prod) — universal mock/live trap; cheap checklist line + one unit test.
- [ ] **Escalate to `pattern-detector`:** the "green ≠ working" family now spans **4 tiers across 3+ cycles** (REQ-20260611 ×3 + REQ-20260612 B1/B2). Common root: *tests assert the partial/happy contract and never exercise the live path.* This is cross-project — promote from project lesson to a framework-level guardrail. (This escalation was already open from the prior retro's "assume instead of inspect/obtain" family; this cycle adds a fourth member.)

---

## 9) Final State

> **Cycle CLOSED 2026-06-14** — feature delivered in mock mode; live code implemented; **6.8 live smoke DEFERRED** (real Stripe `sk_test`/`pk_test`/`whsec` not yet in `.env`).

**Ready / done:**
- **Stripe escrow authorization (happy path), mock mode:** `POST /cliente/cases/{ref}/payment/intent` (JWT, IDOR-guarded, server-derived amount) → `PaymentIntent` `capture_method=manual` → `Payment(authorized)` → `POST /api/webhooks/stripe` (signature on raw bytes before parse, 401 bad sig, 413 body cap, idempotent by PI id, fail-close in prod) → case `payment_authorized` → `GET /cliente/cases/{ref}/payment/status` → frontend `PagoPage`/`PagoProcesandoPage`/`PagoConfirmacionPage`.
- **Live code implemented** behind the factory mock/live split: `LiveStripeClient` (create/retrieve PI, `get_or_create_customer`, `cancel_payment_intent`, `construct_event`) — exercised only by httpx-mock + delta-fix tests, not yet against real keys.
- **Factory fail-safe:** `STRIPE_CLIENT=mock` forbidden in production (`is_prod()` + mock → raise).
- **Migration** `c7e3f8a921b4`: plain UNIQUE index `uq_payments_stripe_payment_intent_id` (new/empty table; `down_revision=a1b2c3d4e5f6`; linear single head). Migration-reviewer APPROVED.
- **Test-infra root fix:** conftest is now the single alembic schema source (`DROP SCHEMA` + `alembic upgrade head`; `Config()` without `.ini`) → idempotent `make test-run`; production-parity schema (real FK ondelete, unique indexes, seeded statuses/platform_config). Documented in lessons-learned 2026-06-13.
- **Reviews:** code-review **APPROVED** (after delta-fix); security **APPROVED_WITH_NOTES** (0 CRITICAL); migration **APPROVED**.
- **Suites green:** backend `make test-run` **353 passed** (idempotent); frontend type-check clean + vitest **72 passed**.

**Remaining / debt:**
- **6.8 live smoke DEFERRED** — needs real Stripe test keys in `backend/.env` (currently commented). Until then, the live client is unverified against the real Stripe API. **Highest-priority follow-up before go-live.**
- **DEFERRED scope (by design):** admin capture/release, payouts/Connect, disputes/refunds, price-adjustment payments, EVT-018 admin inbox, schema D1/D2 (AuditMixin + `cancelled_at`).
- **Security HIGH#2 (accepted operational):** rate-limiter fails open on Redis down for the payment/webhook surface — signature verification still protects the webhook; consider fail-closed or a local token-bucket fallback before go-live.
- **Residuals (non-blocking):** dead `PAYMENT_STATUS_IDLE` constant; code-review MINORs #8–#13 (return-type annotations, broad `except`, `amount: string\|number`, migration filename naming, SA 2.x `Session(bind=)` in unit tests); security MEDIUM ×2 / LOW ×2.
- **`PAYMENT_STATUS_FAILED`** in the contract enum but unreachable this cycle (no failed-marker column) — documented, acceptable.
- No git commit made (consistent with project default; commit on user request).

---

## Confidence: HIGH (on outcomes) · MEDIUM (on cost attribution)

**HIGH** on the feature state and the findings: grounded in the checkpoint's per-phase narrative, the three review reports (code-review APPROVED with per-finding closure evidence, security APPROVED_WITH_NOTES, migration APPROVED), the verified suite numbers (353 backend / 72 frontend), and the test-infra lesson already written. The 6 patches (P12–P17) are each tied to a specific artifact (a review finding, a checkpoint line, or the missing telemetry file).

**MEDIUM** only on cost attribution: **no telemetry was captured**, so §8 is qualitative and the "preventable loops" count (~2–3) is a structural estimate, not a measured token split. P17 exists precisely to remove this blind spot next cycle.
