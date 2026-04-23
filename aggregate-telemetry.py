#!/usr/bin/env python3
"""
aggregate-telemetry.py — Kuraka telemetry dashboard.

Reads every telemetry JSON under docs/process/agent-telemetry/, aggregates
token/time usage per agent across cycles, flags outliers, and emits a Markdown
dashboard.

Usage:
    python3 aggregate-telemetry.py [project_root]
        (default: $PWD)

Output:
    docs/process/agent-telemetry/DASHBOARD.md

Exit codes:
    0 — dashboard written
    1 — no telemetry found or project layout invalid
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime


# Budgets from rules/17 and kuraka-policies.md (median — "target")
BUDGETS = {
    "po-analyst": (80_000, 200_000),
    "story-refiner": (60_000, 180_000),
    "test-engineer": (60_000, 300_000),  # covers both TEST_PLANNING and TEST_WRITING
    "architect-reviewer": (50_000, 150_000),
    "backend-developer": (100_000, 400_000),
    "frontend-developer": (100_000, 400_000),
    "code-reviewer": (70_000, 200_000),
    "security-reviewer": (60_000, 180_000),
    "e2e-tester": (50_000, 200_000),
    "deployment-verifier": (30_000, 120_000),
    "final-auditor": (40_000, 150_000),
    "migration-reviewer": (20_000, 80_000),
    "pattern-detector": (30_000, 100_000),
}


def find_telemetry_files(project_root: Path) -> list[Path]:
    telemetry_dir = project_root / "docs" / "process" / "agent-telemetry"
    if not telemetry_dir.is_dir():
        return []
    return sorted(telemetry_dir.glob("*-telemetry.json"))


def load_cycle(path: Path) -> dict | None:
    try:
        with path.open() as fp:
            return json.load(fp)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"[warn] cannot parse {path.name}: {exc}", file=sys.stderr)
        return None


def render_dashboard(cycles: list[dict]) -> str:
    if not cycles:
        return "# Kuraka Telemetry Dashboard\n\n(no telemetry data yet)\n"

    lines: list[str] = []
    lines.append("# Kuraka Telemetry Dashboard")
    lines.append("")
    lines.append(f"_Generated: {datetime.now().isoformat(timespec='seconds')}_  ")
    lines.append(f"_Cycles analyzed: {len(cycles)}_")
    lines.append("")

    # --- per-cycle summary ---
    lines.append("## Cycles")
    lines.append("")
    lines.append("| Cycle | Mode | Runs | Total tokens | Total tool uses | Total duration |")
    lines.append("|-------|------|-----:|-------------:|----------------:|---------------:|")

    for cycle in cycles:
        name = cycle.get("req_name", "(unknown)")
        mode = cycle.get("mode", "—")
        runs = cycle.get("runs", [])
        tokens = sum(int(r.get("total_tokens", 0) or 0) for r in runs)
        uses = sum(int(r.get("tool_uses", 0) or 0) for r in runs)
        ms = sum(int(r.get("duration_ms", 0) or 0) for r in runs)
        dur = f"{ms / 1000:.1f}s" if ms < 60_000 else f"{ms / 60_000:.1f}min"
        lines.append(f"| {name} | {mode} | {len(runs)} | {tokens:,} | {uses} | {dur} |")

    # --- per-agent aggregate ---
    per_agent: dict[str, dict] = defaultdict(lambda: {
        "invocations": 0,
        "tokens": 0,
        "tool_uses": 0,
        "duration_ms": 0,
        "over_budget": 0,
    })

    for cycle in cycles:
        for run in cycle.get("runs", []):
            agent = run.get("agent", "(unknown)")
            a = per_agent[agent]
            a["invocations"] += 1
            t = int(run.get("total_tokens", 0) or 0)
            a["tokens"] += t
            a["tool_uses"] += int(run.get("tool_uses", 0) or 0)
            a["duration_ms"] += int(run.get("duration_ms", 0) or 0)

            _target, hard_cap = BUDGETS.get(agent, (None, None))
            if hard_cap and t > hard_cap:
                a["over_budget"] += 1

    lines.append("")
    lines.append("## Per-agent aggregate")
    lines.append("")
    lines.append("| Agent | Invocations | Total tokens | Avg tokens | Tokens/use | Avg duration | Over-budget |")
    lines.append("|-------|------------:|-------------:|-----------:|-----------:|-------------:|------------:|")

    ranking = sorted(per_agent.items(), key=lambda kv: kv[1]["tokens"], reverse=True)
    for agent, stats in ranking:
        n = stats["invocations"]
        avg_t = stats["tokens"] / n if n else 0
        per_use = stats["tokens"] / stats["tool_uses"] if stats["tool_uses"] else 0
        avg_dur_ms = stats["duration_ms"] / n if n else 0
        avg_dur = f"{avg_dur_ms / 1000:.1f}s" if avg_dur_ms < 60_000 else f"{avg_dur_ms / 60_000:.1f}min"
        over = stats["over_budget"]
        flag = f"⚠️ {over}/{n}" if over else f"0/{n}"
        lines.append(
            f"| {agent} | {n} | {stats['tokens']:,} | {avg_t:,.0f} | {per_use:,.0f} | {avg_dur} | {flag} |"
        )

    # --- flags ---
    flagged = [(agent, stats) for agent, stats in per_agent.items() if stats["over_budget"]]
    if flagged:
        lines.append("")
        lines.append("## ⚠️ Agents over budget")
        lines.append("")
        for agent, stats in flagged:
            _target, hard_cap = BUDGETS.get(agent, (None, None))
            lines.append(
                f"- **{agent}** — {stats['over_budget']} of {stats['invocations']} invocations exceeded {hard_cap:,} tokens"
            )

    # --- totals ---
    total_tokens = sum(s["tokens"] for s in per_agent.values())
    total_uses = sum(s["tool_uses"] for s in per_agent.values())
    total_ms = sum(s["duration_ms"] for s in per_agent.values())
    lines.append("")
    lines.append("## Totals")
    lines.append("")
    lines.append(f"- Total tokens: **{total_tokens:,}**")
    lines.append(f"- Total tool uses: **{total_uses}**")
    lines.append(f"- Total duration: **{total_ms / 60_000:.1f} min**")
    lines.append(f"- Avg tokens per cycle: **{(total_tokens / len(cycles)):,.0f}**")
    lines.append("")
    lines.append("---")
    lines.append("_Budget table lives in `.claude/skills/kuraka-policies.md` and `rules/17`._")

    return "\n".join(lines) + "\n"


def main() -> int:
    project_root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    telemetry_files = find_telemetry_files(project_root)

    if not telemetry_files:
        print(f"[error] no telemetry JSON found under {project_root}/docs/process/agent-telemetry/", file=sys.stderr)
        return 1

    cycles = [c for c in (load_cycle(p) for p in telemetry_files) if c is not None]
    if not cycles:
        print("[error] all telemetry files failed to parse", file=sys.stderr)
        return 1

    dashboard = render_dashboard(cycles)
    dashboard_path = project_root / "docs" / "process" / "agent-telemetry" / "DASHBOARD.md"
    dashboard_path.write_text(dashboard, encoding="utf-8")
    print(f"[ok] dashboard written to {dashboard_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
