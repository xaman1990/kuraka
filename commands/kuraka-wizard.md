---
description: "Guided Kuraka onboarding wizard. Detects the project's state (mounted? config? code? greenfield vs brownfield) and runs or routes the correct next startup step — mount/update, inspect, amauta (brownfield) or inti (greenfield), up to ready-for-/kuraka. Re-runnable: each run advances one stage, stopping cleanly at restart boundaries."
---

# Task: Kuraka onboarding wizard

Walk the project from "nothing" to "ready for a Kuraka cycle", doing the
scriptable steps and routing to the right agent. Re-run it after each
restart; it always reports state and advances the next pending stage.

**Portability**: vault from `$KURAKA_VAULT` (fallback default); project
root auto-detected via `.claude/`.

## Step 1 — Gather state

Run this block and read its output. It collects everything the wizard
decides on:

```bash
VAULT="${KURAKA_VAULT:-/Users/xmn/Documents/Agentes/AgentesTrabajos/kuraka}"
DIR="$PWD"; while [ "$DIR" != "/" ] && [ ! -d "$DIR/.claude" ]; do DIR="$(dirname "$DIR")"; done
ROOT="${DIR}"; [ -d "$ROOT/.claude" ] || ROOT="$PWD"

echo "VAULT=$VAULT  (exists: $([ -d "$VAULT" ] && echo yes || echo NO))"
echo "PROJECT_ROOT=$ROOT"
echo "mounted_claude=$([ -d "$ROOT/.claude/agents" ] && echo yes || echo no)"
echo "agents_count=$(ls "$ROOT/.claude/agents/"*.md 2>/dev/null | wc -l | tr -d ' ')"
echo "has_config=$([ -f "$ROOT/kuraka.config.yaml" ] && echo yes || echo no)"
echo "has_project_layer=$([ -d "$ROOT/.claude/project" ] && echo yes || echo no)"
echo "has_inspect=$([ -f "$ROOT/inspect-report.json" ] && echo yes || echo no)"
# crude greenfield test: count source-ish files OUTSIDE .claude/, docs/, .git/
echo "source_files=$(find "$ROOT" -type f \
   \( -name '*.ts' -o -name '*.js' -o -name '*.py' -o -name '*.go' -o -name '*.rb' \
      -o -name '*.java' -o -name '*.php' -o -name '*.rs' -o -name '*.vue' \) \
   -not -path '*/.claude/*' -not -path '*/.git/*' -not -path '*/node_modules/*' \
   -not -path '*/docs/*' 2>/dev/null | head -50 | wc -l | tr -d ' ')"
```

## Step 2 — Decide and act

Apply the FIRST matching rule, do its action, then report status and stop
(or continue only where noted). Always end by telling the user the single
next thing to do.

| # | Condition | Action |
|---|---|---|
| A | `VAULT exists = NO` | Stop. Tell the user to `export KURAKA_VAULT="/ruta/a/kuraka"` (and add to `~/.zshrc`), then re-run `/kuraka-wizard`. |
| B | `mounted_claude = no` OR `agents_count = 0` | Run `bash "$VAULT/mount-kuraka.sh" "$ROOT"`. Then STOP: tell the user to restart Claude Code (`/exit` + new session) and run `/kuraka-wizard` again — agents register only at session start. |
| C | `has_config = yes` AND `has_project_layer = yes` | Project is **ready**. Run `bash "$VAULT/validate-kuraka.sh" "$ROOT"` and report PASS/FAIL. Then offer the two entry points: `/kuraka` for a defined requirement, or Discovery ("tengo una idea, no un requerimiento") for a fuzzy new feature. Done. |
| D | `has_config = no` AND `source_files` is `0` (greenfield) | This is a **greenfield** project. Tell the user to invoke `inti` ("quiero empezar un proyecto nuevo: …") to run discovery, then `arki` for the architecture + config. (Optionally run Discovery/Tinkuy first if the idea is fuzzy.) Stop. |
| E | `has_config = no` AND `source_files` > 0 (brownfield) | This is a **brownfield** project. Ensure the inspect report: if `has_inspect = no`, run `python3 "$VAULT/kuraka-inspect.py" "$ROOT" > "$ROOT/inspect-report.json"`. Then invoke the `amauta` subagent to generate `kuraka.config.yaml` + `.claude/project/` from the real code (golden rule: never invent — mark `<TODO>`). If `amauta` isn't a known subagent, tell the user to restart and run `/kuraka-wizard` (or `/amauta`) again. |

## Step 3 — Always close with a clear next step

End every run with one line: exactly what the user should do next
(restart, resolve TODOs in `kuraka.config.yaml`, run `/kuraka`, etc.).
Never leave the user guessing which stage they're in.

## Notes

- The wizard is the in-session equivalent of `kuraka-init.py` (the
  external one-shot initializer). Use the wizard when Kuraka is already
  partly present in the project; use `kuraka-init.py` for a cold start
  from a fresh checkout.
- Greenfield detection (`source_files`) is heuristic. If the user says the
  project has code but it shows 0 (unusual languages, generated dirs),
  treat it as brownfield (rule E).
- This wizard does not write business code. It only mounts, inspects,
  generates config/project layer (via amauta), and routes.
