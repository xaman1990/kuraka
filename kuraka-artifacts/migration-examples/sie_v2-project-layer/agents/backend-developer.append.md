## DD-1031 / Provider-Migration Known-Bug Pre-Flight (MANDATORY)

Before writing ANY code for a provider/migration story, scan your planned
implementation against this checklist. Each item is a bug that has been
generated in PREVIOUS cycles and re-generated in DD-1031-rerun. Treat a
match as a defect to fix BEFORE first `make test`, not after.

- [ ] `ErrNotFound` / `ErrProviderError` / `ErrValidation` — single
      message arg only. NO 2-positional calls. Check `core/exceptions.py`
      signature, do not assume.
- [ ] NO `asyncio.get_event_loop()` — use `asyncio.run(...)` (Python 3.12).
- [ ] ALL `import` statements at module top. ZERO imports inside
      functions/methods (incl. `import re`, `import json`).
- [ ] NO hardcoded DB ids (company/provider/tenant). Resolve by
      `provider_type` / business key.
- [ ] NO hardcoded fallbacks for auth URLs, contract names, credentials or
      retry limits. If a config value is missing, RAISE an error that names
      the missing field — never silently use a `_FALLBACK` / `_DEFAULT`
      (this masked the Keycloak realm misconfig in RETRO-2026-06-04).
- [ ] Any `json.dumps` over data that may contain Mock/objects in tests
      must pass `default=str`.
- [ ] Pytest fixtures that must be visible to a TestClient request use
      `TestingSessionLocal` with explicit commit + cleanup (RETRO #10).
- [ ] Fixture payloads match the real Pydantic schema shape (not flat
      dicts) — e.g. `ProviderContextSchema`.
- [ ] `id_unico` / external-ref formats are replicated from the v1
      oracle EXACTLY (prefix, hash algo, segment order). Confirm against
      the CSV/Postman oracle, never invent.
- [ ] File-size rule: anticipate growth. Split BEFORE crossing 500 LOC.

If any box would be checked, fix it in the first write — do not rely on
the gate to catch it.
