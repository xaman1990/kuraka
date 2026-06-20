# RETRO — REQ-20260616-DD-payment-poll-ratelimit (Kuraka reduced)

**Outcome:** ✅ DONE & verified live. `GET /payment/status` polling no longer hits the 10/min rate limit; the payment "procesando" screen won't freeze. Follow-up from RETRO-REQ-20260616-DD-perito-poll-ratelimit (same bug class on a sibling endpoint).

## Pipeline
REQ-LITE (orchestrator) → 4a backend → 4b frontend (+ a fix to a prior-cycle type error) → 5 code review → 5.5 security → 6 tests → 6.8 smoke → 7. Skipped: 2.5/3/6.5/6.7 (no schema/env; component+service tests + smoke cover behavior).

## What changed
- Backend: generalized the dedicated poll bucket — `PERITO_POLL_LIMIT`→`POLL_LIMIT` (60/60s), `rate_limit_perito_poll`→`rate_limit_poll`, bucket `cliente:perito_poll`→`cliente:poll`. Applied to all 3 read-only polls: `/perito/status`, `/perito/result`, `/payment/status`. `POST /payment/intent` + auth/mutations stay at 10/min.
- Frontend: `PagoProcesandoPage` interval 3000→5000 + 429 backoff (mirror of `PeritoProcesando`); `paymentService.getStatus` surfaces 429 as transient.

## Reviews & tests
- Code review APPROVED_WITH_MINOR (0 BLOCKER/IMPORTANT). MINOR closed in Phase 6: stale `cliente:perito_poll` comment fixed; `PagoProcesandoPage.spec.ts` added.
- Security APPROVED (0 CRITICAL/HIGH; payment-intent + auth stay 10/min; buckets isolated; IDOR-guarded read).
- Tests: backend 380→**382** (+2 payment wiring); frontend 81→**89** (+3 paymentService 429, +5 PagoProcesandoPage component).
- Smoke: 15 rapid `/payment/status` polls → all 200, zero 429.

## Notable
- **Caught a latent gate miss from the prior cycle:** `PeritoProcesando.spec.ts` (added in the perito-poll Phase 6) had a TS2740 type error that `vitest` tolerated but `vue-tsc` (`npm run build` gate) rejected — the prior cycle ran `npm run test` but not `npm run type-check`, so it slipped through with a "green" checkpoint. Fixed here (completed the `PeritoAnalysis` mock). **Lesson: frontend Phase-6 verification must run `npm run type-check`, not only `npm run test` — vitest does not type-check.** Worth encoding in the frontend test/dev workflow.
- The generalized `rate_limit_poll` bucket is now the canonical home for client polling reads — future poll endpoints should use it, not `rate_limit_cliente`.

## Telemetry
See `agent-telemetry/REQ-20260616-DD-payment-poll-ratelimit-telemetry.json` (8 agent runs).
