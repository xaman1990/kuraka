# Security Reviewer - Required Rules

Read these rules before performing the security review:

1. `sie_v2/.claude/CLAUDE.md` - Project conventions (to know auth patterns)
2. `sie_v2/.claude/rules/05-backend-conventions.md` - Secret handling, env vars
3. `sie_v2/.claude/rules/11-security-audit.md` - OWASP Top 10 checklist, GDPR (CRITICAL — this is the primary rules file)

Do NOT read other rules — the security reviewer focuses on security, not architecture or style.

## Output Schema

Use the vocabulary: CRITICAL / HIGH / MEDIUM / LOW / INFO
(this differs from code-reviewer which uses BLOCKER / IMPORTANT / MINOR / SUGGESTION / PRAISE)

## Universal Requirements

Same as other agents: include `## Confidence: HIGH / MEDIUM / LOW` at the end,
and run [[verify-output]] before returning.
