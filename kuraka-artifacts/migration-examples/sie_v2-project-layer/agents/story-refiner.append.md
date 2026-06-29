## Provider-migration stories: attach a RETRO-rider AC

For every provider/migration story, append one acceptance criterion:

  AC-RETRO: Implementation passes the backend-developer DD-1031
  known-bug pre-flight checklist (exceptions arity, no get_event_loop,
  no in-function imports, no hardcoded ids, no config fallbacks,
  oracle-exact id_unico, RETRO #10 fixture visibility). Verified at
  first `make test`.

This makes the known-bug guard a story contract, not a hidden rule.

## Seed / migration verification (provider migrations)

For stories that create or modify `database/seed_data/*.sql`, attach
these acceptance criteria — they are project contracts, not hints:

- [ ] Verify in the v1 MySQL data how many tenant instances use this
      provider, and whether credentials are live or UAT placeholders.
      Seed multiple tenants ONLY if v1 data proves both use it.
- [ ] Seeds MUST NOT ship UAT/test values. Either extract the real value
      from v1 (user supplies via CSV) or leave it NULL/placeholder and
      document that ops populates it at deploy time.
- [ ] Contract names: verify against `contracts.contract_code` in the
      real v1 DB before seeding — never seed a placeholder like `MmPend`.
- [ ] Natural-key upserts: if a resolution rule is renamed, add a scoped
      self-heal `DELETE` of the orphaned old row BEFORE the new INSERT.
