---
name: security-audit
description: "Dedicated security audit of implemented code. Runs OWASP Top 10 checks, secret scan, tenant isolation audit, and authentication audit. Blocks deployment on CRITICAL findings. Used in Phase 5.5."
agent: "[[security-reviewer]]"
phase: "5.5 — see `kuraka`"
---

# Security Audit

Perform a focused security review of the changes in this cycle.

## Input

- Implemented code files (modified in Phase 4)
- REQ document (to understand the security context)
- Environment/config files (`.env.example`, docker-compose)

## Process

### 1. OWASP Top 10 scan

Go through each OWASP category and search for patterns in the changed code.
Use grep to find violations quickly.

### 2. Secret scan

Execute secret-finding regexes across the entire backend:

```bash
grep -rn "password\s*=\s*['\"]" sie_v2/backend/ --include="*.py"
grep -rn "api_key\s*=\s*['\"]" sie_v2/backend/ --include="*.py"
grep -rn "secret\s*=\s*['\"]" sie_v2/backend/ --include="*.py"
```

If any match is not from a test fixture, mark as CRITICAL.

### 3. Tenant isolation audit

For every modified repository:
- Check function signature includes tenant_id
- Check every query filters by tenant_id
- Flag any function that returns cross-tenant data

### 4. Auth audit

For every new/modified endpoint:
- Check it has `Depends(require_role(...))` or equivalent
- Verify role matches REQ requirements

### 5. Produce report

Use the output format from `.claude/agents/security-reviewer.md`.

## Rules

1. **CRITICAL blocks merge** - no overrides
2. **Be explicit about fixes** - show corrected code
3. **Never disable security as a fix**
4. **Run [[verify-output]] before returning**
