---
name: generate-e2e-tests
description: "Generate Playwright E2E tests for critical user flows. Focus on golden path, not exhaustive coverage. Used in Phase 6.5."
agent: "[[e2e-tester]]"
phase: "6.5 — see [[kuraka]]"
---

# Generate E2E Tests

Write Playwright tests for the user flows affected by this REQ.

## Input

- REQ document (to identify user-facing flows)
- Frontend changes (to know what UI to test)
- Existing E2E tests (to reuse patterns)

## Steps

1. **Identify critical flows** from the REQ:
   - Did auth change? → test auth flow
   - Did a tool change? → test its happy path
   - Did outbound change? → test via Guai webhook mock

2. **Check existing tests** — don't duplicate, update instead

3. **Write Page Objects** for any new pages/components

4. **Write test specs** — one file per flow

5. **Run in headless mode** — `npx playwright test`

6. **Verify they pass in CI** — not just locally

## Rules

1. **Max 2 minutes per test**
2. **No hardcoded waits** — always `waitFor*`
3. **Robust selectors** — `getByRole`, `getByLabel`, `getByTestId`
4. **Golden path only** — unit tests handle edge cases
5. **Use fixtures for repeated setup** (auth, seed data)
6. **Clean up test data** in `afterEach`
7. **Run [[verify-output]] before returning**
