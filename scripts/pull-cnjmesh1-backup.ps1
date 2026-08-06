# pull-cnjmesh1-backup.ps1
#
# Pulls the most recent backup archive from cnjmesh1 AND cnjmesh3 to your
# local OneDrive-synced Documents folder so it auto-uploads to OneDrive.
# (cnjmesh2 intentionally excluded - Pi Zero 2W, recovers from git config instead)
#
# As of Aug 6 2026, cnjmesh1's archive includes Malla + CoreScope DB snapshots
# and an aprs-tnc-web MySQL dump, so the archive is multi-GB (Malla's DB alone
# is ~2.3GB). Expect the pull to take a while on a slower connection - this
# script now shows the remote file size and elapsed transfer time.
#
# Usage:
#   Open PowerShell, cd to where this script lives, then run:
#     .\pull-cnjmesh1-backup.ps1
#
# You will be prompted for each Pi's password.

$ErrorActionPreference = "Stop"

$Pis = @(
    @{ Name = "cnjmesh1"; Host = "somog@10.0.0.181"; Dir = "/home/somog/backups"; Prefix = "cnjmesh1-backup" },
    @{ Name = "cnjmesh3"; Host = "somog@10.0.0.186"; Dir = "/home/somog/backups"; Prefix = "cnjmesh3-backup" }
)

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

        $remoteSize = ssh $piHost "du -h '$latestFile' 2>/dev/null | cut -f1"
        $remoteSize = $remoteSize.Trim()
        Write-Host "  Pulling $fileName ($remoteSize) ..."
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        scp "${piHost}:${latestFile}" "$localPath"
        $sw.Stop()

        if (Test-Path $localPath) {
            $elapsed = [math]::Round($sw.Elapsed.TotalSeconds, 1)
            Write-Host "  Success -> $localPath ($remoteSize in ${elapsed}s)" -ForegroundColor Green
            $results += "$name : pulled $fileName ($remoteSize)"
        } else {
            Write-Host "  FAILED" -ForegroundColor Red
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
Read-Host "Press Enter to close"
