param(
    [string]$SourceRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path,
    [string]$TargetRoot = "$env:USERPROFILE\.codex\skills"
)

$skillNames = @(
    "aiui-to-ugui",
    "ugui-feature-logic",
    "game-framework-toolchain"
)

New-Item -ItemType Directory -Path $TargetRoot -Force | Out-Null

foreach ($skillName in $skillNames) {
    $source = Join-Path $SourceRoot $skillName
    $target = Join-Path $TargetRoot $skillName

    if (-not (Test-Path $source)) {
        Write-Host "Skip missing skill: $skillName"
        continue
    }

    if (Test-Path $target) {
        Remove-Item -LiteralPath $target -Recurse -Force
    }

    Copy-Item -LiteralPath $source -Destination $target -Recurse
    Write-Host "Installed $skillName -> $target"
}

Write-Host "Done."
