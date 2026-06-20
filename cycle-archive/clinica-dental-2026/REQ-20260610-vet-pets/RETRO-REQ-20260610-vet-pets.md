# Final Audit — REQ-20260610-vet-pets (Mascotas, Cycle 1)

**Mode:** Kuraka Normal (8 phases) · **Outcome:** all gates passed · smoke GREEN ·
8 code commits · 1 runtime BLOCKER fixed and verified live.
This is a frontend-only repo; `docs/` is gitignored — this RETRO is an on-disk
artifact (mirrored to the vault).

---

## 1) Summary

- **Total iterations:** **medium**. The cycle ran the full pipeline cleanly; rework
  was concentrated in **two avoidable loops** (one routing re-implementation, one
  contract-fidelity correction) plus one unavoidable runtime BLOCKER caught only at
  the live smoke.
- **Main causes of rework:**
  1. **Route pitfall described in prose, not bound.** The architect (Phase 3) caught
     the dead-sibling `path:'customer'` route as a MINOR, the orchestrator amended S6
     AC — but S3 had already created the broken two-sibling form first → a dedicated
     routing-fix sub-task (commit `2a482fa`).
  2. **Verbatim-payload under-modeling.** The frozen schema modeled the authorized-person
     nested item as 7 fields (hash refs, `sex_hash`) when the PO's verbatim `add-pet` /
     `add-authorized` bodies carry **14 fields with INT codes** and `pet_sex_hash`.
     po-analyst AND architect both missed it; only the orchestrator's *directed*
     Phase-5 cross-check caught it → FREEZE AMENDMENT + 14-field rebuild.
  3. **Runtime BLOCKER invisible to `ng build`.** `effect()`/`rxResource()` created
     in an event handler (Add-authorized click) outside injection context → `NG0203`
     at runtime; `ng build` was green. Only the live smoke (6.8) surfaced it.
- **Estimated preventable iterations:** **~2 loops** (the routing re-implementation +
  the verbatim-fidelity loop). The NG0203 loop was **detectable only at runtime** —
  not preventable by build, but preventable as a *known guard* in the frontend profile.
- **Cycle cost:** **1,730,083 tokens** across **16 agent runs** (554 tool uses,
  ~149 min wall). All runs `budget_ok`. No phase flagged over-budget.

---

## 2) Timeline of Rework

| Phase | Issue | Root Cause | Preventable? | Fix |
|-------|-------|-----------|--------------|-----|
| 1 (PO) | GATE0 BLOCKED — 5 blockers (B1 list-pet shape, B2 details shape, B3 hash-vs-INT, B4 master_ids, B5 breed cascade) | Backend contract genuinely ambiguous; PO surfaced rather than invented | **No** (correct behavior — this is the gate working) | User decisions: Cycle-1 scope, defaults+validate-live, B3 verbatim, B5 breed cascade. Resolved → Phase 2 unblocked |
| 1 (PO) | Authorized-person nested item modeled as 7 fields / hash refs / `sex_hash` instead of PO's verbatim 14-field INT body | po-analyst did not run a field-by-field check against the *exact verbatim bodies the user supplied* | **Yes** | Caught at Phase 5 via directed cross-check; FREEZE AMENDMENT A-1/A-2; rebuilt in fix commit `5aac2f5` |
| 3 (Architect) | Same under-modeling passed into the FROZEN schema | Architect froze the contract without a verbatim-payload diff; treated the S6 route issue as MINOR prose, not a binding snippet | **Yes** | Schema FREEZE AMENDMENT (Phase 5); route AC amended on S6 but too late for S3 |
| 4b (S3 dev) | Implemented the broken two-sibling `path:'customer'` form despite the architect's finding #1 | The pitfall lived as a **Technical Note**, not a **binding corrected route snippet**; S3 created routes before S6's amended AC reached the dev | **Yes** | Routing-fix sub-task `2a482fa`: nested `/vet/customer/:customerHash/pets` |
| 5 (Code review) | 1 BLOCKER (NG0203 injection context) + 6 IMPORTANT (authorized 14-field/INT, `pet_sex_hash`, `created_by`, error handlers, modal `customerHash`, tests) | `effect()`/`rxResource()` built in event handler; verbatim-fidelity gap from Phases 1/3 | BLOCKER: **No** (runtime-only). IMPORTANT contract gaps: **Yes** (earlier) | Fix commit `5aac2f5`; focused re-review APPROVED_WITH_MINOR |
| 6.8 (Smoke) | Proved NG0203 fix live; surfaced backend `vet/list-pet` 500 (F10/F19) and cosmetic owner-card hash label | Backend colation bug (not this cycle); cosmetic inherited from customer detail render | n/a (backend follow-ups) | F13 error state handles the 500 correctly; cosmetic → follow-up |

---

## 3) Agent Findings

### po-analyst (Phase 1)
- **What went RIGHT:** GATE0 worked exactly as intended — 5 genuine contract
  ambiguities surfaced as explicit `AskUserQuestion` blockers with safe defaults
  (the `customerType:0` precedent), nothing invented. Verbatim user decisions
  recorded. Two-cycle phasing (highest-value/lowest-ambiguity slice first) was a
  sound scoping call.
- **What failed:** the user supplied **exact verbatim `add-pet` / `add-authorized`
  request bodies**, yet the authorized-person nested item was modeled at 7 fields
  with hash refs and `sex_hash`. A field-by-field fidelity check against those
  bodies was never run — the divergence (14 fields, INT codes, `pet_sex_hash`)
  flowed downstream to the freeze.
- **Why:** the consistency check focused on *what's missing/ambiguous* (gaps), not
  on *what's present and must match exactly* (fidelity). When the PO has the
  authoritative bytes, fidelity is a distinct, higher-leverage check.
- **Instruction update (project-layer, preferred):** add a "verbatim-payload
  fidelity" check — see Patch P1.

### story-refiner (Phase 2)
- **What went RIGHT:** clean S1–S6 decomposition with file paths, API contracts, TS
  types, i18n keys; encoded the verbatim casing (`upd-Allergies`, `add-disease`) and
  N3/N4 "do not correct" notes so the dev didn't normalize them.
- **What failed:** the route nesting correction (once known) was expressed as
  Technical-Note prose on S6 rather than a **binding corrected route snippet** that
  the S3 dev was forced to copy. Prose AC is weaker than a literal snippet.
- **Instruction update (project-layer):** route/structural pitfalls become binding
  corrected snippets — see Patch P2.

### test-engineer (Phases 2.5 + 6)
- **What went RIGHT:** 28-test plan up front, then 48 unit specs all green on
  ChromeHeadless, asserting the load-bearing details (verbatim URLs, B3 hash payload,
  `pet_sex_hash`, authorized 14-field INT, state flags, `backendError`). Tests
  encoded the *corrected* contract — good regression lock.
- **What failed:** nothing actionable. Note: unit tests (Jasmine) could **not** catch
  the NG0203 injection-context BLOCKER (it's a runtime-context error, not a logic
  error) — this is a known Angular gap, addressed below as a developer guard.

### architect-reviewer (Phase 3)
- **What went RIGHT:** caught the dead-sibling route as finding #1; produced a frozen
  schema with explicit `[VERIFIED]` / `[ASSUMED — validate in vivo]` tagging that made
  the GATE0 risk auditable.
- **What failed (two items):**
  1. Froze the contract **without** a field-by-field diff against the PO's verbatim
     bodies → carried the 7-vs-14-field / `sex_hash` under-modeling into the freeze.
  2. Surfaced the route pitfall as a MINOR note instead of **rejecting** the
     two-sibling structure with a binding corrected snippet in the freeze.
- **Instruction update (project-layer):** the schema-freeze step gains a
  verbatim-fidelity gate AND a "binding-snippet for structural pitfalls" rule —
  Patches P1 + P2.

### frontend-developer (Phase 4b, ×7 runs)
- **What went RIGHT:** F13 backend-error pattern reused correctly; B3 verbatim
  discipline (hash in nested `add-pet`, INT in standalone) held; tenant key from
  `UserService` (never route param); breed cascade (B5) implemented; `ng build`
  green every story. The S5 dev **proactively flagged** the authorized field-set gap
  for Phase 5 — good signal-passing.
- **What failed:**
  1. S3 created the broken two-sibling route despite the architect's finding (root
     cause is upstream — prose vs binding snippet, see P2).
  2. Introduced the NG0203 BLOCKER: `effect()`/`rxResource()` created in the
     Add-authorized event handler outside injection context.
- **Instruction update (project-layer):** Angular-19 reactive-primitives guard —
  Patch P3.

### code-reviewer (Phase 5, ×2 runs)
- **What went RIGHT — the hero of this cycle.** The **directed** payload cross-check
  (orchestrator instruction) caught both the NG0203 BLOCKER and the verbatim-fidelity
  gaps (authorized 14-field/INT, `pet_sex_hash`, `created_by`) that Phases 1 and 3
  missed. Focused re-review confirmed all 6 fixes PASS with no new BLOCKER/IMPORTANT.
- **What failed:** nothing. The lesson is *upstream*: a contract-fidelity check
  belongs in PO/architect, not only as a code-review rescue (which is the most
  expensive place to catch it — 138K + 94K review tokens + a 113K fix run).

### security-reviewer (Phase 5.5)
- **What went RIGHT:** PASS, no CRITICAL/HIGH — tenant isolation correct, 0 PII/token
  leak, 7/7 sensitive controls gated by `*appCanAccess`, 0 secrets. 1 LOW
  (`company_hash` optional in types) noted. Proportionate, fast (132s).

---

## 4) Systemic Issues

1. **Fidelity vs. gap-finding are different jobs.** Both PO and architect optimized
   for *unknowns* (GATE0 blockers) and under-invested in *fidelity to known-exact
   inputs*. When the user hands over verbatim payloads, those bytes are the highest-
   authority contract and deserve a dedicated diff. The cost of missing it here was a
   full review→fix→re-review loop (~346K tokens) for what a 5-minute field diff in
   Phase 1 would have prevented.
2. **Prose pitfalls don't bind implementers.** A known structural pitfall (route
   nesting) described as a Technical Note got re-implemented wrong. Implementers copy
   snippets, not warnings.
3. **`ng build` green ≠ runtime-safe.** Angular reactive primitives (`effect`,
   `rxResource`, `toSignal`) created **outside** the constructor/field initializer —
   e.g. inside an event handler — throw `NG0203` only at runtime. The build gate and
   unit tests both passed; only the live authenticated smoke caught it. This is a
   recurring class for this Angular-19 + signals stack and must be a standing guard.
4. **Telemetry present and clean** — no missing-file issue; all 16 runs recorded with
   tokens/tool_uses/duration and `budget_ok`.

---

## 5) Workflow Improvements (Concrete)

1. **Add a verbatim-payload fidelity gate to Phase 1 and Phase 3.** When the user/PO
   supplies exact request/response bodies, produce a field-by-field table (name ·
   type · hash-vs-INT · per-endpoint) and diff every interface against it before the
   freeze. (P1)
2. **Structural/route pitfalls become binding corrected snippets, not prose.** The
   architect rejects the wrong structure and the story carries the exact corrected
   route block as a copy-this AC. (P2)
3. **Standing Angular-19 reactive-context guard** in the frontend profile:
   `effect()`/`rxResource()`/`toSignal()` created anywhere other than a
   constructor/field initializer MUST use `runInInjectionContext(injector, …)`. (P3)
4. **Keep the directed code-review cross-check** — it paid for itself. Make it
   *reusable* (project review-check) rather than an ad-hoc orchestrator instruction
   per cycle. (P4)
5. **For modules consuming a known-buggy backend endpoint** (colation 500s, F10),
   pre-flag the F13 error-state requirement in the story so the smoke expectation is
   "error state renders," not "data renders."

---

## 6) Patches Proposed

### P1 — Verbatim-payload field-by-field fidelity check (PO + architect)
- **Type:** project-layer
- **Target:** `.claude/project/review-checks/verbatim-payload-fidelity.md` (new)
- **Change:** create the file:
  ```markdown
  # Review check — Verbatim-payload fidelity
  applies_to: [po-analyst, architect-reviewer]

  TRIGGER: the user/PO supplies exact request or response bodies (copied from
  Postman, the backend, or a chat message).

  RULE: before freezing any interface, build a field-by-field table for EACH
  supplied body — `field · type · hash-vs-INT · endpoint(s) that send it` — and
  diff every generated interface against it. A field present in the verbatim body
  but absent/renamed/retyped in the interface is a BLOCKER-adjacent finding, not a
  minor. Casing, `*_hash` vs `master_*` INT, and field-name renames
  (`sex_hash`→`pet_sex_hash`, `phone`→`numero`) are load-bearing.

  ORIGIN: REQ-20260610-vet-pets — authorized-person item modeled at 7 fields/hash
  when the verbatim add-pet/add-authorized body had 14 fields/INT; only a directed
  Phase-5 cross-check caught it (~346K tokens of rescue).
  ```
- **Insertion point:** new file; reference it from `po-analyst.append.md` and
  `architect-reviewer.append.md` (create if absent) with one line: `When the PO
  supplies verbatim bodies, run review-checks/verbatim-payload-fidelity.md.`

### P2 — Structural/route pitfalls must be binding corrected snippets
- **Type:** project-layer
- **Target:** `.claude/project/review-checks/binding-pitfall-snippets.md` (new)
- **Change:** create the file:
  ```markdown
  # Review check — Binding pitfall snippets
  applies_to: [architect-reviewer, story-refiner]

  RULE: when a review identifies a structural pitfall (route nesting, provider
  scope, lazy-load shape), do NOT describe it as a Technical Note. REJECT the wrong
  structure and embed the EXACT corrected block as a copy-this acceptance criterion
  in the owning story. The developer must be able to paste it verbatim.

  ANTI-PATTERN (observed): "Note: avoid two sibling path:'customer' routes" as
  prose → S3 dev re-created the broken structure → routing-fix sub-task.
  CORRECT: the story AC contains the literal nested-route block to copy.

  ORIGIN: REQ-20260610-vet-pets architect finding #1 (dead-sibling route).
  ```

### P3 — Angular-19 reactive-primitives injection-context guard
- **Type:** project-layer
- **Target:** `.claude/project/conventions/architecture.md` (append a subsection) —
  also surface in the frontend stack profile.
- **Change:** append:
  ```markdown
  ## Reactive primitives outside the constructor (NG0203 guard)

  `effect()`, `rxResource()`, `toSignal()` and other reactive primitives MUST be
  created in a constructor, field initializer, or other injection context. If you
  create one inside an EVENT HANDLER or any method that runs later (e.g. an
  "add row" click that spawns a per-row `effect()`/`rxResource()`), it throws
  `NG0203: inject() must be called from an injection context` at RUNTIME — `ng build`
  will NOT catch it.

  REQUIRED: wrap such dynamic creations in
  `runInInjectionContext(this.injector, () => { … })` with
  `private readonly injector = inject(Injector)`, and clean up returned
  `EffectRef`/subscriptions on row removal / destroy.

  ORIGIN: REQ-20260610-vet-pets BLOCKER (pet-authorized-person-form, "Agregar
  persona"); build was green, only the live smoke (6.8) caught it.
  ```

### P4 — Promote the directed payload cross-check to a standing review-check
- **Type:** project-layer
- **Target:** `.claude/project/review-checks/directed-contract-crosscheck.md` (new)
- **Change:** create the file so Phase-5 code review *always* runs a payload
  cross-check against the frozen schema + any verbatim bodies, instead of relying on
  a per-cycle orchestrator instruction. Reference it from the code-reviewer rules.
  ```markdown
  # Review check — Directed contract cross-check (Phase 5)
  applies_to: [code-reviewer]

  ALWAYS cross-check the implemented request/response bodies against (a) the FROZEN
  schema and (b) any verbatim bodies the PO supplied. Field name, type, hash-vs-INT,
  casing. This check caught the cycle's BLOCKER-adjacent gaps in REQ-20260610.
  ```

### P5 — Record the lesson
- **Type:** project-layer
- **Target:** `.claude/project/lessons-learned/` + `INDEX.md`
- **Change:** add `LL-001-verbatim-payload-fidelity.md` (origin REQ-20260610;
  symptom: 7-vs-14-field authorized item + `sex_hash`; cause: no fidelity diff vs
  verbatim body; rule: P1) and `LL-002-ng0203-runtime-guard.md` (rule: P3). Add both
  rows to the INDEX table. Mirror to the vault per rule 16.

> **Framework patches:** none proposed. Every finding here is specific to this
> project's stack (Angular 19 signals, verbatim-Spanish backend bodies, the
> hash-vs-INT B3 idiom) — project-layer is the correct home. No universal lesson
> warrants versioning the framework agents.

---

## 7) Next-Requirement Guardrails

**Mandatory pre-implementation checks:**
- [ ] If the user supplied verbatim payloads → run **P1** field-by-field diff in
      Phase 1 AND before the Phase-3 freeze.
- [ ] Any structural/route pitfall found in review → ships as a **binding corrected
      snippet** in the story AC (P2), never as prose.

**Mandatory naming/contract checks (this stack):**
- [ ] hash-vs-INT per endpoint is explicit (B3 idiom): nested `add-*` uses `*_hash`,
      standalone `add/upd-*` uses `master_*` INT.
- [ ] Field renames honored verbatim: `pet_sex_hash` (not `sex_hash`), `numero`
      (not `phone`), `upd-Allergies` capital A, `add-disease` singular.

**Mandatory runtime/schema checks:**
- [ ] No `effect()`/`rxResource()`/`toSignal()` created in an event handler without
      `runInInjectionContext` (P3) — grep the diff before declaring build-green a pass.
- [ ] A **live authenticated smoke** runs for any module with dynamic reactive
      primitives — `ng build` green is necessary but not sufficient.

**Open backend follow-ups carried out of the cycle:**
- **F10 / F19** — `vet/list-pet` returns **HTTP 500** (colation bug 1267,
  `sp_vet_*`), same family as `list-customer`. FE handles it via F13 error state;
  data path unverifiable until backend fixes the SP collation.
- **F18** — `MASTER_IDS = 0` placeholders (especie/raza/sexo/sangre/alergia/severidad/
  estado), plus confirm `DNI_DOC_CODE` (DNI INT code for the per-row trigger) and the
  masterargu **option field name** (`optionId` vs alternative). Selects render empty
  until confirmed in vivo.
- **F20** — **Cycle 2** (S7–S11): pet-detail screen + granular sub-entity management
  (allergy/disease/authorized modals + `upd-Allergies`/`add-disease`/`add-authorized`
  with `created_by`); depends on B2 (`vet/list-details-pets` embed shape).
- **Cosmetic (minor)** — owner card on Cliente-Detalle shows the `tipo_doc` **hash**
  (`0zD2…: 46283766`) instead of "DNI 46283766"; inherited from the customer-detail
  render — resolve the masterargu label.

---

## 8) Token & Latency Telemetry

Ranked by `total_tokens` descending.

| Phase | Agent | Tokens | Tool uses | Duration | Produced | Notes |
|-------|-------|-------:|----------:|---------:|----------|-------|
| 3 | architect-reviewer | 148,865 | 20 | 161s | APPROVED_WITH_MINOR + frozen schema | Highest single run; froze contract but missed verbatim diff (P1) |
| 6 | test-engineer (writing) | 142,031 | 60 | 929s | 6 specs, 48 tests green | Locked corrected contract as regression |
| 5 | code-reviewer (review) | 138,531 | 86 | 409s | CHANGES_REQUIRED: 1 BLOCKER + 6 IMPORTANT | **High value** — directed cross-check caught BLOCKER + fidelity gaps |
| 2 | story-refiner | 122,574 | 44 | 447s | S1–S6 stories | — |
| 5.5 | security-reviewer | 117,432 | 19 | 132s | PASS, 1 LOW | Proportionate |
| 5 | frontend-developer (fixes) | 113,767 | 43 | 336s | 6 fixes (runInInjectionContext, pet_sex_hash, 14-field authorized, …) | Rescue cost of the fidelity gap |
| 1 | po-analyst | 109,043 | 21 | 500s | REQ + GATE0 (5 blockers) + 11 stories + phasing | — |
| 4b | frontend-developer (S5) | 107,767 | 40 | **4,169s** | 3 sub-components, nested arrays | ⚠️ **Duration outlier** (~69 min) vs ~107K tokens — long wall time relative to tokens (likely build/wait stalls), not a token overrun |
| 4b | frontend-developer (S4) | 107,685 | 39 | 235s | pet modal shell + B5 cascade | — |
| 4b | frontend-developer (S3) | 107,489 | 41 | 257s | Cliente-Detalle host + pet-modal stub | Created broken sibling route (fixed next run) |
| 2.5 | test-engineer (planning) | 103,067 | 18 | 190s | 28-test plan | — |
| 4b | frontend-developer (S6) | 94,183 | 36 | 149s | nav/viewPets/i18n/icons | — |
| 5 | code-reviewer (re-review) | 94,058 | 50 | 189s | APPROVED_WITH_MINOR | All 6 fixes PASS |
| 4b | frontend-developer (S2) | 79,573 | 15 | **682s** | 4 services | Duration high vs 15 tool uses / 79K tokens — wall-time stall, not token overrun |
| 4b | frontend-developer (S1) | 78,206 | 14 | 105s | 5 interface/constant files | Leanest run |
| 4b | frontend-developer (S3 route fix) | 65,812 | 8 | 41s | dead-sibling route fix | **Pure rework** — cost of P2 not being applied |

**Totals:** **1,730,083** tokens across **16** agent runs (554 tool uses, ~149 min wall).

**Observations:**
- **No phase over budget on tokens** — all `budget_ok`. The pipeline was well-scaled
  to a Normal-mode, contract-heavy module.
- **Token cost of preventable rework ≈ 65,812** (the S3 route-fix run, P2) **+ ~252,298**
  (the Phase-5 review 138,531 + fix 113,767 attributable in large part to the
  verbatim-fidelity gap that P1 would have prevented upstream). Catching these in
  Phase 1/3 would have shifted them from rescue (≥318K) to a sub-5-minute check.
- **Two duration outliers** (S5 ~69 min, S2 ~11 min) are **wall-time**, not token,
  anomalies — token counts are in-band for their tool-use counts. Likely
  build/dev-server waits; worth watching but not a cost issue.
- **Highest-value runs:** the Phase-5 code-review pair (directed cross-check) and the
  Phase-6 test-writing — both bought durable correctness.

**Optimization backlog (carry into next cycle / Cycle 2):**
- [ ] Apply P1 in Phase 1 to retire the ≥318K rescue cost when verbatim bodies exist.
- [ ] Apply P2 to eliminate the route-fix rework class (65K/cycle).
- [ ] Apply P3 + mandatory live smoke for reactive-primitive modules (Cycle 2 has
      allergy/disease/authorized modals — same NG0203 risk surface).
- [ ] Investigate the S5/S2 wall-time stalls (dev-server/build waits) — no token
      action needed, but they inflate cycle latency.

---

## Confidence: HIGH

Telemetry, checkpoint, REQ, frozen schema + FREEZE AMENDMENT, and smoke were all
present and consistent; every finding is traced to a named artifact and commit.
