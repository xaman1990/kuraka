---
id: LL-004
title: Test plans must respect the story's Out of Scope section, not silently add cases
date: 2026-XX-XX
incident_ref: docs/process/agent-retrospectives/ (test-engineer retro)
applies_to: [test-engineer]
severity: medium
tags: [test-planning, scope, contract]
---

## Context

The `test-engineer` generated test plans that included test cases for
items the story had explicitly placed under "Out of Scope". The added
test cases drove the implementation to cover those cases too,
expanding the story's actual scope without going through the PO/architect
gates. The result: stories with hidden creep, and rework when the
expanded code didn't pass review.

## Pattern to detect

A story has a clearly marked "Out of Scope" section (usually at the top
or under the Scope heading). The test plan being generated includes one
or more test cases for items listed there.

## Required action by the test-engineer

Before generating ANY test case for a story:

1. Read the story's "Out of Scope" section in full.
2. List the excluded items explicitly in the test plan under a heading
   like "Excluded Categories" so the developer can see what's deliberately
   not covered.
3. Do NOT include test cases for excluded items.

## When you disagree with an exclusion

If you believe an exclusion is incorrect (e.g., the risk profile
warrants testing despite the story's call):

1. Create a "Test Plan vs Story Scope Conflict" finding.
2. STOP test plan generation.
3. Wait for resolution (PO or architect-reviewer revisits the story's
   Out of Scope).
4. Do NOT silently include the excluded test cases as a unilateral
   override.

## Why this exists

The story's scope is a contract among PO, architect, and developer.
Adding test cases for excluded behavior unilaterally turns the
test-engineer into a silent scope decider, bypasses the gate, and
produces work that wasn't agreed to. Disagreements are valid — flag them
through the proper channel.

## Related

- The `test-engineer` agent prompt has the "MANDATORY — Out of Scope
  Check" section that operationalizes this lesson.
