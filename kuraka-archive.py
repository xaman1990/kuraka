#!/usr/bin/env python3
"""kuraka-archive.py — collect a consumer project's cycle diagnostics into the vault.

After a Kuraka cycle's Final Audit (Phase 7), the consumer project holds, per cycle:
    <project>/docs/process/agent-retrospectives/RETRO-<REQ>.md   (final-auditor)
    <project>/docs/process/agent-telemetry/<REQ>-telemetry.json  (per-cycle telemetry)

This pulls each not-yet-archived cycle BACK into the vault so every cycle run by every
Kuraka-using project is kept centrally for cross-project analysis:

    <vault>/cycle-archive/<project-slug>/<REQ>/RETRO-<REQ>.md
                                              /<REQ>-telemetry.json
                                              /meta.yaml
    <vault>/cycle-archive/INDEX.md   (rolling cross-project index)

The archive is the data source for cross-project pattern-detection → a cross-project
RECURRING-ISSUES → the RETRO Triage board: i.e. "where did Kuraka fail, across ALL
projects, so we can improve the agents and the bases."

Run it:
  - manually:           python3 kuraka-archive.py /path/to/project
  - after Phase 7:      the orchestrator calls it once the RETRO is written + synced
  - control-plane:      the "Sync" action wraps it

Copies (never moves) — the project keeps its own copies. Idempotent: cycles already
archived are skipped (use --force to re-copy). No external dependencies.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
from datetime import date
from pathlib import Path

DEFAULT_VAULT = "/Users/xmn/Documents/Agentes/AgentesTrabajos/kuraka"
ARCHIVE_DIRNAME = "cycle-archive"


def err(msg: str) -> None:
    print(msg, file=sys.stderr)


def slugify(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", name).strip("-").lower()
    return s or "project"


def project_slug(project: Path, override: str | None) -> str:
    """Prefer kuraka.config.yaml project.name; fall back to the folder name."""
    if override:
        return slugify(override)
    cfg = project / "kuraka.config.yaml"
    if cfg.exists():
        in_project = False
        for line in cfg.read_text(encoding="utf-8", errors="ignore").splitlines():
            if re.match(r"^project:\s*$", line):
                in_project = True
                continue
            if in_project:
                m = re.match(r"^\s+name:\s*(.+?)\s*$", line)
                if m:
                    return slugify(m.group(1).strip().strip('"\''))
                if re.match(r"^\S", line):  # left the project: block
                    break
    return slugify(project.name)


def find_verdict(retro_text: str) -> str:
    """Best-effort: pull a one-line verdict/confidence from the RETRO."""
    for pat in (r"##\s*Confidence:\s*(.+)", r"Confidence:\s*(\w+)", r"Verdict:\s*(.+)"):
        m = re.search(pat, retro_text)
        if m:
            return m.group(1).strip()[:60]
    return ""


def archive_cycle(retro: Path, telem_dir: Path, dest_root: Path, slug: str,
                  today: str, force: bool) -> dict | None:
    req = retro.stem[len("RETRO-"):] if retro.stem.startswith("RETRO-") else retro.stem
    dest = dest_root / slug / req
    if dest.exists() and not force:
        return {"req": req, "status": "skip"}
    dest.mkdir(parents=True, exist_ok=True)

    retro_text = retro.read_text(encoding="utf-8", errors="ignore")
    shutil.copy2(retro, dest / retro.name)

    telem = telem_dir / f"{req}-telemetry.json"
    has_telem = telem.exists()
    if has_telem:
        shutil.copy2(telem, dest / telem.name)

    verdict = find_verdict(retro_text)
    (dest / "meta.yaml").write_text(
        f"project: {slug}\nreq: {req}\narchived_at: {today}\n"
        f"source_retro: {retro}\nhas_telemetry: {str(has_telem).lower()}\n"
        f"verdict: \"{verdict}\"\n",
        encoding="utf-8",
    )
    return {"req": req, "status": "archived", "verdict": verdict, "telem": has_telem}


def update_index(index: Path, rows: list[dict], slug: str, today: str, force: bool) -> int:
    if not index.exists():
        index.write_text(
            "# Cycle archive — cross-project index\n\n"
            "Every Kuraka cycle pulled back from a consumer project. Feeds cross-project\n"
            "pattern-detection. Append-only; one row per archived cycle.\n\n"
            "| Archived | Project | Cycle (REQ) | Verdict | Telemetry |\n"
            "|---|---|---|---|---|\n",
            encoding="utf-8",
        )
    text = index.read_text(encoding="utf-8")
    added = 0
    new_lines = []
    for r in rows:
        if r["status"] != "archived":
            continue
        key = f"| {slug} | {r['req']} "
        if (key in text or any(key in nl for nl in new_lines)) and not force:
            continue
        tel = "✓" if r.get("telem") else "—"
        new_lines.append(f"| {today} | {slug} | {r['req']} | {r.get('verdict','') or '—'} | {tel} |")
        added += 1
    if new_lines:
        index.write_text(text.rstrip() + "\n" + "\n".join(new_lines) + "\n", encoding="utf-8")
    return added


def main() -> int:
    ap = argparse.ArgumentParser(description="Archive a project's Kuraka cycle diagnostics into the vault.")
    ap.add_argument("project", nargs="?", help="consumer project root")
    ap.add_argument("--project", dest="project_opt", help="consumer project root")
    ap.add_argument("--name", help="project slug override (default: config project.name or folder)")
    ap.add_argument("--vault", default=os.environ.get("KURAKA_VAULT", DEFAULT_VAULT))
    ap.add_argument("--docs-root", default="docs/process", help="project-relative docs/process root")
    ap.add_argument("--force", action="store_true", help="re-archive cycles already present")
    args = ap.parse_args()

    try:
        sys.stdout.reconfigure(line_buffering=True)
    except (AttributeError, ValueError):
        pass

    vault = Path(args.vault).expanduser().resolve()
    if not vault.is_dir():
        err(f"❌ vault no encontrado: {vault}")
        return 1
    project_raw = args.project_opt or args.project
    if not project_raw:
        err("❌ falta la ruta del proyecto.")
        return 1
    project = Path(project_raw).expanduser().resolve()
    if not project.is_dir():
        err(f"❌ proyecto no es un directorio: {project}")
        return 1

    docs = project / args.docs_root
    retro_dir = docs / "agent-retrospectives"
    telem_dir = docs / "agent-telemetry"
    if not retro_dir.is_dir():
        err(f"⚠️  sin {retro_dir} — ¿el proyecto ya cerró un ciclo (Phase 7)? Nada que archivar.")
        return 0

    slug = project_slug(project, args.name)
    today = date.today().isoformat()
    dest_root = vault / ARCHIVE_DIRNAME

    retros = sorted(p for p in retro_dir.glob("RETRO-*.md") if p.name != "RETRO-LATEST.md")
    if not retros:
        err(f"⚠️  sin RETRO-*.md en {retro_dir}. Nada que archivar.")
        return 0

    print(f"🗄️  kuraka-archive · {slug}")
    print(f"   proyecto: {project}")
    print(f"   destino:  {dest_root}/{slug}/")
    print("")

    rows = []
    for retro in retros:
        r = archive_cycle(retro, telem_dir, dest_root, slug, today, args.force)
        if r:
            rows.append(r)
            mark = "+ " if r["status"] == "archived" else "✓ "
            extra = f"  (telemetría {'✓' if r.get('telem') else '—'})" if r["status"] == "archived" else " (ya estaba)"
            print(f"   {mark}{r['req']}{extra}")

    added = update_index(dest_root / "INDEX.md", rows, slug, today, args.force)
    n_arch = sum(1 for r in rows if r["status"] == "archived")
    print("")
    print(f"✅ {n_arch} ciclo(s) archivado(s), {added} fila(s) nuevas en INDEX.md "
          f"({len(rows) - n_arch} ya estaban).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
