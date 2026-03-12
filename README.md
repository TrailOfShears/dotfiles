# Dotfiles

This repository backs up Codex environment customizations that live locally under `C:\Users\Jlockwood\.codex`.

## Contents

- `.codex/skills/` - local and customized Codex skills
- `.codex/AGENTS.md` - global Codex loader instructions
- `.codex/config.toml` - Codex configuration that matters across machines
- `scripts/sync-codex-backup.ps1` - mirror local Codex customizations into this repo
- `scripts/watch-codex-backup.ps1` - watch local Codex files and auto-sync changes
- `scripts/restore-codex-backup.ps1` - restore backed-up Codex files onto another machine

## Usage

Manual sync:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\sync-codex-backup.ps1 -Commit -Push
```

Manual restore:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\restore-codex-backup.ps1
```

The local startup launcher on this machine runs the watcher so future skill changes are mirrored here automatically.
