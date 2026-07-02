#!/usr/bin/env python3
"""
kuraka-inspect.py — Stack detector for any project.

Scans a target directory and emits a JSON report describing the project's
tech stack, used downstream by the amauta agent (brownfield onboarding) or
by the user directly for Kuraka initialization.

Usage:
    python3 kuraka-inspect.py [target_dir]
        (default: $PWD)

Output:
    - JSON report to stdout (pipe to jq, or redirect to file)
    - Human-readable summary to stderr

Exit codes:
    0 — detection ran (may include partial results)
    1 — target directory invalid
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Any

# Emit UTF-8 regardless of the console code page (Windows cp1252/cp850 crash guard).
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError, OSError):
        pass


# ---------------------------------------------------------------------------
# Language detection — file counts per extension
# ---------------------------------------------------------------------------

LANGUAGE_EXTS: dict[str, list[str]] = {
    "python": [".py"],
    "typescript": [".ts", ".tsx"],
    "javascript": [".js", ".jsx", ".mjs", ".cjs"],
    "go": [".go"],
    "rust": [".rs"],
    "java": [".java"],
    "kotlin": [".kt", ".kts"],
    "csharp": [".cs"],
    "php": [".php"],
    "ruby": [".rb"],
    "vue": [".vue"],
    "svelte": [".svelte"],
}

# Directories to ignore when scanning file extensions
IGNORED_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv", "env",
    "dist", "build", ".next", ".nuxt", ".svelte-kit", "target",
    ".pytest_cache", ".ruff_cache", ".mypy_cache", "coverage",
    ".idea", ".vscode", "vendor", ".cargo", ".gradle",
}


def count_files_by_language(root: Path) -> dict[str, int]:
    counts: dict[str, int] = {lang: 0 for lang in LANGUAGE_EXTS}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        ext = path.suffix.lower()
        for lang, exts in LANGUAGE_EXTS.items():
            if ext in exts:
                counts[lang] += 1
                break
    return {lang: n for lang, n in counts.items() if n > 0}


# ---------------------------------------------------------------------------
# Backend detection — dependency files
# ---------------------------------------------------------------------------

def read_text_safe(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def detect_python_backend(root: Path) -> dict[str, Any] | None:
    deps = ""
    for fname in ("pyproject.toml", "requirements.txt", "requirements-dev.txt", "Pipfile", "setup.py"):
        for match in root.rglob(fname):
            if any(part in IGNORED_DIRS for part in match.parts):
                continue
            deps += read_text_safe(match).lower() + "\n"

    if not deps:
        return None

    framework_matches = []
    if "fastapi" in deps:
        framework_matches.append("fastapi")
    if "django" in deps and "djangorestframework" not in deps:
        framework_matches.append("django")
    if "djangorestframework" in deps or "rest_framework" in deps:
        framework_matches.append("django-rest-framework")
    if "flask" in deps:
        framework_matches.append("flask")
    if "starlette" in deps and "fastapi" not in deps:
        framework_matches.append("starlette")
    if "aiohttp" in deps:
        framework_matches.append("aiohttp")
    if "tornado" in deps:
        framework_matches.append("tornado")

    orm_matches = []
    if "sqlalchemy" in deps:
        orm_matches.append("sqlalchemy")
    if "django.db" in deps or "django==" in deps or "django>=" in deps:
        orm_matches.append("django-orm")
    if "tortoise-orm" in deps:
        orm_matches.append("tortoise")
    if "pony" in deps:
        orm_matches.append("pony")
    if "peewee" in deps:
        orm_matches.append("peewee")

    migration_tool = None
    if "alembic" in deps or (root / "alembic.ini").exists() or (root / "backend" / "alembic.ini").exists():
        migration_tool = "alembic"
    elif any(root.rglob("migrations/0001_initial.py")):
        migration_tool = "django-migrations"

    return {
        "language": "python",
        "framework": framework_matches[0] if framework_matches else None,
        "framework_candidates": framework_matches,
        "orm_candidates": orm_matches,
        "migration_tool": migration_tool,
    }


def detect_node_backend(root: Path) -> dict[str, Any] | None:
    pkgs = []
    for pkg_path in root.rglob("package.json"):
        if any(part in IGNORED_DIRS for part in pkg_path.parts):
            continue
        try:
            pkgs.append(json.loads(read_text_safe(pkg_path)))
        except json.JSONDecodeError:
            continue

    if not pkgs:
        return None

    deps: dict[str, str] = {}
    for pkg in pkgs:
        deps.update(pkg.get("dependencies", {}))
        deps.update(pkg.get("devDependencies", {}))

    # Backend frameworks
    framework_matches = []
    for key in ("express", "fastify", "koa", "hapi", "nestjs", "@nestjs/core", "next", "hono", "elysia"):
        if key in deps:
            framework_matches.append(key.replace("@nestjs/core", "nestjs"))

    orm_matches = []
    for key in ("prisma", "@prisma/client", "drizzle-orm", "typeorm", "sequelize", "mikro-orm", "mongoose", "knex"):
        if key in deps:
            orm_matches.append(key.replace("@prisma/client", "prisma"))

    is_typescript = "typescript" in deps or any(root.rglob("tsconfig.json"))

    return {
        "language": "typescript" if is_typescript else "javascript",
        "framework": framework_matches[0] if framework_matches else None,
        "framework_candidates": framework_matches,
        "orm_candidates": orm_matches,
        "migration_tool": _node_migration_tool(deps),
    }


def _node_migration_tool(deps: dict[str, str]) -> str | None:
    if "prisma" in deps or "@prisma/client" in deps:
        return "prisma-migrate"
    if "drizzle-kit" in deps:
        return "drizzle-kit"
    if "typeorm" in deps:
        return "typeorm-migrations"
    if "knex" in deps:
        return "knex-migrations"
    if "sequelize" in deps:
        return "sequelize-migrations"
    return None


def detect_go_backend(root: Path) -> dict[str, Any] | None:
    go_mod = root / "go.mod"
    if not go_mod.exists():
        return None

    deps = read_text_safe(go_mod).lower()

    framework_matches = []
    for key in ("github.com/gin-gonic/gin", "github.com/labstack/echo", "github.com/gofiber/fiber",
                "github.com/go-chi/chi", "github.com/gorilla/mux", "net/http"):
        if key in deps:
            framework_matches.append(key.split("/")[-1] if "/" in key else key)

    orm_matches = []
    for key in ("gorm.io/gorm", "github.com/jmoiron/sqlx", "github.com/uptrace/bun", "entgo.io/ent"):
        if key in deps:
            orm_matches.append(key.split("/")[-1])

    return {
        "language": "go",
        "framework": framework_matches[0] if framework_matches else None,
        "framework_candidates": framework_matches,
        "orm_candidates": orm_matches,
        "migration_tool": "golang-migrate" if "golang-migrate" in deps else None,
    }


def detect_rust_backend(root: Path) -> dict[str, Any] | None:
    cargo = root / "Cargo.toml"
    if not cargo.exists():
        return None

    deps = read_text_safe(cargo).lower()
    framework_matches = [f for f in ("actix-web", "axum", "rocket", "warp", "poem") if f in deps]
    orm_matches = [o for o in ("diesel", "sqlx", "sea-orm") if o in deps]

    return {
        "language": "rust",
        "framework": framework_matches[0] if framework_matches else None,
        "framework_candidates": framework_matches,
        "orm_candidates": orm_matches,
        "migration_tool": "sqlx-migrate" if "sqlx" in deps else ("diesel" if "diesel" in deps else None),
    }


def detect_ruby_backend(root: Path) -> dict[str, Any] | None:
    gemfile = root / "Gemfile"
    if not gemfile.exists():
        return None

    deps = read_text_safe(gemfile).lower()
    framework = "rails" if "rails" in deps else ("sinatra" if "sinatra" in deps else None)

    return {
        "language": "ruby",
        "framework": framework,
        "framework_candidates": [framework] if framework else [],
        "orm_candidates": ["activerecord"] if framework == "rails" else [],
        "migration_tool": "rails-migrations" if framework == "rails" else None,
    }


def detect_php_backend(root: Path) -> dict[str, Any] | None:
    composer = root / "composer.json"
    if not composer.exists():
        return None

    try:
        data = json.loads(read_text_safe(composer))
    except json.JSONDecodeError:
        return None

    deps = data.get("require", {}) | data.get("require-dev", {})
    framework_matches = [f for f in ("laravel/framework", "symfony/symfony", "slim/slim") if f in deps]
    return {
        "language": "php",
        "framework": framework_matches[0].split("/")[0] if framework_matches else None,
        "framework_candidates": [f.split("/")[0] for f in framework_matches],
        "orm_candidates": ["eloquent"] if any("laravel" in f for f in framework_matches) else [],
        "migration_tool": "laravel-migrations" if any("laravel" in f for f in framework_matches) else None,
    }


BACKEND_DETECTORS = [
    detect_python_backend,
    detect_node_backend,
    detect_go_backend,
    detect_rust_backend,
    detect_ruby_backend,
    detect_php_backend,
]


# ---------------------------------------------------------------------------
# Frontend detection
# ---------------------------------------------------------------------------

def detect_frontend(root: Path) -> dict[str, Any] | None:
    deps: dict[str, str] = {}
    has_any = False
    for pkg_path in root.rglob("package.json"):
        if any(part in IGNORED_DIRS for part in pkg_path.parts):
            continue
        try:
            pkg = json.loads(read_text_safe(pkg_path))
            deps.update(pkg.get("dependencies", {}))
            deps.update(pkg.get("devDependencies", {}))
            has_any = True
        except json.JSONDecodeError:
            continue

    if not has_any:
        return None

    framework = None
    for key in ("vue", "react", "svelte", "solid-js", "@angular/core", "qwik", "preact"):
        if key in deps:
            framework = key.replace("@angular/core", "angular").replace("solid-js", "solid")
            break

    meta_framework = None
    for key in ("next", "nuxt", "@sveltekit", "@nuxt/kit", "astro", "remix"):
        if key in deps:
            meta_framework = key.split("/")[0].lstrip("@") if "@" in key else key
            break

    bundler = None
    for key in ("vite", "webpack", "rollup", "esbuild", "parcel", "turbopack"):
        if key in deps:
            bundler = key
            break

    state_manager = None
    for key in ("pinia", "vuex", "redux", "zustand", "jotai", "recoil", "mobx", "@ngrx/store"):
        if key in deps:
            state_manager = key.replace("@ngrx/store", "ngrx")
            break

    styling = []
    for key in ("tailwindcss", "styled-components", "@emotion/react", "sass", "less", "postcss"):
        if key in deps:
            styling.append(key.replace("@emotion/react", "emotion"))

    typescript = "typescript" in deps

    if not framework and not meta_framework:
        return None

    return {
        "framework": framework,
        "meta_framework": meta_framework,
        "bundler": bundler,
        "state_manager": state_manager,
        "styling": styling,
        "typescript": typescript,
    }


# ---------------------------------------------------------------------------
# Testing detection
# ---------------------------------------------------------------------------

def detect_testing(root: Path) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {"backend": [], "frontend": [], "e2e": []}

    # Backend python
    py_deps = ""
    for fname in ("pyproject.toml", "requirements.txt", "requirements-dev.txt"):
        for path in root.rglob(fname):
            if any(part in IGNORED_DIRS for part in path.parts):
                continue
            py_deps += read_text_safe(path).lower() + "\n"
    for key in ("pytest", "pytest-asyncio", "unittest", "nose2"):
        if key in py_deps and key not in result["backend"]:
            result["backend"].append(key)

    # Node
    node_deps: dict[str, str] = {}
    for pkg_path in root.rglob("package.json"):
        if any(part in IGNORED_DIRS for part in pkg_path.parts):
            continue
        try:
            pkg = json.loads(read_text_safe(pkg_path))
            node_deps.update(pkg.get("dependencies", {}))
            node_deps.update(pkg.get("devDependencies", {}))
        except json.JSONDecodeError:
            continue

    for key in ("jest", "vitest", "mocha", "ava", "tape", "@testing-library/vue",
                "@testing-library/react", "@vue/test-utils"):
        if key in node_deps and key.lstrip("@") not in result["frontend"]:
            result["frontend"].append(key.lstrip("@"))
    for key in ("playwright", "@playwright/test", "cypress"):
        if key in node_deps and key.lstrip("@").split("/")[0] not in result["e2e"]:
            result["e2e"].append(key.lstrip("@").split("/")[0])

    return {k: v for k, v in result.items() if v}


# ---------------------------------------------------------------------------
# Linting / formatting
# ---------------------------------------------------------------------------

def detect_tooling(root: Path) -> dict[str, list[str]]:
    detected: list[str] = []

    markers = {
        "ruff": ("ruff.toml", "pyproject.toml"),
        "black": ("pyproject.toml",),
        "mypy": ("mypy.ini", "pyproject.toml"),
        "eslint": (".eslintrc", ".eslintrc.js", ".eslintrc.json", ".eslintrc.cjs", "eslint.config.js"),
        "prettier": (".prettierrc", ".prettierrc.json", "prettier.config.js"),
        "rubocop": (".rubocop.yml",),
        "rustfmt": ("rustfmt.toml", ".rustfmt.toml"),
        "golangci-lint": (".golangci.yml", ".golangci.yaml"),
        "gofmt": ("go.mod",),  # gofmt is always available if Go is used
    }

    for tool, files in markers.items():
        for f in files:
            if any(root.rglob(f)) or (root / f).exists():
                # Extra check: some pyproject.toml don't actually configure the tool
                if f == "pyproject.toml" and tool in ("ruff", "black", "mypy"):
                    content = read_text_safe(root / "pyproject.toml")
                    if f"[tool.{tool}" not in content:
                        # Check subdir pyproject.toml
                        found = False
                        for p in root.rglob("pyproject.toml"):
                            if tool in read_text_safe(p):
                                found = True
                                break
                        if not found:
                            continue
                detected.append(tool)
                break

    return {"detected": sorted(set(detected))}


# ---------------------------------------------------------------------------
# CI / containers / structure
# ---------------------------------------------------------------------------

def detect_ci(root: Path) -> str | None:
    if (root / ".github" / "workflows").is_dir() and any((root / ".github" / "workflows").iterdir()):
        return "github-actions"
    if (root / ".gitlab-ci.yml").exists():
        return "gitlab-ci"
    if (root / ".circleci" / "config.yml").exists():
        return "circleci"
    if (root / "bitbucket-pipelines.yml").exists():
        return "bitbucket"
    if (root / "azure-pipelines.yml").exists():
        return "azure-pipelines"
    return None


def detect_containers(root: Path) -> dict[str, bool]:
    return {
        "dockerfile": any(root.rglob("Dockerfile")) and not all(
            any(part in IGNORED_DIRS for part in p.parts) for p in root.rglob("Dockerfile")
        ),
        "docker_compose": any(root.rglob("docker-compose*.yml")) or any(root.rglob("compose.yml")),
        "kubernetes": any(root.rglob("*.k8s.yaml")) or (root / "k8s").is_dir() or (root / "kubernetes").is_dir(),
    }


def detect_structure(root: Path) -> str:
    if (root / "pnpm-workspace.yaml").exists():
        return "monorepo-pnpm"
    if (root / "turbo.json").exists():
        return "monorepo-turbo"
    if (root / "nx.json").exists():
        return "monorepo-nx"
    if (root / "lerna.json").exists():
        return "monorepo-lerna"
    if (root / "go.work").exists():
        return "monorepo-go-workspaces"
    # npm / yarn classic workspaces: root package.json "workspaces" field
    # (array, or object with a "packages" array). Missed before → dbcanvas was
    # misdetected as single-package.
    pkg = root / "package.json"
    if pkg.is_file():
        try:
            data = json.loads(pkg.read_text(encoding="utf-8"))
            ws = data.get("workspaces")
            if isinstance(ws, dict):
                ws = ws.get("packages")
            if isinstance(ws, list) and ws:
                return "monorepo-npm-workspaces"
        except (json.JSONDecodeError, OSError):
            pass
    # Heuristic: a populated packages/ or apps/ dir of sub-packages
    for sub in ("packages", "apps"):
        d = root / sub
        if d.is_dir() and any(
            (child / "package.json").is_file() for child in d.iterdir() if child.is_dir()
        ):
            return "monorepo-de-facto"
    # Heuristic: backend/ + frontend/ at top = de-facto monorepo
    if (root / "backend").is_dir() and (root / "frontend").is_dir():
        return "monorepo-de-facto"
    return "single-package"


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def run_detection(root: Path) -> dict[str, Any]:
    languages = count_files_by_language(root)

    backend: dict[str, Any] | None = None
    for detector in BACKEND_DETECTORS:
        result = detector(root)
        if result:
            backend = result
            break

    frontend = detect_frontend(root)
    testing = detect_testing(root)
    tooling = detect_tooling(root)
    ci = detect_ci(root)
    containers = detect_containers(root)
    structure = detect_structure(root)

    # Confidence heuristic: more signals → higher confidence
    signals = sum([
        1 if backend else 0,
        1 if frontend else 0,
        1 if testing else 0,
        1 if tooling.get("detected") else 0,
        1 if ci else 0,
        1 if containers.get("dockerfile") else 0,
    ])
    confidence = min(1.0, signals / 6.0)

    return {
        "detected_at": datetime.now().isoformat(timespec="seconds"),
        "project_root": str(root.resolve()),
        "languages": languages,
        "backend": backend,
        "frontend": frontend,
        "testing": testing,
        "tooling": tooling,
        "ci": ci,
        "containers": containers,
        "structure": structure,
        "confidence": round(confidence, 2),
    }


def render_summary(report: dict[str, Any]) -> str:
    lines = ["🪢 kuraka-inspect — summary", f"   project: {report['project_root']}", ""]

    if report["languages"]:
        top = sorted(report["languages"].items(), key=lambda kv: kv[1], reverse=True)[:5]
        lines.append("  Languages: " + ", ".join(f"{k} ({v})" for k, v in top))

    b = report.get("backend")
    if b:
        fw = b.get("framework") or "(no framework detected)"
        orm = ", ".join(b.get("orm_candidates", [])) or "—"
        mig = b.get("migration_tool") or "—"
        lines.append(f"  Backend:   {b.get('language')} / {fw}")
        lines.append(f"             ORM: {orm}  |  Migrations: {mig}")
    else:
        lines.append("  Backend:   (none detected)")

    f = report.get("frontend")
    if f:
        parts = [f.get("framework") or "?"]
        if f.get("meta_framework"):
            parts.append(f.get("meta_framework"))
        if f.get("bundler"):
            parts.append(f"bundler={f['bundler']}")
        if f.get("state_manager"):
            parts.append(f"state={f['state_manager']}")
        if f.get("styling"):
            parts.append("styling=" + ",".join(f["styling"]))
        if f.get("typescript"):
            parts.append("TS")
        lines.append("  Frontend:  " + " · ".join(p for p in parts if p))
    else:
        lines.append("  Frontend:  (none detected)")

    t = report.get("testing") or {}
    if t:
        for k, vs in t.items():
            lines.append(f"  Testing ({k}): {', '.join(vs)}")

    tooling = report.get("tooling", {}).get("detected", [])
    if tooling:
        lines.append(f"  Tooling:   {', '.join(tooling)}")

    if report.get("ci"):
        lines.append(f"  CI:        {report['ci']}")

    c = report.get("containers") or {}
    containers = [k for k, v in c.items() if v]
    if containers:
        lines.append(f"  Containers: {', '.join(containers)}")

    lines.append(f"  Structure: {report.get('structure')}")
    lines.append("")
    lines.append(f"  Confidence: {report['confidence']}")
    return "\n".join(lines)


def main() -> int:
    target = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    if not target.is_dir():
        print(f"[error] not a directory: {target}", file=sys.stderr)
        return 1

    report = run_detection(target)

    # Human summary to stderr
    print(render_summary(report), file=sys.stderr)
    print("", file=sys.stderr)

    # JSON to stdout
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
