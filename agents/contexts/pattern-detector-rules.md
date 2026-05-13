# pattern-detector — Context Loading

Read these sources in order before detecting recurring patterns.

## 1. Project configuration (always)

- `kuraka.config.yaml` at the project root.

Use:

- `architecture.paths.docs_process_root` — to locate retros and write the
  patterns report.

## 2. Project specialization layer (when present)

Read each in order:

1. `.claude/project/lessons-learned/*.md` — files whose frontmatter
   `applies_to` includes `pattern-detector`. These may include
   meta-lessons from prior pattern analyses (e.g., "patterns we've
   already fixed structurally").
2. `.claude/project/agents/pattern-detector.append.md` — if present,
   addendum.

## 3. RETRO corpus (always, current input)

- All `RETRO-*.md` files in
  `${architecture.paths.docs_process_root}/agent-retrospectives/`.

If there are fewer than 3 retros in the corpus, return a notice that
pattern detection requires more data and wait.

## 4. Output schema (always, before returning)

- `.claude/agents/contexts/output-schemas.md#pattern-detector` (if
  defined; the agent's prompt has a default template otherwise).

## Loading rationale

You operate across cycles, not within one. The retros are your input;
the project layer tells you what's already been fixed (so you don't
re-propose the same fix). Your proposals favor the project layer over
the framework prompts because most patterns are project-specific.
