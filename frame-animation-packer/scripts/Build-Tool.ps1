param([string]$MSBuild)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
if (!$MSBuild) {
    $vswhere=Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
    if (Test-Path $vswhere) { $MSBuild=& $vswhere -latest -products '*' -requires Microsoft.Component.MSBuild -find 'MSBuild\**\Bin\MSBuild.exe' | Select-Object -First 1 }
}
if (!$MSBuild -or !(Test-Path $MSBuild)) { throw 'Specify -MSBuild with the Visual Studio MSBuild.exe path.' }
& $MSBuild (Join-Path $root 'tool\FrameAnimeExportor.csproj') /t:Build /p:Configuration=Release /nologo /verbosity:minimal
if ($LASTEXITCODE -ne 0) { throw 'Build failed; runtime was not updated.' }
Get-ChildItem (Join-Path $root 'tool\bin\Release') -File |
    Where-Object {$_.Extension -in '.exe','.dll','.config'} |
    Copy-Item -Destination (Join-Path $root 'runtime') -Force
Write-Output 'Runtime refreshed from bundled source.'
