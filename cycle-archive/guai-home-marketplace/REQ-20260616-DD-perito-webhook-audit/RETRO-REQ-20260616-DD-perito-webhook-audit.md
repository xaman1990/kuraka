# Final Audit - REQ-20260616-DD-perito-webhook-audit

**Feature:** Append-only audit table `perito_webhook_events` for every Perito guAI
webhook delivery (full raw payload + selected headers + source IP + returned HTTP
status, captured after auth and before validation).
**Mode:** Normal (8-phase). **Date:** 2026-06-16.
**Outcome:** Feature DONE and green (373 tests pass, smoke PASS). **Merge GATED**
on 2 CRITICAL repo-hygiene items (untracked live `.env.*` + broken `.gitignore`)
that are NOT in the feature code — user-owned, report-only remediation accepted.

## 1) Summary

- **Total iterations:** Medium. The feature itself ran clean — one architect
  correction (independent session, caught at the gate, before code) and one
  code-review fix loop (2 LOC violations). No bug-driven rework on the feature.
- **Main causes of cost:** A **mid-cycle scope expansion** dominated this cycle:
  the pure-JSONB requirement collided with the project's SQLite-in-memory unit
  tests and forced migrating 8 test files (~176 tests) to the Postgres test DB
  before the JSONB variant scaffold could be dropped. This was pulled forward by
  explicit user decision ("JSONB puro ya, adelantar limpieza SQLite") and is the
  dominant token cost (482K / 1.379M ≈ 35% of the cycle).
- **Estimated preventable iterations:** **~1 loop.** The JSONB-vs-SQLite collision
  was structurally foreseeable at GATE0 / architect-freeze (a Postgres-only column
  type breaks `Base.metadata.create_all` on SQLite). Catching it as a GATE0
  consistency question would not have removed the work, but would have planned the
  482K SQLite-removal sub-phase up front instead of discovering it at Phase 4.
  The 2 LOC violations (1 fix loop) were preventable by sizing during refinement.

## 2) Timeline of Rework

| Phase | Issue | Root Cause | Preventable? | Fix |
|-------|-------|-----------|--------------|-----|
| 1 Analysis | REQ noted "test DB is also Postgres … JSONB works in tests" (§8) but did NOT trace that the project's unit tests use SQLite in-memory `create_all`, which JSONB cannot compile. | PO read `docker-compose.test.yml` (Postgres) and concluded JSONB-in-tests was safe; missed that ~8 unit files bypass that with a local SQLite engine. | **Partial** | GATE0 consistency check: "does any existing unit test build schema via `Base.metadata.create_all` on SQLite?" whenever a new model uses a Postgres-only type. |
| 2.5 Test Plan | TC-S1-1 correctly flagged "S1 must use real Postgres JSONB, do NOT use SQLite for S1 tests." But the **implication** — that adding the model to `Base.metadata` breaks every OTHER SQLite test via `create_all` — was not traced. | Test-engineer scoped the constraint to the new S1 tests, not to the global metadata blast-radius. | **Partial** | When flagging a Postgres-only type, add: "this enters `Base.metadata`; any SQLite `create_all` test will now fail at import/setup." |
| 3 Architect | Decision 2: audit write must use an independent `SessionLocal()`, not the injected `db` (`expire_on_commit=True` → object expiry + transaction bleed + R3 coupling). Stories assumed injected `db`. | Subtle SQLAlchemy session-lifecycle detail not surfaced at refinement. | **No (caught at gate — working as designed)** | None. This is the gate doing its job: corrected on paper (AC16/AC8/AC9 amended) before a line of code was written. Positive. |
| 4a Implement S1 | Collision **surfaced**: pure JSONB broke the SQLite unit tests. Developer shipped S1 with a temporary `JSONB().with_variant(JSON(),"sqlite")` to keep the suite green (353 passed). | The orchestrator instruction was "pure JSONB, no variant"; developer deviated. The deviation **exposed** the real conflict and kept the suite green during the transition. | **Productive deviation** | Classify as productive (see §3 backend-developer). Note role-instruction adherence: deviations should be announced, not silent. |
| 4a-sqlite-removal | 8 test files (~176 tests) migrated SQLite→Postgres: FK enforcement, tz-aware datetimes, shared-DB sequencing. Pulled forward as REQ-20260616-DD-remove-sqlite-tests. | Direct consequence of the Phase-1 gap above. | **Partial (work was real; the surprise was preventable)** | Handled well: one agent derived a reusable recipe on the smallest file, then sequential batches per Rule T6. |
| 5 Code Review | 2 IMPORTANT LOC-limit violations: `receive_perito_webhook` = 106 LOC (limit 50), `record()` = 55 LOC. | Audit wiring (5 status calls + try/except blocks) was added to an already-long endpoint function without an extraction plan; `record()` docstring inflated LOC. | **Yes** | Size the target function during refinement; if adding wiring pushes it over `max_function_loc`, mandate extraction in the story. |
| 5 Code Review | Finding #3: zero dedicated audit tests at end of Phase 4. | By design — tests are Phase 6. Code review surfaced it as a gap to hand to Phase 6, not a defect. | **No** | None (test-engineer wrote all 20 in Phase 6; full suite 373 pass, no impl bugs). |

## 3) Agent Findings

### po-analyst (Phase 1 — 66.6K)
- **What went RIGHT:** Excellent REQ. GATE0 honored pre-agreed decisions without
  re-litigating; risk table R1–R7 was thorough (PII retention, response_status
  capture, failure isolation, idempotency-by-design, 413 interaction, malformed
  body, layer-violation); correct 2-story split with Rule T6 sequencing called out;
  correct head revision `c7e3f8a921b4`.
- **What failed:** Did not trace the Postgres-only-type → SQLite-`create_all`
  blast radius. §8 asserted "JSONB works in tests" based on the Postgres test
  container, missing that 8 unit files use a private SQLite engine.
- **Instruction update (project-layer — preferred):** Add a project-layer
  conventions note (see §6 patch P1). Now **partly moot** because SQLite was removed
  from the test suite this cycle — but the *general* lesson (a Postgres-only column
  type is a GATE0 consistency question) survives and should be encoded.

### story-refiner (Phase 2 — 68.0K)
- **What went RIGHT:** Clean S1/S2 split, resolved R2 to option a+c, confirmed
  unknown-session=404. Stories were faithful enough that architect found zero
  BLOCKERs.
- **What failed:** Did not size `receive_perito_webhook` against `max_function_loc`
  before assigning the audit wiring to it. The endpoint was already near the limit;
  adding 5 status calls + try/except guaranteed a violation later.
- **Instruction update (framework-level, narrow):** see §6 patch P2 — when a story
  adds branching/wiring to an existing function, the AC should state the post-change
  LOC target and pre-authorize a named extraction.

### test-engineer (Phase 2.5 — 83.9K; Phase 6 — 108.8K)
- **What went RIGHT (2.5):** TC-S1-1 correctly forbade SQLite for S1 tests; the
  413-monkeypatch and `expire_on_commit` questions were flagged for the architect —
  both turned into clean architect rulings. **What went RIGHT (6):** All 20 planned
  tests written; full suite 373 passed, 0 failed, no implementation bugs found —
  the plan held.
- **What failed (2.5):** Scoped the JSONB/SQLite constraint to the new S1 tests
  only; did not state that the model entering `Base.metadata` breaks every existing
  SQLite `create_all` test. That global implication is exactly what surfaced at
  Phase 4.
- **Instruction update:** see §6 patch P1 (shared with po-analyst).

### architect-reviewer (Phase 3 — 97.7K)
- **What went RIGHT:** Best save of the cycle. Caught the `expire_on_commit=True`
  session hazard with decisive evidence (`core/database.py:51`) and three concrete
  failure modes, ruled independent `SessionLocal()`, and amended the ACs — all on
  paper before implementation. Also pinned the 5-path `response_status` placement
  table and sanctioned the 413 monkeypatch. Schema frozen cleanly.
- **What failed:** Re-confirmed "JSONB works in tests" without flagging the SQLite
  `create_all` collision (had the test plan in hand). The architect is the last gate
  positioned to catch a schema-vs-test-harness consistency problem before code.
- **Instruction update:** see §6 patch P1.

### backend-developer (Phases 4a, 4a-sqlite-removal ×6, 5-fix — ~700K combined)
- **What went RIGHT:** Clean S1/S2 implementation; textbook session isolation
  (praised by both code + security review); all 5 status paths wired correctly;
  R3 failure isolation symmetric; LOC fixes done cleanly (`_process_perito_payload`
  + `_schedule_pipeline_task` extracted, docstring trimmed, all ≤50 LOC). The
  SQLite-removal recipe-then-batch approach (Rule T6 sequential) delivered ~0
  cross-file rework — exactly the discipline RETRO-DD-1031 prescribed.
- **Productive deviation:** Orchestrator said "pure JSONB, no variant" for S1;
  developer shipped `JSONB().with_variant(JSON(),"sqlite")` instead. This kept the
  353-test suite green during S1 and **exposed** the true conflict cleanly, letting
  the SQLite removal be sequenced as its own sub-phase rather than crashing the
  suite. Classify as **productive** — the deviation produced a better outcome than
  literal compliance would have. **However:** role-instruction adherence should mean
  *announcing* the deviation and its rationale, not silently substituting. The
  variant was later removed (pure JSONB, zero sqlite in tests) as planned.
- **Instruction update:** see §6 patch P3 — encode "when you must deviate from an
  explicit orchestrator instruction, announce it + rationale in the run summary;
  do not silently substitute."

### code-reviewer (Phase 5 — 128.5K, top consumer)
- **What went RIGHT:** Thorough 6D review; correctly caught both LOC violations and
  the (by-design) missing-tests gap; 4 PRAISE findings documenting exactly why the
  session isolation, no-mixin model, migration, and X-Api-Key non-storage were
  correct. High signal.
- **What failed:** Nothing material. Highest token consumer (48 tool uses, ~49 min
  duration) — see §8; some of this is justified by tracing all 5 status paths.

### migration-reviewer (Phase 5 — 48.1K)
- **What went RIGHT:** Tight, fast (46s), APPROVED. Verified chain integrity,
  non-unique indexes (R4), JSONB, Python-side `received_at` default, clean downgrade.
  Model exemplar of a conditional reviewer staying in scope.

### security-reviewer (Phase 5.5 — 79.3K)
- **What went RIGHT:** All 6 cycle-specific feature checks PASS (no API-key storage,
  no PII in logs, auth-before-audit ordering, no DoS via audit session, parameterized
  JSONB, no log injection). Correctly separated **feature-clean** from
  **working-tree-dirty** and BLOCKED on the real risk: 2 untracked live `.env.*`
  files + a misspelled `.gitignore` one `git add -A` from leaking secrets.
- **No failure.** This is the gate functioning. See §5.

### deployment-verifier (Phase 6.7 — not in telemetry JSON)
- **What went RIGHT:** Confirmed single linear migration head, Docker config parses,
  no new env vars, ORM↔migration match. Flagged the **missing CI/CD** (`.github/
  workflows/` absent) as a non-blocking standing gap — correct call.

## 4) Systemic Issues

- **A Postgres-only column type (JSONB/ARRAY/HSTORE/etc.) is a cross-cutting
  consistency question, not a local model detail.** It enters `Base.metadata`, so
  any test that builds schema via `Base.metadata.create_all` on SQLite breaks
  globally. This blast radius was not traced at Phase 1 / 2.5 / 3 and surfaced only
  at Phase 4. (Now partly moot: SQLite was removed from the suite this cycle, so the
  trap no longer exists in this project — but the GATE0 reflex should be encoded for
  future projects / new Postgres-only types.)
- **Mid-cycle scope expansion is the dominant cost driver and was not budgeted.**
  ~35% of the cycle's tokens (482K) went to a sub-phase that did not exist in the
  original 2-story plan. The expansion was the right call (user decision; aligns with
  project guidelines that tests run on Dockerized Postgres) and was executed well,
  but it was *discovered*, not *planned*.
- **Function-sizing is not checked at refinement.** LOC violations are caught at
  Phase 5 (code review) and fixed in a follow-up loop, when they could be pre-empted
  by the story sizing the target function.
- **No CI/CD.** Every cycle relies on local `make test-run`; no automated gate on PRs
  (migration heads, lint, tests). Standing gap, flagged again by deployment-verifier.
- **Telemetry completeness:** the JSON has 17 runs and omits deployment-verifier
  (6.7), the smoke test (6.8), and this audit (7). Minor — totals below reflect the
  17 recorded agent runs only.

## 5) Workflow Improvements (Concrete)

1. **GATE0 reflex for Postgres-only types.** At Phase 1, when a new model uses a
   dialect-specific column type, the PO must answer: "does any existing test build
   schema on a non-Postgres engine?" If yes → flag a test-harness consistency
   sub-task and budget it in the REQ.
2. **Size the target function at refinement.** When a story adds branches/wiring to
   an existing function, the story must record the function's current LOC and, if the
   change would exceed `max_function_loc`, pre-authorize a named extraction in the AC.
3. **Announce deviations.** Implementers must surface any deviation from an explicit
   orchestrator instruction (with rationale) in their run summary — never silently
   substitute, even when the substitution is better.
4. **Budget scope expansions explicitly.** When the user pulls work forward
   mid-cycle, write a one-paragraph mini-REQ (as was done here) AND record the
   expected token/phase impact so the cycle total is not a surprise.
5. **Keep the recipe-then-sequential-batch pattern** for mechanical multi-file
   migrations — it delivered ~0 cross-file rework and is consistent with Rule T6.

## 6) Patches Proposed

### P1 — Postgres-only column type → SQLite-create_all consistency check
```
- Type: project-layer
- Target: .claude/project/conventions/postgres-only-types.md (new file)
- Change:
  # Postgres-only column types and the test harness
  When a new SQLAlchemy model uses a dialect-specific type
  (postgresql.JSONB, ARRAY, HSTORE, JSONB-with-GIN, etc.):
  - It enters Base.metadata. Any test that builds schema via
    `Base.metadata.create_all(bind=<sqlite engine>)` will fail at setup,
    because these types have no SQLite compilation.
  - This is a GATE0 / architect-freeze consistency question, NOT a local
    model detail — trace the FULL blast radius before Phase 4.
  - This project removed all SQLite-in-memory unit tests on 2026-06-16
    (REQ-20260616-DD-remove-sqlite-tests); tests now run only on the
    Dockerized Postgres test DB. So the specific JSONB/SQLite trap is closed
    here — but re-verify for any NEW non-Postgres test engine introduced later.
  applies_to: [po-analyst, test-engineer, architect-reviewer]
```

### P2 — Size existing functions before adding wiring
```
- Type: framework  (affects story-refiner across consumers; narrow, universal)
- Target: agents/story-refiner.md
- Change: In the AC-authoring guidance, add:
  "When a story adds branches, try/except blocks, or service calls to an
   EXISTING function, record that function's current LOC. If the addition
   would push it past conventions.max_function_loc, the story MUST pre-authorize
   a named private-helper extraction in an acceptance criterion, so the
   implementer does not have to choose (and code review does not have to catch it)."
```

### P3 — Announce deviations from explicit orchestrator instructions
```
- Type: framework  (affects backend-developer + frontend-developer; universal)
- Target: agents/backend-developer.md (and mirror in frontend-developer.md)
- Change: In the run-summary section, add:
  "If you deviate from an EXPLICIT orchestrator/story instruction (e.g. you were
   told 'pure JSONB, no variant' but you ship a temporary variant to keep the
   suite green), you MUST: (1) flag the deviation prominently in your run summary,
   (2) state the rationale, (3) state the planned path back to the instructed
   end-state. Never substitute silently."
```

### P4 — (optional, standing) Add CI/CD
```
- Type: project-layer
- Target: .github/workflows/ci.yml (new file — out of cycle scope; follow-up)
- Change: On PR, run `docker compose exec -T backend ruff check .`, `make test-run`,
  and `alembic heads` (assert single head). Recommended by deployment-verifier
  across multiple cycles.
```

## 7) Next-Requirement Guardrails

- **Mandatory pre-implementation checks:**
  - For any new model with a dialect-specific column type → run the P1 consistency
    check (now: confirm no non-Postgres test engine was reintroduced).
  - Confirm the Alembic head before writing a migration (`alembic heads`); this
    cycle correctly chained on `c7e3f8a921b4`.
- **Mandatory naming checks:** index names must match the frozen schema
  (`ix_<table>_<col>`); non-unique where idempotency/retries require duplicates (R4).
- **Mandatory schema checks:** append-only audit tables use explicit `received_at`,
  NOT TimestampMixin; `nullable=False` enforced at DB with a Python-side default.
- **Mandatory function-sizing check:** when wiring into an existing function, verify
  the post-change LOC against `max_function_loc=50` and plan extraction (P2).
- **Secrets hygiene (carry from §5.5):** before any cycle that touches `.env*` or
  `.gitignore`, run `git check-ignore backend/.env.production backend/.env.staging`
  and confirm `!backend/.env.example` stays tracked.

## 8) Token & Latency Telemetry

Ranked by `total_tokens` descending (17 recorded agent runs).

| Rank | Phase | Agent | Tokens | Tool uses | Duration | Produced | Notes |
|---:|-------|-------|-------:|----------:|---------:|----------|-------|
| 1 | 5 | code-reviewer | 128,544 | 48 | 49.4 min | APPROVED_WITH_MINOR (3 IMPORTANT) | Top consumer; partly justified tracing all 5 status paths |
| 2 | 4a-sqlite-removal | backend-developer | 111,364 | 38 | 21.7 min | 3 small files → Postgres (32 tests) | SQLite-removal sub-phase |
| 3 | 6 | test-engineer | 108,825 | 48 | 46.2 min | 20 audit tests; suite 373 pass | Largest write phase |
| 4 | 4a-sqlite-removal | backend-developer | 103,644 | 26 | 7.4 min | perito_start + repositories_perito → PG | SQLite-removal sub-phase |
| 5 | 4a-sqlite-removal | backend-developer | 99,439 | 25 | **33.0 min** | perito_webhook_service (62 tests) → PG | SQLite-removal; longest single run |
| 6 | 3 | architect-reviewer | 97,705 | 14 | 2.8 min | APPROVED-WITH-CONDITIONS; schema frozen | High value/token (best save) |
| 7 | 2.5 | test-engineer | 83,864 | 15 | 2.2 min | TEST-PLAN (20 tests) | — |
| 8 | 4a | backend-developer | 81,533 | 39 | 6.2 min | S1 model+migration+repo (temp variant) | — |
| 9 | 5.5 | security-reviewer | 79,292 | 25 | 2.3 min | BLOCKED on 2 CRITICAL repo-hygiene | — |
| 10 | 4a | backend-developer | 73,715 | 29 | 4.6 min | S2 service+endpoint (5 paths) | — |
| 11 | 2 | story-refiner | 67,951 | 13 | 2.9 min | S1+S2 stories | — |
| 12 | 1 | po-analyst | 66,591 | 5 | 1.7 min | REQ doc | — |
| 13 | 5-migration | (backend-developer*) | 62,108 | 6 | 1.7 min | perito_service → PG (resumed) | SQLite-removal; *agent field=backend-developer |
| 14 | 5-fix | backend-developer | 61,343 | 25 | 4.1 min | LOC fixes (2 extractions + docstring) | Preventable loop (see §2) |
| 15 | 4a-sqlite-removal | backend-developer | 60,295 | 21 | 2.7 min | test_cliente_service → PG + reusable recipe | Recipe-deriving agent |
| 16 | 5-migration | migration-reviewer | 48,058 | 11 | 0.8 min | APPROVED | Most efficient reviewer |
| 17 | 4a-sqlite-removal | backend-developer | 45,073 | 13 | 23.8 min | pure JSONB; zero sqlite; 353 pass | Drops the variant |

**Totals:** `1,379,344` tokens across `17` agent runs.
(Excludes deployment-verifier 6.7, smoke 6.8, and this audit 7 — not in the JSON.)

**Observations:**
- **The SQLite-removal sub-phase dominates:** 6 backend-developer runs (rows 2,4,5,13,15,17)
  total **481,923 tokens ≈ 35%** of the cycle — for work that was NOT in the original
  2-story plan. This is the single biggest lever and was an avoidable *surprise* (not
  avoidable *work*): planning it at GATE0 would not have shrunk it but would have
  framed the cycle cost honestly.
- **code-reviewer (128.5K) and test-engineer Phase 6 (108.8K)** are the two largest
  single runs. The code-review size is broadly justified (it traced all 5 status
  paths and produced high-signal PRAISE + 3 actionable findings); worth watching
  whether the 48 tool-uses can be trimmed with a tighter context digest.
- **Duration outliers:** `perito_webhook_service` migration (33 min) and the
  pure-JSONB full-suite run (23.8 min) and the 3-small-batch (21.7 min) reflect real
  Postgres test-DB round-trips, not token waste.
- **Best value/token:** architect-reviewer (97.7K, 2.8 min) — prevented the
  `expire_on_commit` defect before any code; migration-reviewer (48K, 0.8 min) —
  tightest reviewer.
- No run exceeded budget (`budget_ok: true` on all 17).

**Optimization backlog (carry into next cycle):**
- [ ] Pre-cook a context digest (Rule T1) for multi-file mechanical migrations so
      each batch agent re-reads less — the 6 SQLite-removal runs shared conftest +
      fixture patterns and could share a pre-extracted recipe header.
- [ ] Trim code-reviewer tool-uses (48) via a tighter pre-extracted file map when the
      change set is known and small.
- [ ] Add CI so local `make test-run` cost isn't re-paid manually each cycle.

---

## Systemic Lesson (headline)

**Green tests + approved reviews ≠ done** — and this cycle proved the converse too:
the smoke test (Phase 6.8) closed the loop by writing 3 real audit rows (200/422/404)
to the live dev DB and confirming the `X-Api-Key` is never persisted, so "done" was
demonstrated, not assumed.

**The key lesson is the mid-cycle scope expansion:** a single Postgres-only column
type (`JSONB`) cascaded into a 482K-token, 8-file, ~176-test migration. A
dialect-specific column type must be treated as a **GATE0 consistency question about
the whole test harness**, not a local model decision. (Mitigated here permanently by
removing SQLite from the suite — but encode the reflex for the next project.)

---
*final-auditor · Kuraka Phase 7 · 2026-06-16*
