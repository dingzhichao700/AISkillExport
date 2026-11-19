#Requires -Version 5.1
param([Parameter(Mandatory = $true)][string]$WorkRoot)
$ErrorActionPreference = 'Stop'
$repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$helper = Join-Path $repo 'Templates/GameFramework/ProjectFiles/Tools/Test-GameFrameworkProjectSettings.ps1'
$fixture = Join-Path ([IO.Path]::GetFullPath($WorkRoot)) ('background-policy-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path (Join-Path $fixture 'ProjectSettings'), (Join-Path $fixture 'Tools') -Force | Out-Null
Copy-Item -LiteralPath $helper -Destination (Join-Path $fixture 'Tools')
$settings = Join-Path $fixture 'ProjectSettings/ProjectSettings.asset'
$checks = [Collections.Generic.List[string]]::new()
function Test-Case([string]$Name, [string]$Content, [bool]$ExpectedPass) {
    [IO.File]::WriteAllText($settings, $Content)
    $before = (Get-FileHash -LiteralPath $settings).Hash
    $ok = $true
    try { & $helper -ProjectPath $fixture } catch { $ok = $false }
    if ($ok -ne $ExpectedPass) { throw "Unexpected policy result: $Name" }
    if ((Get-FileHash -LiteralPath $settings).Hash -ne $before) { throw "Check mutated settings: $Name" }
    $checks.Add($Name)
}
Test-Case 'enabled' "PlayerSettings:`n  runInBackground: 1`n" $true
Test-Case 'disabled is rejected without mutation' "PlayerSettings:`n  runInBackground: 0`n" $false
Test-Case 'missing field is rejected' "PlayerSettings:`n  productName: Test`n" $false
Test-Case 'duplicate enabled fields are rejected' "PlayerSettings:`n  runInBackground: 1`n  runInBackground: 1`n" $false
Test-Case 'conflicting duplicate fields are rejected' "PlayerSettings:`n  runInBackground: 1`n  runInBackground: 0`n" $false
Test-Case 'invalid value is rejected' "PlayerSettings:`n  runInBackground: true`n" $false
# Extract only the real generator's validation function. Never execute project generation.
$tokens = $null; $parseErrors = $null
$ast = [Management.Automation.Language.Parser]::ParseFile((Join-Path $repo 'Tools/Generate-GameFrameworkProject.ps1'), [ref]$tokens, [ref]$parseErrors)
if ($parseErrors.Count -ne 0) { throw 'Generator parse errors' }
$function = $ast.Find({param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq 'Assert-ExportComplete'}, $true)
if ($null -eq $function) { throw 'Missing generator output validation' }
. ([scriptblock]::Create($function.Extent.Text))
[IO.File]::WriteAllText($settings, "PlayerSettings:`n  runInBackground: 0`n")
$before = (Get-FileHash -LiteralPath $settings).Hash
$message = ''
try { Assert-ExportComplete -ProjectPath $fixture } catch { $message = $_.Exception.Message }
if ($message -notmatch 'Run In Background') { throw "Generated output regression was not detected: $message" }
if ((Get-FileHash -LiteralPath $settings).Hash -ne $before) { throw 'Generator validation mutated settings' }
$checks.Add('real generated-output validator rejects regression after template copy')
# Validate existing-project default invocation from an unrelated working directory.
[IO.File]::WriteAllText($settings, "PlayerSettings:`n  runInBackground: 1`n")
& (Join-Path $fixture 'Tools/Test-GameFrameworkProjectSettings.ps1')
$checks.Add('delivered existing-project entry resolves its own project root')
$checks | ForEach-Object { Write-Host "[background-policy] passed: $_" }
Write-Host "[background-policy] $($checks.Count) checks passed; fixtures: $fixture"

$adapterPath=Join-Path $repo 'Templates/GameFramework/ProjectFiles/Assets/Editor/FrameworkWeChatBuild.cs'
$adapter=[IO.File]::ReadAllText($adapterPath)
if($adapter -notmatch 'var result = ExportWithPreservedBackgroundSetting\(\(\) => WXConvertCore.DoExport\(true\)\);') {throw 'SDK export bypasses background setting restoration'}
if(([regex]::Matches($adapter,'WXConvertCore.DoExport\(')).Count -ne 1){throw 'Unreviewed direct SDK export entry'}
$start=$adapter.IndexOf('private static WXConvertCore.WXExportError ExportWithPreservedBackgroundSetting(')
if($start -lt 0){throw 'Missing SDK setting restoration guard'}
$guard=$adapter.Substring($start,$adapter.IndexOf("`n    }",$start)-$start)
foreach($required in @('bool original = PlayerSettings.runInBackground;', 'if (!original)', 'return export();', 'finally {', 'PlayerSettings.runInBackground = original;', 'AssetDatabase.SaveAssets();')){
 if(!$guard.Contains($required)){throw "Incomplete SDK background setting guard: $required"}
}
Write-Host '[background-policy] SDK export is guarded; disabled baseline rejected and persistent setting restored in finally'
