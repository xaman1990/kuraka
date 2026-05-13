# Review checks — po-analyst (sie_v2)

Project-specific checks the `po-analyst` agent runs in addition to its
generic framework instructions. Loaded automatically when the agent runs
in this project.

## 1. Provider directory full file coverage

**When it applies**: any requirement involving a provider integration
(insurance company, email broker, external API). Examples of providers:
asitur, generali, caser, ima, santander, kutxa, linea_directa.

**The check**:

When analyzing a provider, the `po-analyst` must enumerate **every** file
in the provider's directory tree, not just the obvious ones from the
ticket description. Files easily missed:

- `utils/*.js` or `utils/*.py` called only from edge cases
- `helpers/` or `lib/` files that wrap third-party clients
- Test fixtures that document expected payloads
- Migration / seeding files in `database/seed_data/` related to the provider
- Config files referenced from `.env` keys

**Execution**:

```bash
# Replace {provider} with the actual provider name (lowercase, no spaces)
find backend/src/providers/{provider}/ -type f \
  | sort

# Cross-check against what the ticket lists; flag every file in the directory
# that the ticket does not mention.
```

**What to do with the findings**: include every file in the REQ's
"Affected Services & Repositories" section, with a brief explanation of
whether the file is part of scope (modified), out of scope (not touched
but co-located), or boundary (needs review even if not modified — e.g.,
a shared utility called from the touched files).

**Why**: see `lessons-learned/LL-DD-896-FM-01-provider-file-coverage.md`.

## 2. Mailbox/contract convention validation

**When it applies**: any requirement that adds or modifies email-based
provider integration.

**The check**: verify that proposed mailbox names follow the convention
`<Provider> cuidacasa` and `<Provider> guainsurtech` (the two operational
tenant mailboxes per provider). Verify that proposed `scheduling_tasks`
entries use `mailbox_id` for email tasks and `company_id` for API tasks
— never both, never neither.

**Reference**: `conventions/cross-provider-conventions.md` (when created
during the Fase 3 refactor of agents that emit cross-provider checks).

## 3. Tenant strategy explicit per table

**When it applies**: any requirement that adds, alters, or relates to a
database table.

**The check**: every table mentioned in the REQ's "Table Inventory"
section must explicitly state whether it is tenant-scoped (has
`tenant_id` column + FK) or globally scoped (justified exception).
Tables without an explicit decision get flagged in the REQ as a
"BLOCKER for architect review" pending decision.

**Reference**: `conventions/tenant-isolation.md`.
