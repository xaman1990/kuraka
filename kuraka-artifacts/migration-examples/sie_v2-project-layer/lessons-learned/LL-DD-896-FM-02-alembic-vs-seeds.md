---
id: LL-DD-896-FM-02
title: Architect approved an Alembic data migration that violated the project's SQL-seeds convention
date: 2026-04-23
incident_ref: docs/process/agent-retrospectives/RETRO-DD-896-linea-directa.md
applies_to: [architect-reviewer, migration-reviewer]
severity: high
tags: [migration, alembic, seeds, dd-896, finding-mode-02]
---

## Context

During DD-896 (Linea Directa migration), the `architect-reviewer` and
`migration-reviewer` both approved an Alembic migration that inserted
provider data. The migration was technically correct (it parsed and ran),
but violated the project's convention: provider data goes in
`database/seed_data/{NN}_{provider}.sql`, not in Alembic.

The mismatch surfaced in Phase 5/6 as foreign key violations at runtime.
Recovery required 3 iterations of `make test` (~120K tokens) and an
architectural rewrite of the migration to a no-op + a new canonical SQL
seed file.

## Pattern to detect

A story or implementation proposes:

- An Alembic migration that contains an `op.bulk_insert(...)` or
  `op.execute("INSERT INTO ...")` for domain/provider data.

AND

- Other providers/modules in the project have seed files in
  `database/seed_data/{NN}_{name}.sql`.

## Required action by the reviewer

Before approving the story / migration:

1. Search `database/seed_data/` for existing seed files for the same
   category of data.
2. If existing seeds are present, REJECT the Alembic data-insert
   migration with the BLOCKER text:

   > Patrón sin precedente — convención del proyecto es SQL seeds en
   > `database/seed_data/`. Re-cut la story para usar la convención.

3. Propose the SQL seed alternative: filename, content shape, and the
   `psql -f` command that applies it in deploys.

## Why this exists

Convention parity matters more than tool flexibility. An Alembic data
migration "works" technically but produces inconsistency across providers
and breaks the team's mental model of "where does provider data live".
The downstream cost of inconsistency (debug confusion, FK violations,
rewrite) is much higher than the cost of catching it in Phase 3.

## Related

- `review-checks/architect-reviewer.md` checks #1.1 and #1.2 — operational
  version of this lesson.
- `lessons-learned/LL-DD-896-FM-01-provider-file-coverage.md` — the other
  finding mode from the same cycle.
