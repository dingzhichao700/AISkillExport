#Requires -Version 5.1
param([Parameter(Mandatory=$true)][string]$WorkRoot)
$ErrorActionPreference='Stop'
$generator=Join-Path $PSScriptRoot '../Generate-GameFrameworkProject.ps1'
$tokens=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile($generator,[ref]$tokens,[ref]$errors)
if($errors.Count){throw 'Generator parse errors'}
foreach($name in @('Test-LogFailure','Assert-HybridCLRDependency','Assert-FirstRunEvidence')){
 $fn=$ast.Find({param($n)$n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq $name},$true)
 if(!$fn){throw "Missing guard $name"}; . ([scriptblock]::Create($fn.Extent.Text))
}
$fixture=Join-Path ([IO.Path]::GetFullPath($WorkRoot)) ('first-run-guards-'+[guid]::NewGuid().ToString('N'))
$hash='1234567890abcdef1234567890abcdef12345678'
$package=Join-Path $fixture 'Library/PackageCache/com.code-philosophy.hybridclr@1234567890'
New-Item -ItemType Directory -Path (Join-Path $fixture 'Packages'),(Join-Path $package 'Runtime'),(Join-Path $package 'Editor') -Force|Out-Null
$version='https://example.invalid/hybridclr.git#'+$hash
@{dependencies=@{'com.code-philosophy.hybridclr'=$version}}|ConvertTo-Json -Depth 5|Set-Content (Join-Path $fixture 'Packages/manifest.json')
@{dependencies=@{'com.code-philosophy.hybridclr'=@{source='git';version=$version;hash=$hash}}}|ConvertTo-Json -Depth 5|Set-Content (Join-Path $fixture 'Packages/packages-lock.json')
'{"name":"com.code-philosophy.hybridclr"}'|Set-Content (Join-Path $package 'package.json')
foreach($rel in @('Runtime/HybridCLR.Runtime.asmdef','Runtime/RuntimeApi.cs','Editor/HybridCLR.Editor.asmdef')){'fixture'|Set-Content (Join-Path $package $rel)}
function Must-Fail([scriptblock]$Action,[string]$Label){$blocked=$false;try{& $Action}catch{$blocked=$true};if(!$blocked){throw "Failed to block: $Label"};Write-Host "PASS: $Label rejected"}
Assert-HybridCLRDependency $fixture
Write-Host 'PASS: pinned complete HybridCLR package accepted'
$identity=Join-Path $package 'package.json'
'{"name":"com.example.wrong"}'|Set-Content $identity
Must-Fail {Assert-HybridCLRDependency $fixture} 'wrong package identity'
'{"name":"com.code-philosophy.hybridclr"}'|Set-Content $identity
$api=Join-Path $package 'Runtime/RuntimeApi.cs'
[IO.File]::WriteAllText($api,'')
Must-Fail {Assert-HybridCLRDependency $fixture} 'empty runtime API'
Remove-Item -LiteralPath $api
Must-Fail {Assert-HybridCLRDependency $fixture} 'missing runtime API'
'fixture'|Set-Content $api
$bad=Join-Path (Split-Path $package -Parent) 'com.code-philosophy.hybridclr@abcdef1234'
Move-Item -LiteralPath $package -Destination $bad
Must-Fail {Assert-HybridCLRDependency $fixture} 'wrong resolved revision'
Move-Item -LiteralPath $bad -Destination $package
$manifest=Join-Path $fixture 'Packages/manifest.json'
'{"dependencies":{}}'|Set-Content $manifest
Must-Fail {Assert-HybridCLRDependency $fixture} 'missing manifest dependency'
@{dependencies=@{'com.code-philosophy.hybridclr'=($version+'bad')}}|ConvertTo-Json -Depth 5|Set-Content $manifest
Must-Fail {Assert-HybridCLRDependency $fixture} 'manifest lock mismatch'
New-Item -ItemType Directory -Path (Join-Path $fixture 'ProjectSettings')|Out-Null
$platformFile=Join-Path $fixture 'ProjectSettings/FrameworkPlatform.json'
'{"platform":"Standalone"}'|Set-Content $platformFile
'{"dependencies":{}}'|Set-Content $manifest
Assert-HybridCLRDependency $fixture
Write-Host 'PASS: explicit Standalone without HybridCLR remains supported'
'{"platform":"WeChat"}'|Set-Content $platformFile
Must-Fail {Assert-HybridCLRDependency $fixture} 'WeChat without HybridCLR'
$marker=Join-Path $fixture 'Library/template-runtime-validation.txt';$log=Join-Path $fixture 'run.log'
'BatchMode: 0'|Set-Content $log
Must-Fail {Assert-FirstRunEvidence $fixture $log} 'missing runtime result'
'failed: timeout'|Set-Content $marker
Must-Fail {Assert-FirstRunEvidence $fixture $log} 'failed runtime flow'
'ok: Opening -> Login -> Option -> Loading -> Main'|Set-Content $marker
Assert-FirstRunEvidence $fixture $log
Write-Host 'PASS: non-batch successful runtime evidence accepted'
foreach($failure in @('BatchMode: 1','BatchMode: 0`nerror CS0246: HybridCLR missing','BatchMode: 0`nCorrupted Library Detected','BatchMode: 0`nNullReferenceException: failure','BatchMode: 0`nAsset import failed')){
 $failure.Replace('`n',"`n")|Set-Content $log
 Must-Fail {Assert-FirstRunEvidence $fixture $log} $failure
}
$text=[IO.File]::ReadAllText($generator)
$run=$text.LastIndexOf('    Invoke-UnityFirstRun -ProjectPath $TargetProject')
$final=$text.LastIndexOf("'Logs\export-final-open.log'")
$success=$text.LastIndexOf('    $exportSucceeded = $true')
if(!($final -gt 0 -and $run -gt $final -and $success -gt $run)){throw 'Runtime gate must precede export success at final path'}
$fn=$ast.Find({param($n)$n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq 'Invoke-UnityFirstRun'},$true).Extent.Text
if($fn.Contains("'-batchmode'") -or $fn.Contains("'-nographics'")){throw 'First run must use a normal graphics editor'}
if($fn.IndexOf('Remove-Item -LiteralPath $marker') -gt $fn.IndexOf('Start-Process') -or !$fn.Contains('Remove-Item -LiteralPath $marker')){throw 'Stale runtime marker must be removed before launch'}
Write-Host 'PASS: fresh-result, non-batch and final-delivery gate ordering'
# Exercise the orchestration with an owned-process double; never start Unity in this fixture.
$invoke=$ast.Find({param($n)$n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq 'Invoke-UnityFirstRun'},$true)
. ([scriptblock]::Create($invoke.Extent.Text))
$script:UnityEditorPath='fixture-only-no-unity'
$script:mode='success';$script:killed=$false
function Wait-ProjectUnlocked([string]$ProjectPath){}
function Assert-ExportComplete([string]$ProjectPath){}
function Start-Process {
 param($FilePath,$ArgumentList,[switch]$PassThru,$WindowStyle)
 if(Test-Path -LiteralPath $marker){throw 'Stale marker survived until launch'}
 if(Test-Path -LiteralPath $log){throw 'Stale log survived until launch'}
 if($ArgumentList -contains '-batchmode' -or $ArgumentList -contains '-nographics'){throw 'Wrong editor mode'}
 if($script:mode -ne 'no-result'){'ok: Opening -> Login -> Option -> Loading -> Main'|Set-Content $marker}
 'BatchMode: 0'|Set-Content $log
 $process=[pscustomobject]@{ExitCode=0}
 if($script:mode -eq 'exit-failure'){$process.ExitCode=1}
 $process|Add-Member ScriptMethod WaitForExit {param($timeout) if($script:mode -eq 'timeout'){return $false};return $true}
 $process|Add-Member ScriptMethod Refresh {}
 $process|Add-Member ScriptMethod Kill {$script:killed=$true}
 return $process
}
'ok: stale success'|Set-Content $marker
'BatchMode: 0 stale'|Set-Content $log
Invoke-UnityFirstRun $fixture $log
Write-Host 'PASS: orchestration deletes stale marker/log before launch and accepts fresh success'
foreach($mode in @('no-result','exit-failure','timeout')){
 $script:mode=$mode
 Must-Fail {Invoke-UnityFirstRun $fixture $log} "orchestration $mode"
}
if(!$script:killed){throw 'Timed-out owned process was not handled'}
Write-Host 'First-run guard fixture checks passed; actual Unity export remains separately required.'
