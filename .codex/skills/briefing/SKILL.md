---
name: briefing
description: inspect the current git repository and brief the user on recent project context by reading the dev log, related files, branch state, commits, and working tree status. use when the user asks for a briefing, asks what they were last working on, wants to resume a project, or needs a concise situation report before continuing. this skill is for context gathering and briefing only, not implementation.
---

# Briefing

Create a concise resume-ready briefing for the current git repository.

- Do not modify files, run write operations, or make commits as part of this skill.
- This skill is for inspection, context gathering, and briefing only.
- If the user also asks for implementation, stop after the briefing and wait for a separate follow-up request.
- When referring to this skill or its files, use paths relative to `.codex\skills`, such as `briefing/SKILL.md` or `briefing/scripts/briefing_context.py`.

## Workflow

1. Confirm the current directory is inside a git repository.
2. Run `scripts/briefing_context.py` from this skill to gather:
   - repo root
   - preferred dev log path
   - latest dev log section
   - files mentioned in that section that still exist
   - current branch
   - recent commits
   - current working tree status
3. Read the latest dev log entry first. Treat it as the primary signal for what the user was last working on.
4. Open the referenced files that seem most important to that entry.
5. If the entry mentions architecture, runbooks, tests, scripts, or specific source files, read those before briefing.
6. Write a short briefing with:
   - what the user was working on
   - what is already done
   - what appears to still be in progress
   - blockers or risks that are visible
   - 2 to 4 concrete suggestions for how to proceed next

## Response Shape

Prefer this structure:

```md
**Current Situation**
<2-4 sentence summary>

**What Looks Done**
- item
- item

**What Still Needs Attention**
- item
- item

**Suggested Next Steps**
1. step
2. step
3. step
```

## Guardrails

- Use the latest dev log entry as the main anchor unless the repo state clearly contradicts it.
- Prefer repository facts over speculation.
- Keep suggestions practical and near-term.
- Mention tests, deployments, approval steps, or environment setup when they are relevant to resuming work.
- If there is no dev log, fall back to recent commits and current working tree status.
- If the latest dev log entry references files that no longer exist, ignore them and continue with the remaining context.

## Commands

Collect context:

```powershell
python briefing/scripts/briefing_context.py
```
