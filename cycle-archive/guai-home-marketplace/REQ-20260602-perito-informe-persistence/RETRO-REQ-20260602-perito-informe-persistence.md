# Final Audit — REQ-20260602-perito-informe-persistence

**Mode:** Normal (8 phases) + migration-reviewer mandatory · **Date:** 2026-06-02
**Result:** 127 tests green + live smoke GREEN · migration `32d9cda5360b` · 0 commits (user requested no commit) · 0 CRITICAL/HIGH security (2 debts MEDIUM/LOW accepted).

## 1) Summary

- **Total iterations:** Medium. 18 agent runs (15 token-bearing). The 8-phase pipeline ran clean; the cost came from **3 mid-cycle scope/decision shifts** that surfaced during implementation rather than planning.
- **Main causes of rework:**
  1. **D11** — `alert_type`/`severity`/`priority` Enums were frozen against ONE rich report; the second real fixture (§12 "Anomalía metadatos") fell outside the closed Enum → would have silently dropped alerts. Caught in S1 (Phase 4), not Phase 1/3.
  2. **Fixture mis-characterized** — REQ/test-plan described `informe_pericial_sample.docx` as "poor (no §5/§8/§10/§12)" but it actually had them. The fixture was assumed, not inspected. Cost a blocker pause in S1.
  3. **D12** — user removed the category→`categories` mapping mid-Phase-4 (after S2 was already implemented) → in-place edit of migration `32d9cda5360b` to drop `match_keywords` + seed, cancel S4, add `category_text`.
  4. **Code-review BLOCKER** — `guai_client.py` (574 > 500 LOC) tripped the project's hard file limit; the file was already large and the architect/story did not flag the growth.
  5. **S0 refactor** — `perito_service.py` (709 > 500) surfaced from a mid-cycle user audit (B4), not the Phase-1 analysis.
- **Estimated preventable iterations:** **3 loops** (D11 re-freeze, fixture blocker pause, guai_client BLOCKER split). D12 was a genuine product decision change (1 loop, partly avoidable by asking earlier). S0 was net-positive scope (not waste).

## 2) Timeline of Rework

| Phase | Issue | Root Cause | Preventable? | Earliest catch | Fix |
|-------|-------|-----------|--------------|----------------|-----|
| 3 (Architect) | D11: `alert_type` frozen as 3-value closed Enum | Schema frozen from a SINGLE sample (the rich report); externally-defined catalog assumed closed | **Yes** | Phase 3 (architect) — had two real reports available (CLM-MAN-20C98766 + CLM-MAN-75B33F05) but froze from one | Phase 4 amended schema-freeze → D11 `String` open-catalog (NFKD+slug normalized, no drop) |
| 4 (S1) | Fixture not "poor" — it had §5/§8/§10/§12; §12 carried out-of-Enum type | Fixture characterized from prose, never inspected; asserts written against the assumption | **Yes** | Phase 2.5 (test-plan) flagged "fixture rich.docx in CI" as a risk but didn't inspect content | S1 blocker → orchestrator decision: String catalog (Option A) + synthetic empty DOCX for the no-§12 case |
| 4 (post-S2) | D12: category mapping removed after S2 implemented | Product decision ("show as text vs map") not surfaced as an explicit question in Phase 1; B2 resolved the *mechanism* (match_keywords) but not the *intent* | **Partial** | Phase 1 GATE0 (B2) — should have asked "map to category_id, or just display the text?" before designing keyword mechanism | S4 cancelled; migration edited in-place (drop `match_keywords`+seed, add `category_text`); 107 passed |
| 5 (Code-review) | BLOCKER: `guai_client.py` 574 > 500 LOC | File already large; the cycle added `informe_id` capture to it; no story/architect pre-flag of the file-size headroom | **Yes** | Phase 3 (architect) — should have measured baseline LOC of every file a story ALTERs and flagged ones within ~50 LOC of the 500 limit | Fix round: split `_guai_http.py` (167 LOC) → guai_client 431 |
| 2b (Architecture audit) | S0: `perito_service.py` 709 > 500 | Pre-existing tech debt; not detected in the Phase-1 affected-files scan | **Partial** | Phase 1 — REQ §5 *did* note "vigilar el límite de 500 líneas" for perito_service but didn't measure it (709) or propose the split | User audit (B4) → S0 refactor story; split to package, 0 behavior change, 85 tests green |

## 3) Agent Findings

### po-analyst (Phase 1 — 101,649 tok, 19 tool uses, GATE0 BLOCKED)
- **What went RIGHT:** GATE0 correctly **blocked** before implementation on B1 (`informe_id` — does the payload even return it?) and B2 (category catalog/mechanism). B1 was a textbook "don't persist a column the channel never delivers" catch (same failure mode as the old always-NULL `report_url`). Notes N1–N5 with safe defaults were well-reasoned. Confidence honestly set to MEDIUM pending blockers.
- **What failed:**
  1. Characterized `informe_pericial_sample.docx` as "poor (no §5/§8/§10/§12)" **without opening it** — it had those sections. Drove a Phase-4 blocker pause.
  2. Flagged `perito_service.py` as near the 500-LOC limit ("hoy el archivo es grande") but **did not measure it (709)** nor propose the split — left it to a later user audit (B4).
  3. B2 resolved the category *mechanism* (match_keywords column) but never asked the prior question: *do we map to `category_id` at all, or just display the text?* — which the user reversed mid-cycle (D12).
- **Instruction update:**
  - Project-layer (preferred): new `.claude/project/review-checks/po-analyst.md` requiring (a) inspect every fixture before describing its contents, (b) measure actual LOC of every ALTERed file, (c) for reversible product decisions (map vs display), ask the intent question, not just the mechanism. See §6.

### story-refiner (Phase 2 — 94,945 tok, 33 tool uses)
- **What went RIGHT:** Independently detected `perito_service.py` 709 > 500 and **wrote the split requirement into S3** (to `api/services/perito/` package). Correctly sequenced S3‖S4 parallel after S2. Compact, well-bounded AC counts.
- **What failed:** Like the PO, it propagated the "poor fixture" assumption into S1's asserts without inspection. It did not pre-measure `guai_client.py` (574) — the file S1/S3 would touch — so the 500-LOC breach surfaced only in code-review.
- **Instruction update:** project-layer check — when a story ALTERs an existing file, record its current LOC in the story header and flag if `current + estimated_delta > max_file_loc`. See §6.

### test-engineer (Phase 2.5 plan + Phase 6 — 96,482 + 142,977 tok)
- **What went RIGHT:** Phase-2.5 plan listed 5 sharp risks including "fixture rich.docx in CI" and "perito_service > 500 (architect must freeze split)". Phase 6 added 19 targeted repo-level tests (IDOR isolation, open-catalog `anomalia_metadatos` survival, idempotent delete-then-insert). Final 127 green.
- **What failed:** The 2.5 plan *named* the fixture as a risk but **wrote asserts against the assumed "poor" content** instead of mandating a fixture-content inspection step before writing asserts. The risk was identified but not actioned.
- **Instruction update:** test-engineer test-plan must include a "fixture reality check" step — read/parse each real fixture and base asserts on observed content, not on the REQ's prose description. See §6.

### architect-reviewer (Phase 3 — 139,775 tok, 26 tool uses, APPROVED_WITH_MINOR)
- **What went RIGHT (strong):** Caught **2 silent bugs** that unit tests would not have surfaced — D2 (`match_keywords` must be JSON, not Text) and D9 (seed UPDATE by `slug`, not `name` — accented names would never match). D5 (shim re-exports `settings` to preserve the `_demo_off` monkeypatch) prevented a test-breakage. No false BLOCKERs.
- **What failed (the central lesson of this cycle):** Froze `alert_type`/`severity`/`priority` as **closed native Enums from a single sample report**. Two real reports were available; the second carried "Anomalía metadatos" (§12) outside the 3-value set → would have **silently dropped alerts in production**. A closed Enum on a catalog defined by an *external* system is a freeze-time hazard. Discovered in S1, forcing a schema-freeze amendment (D11 → open String catalog).
- **Instruction update (framework-worthy, see §6):** Before freezing any Enum whose value set originates from an external/upstream system, require ≥2 real samples; if the catalog is open-ended or owned by a third party, prefer **open String (normalized) + an Enum-as-reference for known values**, never a closed `native_enum`. Also: pre-measure LOC of every ALTERed file and flag breaches at freeze time.

### backend-developer (Phase 4 ×5 + Phase 5 fixes — 108K+147K+118K+130K+93K+105K tok)
- **What went RIGHT:** Handled S0 refactor cleanly (709 → package: result 357 / start 153 / poll 134 / shim 24) with **0 behavior change and 85 tests untouched**; correctly documented `cliente_service` as a non-fit for the shared helpers (AC6) rather than force-fitting. Found and fixed two real DOCX parser bugs (self-closing `<w:t/>`, `^N` anchoring). Idempotent delete-then-insert persistence. Kept the Mock fallback intact through every story (`anomalia_metadatos` survives). Applied Rule T6 (`make test-run` after the BD-touching story).
- **What failed:** Nothing attributable to the developer — the rework it absorbed (D11 amend, fixture blocker, D12 in-place migration edit, guai_client split) originated upstream (architect/PO) or from the user. The S1 run was very long (1,690s / 147K tok), largely DOCX-parser debugging that was unavoidable given fixture fragility.

### migration-reviewer (Phase 5 — 100,059 tok, 57 tool uses, APPROVED)
- **What went RIGHT:** Verified the migration production-ready — 4 additive tables, 5 nullable columns, non-blocking indexes (new tables only), symmetric round-trip up/down/up, coherent with the late D11/D12 changes. Zero findings. The mandatory inclusion of this reviewer for a schema change paid off (it confirmed the in-place D12 edit didn't break the round-trip).

### code-reviewer (Phase 5 — 151,253 tok, 86 tool uses, APPROVED_WITH_MINOR)
- **What went RIGHT:** Caught the `guai_client.py` 574 > 500 BLOCKER (project hard limit) and 2 IMPORTANTs (`_refresh_collected_fields` duplication → `bulk_replace`; `anon_guard` return type). Confirmed D1–D12 compliance, defensive parser, idempotency, PII/key handling. Most expensive single run of the cycle (151K) but high yield.
- **What failed:** The file-size BLOCKER is a *late* catch — a 500-LOC breach on a file the story ALTERs is mechanically predictable at freeze time. Not a code-reviewer fault, but evidence the limit should be checked earlier (PO/architect).

### security-reviewer (Phase 5.5 — 101,473 tok, APPROVED, no CRITICAL/HIGH)
- **What went RIGHT:** Confirmed IDOR guard runs first in all 3 flows, X-API-Key never logged nor sent to S3, 0 hardcoded secrets, 0 PII in logs, ORM-parameterized, no XXE/ReDoS. Surfaced the 2 accepted debts (MEDIUM zip-bomb no size cap; LOW `PERITO_DEMO_CLAIM_REF` prod fail-fast) with correct mitigation rationale. Cheapest reviewer (139s) for solid coverage.

### deployment-verifier (Phase 6.7 — 87,844 tok, APPROVED)
- **What went RIGHT:** Migration round-trip OK, single head, 4 models registered, env documented without secrets, docker-compose dev+test valid. Correctly justified the 6.5 E2E skip (backend-only change).

### orchestrator-direct (Phase 2b audit + Phase 6.8 smoke — 0 metered tok)
- **What went RIGHT:** The **live runtime smoke** (case GUAI-SEFKMT) validated D11/D12 against the real DB, not just unit mocks: persisted 4 valuation_lines, 3 alerts including the open-catalog `anomalia_metadatos`, 2 work_items, 4 recommendations, `informe_id`, conclusions, `video_url`+153s, `category_text` NULL (claim has no §1 — correct), price 98.01 intact. This is exactly the "smoke must exercise the real path, not only the happy unit case" lesson from the prior perito retro applied well.

## 4) Systemic Issues

1. **Single-sample schema freezing (RECURRING-RISK).** D11 is the headline systemic issue: an Enum was frozen from one example of data that is produced by a third party. This is the same class of surprise as the prior cycle's "ZIP real had v2 manifest, not the documented structure" and "get_evidence returned an array, not the documented object". **Pattern: GuaInsurTech-sourced data repeatedly diverges from a single assumed shape.** → escalate to `pattern-detector`.
2. **Fixtures described, not inspected.** Both PO and test-engineer wrote about fixture contents from prose. The fixture is on disk and parseable — the assumption was cheap to verify and expensive to get wrong.
3. **File-LOC headroom not measured at plan time.** Two separate 500-LOC breaches (perito_service 709 surfaced by user audit; guai_client 574 surfaced by code-review). The 500 limit is a known hard project rule (`conventions.max_file_loc: 500`) yet no phase mechanically measured ALTERed files against it before implementation.
4. **Reversible product decisions resolved at the mechanism level, not the intent level.** B2 nailed *how* to map (match_keywords column) but never asked *whether* to map — the user reversed the whole intent (D12) after S2 shipped.
5. **No CI / no automated test gate** (deployment-verifier INFO). The pipeline relies on `make test-run` invoked by the orchestrator; there is no CI to catch a regression on a future change.

## 5) Workflow Improvements (Concrete)

1. **≥2 real samples before freezing any externally-sourced catalog/Enum.** For data whose value set is owned by a third party (guAI), the architect must require ≥2 real samples and default to open `String` (normalized) + Enum-as-reference, not a closed `native_enum`. (Would have prevented D11 entirely.)
2. **Inspect every fixture before writing asserts.** PO and test-engineer must open/parse each real fixture and describe observed content, never the ticket's prose. (Would have prevented the S1 fixture blocker.)
3. **Measure LOC of every ALTERed file at plan/freeze time.** PO records it, story-refiner records it in the story header, architect flags any `current + delta` within ~10% of `max_file_loc`. (Would have pre-empted both 500-LOC breaches.)
4. **For reversible map-vs-display decisions, ask the intent question in GATE0**, before designing the mechanism. (Would have de-risked D12.)
5. **Keep the live runtime smoke** as the closing gate for any persistence change — it validated the late D11/D12 deltas that unit tests alone could miss. (Reinforce, don't change.)

## 6) Patches Proposed

> All patches below are **PROPOSALS**. Per rule `16-agent-backup.md` and the user's instruction, **nothing here has been applied, synced, or committed.** The orchestrator/user decides. Framework patches additionally require contributing back to the framework repo + a backup sync.

### Patch 1 — Architect: ≥2 samples + open-catalog default for external Enums (FRAMEWORK)
- **Type:** framework
- **Target:** `.claude/agents/architect-reviewer.md`
- **Insertion point:** inside `## Schema Freeze Process` (currently lines 83–89), append after the "Marker" bullet (line 89).
- **Change (exact text to add):**
  ```markdown
  ### External-catalog Enum rule (mandatory)
  Before freezing any Enum (or `native_enum` column) whose value set originates
  from an EXTERNAL/upstream system (third-party API, partner-generated document):
  - Require **≥ 2 real samples** of the source data. Freezing a closed value set
    from a single sample is a BLOCKER-class hazard (a value seen only in the 2nd
    sample is silently dropped in production).
  - If the catalog is open-ended or owned by a third party, **prefer open
    `String` (normalized, e.g. NFKD+slug) + an Enum-as-reference for the known
    values** — never a closed `native_enum=True`.
  - Record in the freeze doc: which samples were inspected and why the type
    (open String vs closed Enum) was chosen.
  ```
- **Rationale:** D11 this cycle; same divergence class recurred across 3 guAI cycles. Universal lesson → framework.

### Patch 2 — Architect: LOC headroom check at freeze time (FRAMEWORK)
- **Type:** framework
- **Target:** `.claude/agents/architect-reviewer.md`
- **Insertion point:** in the review checks list (the numbered table around lines 55–57; add a new check row #8).
- **Change (exact text to add as a new check):**
  ```markdown
  | 8 | Every file a story ALTERs has `current_LOC + estimated_delta ≤ conventions.max_file_loc`; flag any breach as BLOCKER with a split plan before freeze | conventions.max_file_loc |
  ```
- **Rationale:** guai_client 574>500 reached code-review late; perito_service 709>500 reached a user audit late. Mechanically predictable. Universal (every project has a max_file_loc) → framework.

### Patch 3 — Project-layer: po-analyst review-checks (PROJECT-LAYER, preferred)
- **Type:** project-layer
- **Target:** `.claude/project/review-checks/po-analyst.md` (NEW FILE — referenced by po-analyst.md rule #9)
- **Change (exact file content):**
  ```markdown
  # po-analyst — project-specific checks (GuaiHome)

  Run these IN ADDITION to the framework rules.

  ## C-FIXTURE — Inspect fixtures, never describe them from prose
  For every fixture the REQ/test-plan references (`*.docx`, `*.zip`, `*.json`),
  open/parse it and describe its ACTUAL content. Do NOT carry over a prose
  description ("poor report, no §5/§8/§10/§12") without verifying — in this
  project the guAI sample DID contain those sections (cycle 2026-06-02).

  ## C-LOC — Measure ALTERed files against the 500-LOC limit
  For every existing file listed in "Affected Services & Repositories" with
  action ALTER, run `wc -l <file>` and record the count. If `current + estimated
  delta` is within ~50 LOC of `conventions.max_file_loc` (500), propose a split
  story up front. (perito_service was 709, guai_client 574 — both surfaced late.)

  ## C-INTENT — Ask the intent question for reversible product decisions
  When a requirement involves a reversible decision (map a value to an entity vs
  just store/display the raw text), ask the INTENT in GATE0 ("map to category_id,
  or store category_text for display?") BEFORE designing the mechanism. (D12:
  the user reversed the whole mapping after the keyword mechanism was built.)

  ## C-EXTERNAL-SHAPE — guAI payloads diverge from docs
  guAI-sourced data has repeatedly differed from a single assumed shape
  (ZIP v2 manifest, get_evidence array, §12 alert types). For any guAI field,
  verify against ≥2 real payloads/reports before asserting its shape or catalog.
  ```
- **Rationale:** project-specific (guAI quirks, this fixture). Preferred over framework per the "prefer project-layer" guideline.

### Patch 4 — Project-layer: test-engineer fixture-reality step (PROJECT-LAYER)
- **Type:** project-layer
- **Target:** `.claude/project/review-checks/test-engineer.md` (NEW FILE or append if exists)
- **Change (exact text to add):**
  ```markdown
  ## C-FIXTURE-ASSERT — Base asserts on observed fixture content
  Before writing any assert against a real fixture, parse the fixture and list
  the sections/keys it actually contains. Write asserts against the observed
  content, not against the REQ's prose. If a "negative" case is needed (e.g. a
  report with NO §12), and no real fixture matches, build a minimal synthetic
  fixture rather than mischaracterizing a real one. (Cycle 2026-06-02: the
  "poor" sample actually had §5/§8/§10/§12.)
  ```
- **Rationale:** project-specific testing convention; cheap, high-leverage.

### Patch 5 — Escalation to pattern-detector (ACTION, not a file patch)
- **Type:** escalation
- **Target:** `pattern-detector` (next invocation)
- **Change:** Flag the recurring pattern **"guAI / GuaInsurTech-sourced data shape diverges from the single assumed shape"** across 3 cycles (2026-05-30 ZIP v2 manifest; 2026-06-01 get_evidence array; 2026-06-02 §12 alert catalog / fixture sections). Recommend a standing project rule: any guAI integration story must verify field shape against ≥2 real payloads.

## 7) Next-Requirement Guardrails

- **Mandatory pre-implementation checks:**
  - For any guAI-sourced field/catalog: inspect ≥2 real payloads/reports before freezing its type. Default to open `String` for third-party catalogs.
  - Inspect (parse) every fixture; describe observed content, not prose.
  - `wc -l` every file a story will ALTER; flag any within ~50 LOC of 500 with a split plan in the story.
- **Mandatory naming checks:** seed UPDATEs match by `slug`, not `name` (accents never match — D9). Keep this in the architect's freeze checklist.
- **Mandatory schema checks:**
  - JSON columns declared as `JSON`, not `Text` (D2).
  - Externally-defined catalogs → open `String` + Enum-as-reference, not closed `native_enum` (D11).
  - New persistence change → keep the **live runtime smoke** as the closing gate (validated D11/D12 against the real DB).
- **Product-intent guardrail:** for map-vs-display style reversible decisions, resolve the intent in GATE0 before building the mechanism (D12).

## 8) Token & Latency Telemetry

Ranked by `total_tokens` descending.

| Phase | Agent | Tokens | Tool uses | Duration | Produced | Notes |
|-------|-------|-------:|----------:|---------:|----------|-------|
| 5-code-review | code-reviewer | 151,253 | 86 | 310s | 1 BLOCKER + 2 IMPORTANT + 5 MINOR | Most expensive run; high yield (caught 500-LOC BLOCKER) |
| 4-S1-parser | backend-developer | 147,122 | 69 | **1,690s** | informe_parser package, DTOs, DOCX bug fixes | Longest run by far — DOCX-parser debugging; fixture fragility |
| 6-tests | test-engineer | 142,977 | 82 | 464s | +19 repo tests, coverage validation, 127 passed | Justified by IDOR/idempotency/open-catalog coverage |
| 3-architect-review | architect-reviewer | 139,775 | 26 | 319s | SCHEMA-FROZEN + D1/D2/D5/D9; 2 silent bugs caught | High value; but froze D11 from 1 sample (the cycle's main miss) |
| 4-S3-persistence | backend-developer | 130,037 | 53 | 338s | 4 repos + persistence, 0 db.query in service, idempotent | — |
| 4-S2-models+migration | backend-developer | 118,442 | 54 | 533s | 4 models + migration 32d9cda5360b, round-trip OK | — |
| 4-S0-refactor | backend-developer | 108,223 | 42 | 330s | perito_service 709→package, shared helpers, 85 green | Net-positive (debt paydown), not rework |
| 5-code-review-fixes | backend-developer | 105,873 | 48 | 279s | guai_client 574→431 (+_guai_http 167), IMPORTANTs | Rework directly traceable to late LOC catch |
| 1-po-analysis | po-analyst | 101,649 | 19 | 284s | REQ + 4 stories + GATE0 BLOCKED (B1,B2) | On budget; GATE0 paid off |
| 5.5-security-review | security-reviewer | 101,473 | 23 | **139s** | APPROVED, 2 debts surfaced | Best value/latency ratio |
| 5-migration-review | migration-reviewer | 100,059 | 57 | 224s | Migration production-ready, no findings | Mandatory inclusion justified |
| 2.5-test-planning | test-engineer | 96,482 | 22 | 230s | TEST-PLAN, 42 tests, 5 risks | Named fixture risk but didn't action it |
| 2-story-refinement | story-refiner | 94,945 | 33 | 371s | 4 stories; detected 709-LOC split into S3 | Good independent LOC catch on perito_service |
| 4-D12-categoria-texto | backend-developer | 93,503 | 48 | 564s | S4 cancelled, migration edited in-place, category_text | Pure rework from product reversal |
| 6.7-deployment-verification | deployment-verifier | 87,844 | 47 | 101s | Migration/head/models/env verified | Fast, clean |
| 2b-architecture-audit | orchestrator-direct | 0 | — | — | perito_service audit → S0 | Read-only, unmetered |
| 4-S1-parser-blocker | backend-developer | 0 | — | — | Fixture blocker resolution (String catalog) | Unmetered note |
| 6.8-smoke-runtime | orchestrator-direct | 0 | — | — | Live smoke GUAI-SEFKMT GREEN | Unmetered; validated D11/D12 vs live |

**Totals:** **1,719,657 tokens** across **15 metered agent runs** (18 runs total; 3 unmetered orchestrator-direct/notes).

**Phase bucket split:** Analysis (Ph 1–2.5) ≈ 432.9K (25%) · Implementation (Ph 4) ≈ 597.3K (35%) · Review (Ph 5–5.5) ≈ 458.7K (27%) · Verify (Ph 6) ≈ 230.8K (13%). **Analysis : implementation ≈ 0.72** — a healthy ratio; this cycle was implementation-dominant, as expected for a schema+persistence change.

**Observations:**
- **Most expensive phase bucket: implementation (35%)**, driven by the S1 parser (147K / 1,690s) — DOCX parsing of a fragile third-party template. Unavoidable given the source format; the long-term fix is the registered debt (ask guAI for structured JSON).
- **D12 rework cost ≈ 93.5K tokens** (one full backend-developer run) that was largely avoidable had the map-vs-display intent been resolved in GATE0.
- **The code-review→fixes round cost ≈ 257K** combined (151K review + 106K fixes); the `guai_client` split portion was a predictable late catch (Patch 2 would move it to freeze time, cheaper).
- **Rule T6 applied** (make test-run after the BD-touching S2) — confirmed in S2's note; good.
- **Rule T5 partially applied:** Phase-4 notes report files/ACs rather than self-verifying; the orchestrator ran the live smoke externally. Consistent with T5.
- **Rule T1 (context digest) not evidenced** — with 5 backend-developer runs sharing the same perito/parser context, a pre-cooked digest could have trimmed re-reads. Carry into backlog.

**Optimization backlog (carry into next cycle):**
- [ ] Pre-cook a parser/perito **context digest** (T1) shared across the multiple backend-developer runs (5 this cycle) to cut re-reads.
- [ ] Move the 500-LOC headroom check to Phase 1/3 (Patch 2/3) so the `guai_client` split happens before code-review, saving the ~106K fix round.
- [ ] Resolve reversible product-intent (map vs display) in GATE0 to avoid D12-style mid-Phase-4 reversals (~93K).
- [ ] Register debt (already in lessons-learned): ask guAI for structured JSON → would slash the 147K/1,690s S1 parser cost on future report-field cycles.

## Confidence: HIGH

Reason: every claim is grounded in the cycle's telemetry JSON, the REQ (GATE0 B1–B4, D11/D12), and the prior retros. The two main misses (D11 single-sample Enum, fixture-not-inspected) are concrete, attributable, and have exact-text patches. Telemetry totals were computed directly from the JSON. The one soft area is whether Patch 1/2 should be framework vs project-layer — I recommend framework for the two universal lessons and project-layer for the guAI-specific checks, but the user decides.
