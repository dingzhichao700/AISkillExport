param(
    [Parameter(Mandatory = $true)][string]$UnityEditor,
    [Parameter(Mandatory = $true)][string]$OutputRoot
)
$ErrorActionPreference = 'Stop'
$taskTemplate = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../Templates/GameFramework/ProjectFiles'))
$taskOutput = [IO.Path]::GetFullPath($OutputRoot)
if (Test-Path -LiteralPath $taskOutput) { throw 'Use a new isolated output directory.' }
if (!(Test-Path -LiteralPath $UnityEditor -PathType Leaf)) { throw 'Unity executable does not exist.' }
New-Item -ItemType Directory -Path (Join-Path $taskOutput 'Assets/Editor'), (Join-Path $taskOutput 'Packages'), (Join-Path $taskOutput 'ProjectSettings') | Out-Null
Copy-Item -LiteralPath (Join-Path $taskTemplate 'Assets/Scripts/csharp/foundation/core/component/frameAnimation/view/FrameShadowGraphic.cs') -Destination (Join-Path $taskOutput 'Assets/FrameShadowGraphic.cs')
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'Tests/FrameShadowRegression.cs') -Destination (Join-Path $taskOutput 'Assets/Editor/FrameShadowRegression.cs')
Copy-Item -LiteralPath (Join-Path $taskTemplate 'ProjectSettings/ProjectVersion.txt') -Destination (Join-Path $taskOutput 'ProjectSettings/ProjectVersion.txt')
[IO.File]::WriteAllText((Join-Path $taskOutput 'Packages/manifest.json'), '{"dependencies":{"com.unity.ugui":"1.0.0"}}')
$taskLog = Join-Path $taskOutput 'unity.log'
$taskArgs = @('-batchmode', '-nographics', '-projectPath', ('"' + $taskOutput + '"'), '-executeMethod', 'FrameShadowRegression.Run', '-logFile', ('"' + $taskLog + '"'))
$taskProcess = Start-Process -FilePath $UnityEditor -ArgumentList $taskArgs -WindowStyle Hidden -PassThru
Write-Output "Isolated Unity PID=$($taskProcess.Id), log=$taskLog"
if (!$taskProcess.WaitForExit(240000)) {
    throw "Isolated Unity timed out; inspect PID=$($taskProcess.Id) and $taskLog. User editor was not touched."
}
$taskResult = Join-Path $taskOutput 'frame-shadow-result.txt'
if ($taskProcess.ExitCode -ne 0 -or !(Test-Path -LiteralPath $taskResult)) { throw "Unity verification failed; see $taskLog" }
$taskSummary = [IO.File]::ReadAllText($taskResult)
if (!$taskSummary.StartsWith('passed:')) { throw $taskSummary }
Write-Output $taskSummary
