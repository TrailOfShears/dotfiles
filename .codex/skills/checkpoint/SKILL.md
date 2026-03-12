---
name: checkpoint
description: Create a git checkpoint for the current repository. Use when the user asks to checkpoint progress, save work, push current changes, update a dev log, or capture a summary of what was accomplished since the last checkpoint. This skill should append a concise entry to a repo dev log, commit with a `checkpoint:` message, and push the current branch.
---

# Checkpoint

Create a durable progress snapshot for the current git repository.

- When referring to this skill or its files, use paths relative to `.codex\skills`, such as `checkpoint/SKILL.md` or `checkpoint/scripts/checkpoint_context.py`.

## Workflow

1. Confirm the working directory is inside a git repository.
2. Run `scripts/checkpoint_context.py` from this skill to gather:
   - repo root
   - current branch
   - preferred dev log path
   - last checkpoint commit
   - commits and file changes since the last checkpoint
   - current working tree status
3. Review the collected context and write a short, high-signal summary of what was accomplished since the last checkpoint.
4. Create or update the dev log file:
   - prefer an existing `devlog.md` in the repo root
   - otherwise prefer `docs/devlog.md`
   - otherwise create `devlog.md` in the repo root
5. Append one new entry in this format:

```md
## 2026-03-10 16:30 - Checkpoint

- Branch: `feature-or-current-branch`
- Since: `last-checkpoint-hash` or `start of branch`
- Accomplished:
  - item
  - item
  - item
- Notes:
  - blockers, risks, follow-up items if relevant
```

6. Stage the dev log update and the rest of the current repository changes.
7. Commit with message format:

```text
checkpoint: <very short summary>
```

8. Push the current branch:
   - use the existing upstream if it exists
   - otherwise set upstream with `git push -u origin <branch>` when `origin` exists
9. Report:
   - dev log path
   - new commit hash
   - push result

## Guardrails

- Do not use this skill outside a git repository.
- Do not checkpoint with unresolved merge conflicts, rebase state, or cherry-pick state.
- Keep the dev log summary focused on changes since the last checkpoint, not the whole project history.
- Prefer concrete outcomes over low-signal file lists.
- Mention important tests run, migrations applied, or operational setup completed when relevant.
- If there are no meaningful changes since the last checkpoint, say so instead of creating a noisy entry.

## Commands

Collect context:

```powershell
python checkpoint/scripts/checkpoint_context.py
```

Typical git sequence after updating the dev log:

```powershell
git add .
git commit -m "checkpoint: short summary"
git push
```

If no upstream exists:

```powershell
git push -u origin <branch>
```
