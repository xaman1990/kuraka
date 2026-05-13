---
name: run-audit
description: "Run final audit/retrospective after completing a development cycle. Analyzes rework causes, agent failures, and produces improvement recommendations. Used in Phase 7."
agent: "[[final-auditor]]"
phase: "7 — see `kuraka`"
---

# Run Audit

You are executing the Final Audit skill (Phase 7 of the workflow).

## Input

The complete development cycle:
- REQ document (Phase 1)
- Story files (Phase 2)
- Architect review (Phase 3) and Code review (Phase 5)
- Implemented code (Phase 4)
- Test results (Phase 6)
- User corrections/feedback throughout

## Steps

### 1. Collect Evidence

Read:
- `sie_v2/docs/process/REQ-*.md` (the REQ for this cycle)
- `sie_v2/docs/process/stories/*.md` (all stories)
- Previous retros in `sie_v2/docs/process/agent-retrospectives/`
- The conversation history for user corrections

### 2. Count Iteration Loops

An iteration loop = user correction -> agent response -> user correction.

For each loop, document:
- What was corrected
- Which agent produced the incorrect output
- At what phase it could have been caught
- Was it preventable?

### 3. Analyze Each Agent

For each agent (po-analyst, story-refiner, architect-reviewer, code-reviewer, backend-developer, test-engineer):

- **What failed?** Specific failure, not vague
- **Why?** Root cause (missing check, stale data, wrong assumption)
- **Instruction update:** Concrete text to add to the agent's prompt file

### 4. Identify Systemic Issues

Patterns that span multiple agents:
- Naming consistency failures
- Architecture rule violations
- Scope creep
- Communication gaps

### 5. Propose Improvements

Concrete, actionable changes:
- New gates/checkpoints to add to workflow
- New checks to add to agents
- Process changes

### 6. Write Agent Prompt Patches

For each agent that needs updating, specify:
- Exact file path
- Exact text to add (not vague suggestions)

### 7. Produce RETRO Document

Create at `sie_v2/docs/process/agent-retrospectives/RETRO-{REQ-name}.md`

Also copy to `RETRO-LATEST.md` for easy access.

### 8. Ask User

"Should I apply the agent prompt patches from section 6? This updates the agents for the next development cycle."
