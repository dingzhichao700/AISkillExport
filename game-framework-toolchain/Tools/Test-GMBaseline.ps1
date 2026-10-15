#Requires -Version 5.1
param([string]$ProjectFiles = (Join-Path $PSScriptRoot '../Templates/GameFramework/ProjectFiles'))
$ErrorActionPreference = 'Stop'
function Read-Asset([string]$path) { Get-Content -LiteralPath (Join-Path $ProjectFiles $path) -Raw -Encoding UTF8 }
function Assert-Valid([bool]$valid, [string]$message) { if (!$valid) { throw $message } }
$prefab = Read-Asset 'Assets/Prefab/default/gm/GmPanel.prefab'
$control = Read-Asset 'Assets/Scripts/csharp/main/gm/GMControl.cs'
foreach ($name in @('GmPanel', 'GMItem')) {
    Assert-Valid ($prefab.Contains("scriptTypeName: $name, Main")) "Invalid GM binding: $name"
    $path = "Assets/Scripts/csharp/main/gm/view/$name.cs"
    Assert-Valid ($prefab.Contains("csharpAssetPath: $path")) "Invalid GM script path: $name"
    foreach ($suffix in @('', '.meta')) { Assert-Valid (Test-Path (Join-Path $ProjectFiles ($path + $suffix))) "Missing $path$suffix" }
}
$metas = @{}
Get-ChildItem (Join-Path $ProjectFiles 'Assets/Art') -Filter '*.meta' -Recurse | ForEach-Object {
    $text = Get-Content $_.FullName -Raw
    if ($text -match '(?m)^guid: (\w+)') { $metas[$Matches[1]] = $text }
}
foreach ($ref in [regex]::Matches($prefab, 'm_Sprite: \{fileID: (-?\d+), guid: (\w+), type: \d+\}')) {
    $id = $ref.Groups[1].Value; $guid = $ref.Groups[2].Value
    if ($guid.StartsWith('00000000')) { continue }
    Assert-Valid ($metas.ContainsKey($guid)) "Missing GM Sprite GUID: $guid"
    Assert-Valid ($metas[$guid] -match "internalID: $id\b") "Missing GM Sprite fileID: $id"
}
$group = Read-Asset 'Assets/AddressableAssetsData/AssetGroups/Default Local Group.asset'
foreach ($path in @('Assets/Prefab/default/gm/GmPanel.prefab', 'Assets/Art/atlas/default/gm.png')) {
    $guid = [regex]::Match((Read-Asset "$path.meta"), '(?m)^guid: (\w+)').Groups[1].Value
    $entries = @([regex]::Matches($group, '(?ms)^  - m_GUID: .*?(?=^  - m_GUID:|^  m_ReadOnly:|\z)') | Where-Object { $_.Value.Contains("m_GUID: $guid") })
    Assert-Valid ($entries.Count -eq 1) "GM Addressables entry missing or duplicated: $path"
    Assert-Valid ($entries[0].Value.Contains("m_Address: $path") -and $entries[0].Value.Contains('- main-content')) "GM address/label mismatch: $path"
}
$rows = @(Read-Asset 'Assets/ConfigBin/cfgobj_gmobj.json' | ConvertFrom-Json)
$expected = @('log', 'timeScale', 'timePause', 'timeResume', 'closeGM')
Assert-Valid ($rows.Count -eq 5) 'Template must contain exactly five generic GM commands'
foreach ($name in $expected) {
    $matchesForName = @($rows | Where-Object { $_.content -ceq $name })
    Assert-Valid ($matchesForName.Count -eq 1) "GM configuration missing or duplicated: $name"
    Assert-Valid ($control.Contains("RegisterCommand(`"$name`"")) "GM handler missing: $name"
    Assert-Valid ($matchesForName[0].paramFormat.Count -eq $matchesForName[0].paramIntro.Count) "GM parameter mismatch: $name"
}
# Generated Tables is authoritative; never add sample-specific names to the template.
$tables = Read-Asset 'Assets/Scripts/csharp/login/cfg/Tables.cs'
$resource = Read-Asset 'Assets/Scripts/csharp/foundation/core/resource/constant/ResourceConst.cs'
$list = [regex]::Match($resource, '(?s)ALL_CONFIG_LIST.*?\{(.*?)\}').Groups[1].Value
$required = @([regex]::Matches($tables, 'loader\("([^"]+)"\)') | ForEach-Object { $_.Groups[1].Value } | Sort-Object -Unique)
$actual = @([regex]::Matches($list, '"([^"]+)"') | ForEach-Object { $_.Groups[1].Value } | Sort-Object -Unique)
Assert-Valid (@(Compare-Object $required $actual).Count -eq 0) 'Tables and ALL_CONFIG_LIST differ'
Write-Output 'PASS: GM bindings, Sprite references, addresses, commands and configuration preload list'
