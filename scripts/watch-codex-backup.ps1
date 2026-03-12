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

$relevantRootFiles = @("AGENTS.md", "config.toml")

if (-not (Test-Path -LiteralPath $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

$script:Pending = $true
$script:LastEventAt = Get-Date
$script:InstanceMutex = $null
$script:OwnsMutex = $false

function Write-Log {
    param([string]$Message)
    $line = "{0} {1}" -f (Get-Date -Format "s"), $Message
    Add-Content -LiteralPath $logPath -Value $line
}

function Test-RelevantEvent {
    param([object]$EventRecord)

    $isRootEvent = $EventRecord.SourceIdentifier -like "codex.root.*"
    $name = $EventRecord.SourceEventArgs.Name
    return ((-not $isRootEvent) -or ($name -in $relevantRootFiles))
}

function Update-PendingFromEvent {
    param([object]$EventRecord)

    if (Test-RelevantEvent -EventRecord $EventRecord) {
        $script:Pending = $true
        $script:LastEventAt = Get-Date
    }
}

function Drain-QueuedEvents {
    while ($true) {
        $queuedEvent = Get-Event -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($null -eq $queuedEvent) {
            break
        }

        Update-PendingFromEvent -EventRecord $queuedEvent
        Remove-Event -EventIdentifier $queuedEvent.EventIdentifier -ErrorAction SilentlyContinue
    }
}

$createdNew = $false
$script:InstanceMutex = New-Object System.Threading.Mutex($true, "Global\CodexBackupWatcher", [ref]$createdNew)
$script:OwnsMutex = $createdNew

if (-not $script:OwnsMutex) {
    Write-Log "Watcher already running for $SourceCodexHome; exiting duplicate instance"
    $script:InstanceMutex.Dispose()
    $script:InstanceMutex = $null
    return
}

$skillsWatcher = New-Object System.IO.FileSystemWatcher $skillsPath, "*"
$skillsWatcher.IncludeSubdirectories = $true
$skillsWatcher.EnableRaisingEvents = $true

$rootWatcher = New-Object System.IO.FileSystemWatcher $rootPath, "*"
$rootWatcher.IncludeSubdirectories = $false
$rootWatcher.EnableRaisingEvents = $true

$handlers = @()
$handlers += Register-ObjectEvent -InputObject $skillsWatcher -EventName Changed -SourceIdentifier "codex.skills.changed"
$handlers += Register-ObjectEvent -InputObject $skillsWatcher -EventName Created -SourceIdentifier "codex.skills.created"
$handlers += Register-ObjectEvent -InputObject $skillsWatcher -EventName Deleted -SourceIdentifier "codex.skills.deleted"
$handlers += Register-ObjectEvent -InputObject $skillsWatcher -EventName Renamed -SourceIdentifier "codex.skills.renamed"
$handlers += Register-ObjectEvent -InputObject $rootWatcher -EventName Changed -SourceIdentifier "codex.root.changed"
$handlers += Register-ObjectEvent -InputObject $rootWatcher -EventName Created -SourceIdentifier "codex.root.created"
$handlers += Register-ObjectEvent -InputObject $rootWatcher -EventName Deleted -SourceIdentifier "codex.root.deleted"
$handlers += Register-ObjectEvent -InputObject $rootWatcher -EventName Renamed -SourceIdentifier "codex.root.renamed"

Write-Log "Watcher started for $SourceCodexHome"

try {
    while ($true) {
        $event = Wait-Event -Timeout 1
        if ($null -ne $event) {
            Update-PendingFromEvent -EventRecord $event
            Remove-Event -EventIdentifier $event.EventIdentifier -ErrorAction SilentlyContinue
        }

        Drain-QueuedEvents

        if (-not $script:Pending) {
            continue
        }

        $age = (Get-Date) - $script:LastEventAt
        if ($age.TotalSeconds -lt $DebounceSeconds) {
            continue
        }

        Drain-QueuedEvents
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
    if ($script:OwnsMutex -and $null -ne $script:InstanceMutex) {
        $script:InstanceMutex.ReleaseMutex()
        $script:InstanceMutex.Dispose()
    }
    Write-Log "Watcher stopped"
}
