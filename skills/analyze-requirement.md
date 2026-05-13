---
name: analyze-requirement
description: "Analyze a Jira ticket or raw requirement and produce a structured REQ document. Used by po-analyst agent in Phase 1 of the workflow."
agent: "[[po-analyst]]"
phase: "1 — see `kuraka`"
---

# Analyze Requirement

You are executing the PO Analysis skill for the SIE v2 development workflow.

## Input

The user provides either:
- A Jira ticket key (e.g., DD-755) with description
- A raw requirement text

## Steps

### 1. Gather Context

Read these files to understand the project:
- `sie_v2/.claude/CLAUDE.md`
- `sie_v2/.claude/rules/04-backend-architecture.md`
- `sie_v2/.claude/rules/06-project-structure.md`

### 2. Analyze the Requirement

Identify:
- **What** needs to be built (features, endpoints, UI)
- **Where** it fits in the architecture (which layers, modules)
- **What tables** are needed (compare against Jira ticket)
- **What endpoints** are needed
- **What services/repositories** are affected
- **What risks** exist

### 3. Produce REQ Document

Create the file at `sie_v2/docs/process/REQ-{YYYYMMDD}-{ticket}-{slug}.md` using the template from the po-analyst agent definition.

### 4. Table Inventory Validation

For EVERY table you propose:
- Is it mentioned in the Jira ticket? Mark "Yes"
- If NOT in Jira, provide explicit justification or remove it
- Include the action: CREATE, ALTER, or NONE (reference only)

### 5. Scope Boundary

Be explicit about what is IN scope and OUT of scope. Common mistakes:
- Adding auth/user tables when the ticket doesn't mention them
- Adding catalog/lookup tables when enums suffice
- Proposing tables from other tickets

### 6. Present to User

Show the REQ and ask for approval before proceeding to Phase 2.
