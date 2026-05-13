---
name: compact-context
description: "Compress a verbose agent output into a summary before passing to the next agent. Prevents context bloat when one agent reads many files. Invoked automatically when previous output > 5000 tokens."
agent: "orchestrator (automatic)"
phase: "between phases — see `kuraka`"
---

# Compact Context

Summarize an agent's output before forwarding to the next agent.

## When to Invoke

Automatically, when:
- Previous agent output is > 5000 tokens
- The next agent doesn't need the full detail, just the relevant facts
- An Explore agent read 10+ files and the raw output is noisy

Do NOT compact if:
- The next agent specifically needs the full artifact (e.g., code review reading the full REQ)
- The output is already structured (tables, schemas)
- Compaction would lose data needed downstream

## Input

- The full output of the previous agent
- The next agent's role (to know what matters)

## Steps

### 1. Identify the core artifacts

What did the previous agent PRODUCE (vs just investigated)? Keep the produced artifacts.

Example:
- po-analyst output: keep REQ + list of stories; summarize "exploration notes"
- architect-reviewer output: keep findings table and verdict; drop the rule-reading chatter
- test-engineer output: keep test plan table; drop fixture discovery logs

### 2. Extract decisions and conclusions

Keep:
- Verdicts (APPROVED / CHANGES_REQUIRED / etc.)
- Findings (severity + description + fix)
- File paths (absolute)
- Confidence level

Drop:
- Step-by-step reasoning
- File-by-file exploration narration
- Quoted tool outputs (keep only relevant excerpts)

### 3. Preserve contracts

The next agent expects specific fields in the input. Preserve:
- File paths of produced artifacts
- Schema references (e.g., "uses tenant_id column")
- Critical warnings from previous agent

### 4. Produce compacted output

Format:

```markdown
## Compacted Context from {previous agent}

**Verdict:** {verdict}
**Artifacts produced:**
- {file_path}: {one-line description}

**Key findings/decisions:**
1. {finding}
2. {decision}

**Warnings for downstream:**
- {warning}

**Original length:** N tokens → Compacted: M tokens (X% reduction)
```

## Rules

1. **Never lose file paths** — downstream agents need them
2. **Never lose verdicts or severities** — they drive next-phase logic
3. **Preserve confidence level** — if original was LOW confidence, compaction is LOW confidence
4. **Mark what was dropped** — at the end, list "Dropped: exploration narration, rule-reading logs"
5. **If compaction reduces content by < 30%, skip it** — not worth the risk
