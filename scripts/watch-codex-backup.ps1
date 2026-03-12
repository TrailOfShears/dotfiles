param(
    [string]$SourceCodexHome = "$env:USERPROFILE\.codex",
    [string]$RepoRoot = (Split-Path -Parent $PSScriptRoot),
    [int]$DebounceSeconds = 3
)

$ErrorActionPreference = "Stop"

$logDir = Join-Path $env:LOCALAPPDATA "CodexBackup"
$logPath = Join-Path $logDir "watcher.log"
$syncScript = Join-Path $PSScriptRoot "sync-codex-backup.ps1"
$skillsPath = Join-Path $SourceCodexHome "skills"
$rootPath = $SourceCodexHome

if (-not (Test-Path -LiteralPath $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

$script:Pending = $true
$script:LastEventAt = Get-Date

function Write-Log {
    param([string]$Message)
    $line = "{0} {1}" -f (Get-Date -Format "s"), $Message
    Add-Content -LiteralPath $logPath -Value $line
}

function Mark-Pending {
    $script:Pending = $true
    $script:LastEventAt = Get-Date
}

$skillsWatcher = New-Object System.IO.FileSystemWatcher $skillsPath, "*"
$skillsWatcher.IncludeSubdirectories = $true
$skillsWatcher.EnableRaisingEvents = $true

$rootWatcher = New-Object System.IO.FileSystemWatcher $rootPath, "*"
$rootWatcher.IncludeSubdirectories = $false
$rootWatcher.EnableRaisingEvents = $true

$handlers = @(
    Register-ObjectEvent $skillsWatcher Changed -Action { Mark-Pending } ,
    Register-ObjectEvent $skillsWatcher Created -Action { Mark-Pending } ,
    Register-ObjectEvent $skillsWatcher Deleted -Action { Mark-Pending } ,
    Register-ObjectEvent $skillsWatcher Renamed -Action { Mark-Pending } ,
    Register-ObjectEvent $rootWatcher Changed -Action {
        if ($Event.SourceEventArgs.Name -in @("AGENTS.md", "config.toml")) { Mark-Pending }
    },
    Register-ObjectEvent $rootWatcher Created -Action {
        if ($Event.SourceEventArgs.Name -in @("AGENTS.md", "config.toml")) { Mark-Pending }
    },
    Register-ObjectEvent $rootWatcher Renamed -Action {
        if ($Event.SourceEventArgs.Name -in @("AGENTS.md", "config.toml")) { Mark-Pending }
    },
    Register-ObjectEvent $rootWatcher Deleted -Action {
        if ($Event.SourceEventArgs.Name -in @("AGENTS.md", "config.toml")) { Mark-Pending }
    }
)

Write-Log "Watcher started for $SourceCodexHome"

try {
    while ($true) {
        Start-Sleep -Seconds 1
        if (-not $script:Pending) {
            continue
        }

        $age = (Get-Date) - $script:LastEventAt
        if ($age.TotalSeconds -lt $DebounceSeconds) {
            continue
        }

        $script:Pending = $false
        try {
            $output = powershell -ExecutionPolicy Bypass -File $syncScript -SourceCodexHome $SourceCodexHome -RepoRoot $RepoRoot -Commit -Push
            Write-Log "Sync completed: $output"
        } catch {
            Write-Log "Sync failed: $($_.Exception.Message)"
        }
    }
} finally {
    foreach ($handler in $handlers) {
        Unregister-Event -SourceIdentifier $handler.Name -ErrorAction SilentlyContinue
    }
    $skillsWatcher.Dispose()
    $rootWatcher.Dispose()
    Write-Log "Watcher stopped"
}
