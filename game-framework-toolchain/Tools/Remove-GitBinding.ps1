#Requires -Version 5.1
<#
.SYNOPSIS
  Remove all Git metadata from this toolkit directory.

.NOTES
  Close Cursor (or any app using this folder as a Git repo) before running,
  otherwise .git\cursor\crepe\index.bin may stay locked.
#>
$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
$gitDir = Join-Path $root ".git"

Write-Host "Removing Git binding from: $root" -ForegroundColor Cyan

if (Test-Path (Join-Path $root ".gitignore")) {
    Remove-Item (Join-Path $root ".gitignore") -Force
    Write-Host "Removed .gitignore"
}

if (Test-Path $gitDir) {
    try {
        Remove-Item $gitDir -Recurse -Force
        Write-Host "Removed .git"
    }
    catch {
        Write-Host "Could not remove .git (files locked). Close Cursor and run this script again." -ForegroundColor Yellow
        Write-Host $_.Exception.Message
        exit 1
    }
}
else {
    Write-Host ".git already absent"
}

Write-Host "Done. This folder is no longer a Git repository." -ForegroundColor Green
