# Review checks — architect-reviewer (sie_v2)

Project-specific checks the `architect-reviewer` runs in addition to its
generic checklists. Loaded automatically when the agent runs in this
project.

## 1. Pattern parity with existing project conventions

**When it applies**: any story that introduces a NEW pattern (a new
migration kind, a new seed mechanism, a new factory registration, a new
directory layout).

**The check**: before approving the story, verify the proposed pattern
matches at least one existing example in the codebase. Patterns without
precedent are BLOCKER.

### 1.1 Migrations with data

If the story proposes a migration that inserts data:

- Search `backend/migrations/versions/` for prior data-inserting
  migrations.
- If NONE exist (the project uses SQL seeds in
  `database/seed_data/*.sql`), flag as BLOCKER and propose the SQL seed
  alternative.

### 1.2 Seed files

If other providers/modules have seed files in
`database/seed_data/{NN}_{name}.sql` AND the story uses Alembic to
insert data instead, flag as BLOCKER. Convention parity wins over
Alembic flexibility.

### 1.3 Directory structure

If the story proposes a new directory or module structure:

- Verify it mirrors at least one existing provider/module (asitur,
  generali, caser, ima, santander, kutxa, linea_directa).
- If it introduces new top-level directories without precedent, demand
  justification in the story description.

### 1.4 Executable command for the pattern

For each new pattern, the story must propose the exact command that
applies it in deploys (e.g., `psql -f <file>` or `alembic upgrade head`).
If no clear command exists, the pattern is not integrated — flag BLOCKER.

### BLOCKER text

When flagging a pattern without precedent, use this text:

> 🔴 **BLOCKER**: Patrón sin precedente en el proyecto — verificar con el
> orquestador antes de FASE 5.

**Why**: see `lessons-learned/LL-DD-896-FM-02-alembic-vs-seeds.md`.

## 2. Cross-provider naming and ID conventions

For any story touching provider integrations, verify the proposal aligns
with `conventions/cross-provider-conventions.md` (mailbox naming,
`scheduling_tasks` dual-dispatch, contract resolution rules). Flag
deviations as BLOCKER.
