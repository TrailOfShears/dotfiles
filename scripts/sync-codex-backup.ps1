param(
    [string]$SourceCodexHome = "$env:USERPROFILE\.codex",
    [string]$RepoRoot = (Split-Path -Parent $PSScriptRoot),
    [switch]$Commit,
    [switch]$Push
)

$ErrorActionPreference = "Stop"

function Ensure-Directory {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function Remove-IfExists {
    param([string]$Path)
    if (Test-Path -LiteralPath $Path) {
        Remove-Item -LiteralPath $Path -Recurse -Force
    }
}

function Copy-ManagedFile {
    param(
        [string]$SourcePath,
        [string]$DestinationPath
    )

    Ensure-Directory -Path (Split-Path -Parent $DestinationPath)
    if (Test-Path -LiteralPath $SourcePath) {
        Copy-Item -LiteralPath $SourcePath -Destination $DestinationPath -Force
    } elseif (Test-Path -LiteralPath $DestinationPath) {
        Remove-Item -LiteralPath $DestinationPath -Force
    }
}

function Invoke-RobocopyMirror {
    param(
        [string]$SourcePath,
        [string]$DestinationPath
    )

    Ensure-Directory -Path $DestinationPath
    $null = robocopy $SourcePath $DestinationPath /MIR /R:1 /W:1 /NFL /NDL /NJH /NJS /NP /XD __pycache__ /XF *.pyc
    if ($LASTEXITCODE -gt 7) {
        throw "robocopy failed with exit code $LASTEXITCODE"
    }
}

$sourceSkills = Join-Path $SourceCodexHome "skills"
$targetCodex = Join-Path $RepoRoot ".codex"
$targetSkills = Join-Path $targetCodex "skills"

if (-not (Test-Path -LiteralPath (Join-Path $RepoRoot ".git"))) {
    throw "RepoRoot is not a git repository: $RepoRoot"
}

Ensure-Directory -Path $targetCodex

if (-not (Test-Path -LiteralPath $sourceSkills)) {
    throw "Local Codex skills directory not found: $sourceSkills"
}

Invoke-RobocopyMirror -SourcePath $sourceSkills -DestinationPath $targetSkills
Get-ChildItem -LiteralPath $targetSkills -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue |
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -LiteralPath $targetSkills -Recurse -File -Filter "*.pyc" -ErrorAction SilentlyContinue |
    Remove-Item -Force -ErrorAction SilentlyContinue
Copy-ManagedFile -SourcePath (Join-Path $SourceCodexHome "AGENTS.md") -DestinationPath (Join-Path $targetCodex "AGENTS.md")
Copy-ManagedFile -SourcePath (Join-Path $SourceCodexHome "config.toml") -DestinationPath (Join-Path $targetCodex "config.toml")

$status = git -C $RepoRoot status --short -- .codex
$hasChanges = [bool]($status -join "")

if ($Commit -and $hasChanges) {
    git -C $RepoRoot add .codex
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    git -C $RepoRoot commit -m "backup: codex sync $timestamp"
    if ($Push) {
        git -C $RepoRoot push
    }
}

[pscustomobject]@{
    repo_root = $RepoRoot
    source_codex_home = $SourceCodexHome
    target_codex = $targetCodex
    changed = $hasChanges
    committed = [bool]($Commit -and $hasChanges)
    pushed = [bool]($Commit -and $Push -and $hasChanges)
} | ConvertTo-Json -Depth 4
