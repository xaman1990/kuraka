---
name: run-audit
description: "Run final audit / retrospective after completing a development cycle. Analyzes rework causes, agent failures, and produces improvement recommendations. Used in Phase 7."
agent: "`final-auditor`"
phase: "7 — see `kuraka`"
---

# Run Audit

You are executing the Final Audit skill (Phase 7 of the workflow) for
the project described in `kuraka.config.yaml`.

## Input

The complete development cycle:

- REQ document (Phase 1).
- Story files (Phase 2).
- Architect review (Phase 3) and code / security reviews (Phase 5 / 5.5).
- Implemented code (Phase 4).
- Test results (Phase 6).
- Smoke test results (Phase 6.8) if applicable.
- User corrections / feedback throughout.

## Steps

### 1. Collect evidence

Read:

- `${architecture.paths.docs_process_root}/REQ-*.md` (the REQ for this cycle).
- `${architecture.paths.docs_process_root}/stories/*.md` (all stories).
- Previous retros in
  `${architecture.paths.docs_process_root}/agent-retrospectives/`.
- The conversation history for user corrections.

### 2. Count iteration loops

An iteration loop = user correction → agent response → user correction.

For each loop, document:

- What was corrected.
- Which agent produced the incorrect output.
- At what phase it could have been caught.
- Was it preventable?

### 3. Analyze each agent

For each agent invoked in the cycle:

- **What failed?** Specific failure, not vague.
- **Why?** Root cause (missing check, stale data, wrong assumption).
- **Where to fix:** framework prompt OR project layer
  (prefer project layer for project-specific patterns; framework only
  for truly universal issues).
- **Concrete fix text:** exact text to add, with target file path.

### 4. Identify systemic issues

Patterns that span multiple agents:

- Naming consistency failures.
- Architecture rule violations.
- Scope creep.
- Communication gaps.

### 5. Propose improvements

Concrete, actionable changes:

- New gates / checkpoints to add to the workflow.
- New checks to add to agents (framework or project layer).
- Process changes.

### 6. Write patches

For each agent / file that needs updating, specify:

- Type: framework patch (affects all consumers) OR project-layer addition
  (affects only this project).
- Exact file path.
- Exact text to add (not vague suggestions).

### 7. Produce RETRO document

Create at
`${architecture.paths.docs_process_root}/agent-retrospectives/RETRO-{REQ-name}.md`.

Also copy to `RETRO-LATEST.md` for easy access.

### 8. Ask user

"Should I apply the proposed patches from section 6? Project-layer
changes can be applied immediately; framework changes require
contributing back to the framework repo."

### 9. Sync the cycle back to the vault (MANDATORY — last step)

This is the diagnostic "sync" that closes the cycle. After the RETRO is
written, archive it centrally so it joins the cross-project store in the
Kuraka vault:

```bash
python3 "${KURAKA_VAULT:-/Users/xmn/Documents/Agentes/AgentesTrabajos/kuraka}/kuraka-archive.py" <project-root>
```

Copies `RETRO-{REQ}.md` + `{REQ}-telemetry.json` into
`cycle-archive/<project>/<REQ>/` and appends to the cross-project `INDEX.md`.
Idempotent. Do NOT skip — this is what lets Kuraka learn from failures across
ALL projects (the general improvement cycle). Confirm the command exited 0.
