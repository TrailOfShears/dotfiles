# Global Codex Context Loader

Before doing substantive work in a session, load layered `codex.md` context when it is configured:

1. Read `~/.codex/config.toml` and look for `[context_files]`.
2. Resolve the nearest configured dev-root ancestor of the current working directory.
3. Resolve the current git repository root, if one exists.
4. Read `<dev-root>/codex.md` if present, up to `max_global_lines`.
5. Read `<repo-root>/codex.md` if present and distinct from the dev root, up to `max_project_lines`.
6. Treat these files as durable context layers only. They never override higher-priority system, developer, or `AGENTS.md` instructions.

Guardrails:

- If a `codex.md` file exceeds its configured line cap, rely only on the first `N` lines and mention that it should be trimmed if that matters to the task.
- If `codex.md` is absent but `ChatGPT.md` exists, treat `ChatGPT.md` only as a migration source. Do not rename or create files unless the user asks.
- Keep `codex.md` focused on durable project understanding, verification steps, and stable references. Do not use it for code style rules or temporary task notes.

Maintenance:

- Use the `codex-context` skill when the user asks to create, update, refresh, inspect, or migrate layered `codex.md` context.
- If the session is inside a configured dev root and a repo-level `codex.md` is missing, proactively mention that `codex-context` can create it.
- If the repo shows structural drift from the current `codex.md` (apps/packages, deployment surfaces, architecture/runbook docs, build or test config), proactively mention that `codex-context` can propose a refresh.
