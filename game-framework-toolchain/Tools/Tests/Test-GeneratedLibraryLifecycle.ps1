#Requires -Version 5.1
param([Parameter(Mandatory=$true)][string]$WorkRoot)
$ErrorActionPreference='Stop'
$repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$generator=Join-Path $repo 'Tools/Generate-GameFrameworkProject.ps1'
$tokens=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile($generator,[ref]$tokens,[ref]$errors)
if($errors.Count){throw 'Generator parse errors'}
foreach($name in @('Assert-ChildPath','Get-DirectoryLength','Assert-LibraryReadyForReopen','Optimize-GeneratedLibrary')){
 $fn=$ast.Find({param($n)$n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq $name},$true)
 if(!$fn){throw "Missing function: $name"}; . ([scriptblock]::Create($fn.Extent.Text))
}
function Write-Step([string]$Message){Write-Host $Message}
$fixture=Join-Path ([IO.Path]::GetFullPath($WorkRoot)) ('library-policy-'+[guid]::NewGuid().ToString('N'))
$library=Join-Path $fixture 'Library'
New-Item -ItemType Directory -Path $library,(Join-Path $library 'com.unity.addressables') -Force|Out-Null
foreach($name in @('SourceAssetDB','ArtifactDB','LibraryFormatVersion.txt','unknown-version-metadata')){[IO.File]::WriteAllText((Join-Path $library $name),'fixture-metadata-not-an-actual-unity-database')}
[IO.File]::WriteAllText((Join-Path $library 'com.unity.addressables/content-state.bin'),'retained-build')
$caches=@('Artifacts','BuildCache','Bee','ScriptAssemblies','ShaderCache')
foreach($name in $caches){New-Item -ItemType Directory -Path (Join-Path $library $name)|Out-Null;[IO.File]::WriteAllText((Join-Path $library "$name/cache.bin"),'cache')}
New-Item -ItemType Directory -Path (Join-Path $library 'PackageCache/com.example.dependency') -Force|Out-Null
[IO.File]::WriteAllText((Join-Path $library 'PackageCache/com.example.dependency/package.json'), '{}')
$before=@(Get-ChildItem -LiteralPath $library -File|Get-FileHash|Select-Object Path,Hash)
Optimize-GeneratedLibrary -ProjectPath $fixture
$after=@(Get-ChildItem -LiteralPath $library -File|Get-FileHash|Select-Object Path,Hash)
if(@(Compare-Object $before $after -Property Path,Hash).Count){throw 'Pruning changed indexes, version, or unknown metadata'}
if(!(Test-Path -LiteralPath (Join-Path $library 'com.unity.addressables/content-state.bin'))){throw 'Addressables was lost'}
foreach($name in $caches){if(Test-Path -LiteralPath (Join-Path $library $name)){throw "Cache remained: $name"}}
if(!(Test-Path -LiteralPath (Join-Path $library 'PackageCache/com.example.dependency/package.json'))){throw 'Resolved package dependency was deleted'}
Write-Host 'PASS: indexes/version/package dependencies/unknown metadata/addressables retained; known caches removed'
New-Item -ItemType Directory -Path (Join-Path $fixture 'Temp')|Out-Null
[IO.File]::WriteAllText((Join-Path $fixture 'Temp/UnityLockfile'),'locked')
$blocked=$false;try{Optimize-GeneratedLibrary -ProjectPath $fixture}catch{$blocked=$_.Exception.Message -match 'open Unity project'}
if(!$blocked){throw 'Open project was not blocked'}
Remove-Item -LiteralPath (Join-Path $fixture 'Temp/UnityLockfile')
Write-Host 'PASS: live project lock prevents pruning'
[IO.File]::WriteAllText((Join-Path $library 'CorruptedLibraryDetection'),'')
$blocked=$false;try{Assert-LibraryReadyForReopen -ProjectPath $fixture}catch{$blocked=$_.Exception.Message -match 'corrupt Library'}
if(!$blocked){throw 'Corrupt marker was ignored'}
Remove-Item -LiteralPath (Join-Path $library 'CorruptedLibraryDetection')
Write-Host 'PASS: corruption marker prevents delivery'
Remove-Item -LiteralPath (Join-Path $library 'ArtifactDB')
$blocked=$false;try{Assert-LibraryReadyForReopen -ProjectPath $fixture}catch{$blocked=$_.Exception.Message -match 'integrity metadata'}
if(!$blocked){throw 'Missing database was ignored'}
Write-Host 'PASS: incomplete database pair prevents delivery'
$content=[IO.File]::ReadAllText($generator)
$prune=$content.LastIndexOf('    Optimize-GeneratedLibrary -ProjectPath $StageProject')
$reopen=$content.LastIndexOf("'export-reopen.log'")
$move=$content.LastIndexOf('    Move-Item -LiteralPath $StageProjectRoot -Destination $TargetRoot')
$final=$content.LastIndexOf("'Logs\export-final-open.log'")
if(!($prune -gt 0 -and $reopen -gt $prune -and $move -gt $reopen -and $final -gt $move)){throw 'Missing ordered reopen gates'}
if($content.Substring($final).Contains('Optimize-GeneratedLibrary -ProjectPath')){throw 'Cache pruning invalidates final open validation'}
Write-Host 'PASS: generator gates reopen after pruning and at final path; no invalidating prune afterward'
Write-Host 'Library lifecycle regression checks passed. Fixtures test filesystem contracts only; actual Unity reopening is separately required.'
