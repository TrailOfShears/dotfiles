from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from string import Template
from typing import Any


SKILL_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = SKILL_ROOT / "assets" / "templates"
CODEX_CONTEXT_SCRIPT = (
    Path.home() / ".codex" / "skills" / "codex-context" / "scripts" / "context_files.py"
)
MARKDOWN_MARKER = "<!-- Bootstrapped by new-project -->"
TEXT_MARKER = "# Bootstrapped by new-project"
CODE_MARKERS = ("// Bootstrapped by new-project",)
IGNORED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".vscode",
    ".claude",
    ".codex",
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
}
PLANNING_PATTERNS = (
    "spec*.md",
    "plan*.md",
    "brief*.md",
    "notes*.md",
    "phase*_instructions.txt",
)
MARKDOWN_SUFFIXES = {".md", ".txt"}
TEXT_SUFFIXES = {".md", ".txt", ".toml", ".json", ".yaml", ".yml"}
STACKS = ("python", "node-js", "node-ts", "bun-ts", "monorepo", "generic")


@dataclass
class PlanningSource:
    kind: str
    label: str
    path: str
    reference: str
    priority: int
    title: str
    excerpt: str
    content: str


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect and scaffold a planned project.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect")
    add_shared_args(inspect_parser)

    scaffold_parser = subparsers.add_parser("scaffold")
    add_shared_args(scaffold_parser)

    args = parser.parse_args()
    root = Path(args.cwd).resolve() if args.cwd else Path.cwd().resolve()

    if args.command == "inspect":
        payload = inspect_project(root, args.user_context)
        print(json.dumps(payload, indent=2))
        return 0

    payload = scaffold_project(root, args.user_context)
    print(json.dumps(payload, indent=2))
    return 0 if payload["status"] == "scaffolded" else 2


def add_shared_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--cwd", help="Project directory to inspect")
    parser.add_argument(
        "--user-context",
        default="",
        help="Additional project description from the user prompt",
    )


def inspect_project(root: Path, user_context: str) -> dict[str, Any]:
    sources = gather_planning_sources(root, user_context)
    project_name = infer_project_name(root, sources)
    purpose = infer_purpose(sources)
    purpose_short = shorten_text(purpose, 110) or f"Bootstrap {project_name}."
    stack_profile, stack_reasons, stack_ambiguity = infer_stack_profile(root, sources)
    repo_shape = infer_repo_shape(root, stack_profile, sources)
    profile = build_profile_dict(
        root=root,
        sources=sources,
        project_name=project_name,
        purpose=purpose,
        purpose_short=purpose_short,
        stack_profile=stack_profile,
        stack_reasons=stack_reasons,
        repo_shape=repo_shape,
    )
    ambiguities = list(profile["ambiguities"])
    if stack_ambiguity and stack_ambiguity not in ambiguities:
        ambiguities.append(stack_ambiguity)
    if purpose and is_vague_purpose(purpose):
        ambiguities.append("Planning material is too vague to scaffold safely; confirm the project purpose first.")
    profile["ambiguities"] = ambiguities
    profile["ready_to_scaffold"] = not ambiguities
    return profile


def scaffold_project(root: Path, user_context: str) -> dict[str, Any]:
    profile = inspect_project(root, user_context)
    if profile["ambiguities"]:
        return {
            "status": "needs_confirmation",
            "message": "Key project details are ambiguous. Confirm the profile before scaffolding.",
            "profile": profile,
        }

    created_files: list[str] = []
    created_directories: list[str] = []
    skipped_files: list[dict[str, str]] = []
    warnings: list[str] = []
    git_initialized = ensure_git_repo(root)

    for directory in profile["directories"]:
        dir_path = root / directory["path"]
        if directory["action"] == "create":
            dir_path.mkdir(parents=True, exist_ok=True)
            created_directories.append(directory["path"])

    for file_spec in profile["files"]:
        path = root / file_spec["path"]
        action = file_spec["action"]
        if action != "create":
            skipped_files.append({"path": file_spec["path"], "action": action})
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        content = render_file_content(file_spec["path"], profile)
        path.write_text(content, encoding="utf-8")
        created_files.append(file_spec["path"])

    codex_recorded = False
    if any(Path(path).name == "codex.md" for path in created_files) and CODEX_CONTEXT_SCRIPT.exists():
        result = subprocess.run(
            ["python", str(CODEX_CONTEXT_SCRIPT), "record-state", "--cwd", str(root)],
            capture_output=True,
            text=True,
            check=False,
        )
        codex_recorded = result.returncode == 0
        if not codex_recorded and result.stderr.strip():
            warnings.append(result.stderr.strip())

    return {
        "status": "scaffolded",
        "project_root": str(root),
        "git_initialized": git_initialized,
        "codex_state_recorded": codex_recorded,
        "created_directories": created_directories,
        "created_files": created_files,
        "skipped_files": skipped_files,
        "warnings": warnings,
        "profile": profile,
    }


def build_profile_dict(
    *,
    root: Path,
    sources: list[PlanningSource],
    project_name: str,
    purpose: str,
    purpose_short: str,
    stack_profile: str,
    stack_reasons: list[str],
    repo_shape: str,
) -> dict[str, Any]:
    project_slug = slugify(project_name, "-")
    package_name = slugify(project_name, "_")
    ambiguities: list[str] = []

    if not sources:
        ambiguities.append("No planning material or user context was found in the current directory.")
    if not purpose:
        ambiguities.append("Project purpose is not clear from the planning inputs.")
    if stack_profile not in STACKS:
        ambiguities.append("Stack profile could not be determined.")

    desired_dirs, desired_files = desired_layout(
        root=root,
        stack_profile=stack_profile,
        repo_shape=repo_shape,
        package_name=package_name,
        sources=sources,
    )
    existing_paths = discover_existing_paths(root)

    directories = [
        {
            "path": path,
            "action": "create" if not (root / path).exists() else "keep_existing",
        }
        for path in desired_dirs
    ]
    files = []
    for path in desired_files:
        file_path = root / path
        files.append(
            {
                "path": path,
                "action": classify_existing_path(file_path),
            }
        )

    return {
        "project_root": str(root),
        "project_name": project_name,
        "project_slug": project_slug,
        "package_name": package_name,
        "purpose": purpose,
        "purpose_short": purpose_short,
        "stack_profile": stack_profile,
        "stack_reasons": stack_reasons,
        "repo_shape": repo_shape,
        "planning_sources": [
            {
                "kind": source.kind,
                "label": source.label,
                "path": source.path,
                "reference": source.reference,
                "priority": source.priority,
                "title": source.title,
                "excerpt": source.excerpt,
            }
            for source in sources
        ],
        "existing_paths": existing_paths,
        "directories": directories,
        "files": files,
        "would_create": [
            path["path"]
            for path in directories + files
            if path["action"] == "create"
        ],
        "ambiguities": ambiguities,
    }


def gather_planning_sources(root: Path, user_context: str) -> list[PlanningSource]:
    sources: list[PlanningSource] = []
    seen: set[str] = set()

    if user_context.strip():
        text = user_context.strip()
        sources.append(
            PlanningSource(
                kind="user_context",
                label="user_context",
                path="",
                reference="user_context",
                priority=0,
                title=extract_heading(text) or "User context",
                excerpt=shorten_text(extract_summary(text) or text, 220),
                content=text,
            )
        )

    ordered_paths: list[tuple[int, Path]] = []
    direct_candidates = [
        (1, root / "codex.md"),
        (2, root / "README.md"),
    ]
    ordered_paths.extend((priority, path) for priority, path in direct_candidates if path.exists())

    for path in sorted(iter_candidate_files(root), key=lambda item: item.as_posix().lower()):
        priority = match_priority(path.name)
        if priority is None:
            continue
        ordered_paths.append((priority, path))

    trailing_candidates = [
        (6, root / "CLAUDE.md"),
        (6, root / "AGENTS.md"),
        (7, root / "pyproject.toml"),
        (7, root / "package.json"),
        (7, root / "tsconfig.json"),
        (7, root / "requirements.txt"),
    ]
    ordered_paths.extend((priority, path) for priority, path in trailing_candidates if path.exists())

    for priority, path in ordered_paths:
        key = str(path.resolve()).lower()
        if key in seen:
            continue
        seen.add(key)
        content = read_text(path)
        if not content.strip():
            continue
        sources.append(
            PlanningSource(
                kind="file",
                label=path.name,
                path=relpath(path, root),
                reference=f"{relpath(path, root)}:1",
                priority=priority,
                title=extract_heading(content) or path.stem,
                excerpt=shorten_text(extract_summary(content) or content, 220),
                content=content,
            )
        )

    sources.sort(key=lambda item: (item.priority, item.path or item.label))
    return sources


def iter_candidate_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for current_root, dirnames, filenames in os.walk(root):
        current_path = Path(current_root)
        relative_root = current_path.relative_to(root)
        depth = len(relative_root.parts)
        dirnames[:] = [name for name in dirnames if name not in IGNORED_DIRS and depth < 2]
        if depth > 2:
            continue
        for filename in filenames:
            path = current_path / filename
            files.append(path)
    return files


def match_priority(name: str) -> int | None:
    lowered = name.lower()
    for pattern in PLANNING_PATTERNS:
        regex = "^" + pattern.replace(".", r"\.").replace("*", ".*") + "$"
        if re.match(regex, lowered):
            return 3 if lowered.startswith(("spec", "plan", "brief", "notes")) else 4
    return None


def infer_project_name(root: Path, sources: list[PlanningSource]) -> str:
    for source in sources:
        heading = sanitize_project_name(source.title)
        if heading:
            return heading
    return title_case_from_slug(root.name)


def infer_purpose(sources: list[PlanningSource]) -> str:
    for source in sources:
        summary = extract_summary(source.content)
        if summary:
            return normalize_sentence(summary)
    return ""


def infer_stack_profile(root: Path, sources: list[PlanningSource]) -> tuple[str, list[str], str | None]:
    combined = "\n".join(source.content.lower() for source in sources)
    reasons: list[str] = []

    monorepo_signals = 0
    python_signals = 0
    node_signals = 0
    typescript_signals = 0
    bun_signals = 0

    if (root / "apps").exists() and (root / "packages").exists():
        monorepo_signals += 5
    if any(token in combined for token in ("monorepo", "apps/", "packages/", "workspace", "shared package")):
        monorepo_signals += 3
    if (root / "pnpm-workspace.yaml").exists() or (root / "turbo.json").exists():
        monorepo_signals += 4

    if any(token in combined for token in ("python", "fastapi", "flask", "django", "pytest", "pip", "uvicorn")):
        python_signals += 3
    if (root / "pyproject.toml").exists() or (root / "requirements.txt").exists():
        python_signals += 4

    if any(token in combined for token in ("node", "javascript", "package.json", "npm", "yarn")):
        node_signals += 3
    if (root / "package.json").exists():
        node_signals += 3

    if any(token in combined for token in ("typescript", "tsconfig", ".ts", "tsc")):
        typescript_signals += 3
    if (root / "tsconfig.json").exists():
        typescript_signals += 4

    if any(token in combined for token in ("bun", "bunx", "bun run", "bun test")):
        bun_signals += 4
    if (root / "bun.lock").exists() or (root / "bun.lockb").exists():
        bun_signals += 4

    if monorepo_signals >= 4:
        reasons.append("Planning signals imply an apps/packages workspace.")
        return "monorepo", reasons, None
    if bun_signals >= 4 and typescript_signals >= 1:
        reasons.append("Planning signals explicitly mention Bun and TypeScript.")
        return "bun-ts", reasons, None
    if python_signals > 0 and node_signals > 0 and abs(python_signals - node_signals) <= 1:
        return "generic", reasons, "Planning signals conflict between Python and Node; confirm the intended stack."
    if python_signals >= 3:
        reasons.append("Planning signals point to a Python project.")
        return "python", reasons, None
    if typescript_signals >= 3:
        reasons.append("Planning signals point to a TypeScript project.")
        return "node-ts", reasons, None
    if node_signals >= 3:
        reasons.append("Planning signals point to a JavaScript/Node project.")
        return "node-js", reasons, None

    reasons.append("No explicit stack was found; using a generic scaffold.")
    return "generic", reasons, None


def infer_repo_shape(root: Path, stack_profile: str, sources: list[PlanningSource]) -> str:
    if stack_profile == "monorepo":
        return "apps/packages"
    combined = "\n".join(source.content.lower() for source in sources)
    if (root / "apps").exists() and (root / "packages").exists():
        return "apps/packages"
    if "apps/" in combined and "packages/" in combined:
        return "apps/packages"
    return "single-project"


def desired_layout(
    *,
    root: Path,
    stack_profile: str,
    repo_shape: str,
    package_name: str,
    sources: list[PlanningSource],
) -> tuple[list[str], list[str]]:
    combined = "\n".join(source.content.lower() for source in sources)
    wants_root_src = repo_shape == "single-project" or "root src" in combined or "src/" in combined

    directories = ["docs", "tests"]
    if repo_shape == "apps/packages":
        directories.extend(["apps", "packages"])
        if wants_root_src:
            directories.append("src")
    else:
        directories.append("src")

    files = [".gitignore", "README.md", "codex.md", "devlog.md"]

    if stack_profile == "python":
        files.extend(["pyproject.toml", f"src/{package_name}/__init__.py", "tests/__init__.py"])
    elif stack_profile == "node-js":
        files.extend(["package.json", "src/index.js"])
    elif stack_profile == "node-ts":
        files.extend(["package.json", "tsconfig.json", "src/index.ts"])
    elif stack_profile == "bun-ts":
        files.extend(["package.json", "tsconfig.json", "src/index.ts"])

    if repo_shape == "apps/packages":
        files.extend(["apps/.gitkeep", "packages/.gitkeep"])
    if "docs" in directories:
        files.append("docs/.gitkeep")
    if "tests" in directories and stack_profile not in {"python"}:
        files.append("tests/.gitkeep")
    if "src" in directories and stack_profile not in {"python", "node-js", "node-ts", "bun-ts"}:
        files.append("src/.gitkeep")

    return dedupe(directories), dedupe(files)


def discover_existing_paths(root: Path) -> dict[str, list[str]]:
    directories = []
    files = []
    for child in sorted(root.iterdir(), key=lambda item: item.name.lower()):
        if child.name in IGNORED_DIRS:
            continue
        if child.is_dir():
            directories.append(child.name)
        else:
            files.append(child.name)
    return {"directories": directories, "files": files}


def classify_existing_path(path: Path) -> str:
    if not path.exists():
        return "create"
    if path.is_dir():
        return "keep_existing"
    content = read_text(path)
    if not content.strip():
        return "update_with_confirmation"
    if is_managed_file(path, content):
        return "update_with_confirmation"
    return "skip_user_owned"


def is_managed_file(path: Path, content: str) -> bool:
    if path.suffix in MARKDOWN_SUFFIXES and content.startswith(MARKDOWN_MARKER):
        return True
    if path.name == ".gitignore" and content.startswith(TEXT_MARKER):
        return True
    if path.suffix in {".py", ".js", ".ts", ".toml"}:
        return any(content.startswith(marker) for marker in CODE_MARKERS + (TEXT_MARKER,))
    return False


def render_file_content(relative_path: str, profile: dict[str, Any]) -> str:
    if relative_path == "README.md":
        return render_template("universal/README.md.tmpl", template_context(profile))
    if relative_path == "codex.md":
        return render_template("universal/codex.md.tmpl", template_context(profile))
    if relative_path == "devlog.md":
        return render_template("universal/devlog.md.tmpl", template_context(profile))
    if relative_path == ".gitignore":
        return render_gitignore(profile)
    if relative_path == "pyproject.toml":
        return render_template("python/pyproject.toml.tmpl", template_context(profile))
    if relative_path == f"src/{profile['package_name']}/__init__.py":
        return render_template("python/package_init.py.tmpl", template_context(profile))
    if relative_path == "tests/__init__.py":
        return render_template("python/tests_init.py.tmpl", template_context(profile))
    if relative_path == "package.json":
        stack = profile["stack_profile"]
        folder = "node-js" if stack == "node-js" else stack
        return render_template(f"{folder}/package.json.tmpl", template_context(profile))
    if relative_path == "tsconfig.json":
        return render_template(f"{profile['stack_profile']}/tsconfig.json.tmpl", template_context(profile))
    if relative_path == "src/index.js":
        return render_template("node-js/index.js.tmpl", template_context(profile))
    if relative_path == "src/index.ts":
        return render_template(f"{profile['stack_profile']}/index.ts.tmpl", template_context(profile))
    if relative_path == "docs/.gitkeep":
        return read_template("layout/docs.gitkeep")
    if relative_path == "src/.gitkeep":
        return read_template("layout/src.gitkeep")
    if relative_path == "tests/.gitkeep":
        return read_template("layout/tests.gitkeep")
    if relative_path == "apps/.gitkeep":
        return read_template("monorepo/apps.gitkeep")
    if relative_path == "packages/.gitkeep":
        return read_template("monorepo/packages.gitkeep")
    raise ValueError(f"Unsupported scaffold target: {relative_path}")


def render_gitignore(profile: dict[str, Any]) -> str:
    parts = [read_template("gitignore/base.txt").rstrip()]
    if profile["stack_profile"] == "python":
        parts.append(read_template("gitignore/python.txt").strip())
    if profile["stack_profile"] in {"node-js", "node-ts", "bun-ts"}:
        parts.append(read_template("gitignore/node.txt").strip())
    return "\n\n".join(part for part in parts if part) + "\n"


def template_context(profile: dict[str, Any]) -> dict[str, str]:
    planning_sources = profile["planning_sources"][:5]
    planning_lines = "\n".join(
        f"  - `{source['reference']}` - {source['title']}" for source in planning_sources
    ) or "  - No durable planning files were found."
    repo_map = render_repo_map(profile)
    verification = render_verification(profile)
    context_links = "\n".join(render_context_links(profile))
    starter_refs = "\n".join(render_starter_refs(profile))
    what_map = "\n".join(f"  - `{line}`" for line in render_codebase_map(profile))
    created_items = "\n".join(
        f"  - `{item}`" for item in profile["would_create"]
    ) or "  - No new files were required."
    return {
        "project_title": profile["project_name"],
        "project_slug": profile["project_slug"],
        "purpose": profile["purpose"],
        "purpose_short": profile["purpose_short"],
        "stack_profile": profile["stack_profile"],
        "stack_label": render_stack_label(profile["stack_profile"]),
        "repo_shape": profile["repo_shape"],
        "repo_shape_label": profile["repo_shape"],
        "planning_sources": planning_lines,
        "planning_references": planning_lines,
        "repo_map": repo_map,
        "getting_started_extra": render_getting_started_extra(profile),
        "verification": verification,
        "context_links": context_links,
        "what_map": what_map,
        "starter_references": starter_refs,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "created_items": created_items,
    }


def render_repo_map(profile: dict[str, Any]) -> str:
    lines = []
    for directory in profile["directories"]:
        lines.append(f"- `{directory['path']}/`")
    for file_spec in profile["files"]:
        if Path(file_spec["path"]).name.startswith(".gitkeep"):
            continue
        if file_spec["path"] in {"README.md", "codex.md", "devlog.md", ".gitignore"}:
            lines.append(f"- `{file_spec['path']}`")
    return "\n".join(lines)


def render_verification(profile: dict[str, Any]) -> str:
    stack = profile["stack_profile"]
    lines = []
    if stack == "python":
        lines.extend(["  - `pytest`", "  - `python -m pip check` after dependencies are installed"])
    elif stack == "node-js":
        lines.extend(["  - `npm test`", "  - `node src/index.js`"])
    elif stack == "node-ts":
        lines.extend(["  - `npm run typecheck`", "  - `npm run build`"])
    elif stack == "bun-ts":
        lines.extend(["  - `bun run typecheck`", "  - `bun test`"])
    elif stack == "monorepo":
        lines.extend(["  - Add workspace-specific verification commands once each app/package exists"])
    else:
        lines.extend(["  - Add the primary test, typecheck, and build commands once the runtime is chosen"])
    return "\n".join(lines)


def render_context_links(profile: dict[str, Any]) -> list[str]:
    lines = []
    if profile["stack_profile"] == "python":
        lines.append(f"- Python manifest: `pyproject.toml:1`")
    elif profile["stack_profile"] in {"node-js", "node-ts", "bun-ts"}:
        lines.append("- Runtime manifest: `package.json:1`")
    if profile["stack_profile"] in {"node-ts", "bun-ts"}:
        lines.append("- TypeScript config: `tsconfig.json:1`")
    return lines


def render_starter_refs(profile: dict[str, Any]) -> str:
    lines = ["- Starter references:"]
    lines.append("  - `README.md:1`")
    lines.append("  - `devlog.md:1`")
    if profile["stack_profile"] == "python":
        lines.append("  - `pyproject.toml:1`")
        lines.append(f"  - `src/{profile['package_name']}/__init__.py:1`")
    elif profile["stack_profile"] == "node-js":
        lines.append("  - `package.json:1`")
        lines.append("  - `src/index.js:1`")
    elif profile["stack_profile"] in {"node-ts", "bun-ts"}:
        lines.append("  - `package.json:1`")
        lines.append("  - `tsconfig.json:1`")
        lines.append("  - `src/index.ts:1`")
    elif profile["stack_profile"] == "monorepo":
        lines.append("  - `apps/:1`")
        lines.append("  - `packages/:1`")
    return "\n".join(lines)


def render_codebase_map(profile: dict[str, Any]) -> list[str]:
    lines = []
    for directory in profile["directories"]:
        lines.append(f"{directory['path']}/")
    for file_spec in profile["files"]:
        if file_spec["path"].endswith(".gitkeep"):
            continue
        lines.append(file_spec["path"])
    return lines[:12]


def render_getting_started_extra(profile: dict[str, Any]) -> str:
    stack = profile["stack_profile"]
    if stack == "python":
        return "- Create a virtual environment and install project dependencies once the package list is finalized."
    if stack in {"node-js", "node-ts"}:
        return "- Run `npm install` after you confirm the dependency strategy."
    if stack == "bun-ts":
        return "- Run `bun install` after you confirm the dependency strategy."
    if stack == "monorepo":
        return "- Add app and package manifests inside `apps/` and `packages/` as the workspace layout becomes concrete."
    return "- Finalize the runtime and dependency strategy before adding implementation-specific tooling."


def ensure_git_repo(root: Path) -> bool:
    if (root / ".git").exists():
        return False
    result = subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=str(root),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0:
        return True
    fallback = subprocess.run(
        ["git", "init"],
        cwd=str(root),
        capture_output=True,
        text=True,
        check=False,
    )
    if fallback.returncode != 0:
        return False
    subprocess.run(
        ["git", "branch", "-M", "main"],
        cwd=str(root),
        capture_output=True,
        text=True,
        check=False,
    )
    return True


def read_template(relative_path: str) -> str:
    return (TEMPLATE_ROOT / relative_path).read_text(encoding="utf-8")


def render_template(relative_path: str, values: dict[str, str]) -> str:
    template = Template(read_template(relative_path))
    return template.safe_substitute(values)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def extract_heading(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()
    return ""


def extract_summary(text: str) -> str:
    paragraphs = []
    current: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue
        if line.startswith(("#", "-", "*", "`")):
            continue
        current.append(line)
    if current:
        paragraphs.append(" ".join(current))
    for paragraph in paragraphs:
        normalized = normalize_sentence(paragraph)
        if normalized:
            return normalized
    return ""


def normalize_sentence(text: str) -> str:
    value = re.sub(r"\s+", " ", text).strip()
    return value


def is_vague_purpose(text: str) -> bool:
    lowered = normalize_sentence(text).lower()
    vague_phrases = (
        "something interesting",
        "something",
        "some kind of",
        "explore something",
        "need to explore",
        "ideas",
        "tbd",
    )
    if any(phrase in lowered for phrase in vague_phrases):
        return True
    words = [word for word in re.split(r"\W+", lowered) if word]
    return len(words) < 4


def shorten_text(text: str, limit: int) -> str:
    value = normalize_sentence(text)
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip() + "..."


def sanitize_project_name(value: str) -> str:
    cleaned = re.sub(r"\b(Codex Context|Project Guide|Development Log)\b", "", value, flags=re.I)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip(" -")
    return cleaned


def title_case_from_slug(value: str) -> str:
    tokens = re.split(r"[-_ ]+", value)
    return " ".join(token.capitalize() for token in tokens if token)


def slugify(value: str, separator: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9]+", separator, value.strip().lower())
    normalized = re.sub(fr"{re.escape(separator)}+", separator, normalized)
    return normalized.strip(separator) or "project"


def relpath(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered


def render_stack_label(stack: str) -> str:
    labels = {
        "python": "Python",
        "node-js": "Node.js (JavaScript)",
        "node-ts": "Node.js (TypeScript)",
        "bun-ts": "Bun (TypeScript)",
        "monorepo": "Monorepo workspace",
        "generic": "Generic / undecided",
    }
    return labels.get(stack, stack)


if __name__ == "__main__":
    raise SystemExit(main())
