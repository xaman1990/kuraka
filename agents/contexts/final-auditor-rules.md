# final-auditor — Context Loading

Read these sources in order before producing the retro.

## 1. Project configuration (always)

- `kuraka.config.yaml` at the project root.

Use:

- `architecture.paths.docs_process_root` — to locate REQ, stories,
  retros, telemetry.

## 2. Project specialization layer (when present)

Read each in order:

1. `.claude/project/conventions/*.md` — to understand what conventions
   existed when each agent ran (so failures can be attributed correctly).
2. `.claude/project/lessons-learned/*.md` — files whose frontmatter
   `applies_to` includes `final-auditor` (e.g., past retro patterns to
   watch for).
3. `.claude/project/agents/final-auditor.append.md` — if present, addendum.

## 3. Cycle artifacts (always, current input)

- The REQ document
  (`${architecture.paths.docs_process_root}/REQ-*.md` for this cycle).
- All story files
  (`${architecture.paths.docs_process_root}/stories/`).
- Review reports: `architect-reviewer` (Phase 3), `code-reviewer`
  (Phase 5), `security-reviewer` (Phase 5.5).
- The implemented code (Phase 4 output).
- Test results (Phase 6).
- Any user corrections or feedback during the process.

## 4. Telemetry (always, current input)

- `${architecture.paths.docs_process_root}/agent-telemetry/{REQ-name}-telemetry.json`

If missing, note in the retro and continue.

## 5. Output schema (always, before returning)

- `.claude/agents/contexts/output-schemas.md#final-auditor` — your
  retro's required sections.

## Loading rationale

You look at the whole cycle through the lens of "what could have been
prevented earlier". The project layer tells you what conventions
existed — important because some "failures" are actually compliant with
the team's choices and shouldn't be flagged.

Prefer project-layer additions over framework patches when proposing
fixes. The framework agent prompts should change only for truly universal
patterns.
