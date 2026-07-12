# pull-cnjmesh1-backup.ps1
#
# Pulls the most recent cnjmesh1 backup archive to your local
# OneDrive-synced Documents folder so it auto-uploads to OneDrive.
#
# Usage:
#   Open PowerShell, cd to where this script lives, then run:
#     .\pull-cnjmesh1-backup.ps1
#
# You will be prompted for the cnjmesh1 (somog) password.

$ErrorActionPreference = "Stop"

$PiHost   = "somog@10.0.0.181"
$RemoteDir = "/home/somog/backups"
# Adjust this path if your Documents folder isn't the default OneDrive location
$LocalDir = "$env:USERPROFILE\OneDrive\Documents\cnjmesh-backups"

if (-not (Test-Path $LocalDir)) {
    New-Item -ItemType Directory -Path $LocalDir | Out-Null
    Write-Host "Created local backup folder: $LocalDir"
}

Write-Host "Finding latest backup on cnjmesh1..."

# Ask the Pi for the newest backup filename
$latestFile = ssh $PiHost "ls -t $RemoteDir/cnjmesh1-backup-*.tar.gz | head -1"

if ([string]::IsNullOrWhiteSpace($latestFile)) {
    Write-Error "No backup files found on cnjmesh1 in $RemoteDir"
    Read-Host "Press Enter to close"
    exit 1
}

$latestFile = $latestFile.Trim()
$fileName = Split-Path $latestFile -Leaf
$localPath = Join-Path $LocalDir $fileName

if (Test-Path $localPath) {
    Write-Host "Already have the latest backup locally: $fileName"
    Write-Host "Nothing to do."
    Read-Host "Press Enter to close"
    exit 0
}

Write-Host "Pulling $fileName ..."
scp "${PiHost}:${latestFile}" "$localPath"

if (Test-Path $localPath) {
    Write-Host "=== Success ==="
    Write-Host "Saved to: $localPath"
    Write-Host "OneDrive will sync it automatically."
} else {
    Write-Error "Transfer appears to have failed - file not found at $localPath"
    Read-Host "Press Enter to close"
    exit 1
}

Read-Host "Press Enter to close"
