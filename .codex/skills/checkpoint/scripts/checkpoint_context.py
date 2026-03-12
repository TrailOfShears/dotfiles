from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def run_git(args: list[str], cwd: Path) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def try_git(args: list[str], cwd: Path) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def find_repo_root(start: Path) -> Path:
    root = run_git(["rev-parse", "--show-toplevel"], start)
    return Path(root)


def choose_devlog_path(repo_root: Path) -> Path:
    candidates = [
        repo_root / "devlog.md",
        repo_root / "docs" / "devlog.md",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return repo_root / "devlog.md"


def split_lines(text: str) -> list[str]:
    return [line for line in text.splitlines() if line.strip()]


def optional_range_args(revision_range: str) -> list[str]:
    return [revision_range] if revision_range else []


def main() -> int:
    start = Path.cwd()
    try:
        repo_root = find_repo_root(start)
    except subprocess.CalledProcessError:
        print("Not inside a git repository.", file=sys.stderr)
        return 1

    branch = run_git(["rev-parse", "--abbrev-ref", "HEAD"], repo_root)
    head = run_git(["rev-parse", "HEAD"], repo_root)
    upstream = try_git(["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"], repo_root)

    last_checkpoint_hash = try_git(
        ["log", "--grep=^checkpoint:", "--format=%H", "-n", "1"],
        repo_root,
    )
    last_checkpoint_subject = ""
    if last_checkpoint_hash:
        last_checkpoint_subject = try_git(
            ["log", "--format=%s", "-n", "1", last_checkpoint_hash],
            repo_root,
        )

    comparison_base = {
        "kind": "checkpoint" if last_checkpoint_hash else "worktree",
        "hash": last_checkpoint_hash,
        "label": last_checkpoint_subject or "",
    }

    revision_range = ""
    if last_checkpoint_hash:
        revision_range = f"{last_checkpoint_hash}..HEAD"
    elif upstream:
        merge_base = try_git(["merge-base", "HEAD", upstream], repo_root)
        if merge_base and merge_base != head:
            comparison_base = {
                "kind": "merge-base",
                "hash": merge_base,
                "label": f"merge-base with {upstream}",
            }
            revision_range = f"{merge_base}..HEAD"

    commit_lines: list[str] = []
    if revision_range:
        commit_lines = split_lines(
            try_git(
                ["log", "--format=%h %s", revision_range],
                repo_root,
            )
        )
    status_lines = split_lines(run_git(["status", "--short"], repo_root))
    changed_files = split_lines(
        try_git(
            ["diff", "--name-only", *optional_range_args(revision_range)],
            repo_root,
        )
    )
    if not changed_files:
        changed_files = split_lines(try_git(["diff", "--name-only"], repo_root))

    merge_head = (repo_root / ".git" / "MERGE_HEAD").exists()
    rebase_merge = (repo_root / ".git" / "rebase-merge").exists()
    rebase_apply = (repo_root / ".git" / "rebase-apply").exists()
    cherry_pick_head = (repo_root / ".git" / "CHERRY_PICK_HEAD").exists()

    payload = {
        "repo_root": str(repo_root),
        "branch": branch,
        "head": head,
        "upstream": upstream,
        "devlog_path": str(choose_devlog_path(repo_root)),
        "comparison_base": comparison_base,
        "last_checkpoint": {
            "hash": last_checkpoint_hash,
            "subject": last_checkpoint_subject,
        },
        "revision_range": revision_range or "worktree only",
        "commits_since_last_checkpoint": commit_lines,
        "changed_files_since_last_checkpoint": changed_files,
        "working_tree_status": status_lines,
        "blocked_state": {
            "merge": merge_head,
            "rebase": rebase_merge or rebase_apply,
            "cherry_pick": cherry_pick_head,
        },
    }

    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
