---
name: codex-context
description: Create, inspect, refresh, and maintain layered `codex.md` context files for Codex. Use when Codex needs to create a dev-root or project-root `codex.md`, refresh existing context after meaningful repo changes, inspect startup context loading, migrate durable context from `CLAUDE.md` or `ChatGPT.md`, or scaffold concise Codex context for a new project.
---

# Codex Context

## Overview

Use this skill to manage layered `codex.md` files that give Codex durable startup context.
It supports both the global dev-root layer and the active project layer without bloating either file.

## Workflow

1. Run `python codex-context/scripts/context_files.py status` to resolve the active dev root, git root, existing `codex.md` files, migration candidates, line counts, and drift state.
2. If you need facts for a draft or refresh, run:
   - `python codex-context/scripts/context_files.py snapshot --scope dev-root`
   - `python codex-context/scripts/context_files.py snapshot --scope project`
3. Read only the durable sources you need from the snapshot output before editing:
   - `README.md`
   - architecture, deployment, and runbook docs
   - manifests such as `pyproject.toml` and `package.json`
   - existing `CLAUDE.md`, `AGENTS.md`, or `ChatGPT.md` only as source material
4. Draft or refresh `codex.md` with the contract in [`codex-context/references/contract.md`](./references/contract.md).
5. After creating or updating a `codex.md`, record the accepted fingerprint with:

```powershell
python codex-context/scripts/context_files.py record-state
```

## Writing Rules

- Keep the dev-root `codex.md` under 100 lines.
- Keep the project `codex.md` under 300 lines.
- Use `What`, `Why`, and `How` for project files.
- Prefer `path/to/file:line` references over code snippets.
- Use progressive disclosure: point to deeper docs instead of copying task-specific detail into `codex.md`.
- Do not store code style guidelines in `codex.md`.
- Do not edit `CLAUDE.md` or `AGENTS.md` as part of routine `codex.md` refreshes.

## Refresh Triggers

Refresh a project `codex.md` when the user asks or when the snapshot shows meaningful structural drift such as:

- added or removed app/package roots
- new deployment surfaces or infrastructure docs
- build, test, or typecheck configuration changes
- major repo-structure changes
- new architecture or runbook docs that supersede current references

Do not refresh just because source files changed normally.

## Reference Map

- [`codex-context/references/contract.md`](./references/contract.md) for the line-budget and content contract.
- [`codex-context/scripts/context_files.py`](./scripts/context_files.py) for root resolution, snapshots, fingerprinting, and state recording.
