param(
    [string]$RepoRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$TargetCodexHome = "$env:USERPROFILE\.codex"
)

$ErrorActionPreference = "Stop"

function Ensure-Directory {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function Restore-ManagedFile {
    param(
        [string]$SourcePath,
        [string]$DestinationPath
    )

    if (-not (Test-Path -LiteralPath $SourcePath)) {
        return
    }

    Ensure-Directory -Path (Split-Path -Parent $DestinationPath)
    Copy-Item -LiteralPath $SourcePath -Destination $DestinationPath -Force
}

function Invoke-RobocopyMirror {
    param(
        [string]$SourcePath,
        [string]$DestinationPath
    )

    if (-not (Test-Path -LiteralPath $SourcePath)) {
        return
    }

    Ensure-Directory -Path $DestinationPath
    $null = robocopy $SourcePath $DestinationPath /MIR /R:1 /W:1 /NFL /NDL /NJH /NJS /NP
    if ($LASTEXITCODE -gt 7) {
        throw "robocopy failed with exit code $LASTEXITCODE"
    }
}

$sourceCodex = Join-Path $RepoRoot ".codex"

Invoke-RobocopyMirror -SourcePath (Join-Path $sourceCodex "skills") -DestinationPath (Join-Path $TargetCodexHome "skills")
Restore-ManagedFile -SourcePath (Join-Path $sourceCodex "AGENTS.md") -DestinationPath (Join-Path $TargetCodexHome "AGENTS.md")
Restore-ManagedFile -SourcePath (Join-Path $sourceCodex "config.toml") -DestinationPath (Join-Path $TargetCodexHome "config.toml")

[pscustomobject]@{
    repo_root = $RepoRoot
    target_codex_home = $TargetCodexHome
    restored = $true
} | ConvertTo-Json -Depth 4
