---
name: detect-patterns
description: "Detect recurring patterns across multiple RETROs. Produces a structural fix report (RECURRING-ISSUES.md) that goes beyond per-cycle patches. Run monthly or after 5+ RETROs."
agent: "`pattern-detector`"
phase: "cross-cycle — manual invocation"
---

# Detect Patterns

Analyze all RETRO documents to find recurring issues that warrant
structural fixes, for the project described in `kuraka.config.yaml`.

## Input

All files in
`${architecture.paths.docs_process_root}/agent-retrospectives/RETRO-*.md`.

## Steps

### 1. Inventory findings

Extract every finding from every RETRO into a normalized table:

| RETRO | Phase | Agent | Severity | Category | Description | Preventable? |
|-------|-------|-------|----------|----------|-------------|--------------|

### 2. Group by (agent, category)

Count occurrences per group.

### 3. Identify patterns

- 3+ occurrences with same agent + category = PATTERN.
- 2 occurrences = WATCH (document but don't fix yet).
- 1 occurrence = NOISE (skip).

### 4. Assess preventability

For each pattern:

- What phase could it have been caught earlier?
- Would adding a check to that earlier agent prevent recurrence?

### 5. Check for already-applied fixes

Before proposing a fix, grep the agent prompts AND the project layer
files for similar rules — maybe the pattern already has a fix that isn't
being followed (indicates a different problem: rule fatigue, missing
enforcement, or unclear rule).

### 6. Decide where to fix

- **Project layer** (preferred) — new lesson-learned + review-check file
  in `.claude/project/`. Affects this project only.
- **Framework prompt** — only if the pattern is truly universal across
  projects. Affects all consumers and requires versioning the framework.

### 7. Write RECURRING-ISSUES.md

At `${architecture.paths.docs_process_root}/patterns/RECURRING-ISSUES.md`.
Use the format in the `pattern-detector` agent definition.

### 8. Trigger patches

After approval, the patterns' proposed fixes become candidate patches
for the next cycle. They are NOT applied automatically — the user
reviews first.

## Rules

1. **Minimum 3 occurrences for a pattern** — lower threshold = noise.
2. **Cite RETRO sources explicitly** — every pattern lists the RETROs.
3. **Prefer earliest-phase fix** — prevention > detection.
4. **Check for rule fatigue** — if a pattern keeps recurring despite a
   rule, the rule might be too vague.
5. **Prefer project layer over framework patches** unless the pattern is
   universal across projects.
6. **Run `verify-output` before returning**.
