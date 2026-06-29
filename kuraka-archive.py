#!/usr/bin/env python3
"""kuraka-archive.py — archive a project's cycle diagnostics into the central vault.

Thin wrapper kept for backward compatibility (final-auditor / older docs call it).
It archives ONLY the closed-cycle diagnostics (RETRO + telemetry) — equivalent to
`kuraka-backup.py --cycles-only`. For the full state snapshot (layer + state +
cycles) use kuraka-backup.py, which is what Phase 7 now calls.

Writes to the unified store: <vault>/projects/<slug>/cycles/<REQ>/ and appends to
<vault>/projects/INDEX.md. Copies (never moves); idempotent. No external deps.

Usage:
    python3 kuraka-archive.py /path/to/project [--name slug] [--force]
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import kuraka_common as kc

DEFAULT_VAULT = "/Users/xmn/Documents/Agentes/AgentesTrabajos/kuraka"


def err(msg: str) -> None:
    print(msg, file=sys.stderr)


def main() -> int:
    ap = argparse.ArgumentParser(description="Archive a project's Kuraka cycle diagnostics into the vault.")
    ap.add_argument("project", nargs="?", help="consumer project root")
    ap.add_argument("--project", dest="project_opt", help="consumer project root")
    ap.add_argument("--name", help="slug override (default: config project.name or folder)")
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

    slug = kc.project_slug(project, args.name)
    branch = kc.git_branch(project)
    print(f"🗄️  kuraka-archive · {slug}  (rama: {branch})")
    print(f"   proyecto: {project}")
    print(f"   destino:  {kc.cycles_dir(vault, slug)}/")
    print("")

    rows = kc.archive_cycles(project, vault, slug, branch, args.docs_root, args.force)
    if not rows:
        err(f"⚠️  sin RETRO-*.md bajo {project}/{args.docs_root}. Nada que archivar.")
        return 0
    for r in rows:
        mark = "+ " if r["status"] == "archived" else "✓ "
        extra = (f"  (telemetría {'✓' if r.get('telem') else '—'})"
                 if r["status"] == "archived" else " (ya estaba)")
        print(f"   {mark}{r['req']}{extra}")

    added = kc.update_index(vault, rows, slug, args.force)
    n_arch = sum(1 for r in rows if r["status"] == "archived")
    print("")
    print(f"✅ {n_arch} ciclo(s) archivado(s), {added} fila(s) nuevas en INDEX.md "
          f"({len(rows) - n_arch} ya estaban).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
