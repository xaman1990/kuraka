# Review checks — security-reviewer (sie_v2)

Project-specific checks the `security-reviewer` runs in addition to its
generic OWASP / framework instructions. Loaded automatically when the
agent runs in this project.

## 1. Secret scanning — sie_v2 paths

Standard secret patterns plus project-specific scope:

```bash
# Python sources under the backend
grep -rn "password\s*=\s*['\"]"     backend/ --include="*.py"
grep -rn "api_key\s*=\s*['\"]"      backend/ --include="*.py"
grep -rn "secret\s*=\s*['\"]"       backend/ --include="*.py"
grep -rn "BEGIN RSA PRIVATE KEY"    backend/
grep -rn "Bearer [A-Za-z0-9]"       backend/ --include="*.py"

# Frontend (TypeScript / Vue) sources
grep -rn "apiKey:\s*['\"]"          frontend/src/ --include="*.ts" --include="*.vue"
grep -rn "token:\s*['\"][A-Za-z0-9]" frontend/src/ --include="*.ts" --include="*.vue"

# Provider config files commonly used in this project
grep -rn "BEGIN" backend/api/services/providers/ | grep -i "private\|key\|certif"
```

Flag every hardcoded credential found as CRITICAL.

## 2. Tenant isolation audit — sie_v2 paths

```bash
# Repository functions without tenant_id in their signature
grep -rn "def .*:" backend/repositories/ | grep -v "tenant_id"

# Filter calls in tenant-scoped services that don't reference tenant_id
grep -rn "\.filter(" backend/api/services/ | grep -v "tenant_id"
```

For details on the project's tenant pattern and anti-patterns, see
`conventions/tenant-isolation.md`.

## 3. Authentication per endpoint — sie_v2 path

```bash
# FastAPI route declarations under the backend's endpoints
grep -rn "@router\.\(get\|post\|put\|patch\|delete\)" backend/api/endpoints/
```

For each route, verify it has `Depends(require_role(...))` (or the
project's specific auth dependency). Flag every public endpoint that is
NOT in the allowed list (login, health, public webhook endpoints with
signature verification).

## 4. PII inventory cross-check

For any new column storing PII (DNI, IBAN, phone, email, postal address):

- Verify the column is documented in `conventions/pii-inventory.md` if
  the project maintains one.
- Verify the column has encryption-at-rest where required.
- Verify NO log statement includes the PII value (grep for column name
  in `logger.*` calls).

## 5. Provider webhook signature verification

For any endpoint that receives an inbound webhook from a provider
(asitur, generali, caser, ima, santander, kutxa, linea_directa):

- Verify the endpoint validates the webhook signature before processing.
- If the provider does not sign webhooks, verify the endpoint is
  IP-allowlisted at the proxy layer (nginx or equivalent).
- Flag MISSING signature/allowlist as CRITICAL.

## 6. Encrypted-at-rest columns

For the project's known encryption-at-rest columns (defined in
`conventions/pii-inventory.md` or by team convention):

- Verify the column uses the project's encrypted column type
  (e.g., `EncryptedString` wrapping SQLAlchemy `String`).
- Verify the column is NOT logged or returned in any non-detail endpoint.
