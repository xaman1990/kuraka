---
description: Token-saving prompt patterns for orchestrating the Kuraka. Reduces cycle cost ~35% on low-risk changes without sacrificing rigor.
alwaysApply: true
---

# Kuraka Token Optimizations

Apply these rules whenever you orchestrate the Kuraka defined in
`.claude/skills/kuraka.md` (and companion files `kuraka-modes.md`,
`kuraka-policies.md`). They do not replace the Kuraka — they guide
*how* you prompt the subagents and *which* phases you invoke.

Baseline measured on the cycle of 2026-04-21 (homologate-new-scale-frontend):
**458K tokens** for a UI-only restyle of 7 files across 3 phases. Applying the
5 rules below, the same cycle would cost **~270–300K (-35%)**.

---

## Rule 0 — Scale the pipeline to the change's actual risk

Before launching Phase 1, evaluate the change surface and build a reduced
pipeline with only the phases that add value. Announce the pipeline, justify
which phases are skipped, and request user confirmation before invoking any
subagent.

**Surface → pipeline examples:**

| Surface | Phases to run | Phases to skip |
|---------|---------------|----------------|
| UI-only restyle (CSS classes, no logic, no types) | 1 + 2 + 4b | 2.5, 3, 5, 5.5, 6, 6.5, 6.7, 7 |
| Pure type tightening (no logic) | 1 + 4b + 5 | 2.5, 3, 5.5, 6, 6.5, 6.7, 7 |
| New endpoint with logic | full 8 phases | — |
| Auth / provider / schema change | full 8 phases + mandatory 5.5 | — |

Do not apply the rigid "Lite mode" criteria (≤ 3 files, ≤ 50 LOC) as the only
gate — they are narrow. Use them as a hint, not a law.

**Golden rule:** if you doubt whether to skip a phase, ask the user — don't assume.

---

## Rule T1 — Pre-cook a "context digest" into every subagent prompt

**Applies when:** you'll launch ≥ 2 subagents that share the same reference
files (e.g., `main.css`, visual reference pages, common rules).

**How:** before invoking the first agent, read those reference files yourself
(as orchestrator), extract the useful snippets once, and embed them into every
subagent prompt under a fixed header:

```
## Context digest (pre-extracted — do NOT re-read unless ambiguous)

### Design tokens available in main.css
- brand-lime, brand-text, brand-text-dim, brand-card, brand-panel,
  brand-border, brand-muted, brand-dark
- Component classes: card, btn-primary, btn-secondary, btn-danger,
  btn-icon, input-field, badge-lime|amber|blue|red|gray, table-row

### Reference patterns from BaremosPage.vue
- Header: `<h2 class="text-xl font-semibold text-brand-text">`
- Stepper with connector lines: {snippet with line numbers}
- Jobs table row: `<tr class="table-row">`
- Stat card: {snippet}

### Reference patterns from DuplicidadPage.vue
{snippet}
```

The agent only re-reads if it finds ambiguity.

**Estimated savings:** 30–50K tokens per additional subagent. For a 3-phase
workflow: **100–150K total.**

---

## Rule T2 — For restyles: verify only at the end, not per file

**Applies when:** the story does not change types or logic (pure
`<template>` + CSS class edits).

**How:** in the implementer's prompt, replace

> "Run `npm run typecheck` + `npm run lint` after each file. STOP on first error."

with

> "Make all class-level edits across the N files. Run `npm run typecheck` +
> `npm run lint` ONLY at the end. If either fails, identify the offending
> file from the error output and fix it."

**Why:** `vue-tsc --noEmit` reprocesses the full TS graph regardless of how
many files changed. Running it N times is identical in correctness to running
it once at the end, but costs N× in tokens and time.

For changes that **do** modify types or logic, keep the per-file check.

**Estimated savings:** 15–25K tokens + ~40% of implementation-phase time.

---

## Rule T3 — Collapse Phase 1 + Phase 2 into a single subagent for low-risk changes

**Applies when:** the surface is purely cosmetic (restyle, rename) or purely
mechanical (library swap with no contract change).

**How:** instead of [[po-analyst]] → gate → [[story-refiner]] → gate, launch one
subagent in combined mode. Prompt pattern:

```
You produce BOTH deliverables in one pass:
  (a) docs/process/REQ-{date}-{slug}.md — scope, risks, mode recommendation
  (b) docs/process/stories/REQ-{date}-S1.md — story with compact AC table (see T4)
```

This is consistent with `workflow.md`'s existing `LITE_COMBINED` mode; extend
its applicability beyond the strict 9 Lite criteria when the risk evaluation
is low.

**Do NOT collapse** when the change touches business logic, API contracts,
DB, auth or providers — there the phase separation adds real value.

**Estimated savings:** ~80–100K tokens (removes one full subagent startup +
one context re-read).

---

## Rule T4 — Compact "mapping-table" stories for mechanical patterns

**Applies when:** the story is a mechanical replacement pattern (CSS restyle,
identifier rename, import path change).

**How:** instruct the [[story-refiner]] to use a per-file mapping table
instead of narrative AC IDs:

```
Format the acceptance criteria as a mapping table per file, NOT as
narrative AC IDs:

| File | Before | After |
|------|--------|-------|
| UploadStep.vue | `bg-gray-800 rounded-xl p-6` | `card space-y-4` |
| UploadStep.vue | `bg-[#CCFF00] text-black ... hover:bg-[#B7FF1E]` | `btn-primary` |
| ... | ... | ... |

Reserve narrative AC for cases where behavior or ordering matters.
Target: ≤ 100 lines total story, not 300+.
```

**Estimated savings:** 30–40K tokens in the implementation phase (which
re-reads the story). Reference: cycle of 2026-04-21 produced a 314-line /
69-AC story — the same contract fits in ~80 lines as a compact table.

---

## Rule T5 — The subagent does not auto-verify what the orchestrator will verify

**Applies always** when the orchestrator has an external verification plan
(md5 of script blocks, diff stats, grep of imports, re-running
typecheck/lint).

**How:** add to the implementer's prompt:

```
Do NOT run verification scripts (md5, diff, grep) inside this agent.
The orchestrator will verify externally after you finish.
Report only:
  (1) files modified,
  (2) ACs satisfied,
  (3) any AC you couldn't satisfy and why.
```

**Estimated savings:** 10–15K tokens in duplicated verification tool uses.

---

## Checklist before invoking any workflow subagent

- [ ] Evaluated change surface (Rule 0) and picked the minimum phases
- [ ] Proposed the pipeline to the user with per-phase justification
- [ ] If ≥ 2 subagents share reference files → built context digest (T1)
- [ ] If restyle / mechanical → prompt asks for end-only typecheck/lint (T2)
- [ ] If restyle / mechanical → considered Phase 1+2 combined (T3)
- [ ] If restyle / mechanical → story asked as mapping table, not narrative (T4)
- [ ] Implementer prompt explicitly forbids auto-verification (T5)
- [ ] Telemetry JSON is written after every `Agent` invocation

**Golden rule:** if you doubt whether a rule T applies, ask the user — don't
assume. The cost of a one-sentence confirmation is lower than the cost of a
wasted 200K-token subagent invocation.

---

## Rule T6 — Implementación secuencial + `make test` obligatorio por story (provider migrations)

**Aplica cuando** cualquiera de estas es cierta:
- La story crea o modifica un provider, processor o integration handler.
- La story crea un seed o una migration, o cambia un modelo SQLAlchemy.
- La story usa abstract base classes, mocks cross-module o fixtures custom.
- La story implementa más de una feature distinta (riesgo de interdependencia).

**Cómo**:
- NO lanzar varias stories en paralelo. Implementar las stories **secuencialmente**.
- Después de que cada story termine, correr `make test` (o `make test-fast`) **antes** de empezar la siguiente.
- Si `make test` falla, arreglar el bug en la story actual antes de avanzar.
- Esta disciplina demostró entregar ~0 retrabajo cross-story (RETRO-DD-1031-rerun), frente a un batch que acumuló "23 fallos" (RETRO-DD-1031).

**Excepción**: stories puramente frontend sin cambios de backend pueden ir en batch, siempre que la verificación sea por-story.

**Por qué**: en DD-896 (FM-02), 3 bugs distintos de S1 se descubrieron en Phase 6 después de implementar las 7 stories. En DD-1031 el batch paralelo acumuló bugs de S1+S3+S4 que se propagaron por re-implementaciones. Secuencial + make-test por story detecta el bug en su origen.

**Estimación de ahorro**: 50-100K tokens en provider migrations (elimina la tormenta de debugging de errores acumulados).

---

## Rule T7 — Gate command integrity (correctness, not token-saving)

**Aplica siempre** que el resultado de un test/typecheck sea el gate para
avanzar una story o fase.

**Cómo**: correr el comando del gate SIN pipe y asertar sobre **su propio**
exit code (`make test-run`, luego `$?`). NUNCA pipear el comando del gate
(`make ... | tail`, `... | grep`) — el shell reporta el exit code del ÚLTIMO
comando (el del pipe), así que una suite que falla puede leerse como verde. Si
hay que recortar la salida, redirigir a un archivo y leer el archivo.

Además: al planificar el pipeline, verificar que cada gate declarado realmente
**puede fallar**. Un `make test-run` sin `--exit-code-from`, un target que no
propaga el fallo, o un eslint no instalado (exit 127) son gates muertos —
arreglarlos o marcarlos `SKIPPED (broken: <reason>)` explícitamente, nunca
tratarlos como verde.

**Por qué**: REQ-20260611 S3 avanzó en FALSO VERDE (`make ... | tail`) con la
suite fallando en collection. Ver también `kuraka-policies.md` → "Gate command
integrity" y "Definition of green".

---

## Rule T8 — Digest pre-extraído para fix-runs y para el code-reviewer

**Aplica cuando**: (a) lanzás un run de "aplicar N MINOR/IMPORTANT fixes" tras
un review, o (b) invocás al [[code-reviewer]] sobre una superficie grande.

**Problema**: estos runs recargan TODA la superficie para hacer cambios chicos.
Casos reales: un fix de 2 líneas costó **154K tokens** (clinica-dental,
REQ-20260625) porque el agente releyó el módulo/freeze/review completos; el
code-reviewer corrió 25–58 min en 4/8 ciclos releyendo archivos uno por uno
(kuraka-control P1). El costo es el contexto, no el trabajo.

**Cómo** (usá el skill [[compact-context]] para producir el digest):

- **Fix-run**: pasá SOLO `{archivo · rango de líneas · texto exacto del finding
  a aplicar}` por cada fix. Prohibí re-leer la superficie completa salvo
  ambigüedad real.
- **Code-reviewer**: pasá al inicio `{esquema/contratos congelados + tabla de
  decisión/invariantes a verificar + lista de archivos cambiados con su LOC}`.
  Una tabla de ataque/invariantes precisa hace al reviewer rápido aunque la
  superficie sea grande (validado en kuraka-control S5b-1).

**Estimación de ahorro**: 40–80K tokens por fix-run; latencia del reviewer de
25–58 min a in-band.
