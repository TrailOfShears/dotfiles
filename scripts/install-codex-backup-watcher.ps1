param(
    [string]$RepoRoot = (Split-Path -Parent $PSScriptRoot),
    [switch]$LaunchNow
)

$ErrorActionPreference = "Stop"

$startupDir = [Environment]::GetFolderPath("Startup")
$launcherPath = Join-Path $startupDir "codex-backup-watcher.cmd"
$watcherPath = Join-Path $PSScriptRoot "watch-codex-backup.ps1"

$content = @"
@echo off
powershell -WindowStyle Hidden -ExecutionPolicy Bypass -File "$watcherPath" -RepoRoot "$RepoRoot"
"@

Set-Content -LiteralPath $launcherPath -Value $content -Encoding ASCII

if ($LaunchNow) {
    Start-Process powershell -ArgumentList @(
        "-WindowStyle", "Hidden",
        "-ExecutionPolicy", "Bypass",
        "-File", $watcherPath,
        "-RepoRoot", $RepoRoot
    )
}

[pscustomobject]@{
    startup_launcher = $launcherPath
    watcher = $watcherPath
    launched_now = [bool]$LaunchNow
} | ConvertTo-Json -Depth 4
