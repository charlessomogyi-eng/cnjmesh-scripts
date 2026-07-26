# pull-all-backups.ps1
#
# Pulls the most recent backup archive from ALL THREE CNJ Mesh Pis
# (cnjmesh1, cnjmesh2, cnjmesh3) into your OneDrive-synced Documents
# folder so they auto-upload to OneDrive.
#
# Usage:
#   Open PowerShell, cd to where this script lives, then run:
#     .\pull-all-backups.ps1
#
# You'll be prompted for each Pi's password (unless you've set up SSH keys).
#
# Pairs with the git repo: git holds configs/scripts/install-maps/runbook;
# these archives hold the secrets + databases + container run-state.
# Together = full disaster recovery.

$ErrorActionPreference = "Stop"

# --- Per-Pi settings: user@ip, remote backup dir, filename prefix ---
$Pis = @(
    @{ Name = "cnjmesh1"; Host = "somog@10.0.0.181";    Dir = "/home/somog/backups";    Prefix = "cnjmesh1-backup" },
    @{ Name = "cnjmesh2"; Host = "somogyic@10.0.0.91"; Dir = "/home/somogyic/backups"; Prefix = "cnjmesh2-backup" },  # <-- set cnjmesh2 IP
    @{ Name = "cnjmesh3"; Host = "somog@10.0.0.186";    Dir = "/home/somog/backups";    Prefix = "cnjmesh3-backup" }
)

# Adjust if your Documents folder isn't the default OneDrive location
$LocalDir = "$env:USERPROFILE\OneDrive\Documents\cnjmesh-backups"

if (-not (Test-Path $LocalDir)) {
    New-Item -ItemType Directory -Path $LocalDir | Out-Null
    Write-Host "Created local backup folder: $LocalDir"
}

$results = @()

foreach ($pi in $Pis) {
    $name   = $pi.Name
    $piHost = $pi.Host
    $dir    = $pi.Dir
    $prefix = $pi.Prefix

    Write-Host ""
    Write-Host "=== $name ===" -ForegroundColor Cyan

    if ($piHost -match "XXX") {
        Write-Host "  SKIPPED - set $name's IP in the script first (placeholder still present)." -ForegroundColor Yellow
        $results += "$name : SKIPPED (IP not set)"
        continue
    }

    try {
        Write-Host "  Finding latest backup on $name..."
        $latestFile = ssh $piHost "ls -t $dir/$prefix-*.tar.gz 2>/dev/null | head -1"

        if ([string]::IsNullOrWhiteSpace($latestFile)) {
            Write-Host "  No backup files found on $name in $dir" -ForegroundColor Yellow
            $results += "$name : NO BACKUP FOUND"
            continue
        }

        $latestFile = $latestFile.Trim()
        $fileName   = Split-Path $latestFile -Leaf
        $localPath  = Join-Path $LocalDir $fileName

        if (Test-Path $localPath) {
            Write-Host "  Already have latest locally: $fileName"
            $results += "$name : up to date ($fileName)"
            continue
        }

        Write-Host "  Pulling $fileName ..."
        scp "${piHost}:${latestFile}" "$localPath"

        if (Test-Path $localPath) {
            Write-Host "  Success -> $localPath" -ForegroundColor Green
            $results += "$name : pulled $fileName"
        } else {
            Write-Host "  FAILED - file not found locally after scp" -ForegroundColor Red
            $results += "$name : TRANSFER FAILED"
        }
    }
    catch {
        Write-Host "  ERROR: $_" -ForegroundColor Red
        $results += "$name : ERROR ($_)"
    }
}

Write-Host ""
Write-Host "=========== Summary ===========" -ForegroundColor Cyan
$results | ForEach-Object { Write-Host "  $_" }
Write-Host ""
Write-Host "Files are in: $LocalDir"
Write-Host "OneDrive will sync them automatically."
Read-Host "Press Enter to close"
