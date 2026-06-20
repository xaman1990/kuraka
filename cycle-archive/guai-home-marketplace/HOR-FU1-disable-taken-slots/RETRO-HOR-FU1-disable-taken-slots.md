# RETRO — HOR-FU1 deshabilitar franjas ya elegidas

**Cycle:** HOR-FU1 (extensión de REQ-20260617-perito-horarios-calendario) · **Mode:** Reduced-by-risk · **Date:** 2026-06-17

## 1) Summary
Ajuste pedido por el usuario: si una franja (fecha + ventana) ya fue elegida, debe aparecer deshabilitada al intentar re-elegirla. Resuelto a nivel ventana ("Ya elegida") + día deshabilitado cuando sus 3 ventanas están tomadas. Cambio micro frontend (~40 LOC + helpers + tests), 0 retrabajo de scope.

## 2) Timeline
Story (orquestador) → 4b impl (frontend-developer) → smoke navegador → 5 code-review (code-reviewer: APPROVED_WITH_MINOR) → fix de 5 hallazgos → gate verde. Phases omitidas (justificado, micro-cambio): 1+2 PO formal (story directa), 2.5/3/5.5/6.5/6.7.

## 3) Findings por agente
- **frontend-developer (impl):** correcto a la primera; helpers puros `slotId`/`isWindowTaken`/`isDayFull` (honra la convención de testabilidad), 15 tests, manejo del edge de auto-avance vía `watchEffect`.
- **code-reviewer:** 1 IMPORTANT (watchEffect all-taken → `null` en vez de índice 0 tomado) + 3 MINOR + 1 SUGGESTION; 6 PRAISE. Verificó `slotId` vs `DraftSlot.id` (punto de mayor riesgo: off-by-one de mes 0/1-based) — correcto.
- **frontend-developer (fixes):** los 5 resueltos; `windowStates` computed elimina llamadas inline repetidas; test de frontera de mes (diciembre); aria-label suprime "Recomendada" cuando "Ya elegida".

## 4) Systemic / lecciones
- La **convención de testabilidad** (lógica pura en `lib/`) volvió a pagar: los 3 helpers son unit-testeables y dieron la costura para el review. Sin lecciones nuevas; nada que parchear.
- Guard anti-duplicado en 3 capas (UI `canAdd` → `handleAdd` early-return → store dedup) es un buen patrón a mantener.

## 5) Token telemetry (de REQ-20260617-...-telemetry.json, entradas FU1)
- frontend-developer (impl): 64,966 · code-reviewer: 50,905 · frontend-developer (fixes): 48,394. Total FU1 ≈ 164K. Sin fase sobre presupuesto.

## 6) Follow-ups
Ninguno propio. Hereda los pendientes transversales del proyecto (sin commit, secretos, eslint) — fuera del alcance de este ajuste.

## Confidence: HIGH
Gate final verde (type-check exit 0, vitest 146 passed) + smoke navegador PASS (`fu1-ya-elegida.png`).
