param(
    [string]$SourceRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path,
    [string]$TargetRoot = $(
        if ($env:CODEX_HOME) {
            Join-Path $env:CODEX_HOME 'skills'
        }
        else {
            Join-Path $env:USERPROFILE '.codex\skills'
        }
    )
)

$skillNames = @(
    "aiui-to-ugui",
    "game-art-asset-pipeline",
    "game-feature-logic",
    "game-framework-toolchain"
)

New-Item -ItemType Directory -Path $TargetRoot -Force | Out-Null

foreach ($skillName in $skillNames) {
    $source = [System.IO.Path]::GetFullPath((Join-Path $SourceRoot $skillName))
    $target = [System.IO.Path]::GetFullPath((Join-Path $TargetRoot $skillName))

    if (-not (Test-Path -LiteralPath $source -PathType Container)) {
        throw "Missing skill source: $source"
    }

    if (-not (Test-Path -LiteralPath (Join-Path $source 'SKILL.md') -PathType Leaf)) {
        throw "Missing SKILL.md: $source"
    }

    if (Test-Path -LiteralPath $target) {
        $existing = Get-Item -LiteralPath $target -Force
        $existingTarget = if ($existing.LinkType) {
            [System.IO.Path]::GetFullPath([string]$existing.Target)
        }

        if ($existing.LinkType -and $existingTarget -eq $source) {
            Write-Host "Already linked $skillName -> $source"
            continue
        }

        throw "Install target already exists and was not changed: $target"
    }

    $link = New-Item -ItemType Junction -Path $target -Target $source
    Write-Host "Linked $skillName -> $($link.Target)"
}

Write-Host "Done. Restart Codex to refresh skill discovery."
