## Oracle-first assertions (provider migrations)

Before asserting on any value, derive the expected value from the
authoritative oracle in this priority order: (1) v1 production code,
(2) the supplied CSV, (3) the Postman collection, (4) the PDF spec.
NEVER assert against an assumed contract. Specifically:

- Assert error identity on `.code`, not `str(exc)` (the latter is
  human-readable, the former is programmatic).
- `id_unico` / external refs: compare against the CSV-extracted value,
  not a pattern you invented.
- Idempotency tests: confirm the dedupe key against v1 behavior first
  (e.g. if v1 used the message-id, v2 must too).
- Status codes and field presence: verify against the v1 implementation
  before writing the assertion.

If the oracle is not available, flag it as a blocker in the test — do
not guess.
