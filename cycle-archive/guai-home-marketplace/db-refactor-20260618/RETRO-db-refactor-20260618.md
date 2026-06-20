# RETRO — Ciclo de refactor de datos (2026-06-18)

- **Rama**: feature/GuaiHome-DD1067
- **Tipo**: consolidación + alineación de esquema (DBA/arquitectura), dirigido incrementalmente por el usuario.

## Qué se hizo (resumen)
1. **Consolidación de migraciones** 16 → 2 (`000001_baseline_schema` + `000002_seed_reference_data`), first-load limpio.
2. **Baseline magro**: de 39 a 23 tablas (drop de accounts/anon/scaffolds; SQLite→Postgres en tests).
3. **RBAC** real: `roles`/`modules`/`permissions`/`role_permissions`, `users.role_id`, JWT `role_key`, guards `SYSTEM_ADMIN_ROLE`, `require_permission` (definido). Roles ES (cliente/administrador).
4. **De-hardcode**: 8 reglas de pricing → `platform_config`; 7 valores ops → `.env`/Settings (comentados).
5. **Nomenclatura + trim** (DBA): `service_requests`→`cases` (+`case_id`), `tasks`→`perito_tasks` (sin campos operario), `zones`→`coverage_areas` (CP Madrid), drop `professional_profiles`, módulos 6→4, statuses podados a 12 (camino activo), `payments`→case, email cliente Madrid.

## Decisiones clave
- **No migrar features no cerradas**: scaffolds (operario/aseguradoras/reviews/notif) y estados huérfanos fuera del baseline; se re-añaden con su feature (modelo+migración juntos).
- **perito_tasks vs perito_work_items COEXISTEN**: decomposición económica/scope (Alcance) vs narrativa del informe. No fusionar (write-paths y shapes distintos).
- **`policy_number`** se conserva como deuda intencional (se derivará del registro de usuario).
- **Roles en español** (cliente/administrador); `profesional` diferido (por eso antonio fuera del demo).

## Gates aplicados (Kuraka)
architect-reviewer (Phase 3, schema-freeze) · backend/frontend/test-engineer (Phase 4, **Rule T6 secuencial + make test por story**) · code-reviewer (5) · security-reviewer (5.5, RBAC APPROVED 0 CRIT/HIGH) · migration-reviewer (baselines APPROVED) · 432 tests backend + 146 frontend · ruff/eslint limpios · `alembic check` sin drift · Phase 6.8 smoke (ver SMOKE-db-refactor-20260618).

## Lecciones / mejoras de proceso
- Los cambios incrementales dirigidos por el usuario se ejecutaron con agentes Kuraka + gates, pero SIN artefactos formales (REQ/stories/checkpoints/telemetry) por story. Para ciclos grandes conviene abrir un REQ aunque el trabajo llegue troceado, para trazar telemetría y RETRO desde el inicio.
- `architect-reviewer` previo a cada refactor grande (RBAC, rename case) evitó retrabajo: detectó blast-radius (cero `relationship()` → FK-only) y riesgos de auth (bypass/admin-literal) antes de tocar código.
- Regenerar el baseline desde modelos + `alembic check` "no drift" es la verificación más fuerte de coherencia modelo↔esquema en first-load.

## Follow-ups abiertos
- Cablear `require_permission(module, action)` a endpoints cuando se necesite control granular (hoy admin usa `require_any_role`).
- Rol `profesional` + re-añadir operario/antonio al activar ese feature.
- Validar runtime `perito_tasks` (Alcance) y `perito_work_items` (informe) con prueba e2e (pendiente usuario).
- Rotación de secretos (ops) — pendiente desde DD1067.
- `policy_number` deuda técnica.
