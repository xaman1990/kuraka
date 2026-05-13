# Review checks — migration-reviewer (sie_v2)

Project-specific checks the `migration-reviewer` runs in addition to its
generic Alembic safety checklist. Loaded automatically when the agent
runs in this project.

## 1. Mandatory pre-check — Alembic vs SQL seeds

**When it applies**: every migration review, before any other check.

**The check**:

```bash
# Are there other migrations that insert similar data?
grep -l "op.execute\|op.bulk_insert" backend/migrations/versions/*.py

# Are there SQL seeds that insert this same data?
ls backend/database/seed_data/
```

If the project uses **SQL seeds** (`database/seed_data/*.sql` applied
externally) AND the reviewed migration inserts data via Alembic, flag as
**🔴 BLOCKER** with this title:

> Mismatch convención: data en alembic vs SQL seed

Document which existing providers use SQL seeds and demand parity. The
fix is usually to convert the Alembic data-insert migration to a no-op
and add a new canonical SQL seed file in `database/seed_data/`.

**Why**: see `lessons-learned/LL-DD-896-FM-02-alembic-vs-seeds.md`.

## 2. Migration filename convention

Migration files must follow the project's naming pattern:

```
backend/migrations/versions/{YYYYMMDD}_{NNNN}_{slug}.py
```

Where:
- `{YYYYMMDD}` is the creation date.
- `{NNNN}` is a 4-digit sequence number within the day.
- `{slug}` is a kebab-case short description.

Filenames that don't match → MEDIUM finding (cosmetic but breaks the
team's ability to find migrations chronologically).

## 3. Migration order against the frozen schema

Every column, FK, index, and enum mentioned in the migration must
appear in `docs/process/schemas/SCHEMA-FROZEN-{ticket}.md`. Drift
between the migration and the frozen schema → BLOCKER (means the
schema was not actually frozen).
