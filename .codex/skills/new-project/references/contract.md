# `new-project` Contract

## Purpose

`new-project` bootstraps a new repo from planning material that already exists in the current directory or in the user's prompt.

It should:

- inspect before writing
- infer conservatively
- scaffold safely
- avoid dependency installation
- leave user-authored files untouched unless explicitly confirmed

## Planning Priority

Use planning inputs in this order:

1. user-provided project description
2. existing `codex.md`
3. `README.md`
4. `spec*.md`, `plan*.md`, `brief*.md`, `notes*.md`
5. `phase*_instructions.txt`
6. existing `CLAUDE.md` / `AGENTS.md`
7. existing manifests and folder structure

## Inference Rules

- Use an explicit stack or toolchain from planning material when present.
- Infer `monorepo` when the plan clearly implies `apps/` + `packages/` or workspace-style structure.
- If the stack is unclear but the project purpose is clear, use the `generic` profile.
- If the purpose or stack is materially ambiguous, stop and ask before scaffolding.

## Safe Bootstrap Rules

Always create when missing for single-project bootstraps:

- `.gitignore`
- `README.md`
- `codex.md`
- `devlog.md`
- `docs/`
- `src/`
- `tests/`

Conditional additions:

- Python: `pyproject.toml`, `src/<package_name>/__init__.py`, optional `tests/__init__.py`
- Node JS: `package.json`, `src/index.js`
- Node TS: `package.json`, `tsconfig.json`, `src/index.ts`
- Bun TS: `package.json`, `tsconfig.json`, `src/index.ts`
- Monorepo: `apps/`, `packages/`, root docs, and no root `src/` unless the planning material clearly calls for it

## Overwrite Policy

- Missing file: create
- Existing generated file: classify as `update_with_confirmation`
- Existing empty file: classify as `update_with_confirmation`
- Existing user-authored file: classify as `skip_user_owned`

Scaffolding is additive by default. Do not overwrite on a normal run.

## Generated File Expectations

`README.md`:

- project name
- short purpose
- intended stack/runtime
- repo map
- getting started
- verification commands
- references to planning sources or deeper docs

`codex.md`:

- under 300 lines
- uses `What`, `Why`, and `How`
- includes stack, structure, purpose, codebase map, and verification guidance

`devlog.md`:

- starts with a short header
- includes an initial bootstrap entry with date, inferred profile, and planning sources used

`.gitignore`:

- universal ignores
- stack-specific ignore layer when applicable

## Post-Scaffold Behavior

After writing `codex.md`, run `codex-context/scripts/context_files.py record-state` so drift tracking starts from the accepted scaffold.
