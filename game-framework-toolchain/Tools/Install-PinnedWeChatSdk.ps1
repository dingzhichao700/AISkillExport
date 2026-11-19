#Requires -Version 5.1
param([Parameter(Mandatory=$true)][string]$UpstreamPackagePath)
$ErrorActionPreference = 'Stop'
$toolRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$pinRoot = Join-Path $toolRoot 'ThirdParty/WeChatSDK/d288776c50-background-r1'
$target = Join-Path $pinRoot 'Package'
$source = (Resolve-Path -LiteralPath $UpstreamPackagePath).Path
$manifest = Get-Content -LiteralPath (Join-Path $pinRoot 'upstream-files.json') -Raw | ConvertFrom-Json
$patch = Get-Content -LiteralPath (Join-Path $pinRoot 'patch-manifest.json') -Raw | ConvertFrom-Json
if ($manifest.upstreamRevision -ne $patch.upstreamRevision) { throw 'SDK revision mismatch' }
$change = $patch.changes[0]
$patchedFile = Join-Path $pinRoot 'WXConvertCore.cs.patched'
if ((Get-FileHash -LiteralPath $patchedFile -Algorithm SHA256).Hash -ne $change.candidateSha256) { throw 'Patch hash mismatch' }
$rootPrefix = $source.TrimEnd('\','/') + [IO.Path]::DirectorySeparatorChar
foreach ($entry in $manifest.files.PSObject.Properties) {
    $file = [IO.Path]::GetFullPath((Join-Path $source $entry.Name))
    if (-not $file.StartsWith($rootPrefix, [StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe SDK manifest path' }
    if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { throw "Missing SDK file: $($entry.Name)" }
    $hash = (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash
    $allowed = @($entry.Value)
    if ($entry.Name -eq $change.path) { $allowed += $change.candidateSha256 }
    if ($hash -notin $allowed) { throw "SDK hash mismatch: $($entry.Name)" }
}
if (Test-Path -LiteralPath $target) {
    if ($source -ne (Resolve-Path -LiteralPath $target).Path) { throw 'Package already exists; no overwrite. Validate it separately.' }
    & (Join-Path $toolRoot 'Templates/GameFramework/ProjectFiles/Tools/Test-WeChatSdkBackground.ps1') -PackagePath $target
    Write-Output 'Pinned SDK already installed and verified.'
    exit 0
}
# Target is a fixed repository child; copy only paths from the verified manifest.
New-Item -ItemType Directory -Path $target | Out-Null
foreach ($entry in $manifest.files.PSObject.Properties) {
    $destination = Join-Path $target $entry.Name
    New-Item -ItemType Directory -Path (Split-Path $destination -Parent) -Force | Out-Null
    $inputFile = Join-Path $source $entry.Name
    if ($entry.Name -eq $change.path) { $inputFile = $patchedFile }
    Copy-Item -LiteralPath $inputFile -Destination $destination
}
& (Join-Path $toolRoot 'Templates/GameFramework/ProjectFiles/Tools/Test-WeChatSdkBackground.ps1') -PackagePath $target
Write-Output 'Pinned SDK installed and verified; payload remains outside Git.'
