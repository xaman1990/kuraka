---
name: verify-deployment
description: "Verify deployment readiness — Docker builds, nginx config, env vars documented, CI pipeline healthy. Final gate before merge. Used in Phase 6.7."
agent: "[[deployment-verifier]]"
phase: "6.7 — see `kuraka`"
---

# Verify Deployment

Final deployment readiness gate before merge to main.

## Input

- `docker-compose*.yml`
- `Dockerfile` (backend, frontend)
- `nginx.conf`
- `.env.example` (backend + root)
- `.github/workflows/*.yml`
- Migration files

## Steps

### 1. Validate Docker

```bash
cd sie_v2 && docker compose config > /dev/null
```

### 2. Check env vars

- Grep code for `os.environ[...]` and `settings.X` — extract all env var names
- Compare against `.env.example` entries
- Flag missing

### 3. Check nginx (if changed)

```bash
nginx -t -c nginx.conf
```

### 4. Check CI pipeline (if changed)

- Read `.github/workflows/*.yml`
- Verify ruff and tests are in pipeline

### 5. Build smoke test (if Dockerfiles changed)

```bash
docker compose build
docker compose up -d
sleep 10
curl -f http://localhost:8000/api/health
```

### 6. Produce report

Use the format from `deployment-verifier.md`.

## Rules

1. **BLOCKER on missing env vars**
2. **BLOCKER on invalid docker-compose**
3. **Smoke test is mandatory if Docker changed**
4. **Run [[verify-output]] before returning**
