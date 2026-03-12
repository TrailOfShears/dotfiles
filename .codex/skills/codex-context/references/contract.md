# `codex.md` Contract

## Purpose

`codex.md` is a durable startup-context layer for Codex. It should help Codex understand the workspace quickly without replacing live repo inspection.

## Dev-Root File

- Filename: `codex.md`
- Location: configured dev root
- Line budget: under 100 lines
- Include:
  - global working preferences
  - verification habits
  - high-level workspace map
  - reusable conventions that apply across projects
- Exclude:
  - project-specific architecture
  - code style rules
  - temporary task notes

## Project File

- Filename: `codex.md`
- Location: git repo root
- Line budget: under 300 lines
- Default structure:
  - `## What`
  - `## Why`
  - `## How`
- Include:
  - tech overview
  - stack
  - project structure and codebase map
  - apps and shared packages
  - project purpose
  - subsystem roles
  - verification commands
  - test, typecheck, and build references
- Exclude:
  - code style rules
  - narrow task instructions
  - long snippets copied from source files

## Progressive Disclosure

- If context is task-specific, move it to a separate markdown doc in an appropriate repo folder and reference it from `codex.md`.
- Prefer `path/to/file:line` references over pasted snippets.
- Prefer stable docs and manifests over dev-log summaries.

## Update Policy

Refresh on:

- explicit user request
- added or removed app/package roots
- deployment or infrastructure surface changes
- changed test/build/typecheck configuration
- major structure changes
- new architecture or runbook docs that supersede current references

Do not refresh on routine code churn alone.
