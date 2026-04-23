---
name: detect-patterns
description: "Detect recurring patterns across multiple RETROs. Produces a structural fix report (RECURRING-ISSUES.md) that goes beyond per-REQ patches. Run monthly or after 5+ RETROs."
agent: "[[pattern-detector]]"
phase: "cross-cycle — manual invocation"
---

# Detect Patterns

Analyze all RETRO documents to find recurring issues that warrant structural fixes.

## Input

All files in `sie_v2/docs/process/agent-retrospectives/RETRO-*.md`.

## Steps

### 1. Inventory findings

Extract every finding from every RETRO into a normalized table:

| RETRO | Phase | Agent | Severity | Category | Description | Preventable? |
|-------|-------|-------|----------|----------|-------------|--------------|

### 2. Group by (agent, category)

Count occurrences per group.

### 3. Identify patterns

- 3+ occurrences with same agent + category = PATTERN
- 2 occurrences = WATCH (document but don't fix yet)
- 1 occurrence = NOISE (skip)

### 4. Assess preventability

For each pattern:
- What phase could it have been caught earlier?
- Would adding a check to that earlier agent prevent recurrence?

### 5. Check for already-applied fixes

Before proposing a fix, grep the agent files for similar rules — maybe the
pattern already has a fix that isn't being followed (indicates a different
kind of problem: rule fatigue or missing enforcement).

### 6. Write RECURRING-ISSUES.md

Use the format in the [[pattern-detector]] agent definition.

### 7. Trigger patches

After approval, the patterns' proposed fixes become candidate patches for
the next RETRO cycle. They are NOT applied automatically — the user reviews
first.

## Rules

1. **Minimum 3 occurrences for a pattern** — lower threshold = noise
2. **Cite RETRO sources explicitly** — every pattern lists the RETROs
3. **Prefer earliest-phase fix** — prevention > detection
4. **Check for rule fatigue** — if a pattern keeps recurring despite a rule, the rule might be too vague
5. **Run [[verify-output]] before returning**
