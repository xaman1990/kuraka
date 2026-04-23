# Agent Context Snapshots

Condensed rule references per agent type. Each agent reads ONLY its relevant
rules instead of all 16 files — this reduces token consumption by ~60-70%
per agent invocation.

## Rule-to-Agent Mapping

| Rule | PO | Refiner | Architect | Code Rev | Backend | Frontend | Security | Test Eng | Auditor | Pattern |
|------|:--:|:-------:|:---------:|:--------:|:-------:|:--------:|:--------:|:--------:|:-------:|:-------:|
| 01-solid-principles | | | | x | x | | | | | |
| 02-clean-code | | | | x | x | x | | | | |
| 03-file-organization | | | x | x | x | x | | | | |
| 04-backend-architecture | x | x | x | x | x | | | | | |
| 05-backend-conventions | | x | x | x | x | | x | | | |
| 06-project-structure | x | x | x | x | x | x | | | | |
| 07-providers | | | | * | * | | | | | |
| 08-testing | | | x | x | x | | | x | | |
| 09-frontend-standards | | | | * | | x | | | | |
| 10-code-review | | | | x | | | | | | |
| 11-security-audit | | | | | | | x | | | |
| 12-insurance-api-connector | | | | * | * | | | | | |
| 13-db-migrations | | x | x | | x | | | | | |
| 14-incident-integration | | | | | | | | | | |
| 15-data-mapping-specs | | | | | | | | | | |
| 16-agent-backup | | | | | | | | | x | |

`*` = only when the change touches that domain (providers, frontend, insurance APIs)

## Usage

Agents reference their context file in the "Context" section:
```markdown
## Context
Read: `.claude/agents/contexts/{agent}-rules.md` for the list of rules to read.
```

Last updated: 2026-04-17
