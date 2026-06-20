# RETRO — REQ-20260616-DD-perito-poll-ratelimit (Kuraka reduced)

**Outcome:** ✅ DONE & verified live. The Perito client flow no longer freezes on "analizando" — the 429 rate-limit storm on the status poll is fixed; result (170.01 €) is served and the frontend can transition.

## Timeline (reduced pipeline)
1+2 combined (po-analyst LITE_COMBINED) → 4a backend → 4b frontend → 5 code review → 5.5 security → 6 tests → 6.8 smoke → 7 (this). Skipped: 2.5 (folded), 3 (no schema), 6.5 E2E (covered by component test + smoke), 6.7 (no migration/env/docker).

## What changed
- Backend: new `PERITO_POLL_LIMIT=60`/60s constant + `rate_limit_perito_poll` dependency (bucket `cliente:perito_poll`); `GET /perito/status` & `GET /perito/result` moved off the 10/min `cliente` bucket. All mutating/auth/payment endpoints stayed at 10/min.
- Frontend: poll interval 3000→5000ms (`POLL_INTERVAL_MS`), `RATE_LIMIT_BACKOFF_MS=3000`, 429 handled as transient "still waiting" in `getStatus`/`getResult` + `PeritoProcesando` (no error, no nav, keeps polling); FIX-18 202 gate preserved.

## Root cause (for the record)
`PeritoProcesando` polled `/perito/status` every 3s (~20/min) against a 10/min bucket → 429 after ~10 polls → frontend never observed `completed` even though the result was already persisted. Compounded by Docker shared gateway IP pooling all clients into one bucket.

## Reviews & tests
- Code review: APPROVED_WITH_MINOR (0 BLOCKER/IMPORTANT; 2 MINOR test-gaps → closed in Phase 6).
- Security: APPROVED (0 CRITICAL/HIGH; no protection weakened on mutations/auth/payments; buckets isolated; backoff is UX-only).
- Tests: backend 373→**380** (+7 wiring assertions); frontend 76→**81** (+5 component) plus the 4 service 429 tests from S2. Full suites green.
- Smoke (6.8): 15 rapid authenticated polls → all 200, zero 429; `/perito/result` → 200 + 170.01 €.

## Lessons / follow-ups
- **High-frequency polling endpoints need their own rate-limit bucket** sized to the poll cadence — a shared low bucket silently breaks long-running client polls. Candidate sibling issue: `GET /payment/status` is also a poll but kept on the 10/min `cliente` bucket (out of scope here) — watch for the same symptom on the payment wait screen. **Follow-up: consider moving `/payment/status` to a poll bucket.**
- **Docker shared gateway IP** still pools all clients into one bucket; the higher limit makes it tolerable. Prod mitigation already documented in `core/rate_limit.py` (`TRUST_PROXY_HEADERS=True` + `--forwarded-allow-ips`). Not solved this cycle.
- Frontend lint (`npm run lint`) exits 127 — `eslint` not installed in the project. Pre-existing gap, flagged (not this cycle's regression).
- This cycle was a downstream discovery from the audit cycle's live testing — the audit table (`perito_webhook_events`) helped confirm the webhook side was fine, isolating the bug to the frontend poll path quickly.

## Telemetry
See `agent-telemetry/REQ-20260616-DD-perito-poll-ratelimit-telemetry.json` (7 agent runs).
