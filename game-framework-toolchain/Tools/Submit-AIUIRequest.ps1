[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)] [string] $ProjectPath,
    [Parameter(Mandatory = $true)] [ValidateSet('preview', 'finalize', 'cleanup', 'control')] [string] $Queue,
    [Parameter(Mandatory = $true)] [string] $RequestPath,
    [string] $MinimumToolVersion = '0.3.0'
)

$ErrorActionPreference = 'Stop'
$projectRoot = [IO.Path]::GetFullPath($ProjectPath)
$requestFile = [IO.Path]::GetFullPath($RequestPath)
$queueRoot = Join-Path $projectRoot 'Library\AIUI'
$statusPath = Join-Path $queueRoot 'editor-status.json'

if (-not (Test-Path -LiteralPath $requestFile -PathType Leaf)) {
    throw "AIUI request not found: $requestFile"
}
if (-not (Test-Path -LiteralPath $statusPath -PathType Leaf)) {
    throw 'AIUI editor status is unavailable. Open the project in Unity and wait for compilation to finish.'
}

$status = [IO.File]::ReadAllText($statusPath, [Text.Encoding]::UTF8) | ConvertFrom-Json
if ([version]$status.toolVersion -lt [version]$MinimumToolVersion) {
    throw "AIUI tool $($status.toolVersion) is older than required $MinimumToolVersion."
}
if (-not (Get-Process -Id ([int]$status.processId) -ErrorAction SilentlyContinue)) {
    throw "AIUI status belongs to a closed Unity process: $($status.processId)"
}
if ($Queue -ne 'control' -and $status.isPlaying) {
    throw 'Unity is in Play mode. Submit an explicit stopPlay control request before exporting.'
}
if ($Queue -ne 'control' -and ($status.isCompiling -or $status.isUpdating -or $status.isRunning)) {
    throw "Unity is busy: stage=$($status.stage), compiling=$($status.isCompiling), updating=$($status.isUpdating)."
}

$request = [IO.File]::ReadAllText($requestFile, [Text.Encoding]::UTF8) | ConvertFrom-Json
if ([string]::IsNullOrWhiteSpace([string]$request.requestId)) {
    throw 'AIUI request requires a non-empty requestId.'
}

$pendingName = switch ($Queue) {
    'preview' { 'pending-preview.json' }
    'finalize' { 'pending-finalize.json' }
    'cleanup' { 'pending-cleanup.json' }
    'control' { 'pending-control.json' }
}
$pendingPath = Join-Path $queueRoot $pendingName
if (Test-Path -LiteralPath $pendingPath) {
    throw "AIUI queue already contains a pending request: $pendingPath"
}

New-Item -ItemType Directory -Force -Path $queueRoot | Out-Null
$temporaryPath = Join-Path $queueRoot ('.submit-' + [guid]::NewGuid().ToString('N') + '.json')
Copy-Item -LiteralPath $requestFile -Destination $temporaryPath
Move-Item -LiteralPath $temporaryPath -Destination $pendingPath

[pscustomobject]@{
    requestId = $request.requestId
    queue = $Queue
    unityProcessId = $status.processId
    toolVersion = $status.toolVersion
    pendingPath = $pendingPath
}
