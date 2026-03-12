from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import tomllib
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CODEX_HOME = Path.home() / ".codex"
DEFAULT_CONFIG_PATH = CODEX_HOME / "config.toml"
DEFAULT_STATE_PATH = CODEX_HOME / "memories" / "context_files_state.json"
DEFAULT_FILENAME = "codex.md"
LEGACY_FILENAME = "ChatGPT.md"
IGNORED_DIRS = {
    "_archive",
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".vscode",
    ".claude",
    ".codex",
    ".run",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".next",
    ".turbo",
    ".postgres",
}
MANIFEST_NAMES = {
    "package.json",
    "pyproject.toml",
    "requirements.txt",
    "pnpm-workspace.yaml",
    "turbo.json",
    "Cargo.toml",
    "go.mod",
    "tsconfig.json",
    "docker-compose.yml",
    "docker-compose.yaml",
    "compose.yml",
    "compose.yaml",
    "Makefile",
    "justfile",
}
DOC_NAMES = {"README.md", "CLAUDE.md", "AGENTS.md", "codex.md", "ChatGPT.md"}
DOC_KEYWORDS = ("architecture", "runbook", "deployment", "overview", "guide")
ENTRYPOINT_CANDIDATES = (
    "src/server.py",
    "src/main.py",
    "src/app.py",
    "server.py",
    "main.py",
    "app.py",
    "openClaw/app.js",
    "openClaw/orchestrator.js",
    "openClaw/bot.js",
)
@dataclass
class ContextSettings:
    enabled: bool = True
    dev_roots: list[str] | None = None
    filename: str = DEFAULT_FILENAME
    max_global_lines: int = 100
    max_project_lines: int = 300
    update_mode: str = "suggest_then_confirm"

    def __post_init__(self) -> None:
        self.dev_roots = self.dev_roots or []


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect layered codex.md context files.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for command in ("status", "fingerprint", "record-state"):
        sub = subparsers.add_parser(command)
        add_shared_args(sub)
        sub.add_argument("--scope", choices=["auto", "dev-root", "project"], default="auto")

    snapshot = subparsers.add_parser("snapshot")
    add_shared_args(snapshot)
    snapshot.add_argument("--scope", choices=["dev-root", "project"], required=True)

    args = parser.parse_args()
    cwd = Path(args.cwd).resolve() if args.cwd else Path.cwd().resolve()
    settings = load_settings(Path(args.config).resolve() if args.config else DEFAULT_CONFIG_PATH)
    state_path = Path(args.state).resolve() if args.state else DEFAULT_STATE_PATH

    if args.command == "status":
        payload = build_status(cwd, settings, state_path)
    elif args.command == "snapshot":
        payload = build_snapshot(cwd, settings, args.scope)
    elif args.command == "fingerprint":
        payload = build_fingerprint_payload(cwd, settings, state_path, args.scope)
    elif args.command == "record-state":
        payload = record_state(cwd, settings, state_path, args.scope)
    else:  # pragma: no cover
        raise SystemExit(f"Unknown command: {args.command}")

    print(json.dumps(payload, indent=2))
    return 0


def add_shared_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--cwd", help="Working directory to inspect")
    parser.add_argument("--config", help="Path to .codex/config.toml")
    parser.add_argument("--state", help="Path to stored context fingerprint state")


def load_settings(config_path: Path) -> ContextSettings:
    if not config_path.exists():
        return ContextSettings()
    data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    raw = data.get("context_files") or {}
    return ContextSettings(
        enabled=bool(raw.get("enabled", True)),
        dev_roots=list(raw.get("dev_roots") or []),
        filename=str(raw.get("filename") or DEFAULT_FILENAME),
        max_global_lines=int(raw.get("max_global_lines", 100)),
        max_project_lines=int(raw.get("max_project_lines", 300)),
        update_mode=str(raw.get("update_mode") or "suggest_then_confirm"),
    )


def build_status(cwd: Path, settings: ContextSettings, state_path: Path) -> dict[str, Any]:
    dev_root = resolve_dev_root(cwd, settings)
    repo_root = find_git_root(cwd)
    payload = {
        "cwd": str(cwd),
        "settings": asdict(settings),
        "dev_root": str(dev_root) if dev_root else "",
        "repo_root": str(repo_root) if repo_root else "",
        "dev_context": context_file_status(
            dev_root,
            settings.filename,
            settings.max_global_lines,
            scope="dev-root",
            state_path=state_path,
        ),
        "project_context": context_file_status(
            repo_root,
            settings.filename,
            settings.max_project_lines,
            scope="project",
            state_path=state_path,
        ),
        "warnings": [],
    }
    if not settings.enabled:
        payload["warnings"].append("context_files.enabled is false")
    if repo_root is None:
        payload["warnings"].append("No git repository root detected from cwd.")
    if dev_root is None:
        payload["warnings"].append("No configured dev root ancestor matched cwd.")
    if dev_root and repo_root and dev_root == repo_root:
        payload["warnings"].append("Dev root and repo root are the same directory.")
    return payload


def build_snapshot(cwd: Path, settings: ContextSettings, scope: str) -> dict[str, Any]:
    if scope == "dev-root":
        dev_root = resolve_dev_root(cwd, settings)
        if dev_root is None:
            raise SystemExit("No configured dev root ancestor matched cwd.")
        return snapshot_dev_root(dev_root, settings)
    repo_root = find_git_root(cwd)
    if repo_root is None:
        raise SystemExit("No git repository root detected from cwd.")
    return snapshot_project(repo_root, settings)


def build_fingerprint_payload(
    cwd: Path,
    settings: ContextSettings,
    state_path: Path,
    scope: str,
) -> dict[str, Any]:
    dev_root = resolve_dev_root(cwd, settings)
    repo_root = find_git_root(cwd)
    payload: dict[str, Any] = {
        "cwd": str(cwd),
        "scope": scope,
        "dev_root": "",
        "repo_root": "",
        "dev_fingerprint": None,
        "project_fingerprint": None,
    }
    if scope in {"auto", "dev-root"} and dev_root is not None:
        payload["dev_root"] = str(dev_root)
        payload["dev_fingerprint"] = fingerprint_report("dev-root", dev_root, state_path, settings.filename)
    if scope in {"auto", "project"} and repo_root is not None:
        payload["repo_root"] = str(repo_root)
        payload["project_fingerprint"] = fingerprint_report("project", repo_root, state_path, settings.filename)
    return payload


def record_state(
    cwd: Path,
    settings: ContextSettings,
    state_path: Path,
    scope: str,
) -> dict[str, Any]:
    state = load_state(state_path)
    recorded: list[dict[str, Any]] = []
    dev_root = resolve_dev_root(cwd, settings)
    repo_root = find_git_root(cwd)
    if scope in {"auto", "dev-root"} and dev_root is not None:
        recorded.append(store_fingerprint(state, "dev-root", dev_root, settings.filename))
    if scope in {"auto", "project"} and repo_root is not None:
        recorded.append(store_fingerprint(state, "project", repo_root, settings.filename))
    save_state(state_path, state)
    return {
        "state_path": str(state_path),
        "recorded": recorded,
    }


def resolve_dev_root(cwd: Path, settings: ContextSettings) -> Path | None:
    if not settings.enabled:
        return None
    matches: list[Path] = []
    for root_text in settings.dev_roots:
        root = Path(root_text).resolve()
        if is_ancestor(root, cwd):
            matches.append(root)
    if not matches:
        return None
    return max(matches, key=lambda item: len(item.parts))


def context_file_status(
    root: Path | None,
    filename: str,
    max_lines: int,
    *,
    scope: str,
    state_path: Path,
) -> dict[str, Any] | None:
    if root is None:
        return None
    context_path = root / filename
    legacy_path = root / LEGACY_FILENAME
    line_count = count_lines(context_path) if context_path.exists() else 0
    return {
        "scope": scope,
        "root": str(root),
        "path": str(context_path),
        "exists": context_path.exists(),
        "line_count": line_count,
        "max_lines": max_lines,
        "truncated_if_loaded": line_count > max_lines if line_count else False,
        "migration_source": str(legacy_path) if (not context_path.exists() and legacy_path.exists()) else "",
        "fingerprint": fingerprint_report(scope, root, state_path, filename),
    }


def snapshot_dev_root(dev_root: Path, settings: ContextSettings) -> dict[str, Any]:
    projects = []
    for child in sorted(dev_root.iterdir(), key=lambda item: item.name.lower()):
        if not child.is_dir() or is_ignored_dir_name(child.name):
            continue
        projects.append(
            {
                "name": child.name,
                "path": str(child),
                "is_git_repo": (child / ".git").exists(),
                "summary": summarize_project_dir(child),
                "context_files": existing_context_files(child, settings.filename),
            }
        )
    return {
        "scope": "dev-root",
        "dev_root": str(dev_root),
        "configured_filename": settings.filename,
        "projects": projects,
        "fingerprint": structural_fingerprint("dev-root", dev_root, settings.filename),
    }


def snapshot_project(repo_root: Path, settings: ContextSettings) -> dict[str, Any]:
    return {
        "scope": "project",
        "repo_root": str(repo_root),
        "repo_name": repo_root.name,
        "configured_filename": settings.filename,
        "top_level_directories": list_top_level_directories(repo_root),
        "workspace_surfaces": discover_workspace_surfaces(repo_root),
        "existing_context_files": existing_context_files(repo_root, settings.filename),
        "documentation": discover_documentation(repo_root),
        "manifests": discover_manifests(repo_root),
        "entrypoints": discover_entrypoints(repo_root),
        "tests": discover_tests(repo_root),
        "fingerprint": structural_fingerprint("project", repo_root, settings.filename),
    }


def fingerprint_report(scope: str, root: Path, state_path: Path, filename: str) -> dict[str, Any]:
    current = structural_fingerprint(scope, root, filename)
    state = load_state(state_path)
    key = state_key(scope, root)
    previous = state.get("entries", {}).get(key)
    return {
        "current": current,
        "previous_hash": previous.get("fingerprint_hash", "") if previous else "",
        "last_recorded_at": previous.get("recorded_at", "") if previous else "",
        "has_material_drift": bool(previous and previous.get("fingerprint_hash") != current["hash"]),
        "tracked": previous is not None,
    }


def store_fingerprint(state: dict[str, Any], scope: str, root: Path, filename: str) -> dict[str, Any]:
    fingerprint = structural_fingerprint(scope, root, filename)
    entry = {
        "root": str(root),
        "scope": scope,
        "codex_path": str(root / filename),
        "fingerprint_hash": fingerprint["hash"],
        "recorded_at": utc_now(),
    }
    state.setdefault("entries", {})[state_key(scope, root)] = entry
    return entry


def structural_fingerprint(scope: str, root: Path, filename: str) -> dict[str, Any]:
    if scope == "dev-root":
        data = {
            "projects": [
                {
                    "name": child.name,
                    "is_git_repo": (child / ".git").exists(),
                    "context_files": existing_context_files(child, filename),
                }
                for child in sorted(root.iterdir(), key=lambda item: item.name.lower())
                if child.is_dir() and not is_ignored_dir_name(child.name)
            ]
        }
    else:
        data = {
            "top_level_directories": list_top_level_directories(root),
            "workspace_surfaces": discover_workspace_surfaces(root),
            "manifest_digests": {
                item["path"]: item["digest"]
                for item in discover_manifests(root, include_digest=True)
            },
            "documentation_paths": [item["path"] for item in discover_documentation(root)],
        }
    return {
        "scope": scope,
        "root": str(root),
        "hash": hash_payload(data),
        "data": data,
    }


def discover_workspace_surfaces(repo_root: Path) -> list[dict[str, Any]]:
    surfaces: list[dict[str, Any]] = []
    for bucket in ("apps", "packages", "services"):
        bucket_path = repo_root / bucket
        if not bucket_path.is_dir():
            continue
        for child in sorted(bucket_path.iterdir(), key=lambda item: item.name.lower()):
            if child.is_dir() and not is_ignored_dir_name(child.name):
                surfaces.append(
                    {
                        "name": child.name,
                        "path": relpath(child, repo_root),
                        "kind": bucket,
                    }
                )
    if surfaces:
        return surfaces

    for child in sorted(repo_root.iterdir(), key=lambda item: item.name.lower()):
        if not child.is_dir() or is_ignored_dir_name(child.name):
            continue
        if any((child / candidate).exists() for candidate in MANIFEST_NAMES):
            surfaces.append(
                {
                    "name": child.name,
                    "path": relpath(child, repo_root),
                    "kind": "workspace",
                }
            )
            continue
        if any((child / candidate).exists() for candidate in ("app.js", "server.py", "main.py")):
            surfaces.append(
                {
                    "name": child.name,
                    "path": relpath(child, repo_root),
                    "kind": "runtime",
                }
            )
    return surfaces


def discover_documentation(repo_root: Path) -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    for path in walk_files(repo_root, max_depth=2):
        if path.suffix.lower() not in {".md", ".pdf", ".txt"}:
            continue
        name = path.name
        lower_name = name.lower()
        if name in DOC_NAMES or any(keyword in lower_name for keyword in DOC_KEYWORDS):
            docs.append(
                {
                    "path": relpath(path, repo_root),
                    "reference": find_best_reference(path, repo_root),
                    "title": first_heading_or_text(path),
                }
            )
    return docs


def discover_manifests(repo_root: Path, include_digest: bool = False) -> list[dict[str, Any]]:
    manifests: list[dict[str, Any]] = []
    for path in walk_files(repo_root, max_depth=2):
        if path.name not in MANIFEST_NAMES:
            continue
        item = {
            "path": relpath(path, repo_root),
            "reference": find_manifest_reference(path, repo_root),
        }
        if include_digest:
            item["digest"] = sha256(path.read_text(encoding="utf-8", errors="ignore"))
        manifests.append(item)
    return manifests


def discover_entrypoints(repo_root: Path) -> list[dict[str, Any]]:
    entrypoints: list[dict[str, Any]] = []
    for relative in ENTRYPOINT_CANDIDATES:
        path = repo_root / relative
        if not path.exists():
            continue
        entrypoints.append(
            {
                "path": relpath(path, repo_root),
                "reference": find_code_reference(path, repo_root),
            }
        )
    return entrypoints


def discover_tests(repo_root: Path) -> list[dict[str, Any]]:
    tests: list[dict[str, Any]] = []
    for path in walk_files(repo_root, max_depth=2):
        relative = relpath(path, repo_root)
        normalized = relative.replace("\\", "/")
        if path.suffix.lower() not in {".py", ".js", ".ts", ".tsx"}:
            continue
        name = Path(normalized).name
        if name.startswith("test_") or name == "conftest.py":
            tests.append(
                {
                    "path": relative,
                    "reference": first_matching_line_reference(path, repo_root, (r"^def test_", r"^@pytest")),
                }
            )
    return tests


def list_top_level_directories(root: Path) -> list[str]:
    return [
        child.name
        for child in sorted(root.iterdir(), key=lambda item: item.name.lower())
        if child.is_dir() and not is_ignored_dir_name(child.name)
    ]


def existing_context_files(root: Path, filename: str) -> dict[str, Any]:
    return {
        "codex": str(root / filename) if (root / filename).exists() else "",
        "claude": str(root / "CLAUDE.md") if (root / "CLAUDE.md").exists() else "",
        "agents": str(root / "AGENTS.md") if (root / "AGENTS.md").exists() else "",
        "chatgpt": str(root / LEGACY_FILENAME) if (root / LEGACY_FILENAME).exists() else "",
    }


def summarize_project_dir(path: Path) -> str:
    for candidate in ("codex.md", "README.md", "CLAUDE.md", "AGENTS.md"):
        file_path = path / candidate
        if file_path.exists():
            return first_heading_or_text(file_path)
    return ""


def find_git_root(cwd: Path) -> Path | None:
    try:
        output = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except subprocess.CalledProcessError:
        return None
    return Path(output).resolve()


def first_heading_or_text(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        return path.name
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return ""
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()
    for line in lines:
        stripped = line.strip()
        if stripped:
            return stripped[:160]
    return ""


def find_best_reference(path: Path, root: Path) -> str:
    if path.suffix.lower() == ".md":
        return first_matching_line_reference(path, root, (r"^#",))
    return f"{relpath(path, root)}:1"


def find_manifest_reference(path: Path, root: Path) -> str:
    patterns = (r'^\[project\]', r'^\[tool\.pytest', r'^\s*"scripts"\s*:', r'^\[build-system\]')
    return first_matching_line_reference(path, root, patterns)


def find_code_reference(path: Path, root: Path) -> str:
    patterns = (
        r"FastAPI\(",
        r"^class ",
        r"^def main",
        r'^@app\.(get|post)\(',
        r'^if __name__ == "__main__":',
        r'^\s*"start"\s*:',
    )
    return first_matching_line_reference(path, root, patterns)


def first_matching_line_reference(path: Path, root: Path, patterns: tuple[str, ...]) -> str:
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return f"{relpath(path, root)}:1"
    compiled = [re.compile(pattern) for pattern in patterns]
    for index, line in enumerate(lines, 1):
        for pattern in compiled:
            if pattern.search(line):
                return f"{relpath(path, root)}:{index}"
    return f"{relpath(path, root)}:1"


def walk_files(root: Path, max_depth: int) -> list[Path]:
    results: list[Path] = []
    for current_root, dirnames, filenames in os.walk(root):
        current_path = Path(current_root)
        relative_root = current_path.relative_to(root)
        depth = len(relative_root.parts)
        dirnames[:] = [
            name
            for name in dirnames
            if not is_ignored_dir_name(name) and depth < max_depth + 1
        ]
        if depth > max_depth:
            continue
        for filename in filenames:
            path = current_path / filename
            results.append(path)
    return sorted(results, key=lambda item: relpath(item, root).lower())


def count_lines(path: Path) -> int:
    try:
        return len(path.read_text(encoding="utf-8", errors="ignore").splitlines())
    except OSError:
        return 0


def is_ancestor(parent: Path, child: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def relpath(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def is_ignored_dir_name(name: str) -> bool:
    return name in IGNORED_DIRS or name.endswith(".egg-info")


def hash_payload(payload: Any) -> str:
    return sha256(json.dumps(payload, sort_keys=True))


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"version": 1, "entries": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")


def state_key(scope: str, root: Path) -> str:
    return f"{scope}::{str(root).lower()}"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
