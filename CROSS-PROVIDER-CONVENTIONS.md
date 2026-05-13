# Cross-Provider Conventions & Migration Lessons

Doc destilado de los ciclos **DD-896 (Linea Directa v1→v2)** y **LD-unified-mailbox** (mayo 2026). Documenta convenciones cross-provider que NO están en las reglas oficiales del proyecto pero que cualquier futuro ciclo de migración/provider debe asumir como base. Vive en la raíz del vault Kuraka para que esté disponible a TODOS los proyectos, no solo SIE v2.

---

## 1. Mailbox naming convention

**Patrón obligatorio**: `<Compañía> cuidacasa` y `<Compañía> guainsurtech` para los 2 buzones IMAP del proveedor (uno por tenant operacional).

| Provider | Mailbox cuidacasa | Mailbox guainsurtech |
|---|---|---|
| IMA | `IMA cuidacasa` | `IMA guainsurtech` |
| Santander | `Santander cuidacasa` | `Santander guainsurtech` |
| Linea Directa | `Linea Directa cuidacasa` | `Linea Directa guainsurtech` |

**Por qué importa**: el `MailboxOrchestrator` resuelve compañía y contracts por reglas (`company_resolution_rules`, `contract_resolution_rules`), no por el nombre del buzón — pero el naming consistente facilita la lectura visual del frontend, los logs, y la debugging.

**Anti-patrón evitado**: usar nombres de contracts (LdBcn, LdTgn) como nombres de buzones — confunde el rol del buzón (transport) vs el rol del contract (routing destino).

---

## 2. `scheduling_tasks` dual-dispatch rule

**Email tasks usan `mailbox_id`, API tasks usan `company_id`**. NUNCA mezclar.

```sql
-- ✅ CORRECTO: email task con mailbox_id
INSERT INTO scheduling_tasks (tenant_id, mailbox_id, name, task_type, ...)
VALUES (1, <mailbox_id>, '<Provider> email <tenant>', 'email', ...);

-- ✅ CORRECTO: api task con company_id
INSERT INTO scheduling_tasks (tenant_id, company_id, name, task_type, ...)
VALUES (1, <company_id>, '<Provider> API polling', 'api', ...);

-- ❌ INCORRECTO: email task con company_id (ignora el buzón específico)
INSERT INTO scheduling_tasks (tenant_id, company_id, name, task_type, ...)
VALUES (1, <company_id>, 'LD email IMAP', 'email', ...);
```

**Reflexión de paridad**: si tu seed tiene N buzones IMAP, debe tener **N email tasks** (una por buzón). El `MailboxOrchestrator` necesita un task por cada buzón a procesar.

**Validación**: el modelo Pydantic + service layer enforce este contrato en runtime, pero el seed SQL NO tiene constraints. Errores se detectan tarde si no aplicas la convención manualmente.

---

## 3. Seed file numbering convention

**Patrón observado** (no oficialmente documentado):
- Seeds se cargan **alfabéticamente** por `database/scripts/run_seeds.py`
- Numerar `01_*.sql` a `NN_*.sql` con padding para forzar orden
- Dependencias: si `B` necesita data de `A`, numerar `A < B`

**Próximo número disponible**: revisar `ls database/seed_data/` y tomar el siguiente entero libre. **Dejar gaps** (saltar 1-2 números) si se anticipa que un seed nuevo intermedio podría necesitar inserción.

**Ejemplo del ciclo LD**: `25_kutxa.sql` era el último de Kuraka. `26_multiasistencia_rules.sql` se añadió. LD se asignó `29_linea_directa.sql` dejando 27/28 libres para futuras adiciones (Caser regional, AXA expansión, etc.).

---

## 4. Mailbox seeding: pre-cipher con dev key + ops update per env

**Patrón canónico** (IMA/Santander/Kutxa/Linea Directa):

```sql
INSERT INTO mailboxes (tenant_id, name, encrypted_data) VALUES
    (1, '<Provider> cuidacasa', 'ENCv1:<output de utils.encryption.encrypt() local>'),
    (1, '<Provider> guainsurtech', 'ENCv1:<output cifrado dev>')
ON CONFLICT (tenant_id, name) DO UPDATE SET
    encrypted_data = EXCLUDED.encrypted_data,
    active = TRUE,
    updated_at = NOW();
```

**Generación del `ENCv1:` para dev** (mismo patrón para cualquier provider):

```bash
docker exec guai_platform_backend python -c "
from utils.encryption import encrypt
import json
payload = [{
    'host': '<mail.cuidacasa.com>',
    'port': 993,
    'secure': True,
    'user': '<provider@cuidacasa.com>',
    'password': '<password real>',
    'isOffice365': False,  # True para guainsurtech
}]
print(encrypt(json.dumps(payload)))
"
```

**Para staging/prod**: cada entorno tiene su propia `ENCRYPTION_KEY`. Ops actualiza los `encrypted_data` via `POST /api/crud/mailboxes` con creds reales del entorno. El seed sirve como bootstrap; **NUNCA** se promueve a prod sin update por ops.

**Anti-patrón evitado** (DD-901 §11 inicial): excluir mailboxes del seed con justificación "encryption key per env". Todos los otros providers SÍ los incluyen — ser inconsistente solo causa gaps invisibles. La convención es: **siempre incluir mailboxes en seed con dev key; documentar que ops actualiza per env**.

---

## 5. MySQL→PostgreSQL migration script: gotchas

### 5.1. `ON CONFLICT (id) DO NOTHING` puede ocultar fallos de migración

Si la tabla destino YA tiene rows con los mismos IDs (de runs anteriores, tests, orchestrator activo), el INSERT salta esos rows silenciosamente. **No es un error, no aparece en la barra de progreso**, pero los datos NUEVOS de MySQL no llegan a PG.

**Protocolo seguro antes de cualquier migración**:
1. `make clean-cases` (truncate cases, cases_raw, log_tasks, log_tasks_details, outbounds)
2. (Opcional) verifica `SELECT MAX(id) FROM cases` en PG — debería ser 0 o reservado para seeds
3. Corre la migración
4. Verifica counts post-migración contra MySQL (`SELECT status, COUNT(*) FROM expedientes WHERE cliente IN (...)` vs lo mismo en PG)

### 5.2. Host Python deps necesarias

El script importa el código del backend (`utils.encryption` → `utils/__init__.py` → `utils/jwt_utils.py`). Necesita:

```bash
uv pip install --system --break-system-packages -r requirements.txt
# o como mínimo: python-jose[cryptography] bcrypt psycopg2-binary mysql-connector-python python-dotenv
```

Si no, falla en cascada: `ModuleNotFoundError: jose` → `bcrypt` → etc. Documentar en el README del backend que el script requiere setup adicional del host.

### 5.3. `_USER_ROLE_MAP` requiere mapping para CADA user MySQL

El script crashea con `ValueError: User 'X' has unmapped role` si encuentra cualquier user en MySQL `accounts` que no esté en el map. Para users no usados (placeholders, testing), aplicar **opción C** (skip):

```python
_USER_ROLE_MAP = {
    ...,
    "username_inactivo": None,  # skip: persiste en `users` sin role assignment
}
```

Y modificar `_resolve_role` para retornar None y filter en `user_role_values`. Patrón documentado en este ciclo.

### 5.4. ID preservation: cases v1 mantienen su ID en v2

`cases.id` viene de `expedientes.id` MySQL. Permite cross-referencing v1↔v2 directo. Pero el `id_unico` de cases pre-migración (creados por orchestrator de tests) NO comparte el espacio de IDs MySQL — pueden colisionar si los IDs MySQL son pequeños o si hay tests previos en BD. Por eso §5.1.

---

## 6. Phase 6.8 (smoke runtime) DEBE incluir comparación visual v1 ↔ v2 en migraciones legacy

**Regla universal del Kuraka** (añadida en RETRO DD-896 MP-05): ningún ciclo cierra sin smoke runtime end-to-end.

**Refuerzo para migraciones de provider legacy**: cuando el ciclo migra un provider de v1 a v2, el smoke test runtime DEBE incluir:

1. **Crear un caso en v2** (vía task email o API según corresponda)
2. **Comparar visualmente** la página del expediente en frontend v2 vs el mismo caso en v1
3. **Cazar divergencias visuales** que las reviews estáticas y los tests unitarios pueden no detectar:
   - Formato de `caseDescription` (separadores `////`, prefijos `Causa:`, etc.)
   - Bloques de enrichment API ausentes (ej. Encargo en LD)
   - Wrappers artificiales que v1 no tenía
4. **Documentar las divergencias** en `docs/process/smoke-tests/SMOKE-<ticket>.md` como Phase 6.8 deliverable

**Ejemplo cazado en ciclo LD-unified-mailbox**: `_build_case_description` añadía `Causa: ... //// Descripción:` wrapping inexistente en v1. Tests unitarios pasaban. Se detectó solo cuando el usuario comparó el frontend lado a lado.

---

## 7. Cross-provider seed audit: detección de asimetrías

**Pendiente sistémico**: cada provider tiene seed `NN_<provider>.sql` con secciones similares (company, contracts, mailboxes, scheduling_tasks, resolution_rules, ...). Pero las decisiones de qué incluir/excluir han ido divergiendo:

| Sección | Asitur | Generali | IMA | Santander | Kutxa | LD (post-fix) |
|---|---|---|---|---|---|---|
| `mailboxes` | ❌ migrate script | ❌ migrate script | ✅ seed | ✅ seed | ✅ seed | ✅ seed |
| `scheduling_tasks` | ✅ seed | ✅ seed | ✅ seed | ✅ seed | ✅ seed | ✅ seed (3 tasks) |
| `company_resolution_rules` | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| `contract_variant_resolution_rules` | ✅ | ✅ Cm variant | ❌ | ❌ | ❌ | ❌ |

**Acción recomendada para próximo ciclo housekeeping** (IMP-14 del RETRO DD-896 LD): auditar TODOS los seeds, normalizar a un esquema base, generar diff para que asimetrías existan solo por razones documentadas.

**Script propuesto** (`backend/database/scripts/audit_seeds.py`):
1. Para cada `seed_data/NN_<provider>.sql`, contar inserts por tabla.
2. Detectar asimetrías cross-provider (provider A tiene N rows en X, provider B tiene 0).
3. Output: tabla markdown con razones documentadas o flag como CANDIDATE-FOR-NORMALIZATION.

---

## Resumen: checklist antes de cerrar cualquier futuro ciclo de provider migration

- [ ] Mailboxes naming `<Compañía> cuidacasa` / `<Compañía> guainsurtech` (§1)
- [ ] `scheduling_tasks` dual-dispatch: N email tasks (1/buzón) + 1 api task (§2)
- [ ] Seed numbering: siguiente entero libre, gaps deliberados (§3)
- [ ] Mailbox seed: cifrado con dev key, ENCv1 inline, comentario sobre ops update per env (§4)
- [ ] Migration script: clean target tables antes, deps host instaladas, role mapping completo (§5)
- [ ] Phase 6.8 smoke: incluir comparación visual v1↔v2 para migraciones legacy (§6)
- [ ] Seed audit cross-provider: documentar asimetrías o normalizar (§7)

---

*Fuentes*:
- `docs/process/agent-retrospectives/RETRO-DD-896-linea-directa.md` (Phase 7 ciclo DD-896)
- `docs/process/agent-retrospectives/RETRO-LD-unified-mailbox.md` (Phase 7 ciclo LD-unified-mailbox)
- `docs/process/reviews/SECURITY-REVIEW-LD-unified-mailbox.md` (findings GDPR / encryption)
- Migration script: `backend/database/scripts/migrate_mysql_to_postgres.py`
- Seeds reference: IMA (`23_ima.sql`), Santander (`24_santander.sql`), Kutxa (`25_kutxa.sql`), LD (`29_linea_directa.sql`)

*Autor*: Adenda al RETRO LD-unified-mailbox — 2026-05-12
