from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


HEADING_RE = re.compile(r"^##\s+(.+)$")
BACKTICK_PATH_RE = re.compile(r"`([^`]+)`")
MD_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def run_git(args: list[str], cwd: Path, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=check,
    )
    return result.stdout.strip()


def split_lines(text: str) -> list[str]:
    return [line for line in text.splitlines() if line.strip()]


def find_repo_root(start: Path) -> Path:
    root = run_git(["rev-parse", "--show-toplevel"], start)
    return Path(root)


def choose_devlog_path(repo_root: Path) -> Path | None:
    candidates = [
        repo_root / "devlog.md",
        repo_root / "docs" / "devlog.md",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def parse_latest_devlog_section(devlog_path: Path | None) -> dict[str, object]:
    if devlog_path is None or not devlog_path.exists():
        return {
            "title": "",
            "body": "",
            "lines": [],
        }

    lines = devlog_path.read_text(encoding="utf-8").splitlines()
    starts: list[int] = []
    for idx, line in enumerate(lines):
        if HEADING_RE.match(line):
            starts.append(idx)

    if not starts:
        body = "\n".join(lines).strip()
        return {
            "title": "",
            "body": body,
            "lines": lines,
        }

    start = starts[-1]
    end = len(lines)
    section_lines = lines[start:end]
    title_match = HEADING_RE.match(lines[start])
    title = title_match.group(1).strip() if title_match else ""
    body = "\n".join(section_lines[1:]).strip()
    return {
        "title": title,
        "body": body,
        "lines": section_lines,
    }


def extract_referenced_paths(section_text: str, repo_root: Path) -> list[str]:
    raw_candidates: list[str] = []
    raw_candidates.extend(BACKTICK_PATH_RE.findall(section_text))
    raw_candidates.extend(path for _, path in MD_LINK_RE.findall(section_text))

    resolved: list[str] = []
    seen: set[str] = set()
    for candidate in raw_candidates:
        if "://" in candidate:
            continue
        normalized = candidate.replace("/", "\\")
        path = repo_root / normalized
        if path.exists():
            path_str = str(path)
            if path_str not in seen:
                seen.add(path_str)
                resolved.append(path_str)
    return resolved


def main() -> int:
    start = Path.cwd()
    try:
        repo_root = find_repo_root(start)
    except subprocess.CalledProcessError:
        print("Not inside a git repository.", file=sys.stderr)
        return 1

    devlog_path = choose_devlog_path(repo_root)
    latest_section = parse_latest_devlog_section(devlog_path)
    section_text = "\n".join(latest_section["lines"]) if latest_section["lines"] else ""
    referenced_paths = extract_referenced_paths(section_text, repo_root)

    branch = run_git(["rev-parse", "--abbrev-ref", "HEAD"], repo_root)
    head = run_git(["rev-parse", "HEAD"], repo_root)
    recent_commits = split_lines(run_git(["log", "--format=%h %s", "-n", "8"], repo_root))
    status_lines = split_lines(run_git(["status", "--short"], repo_root))

    payload = {
        "repo_root": str(repo_root),
        "devlog_path": str(devlog_path) if devlog_path else "",
        "latest_devlog_entry": {
            "title": latest_section["title"],
            "body": latest_section["body"],
            "referenced_paths": referenced_paths,
        },
        "branch": branch,
        "head": head,
        "recent_commits": recent_commits,
        "working_tree_status": status_lines,
    }

    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
