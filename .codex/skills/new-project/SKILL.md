---
name: new-project
description: Safely bootstrap a new development project from the current directory's planning material and any user-provided context. Use when Codex needs to inspect plans, infer the stack and repo shape, initialize git, create universal starter files such as `README.md`, `codex.md`, `devlog.md`, and `.gitignore`, or scaffold a minimal stack-aware project layout without installing dependencies.
---

# New Project

## Overview

Use this skill to turn planning material into a safe initial project scaffold.
It inspects the current directory first, asks for confirmation when key details are unclear, and writes only additive bootstrap files by default.

## Workflow

1. Run `python new-project/scripts/project_bootstrap.py inspect` first.
2. If the user already described the project in the prompt, pass that context through `--user-context`.
3. Review the emitted profile:
   - project name
   - short purpose
   - stack profile
   - repo shape
   - planning sources used
   - ambiguities
   - files and directories that would be created
   - overwrite classifications for existing files
4. If `ambiguities` is non-empty, stop and confirm with the user before scaffolding.
5. If the profile is ready, run `python new-project/scripts/project_bootstrap.py scaffold`.
6. After scaffolding, summarize:
   - files created
   - files skipped because they already existed
   - whether git was initialized
   - whether `codex-context` state was recorded

## Commands

Inspect the current directory:

```powershell
python new-project/scripts/project_bootstrap.py inspect
```

Inspect with user-supplied context:

```powershell
python new-project/scripts/project_bootstrap.py inspect --user-context "Build a Python CLI for ..."
```

Scaffold when the profile is ready:

```powershell
python new-project/scripts/project_bootstrap.py scaffold
```

## Guardrails

- Treat this as a safe bootstrap skill, not a dependency installer.
- Initialize git when `.git` is missing, but do not create commits automatically.
- Never overwrite an existing user-authored file without confirmation.
- Use existing planning material before guessing.
- If the planning signal is weak, ask for confirmation instead of silently choosing the wrong stack.
- Reuse the `codex.md` contract from [`codex-context/references/contract.md`](../codex-context/references/contract.md).

## Supported Profiles

- `python`
- `node-js`
- `node-ts`
- `bun-ts`
- `monorepo`
- `generic`

## Reference Map

- [`new-project/references/contract.md`](./references/contract.md) for planning priority, overwrite policy, and generated-file expectations.
- [`new-project/scripts/project_bootstrap.py`](./scripts/project_bootstrap.py) for inspection, inference, and scaffolding.
- [`codex-context/references/contract.md`](../codex-context/references/contract.md) for the shared `codex.md` contract.
