# RETRO — Remediación de auditoría CLAUDE.md (2026-06-17)

- **Rama**: feature/GuaiHome-DD1067
- **Origen**: AUDIT-20260617 (73 hallazgos). Reportes: `audit-reports/AUDIT-20260617-{claudemd-rules,backend-33-hallazgos,frontend-34-hallazgos}.md`
- **Modo**: batched por riesgo (A/B/D reduced, C normal). 10 invocaciones de agente.

## Resultado por batch

| Batch | Alcance | Estado | Gate |
|---|---|---|---|
| **A** Config | `.gitignore` → `.env.*` + `!.env.example` | ✅ DONE | `git check-ignore`: `.env.production/.staging/.local` IGNORED; `.env.example` visible |
| **B** Backend mecánico | `Optional` (5), import-top (1), imports muertos (3), naming EN (2), response schemas Pydantic (2) | ✅ DONE | 397 tests PASS · lint PASS · review orquestador |
| **D** Frontend cosmético | hex→tokens (20) + token `muted-light`, `width`→`scaleX` (2), `motion-reduce:` (7), console (1), split `SlotModal` + `handleSubmit` | ✅ DONE | type-check PASS · `npm run build` PASS · vitest 146/146 |
| **C** Backend lógico | Enum `PeritoSessionStatus`, capas, docs try/except, splits | ✅ DONE | 397 tests PASS · code review APPROVED_WITH_MINOR (6 IMPORTANT resueltos) |
| **E** Split tests >700 LOC | 7 archivos divididos en 17 archivos + 7 módulos de helpers, todos <700 | ✅ DONE | 397 tests PASS (mismo total) · ningún test >700 LOC |

### Tareas de tooling (entre C y E)
- ✅ Reinicio del contenedor frontend (`docker compose restart frontend`) — HMR del token `muted-light`.
- ✅ **eslint montado desde cero** (nunca existió): `eslint@9` + `eslint-plugin-vue` + `@vue/eslint-config-typescript` + flat config `eslint.config.js`; script `lint` → `eslint .`. `npm run lint` exit 0. Excepción documentada: `vue/multi-word-component-names` off para `Em.vue`/`Faq.vue`.

### Batch E — detalle
7 archivos de test >700 LOC divididos secuencialmente (Rule T6, `make test` por story, 397 PASS en cada uno):
- `test_perito_webhook_service.py` (1621) → auth/payload/processing (3) + helpers
- `test_perito_service.py` (1311) → lifecycle/demo/informe (3) + helpers
- `test_repositories_perito.py` (1078) → lines/alerts/session (3) + helpers
- `test_guai_client.py` (1063) → claims/evidence (2) + helpers
- `test_perito_result_s6.py` (1046) → auth/breakdown (2) + helpers
- `test_perito_result.py` (832) → unit/poll (2) + helpers
- `test_perito_start.py` (722) → core/data (2) + helpers
Patrón: helpers/fixtures de módulo → `_*_helpers.py`; fixtures autouse importadas con `# noqa: F401` para que pytest las resuelva.

### Hallazgo colateral (Batch E)
`test_perito_webhook_service.py` usaba **SQLite in-memory** (`create_engine("sqlite:///:memory:")`), preservado en el split. PERO la memoria *followup-migrate-sqlite-tests-to-postgres* dice "8 archivos migrados a Postgres DONE 2026-06-16". **Discrepancia**: este archivo quedó fuera de esa migración. El split lo conservó en SQLite (no era scope de E). Pendiente: decidir si migrar este test a Postgres como los otros 8.

## Hallazgo clave del ciclo
La auditoría clasificó **9 try/except como BLOCKER**. La Phase 3 (architect triage) determinó que **ninguno debía borrarse**: todos son excepciones legítimas bajo CLAUDE.md §6/§7 (integración externa, contrato semántico del webhook, o traducción a excepción de dominio ya correcta). Acción correcta = **conservar + documentar**, no eliminar.
**Lección**: un auditor con criterio estricto sobre-reporta; la Phase 3 (architect) es la que aplica la *cláusula de excepción* de la regla. No saltarse Phase 3 en remediaciones de "BLOCKER try/except".

## Conflicto regla-vs-test (resuelto)
D7 (quitar `console.error` de `MapModal.vue`) rompió el test MAP-07 que **exigía** el console. Decisión del usuario: alinear a CLAUDE.md ("NO console"). Como el frontend no tiene logger ni Sentry, el error se surface vía estado (`mapError`) y MAP-07 se realineó para verificar el "no swallow" a nivel de estado. **Lección**: un test puede codificar un anti-patrón; al remediar la regla hay que realinear el test, no revertir el fix.

## Decisiones de alcance
- **Rotación de secretos** (DB/JWT/Stripe/Perito): FUERA de código → follow-up de ops/Key Vault. Los `.env.production/.staging` ya fueron eliminados del working tree por el usuario; `.gitignore` ahora los cubre.
- **Batch E (split de 7 tests >700 LOC)**: NO ejecutado. Pendiente de decisión del usuario (refactor grande y aparte).

## Deuda técnica registrada (del code review C, no bloqueante)
1. `_download_and_persist_evidence` (69 LOC) y `_build_completed_result` (65 LOC) — pre-existentes >50 LOC, no estaban en los 33 hallazgos originales. Extraer en próximo ciclo.
2. `webhooks.py` (409 LOC) y `pipeline.py` (457 LOC) se acercan al techo de 500 — la próxima story que toque estas rutas debe planear extracción (p.ej. `endpoints/stripe_webhooks.py`).
3. `result.py`: `Tuple` de typing → `tuple` builtin (MINOR).
4. `cliente.py:40`: import de DTO interno solo para anotar variable local (MINOR).
5. **Frontend lint gate roto** (`eslint` ausente) — se confió en `type-check` + `build` + vitest. Pendiente reinstalar eslint.
6. `tailwind.config.js` cambió (token `muted-light`) → **requiere reiniciar el contenedor frontend** para HMR.

## Telemetría
`agent-telemetry/REMEDIATION-20260617-claudemd-telemetry.json` — 10 runs, ~730K tokens de subagentes. Todos los batches dentro de budget. Sin retrabajo cross-story (Rule T6 secuencial + `make test` por story cumplió su objetivo: cada cambio verificado en origen).

## Pendientes para el usuario
- [ ] Rotar secretos expuestos (ops).
- [ ] Reiniciar contenedor frontend (HMR del nuevo token).
- [ ] Decidir Batch E (split de tests >700 LOC).
- [ ] Reinstalar `eslint` para restaurar el lint gate del frontend.
