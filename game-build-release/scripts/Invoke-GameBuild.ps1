#Requires -Version 5.1
[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [Parameter(Mandatory = $true)][string]$ProjectPath,
    [ValidateSet('inspect', 'prepare', 'generate', 'export', 'content', 'publish-local')][string]$Action = 'inspect'
)
$ErrorActionPreference = 'Stop'
$project = (Resolve-Path -LiteralPath $ProjectPath).Path
$configPath = Join-Path $project 'ProjectSettings/FrameworkPlatform.json'
if (!(Test-Path -LiteralPath $configPath)) { throw "Missing project platform config: $configPath" }
$config = Get-Content -LiteralPath $configPath -Raw -Encoding UTF8 | ConvertFrom-Json
$queue = Join-Path $project 'Library/AIUI'
function Read-OptionalJson([string]$Name) {
    $path = Join-Path $queue $Name
    if (Test-Path -LiteralPath $path) { return Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json }
    return $null
}
$ready = Read-OptionalJson 'wechat-build-ready.json'
$status = Read-OptionalJson 'editor-status.json'
$previous = Read-OptionalJson 'wechat-build-result.json'
if ($Action -eq 'inspect') {
    [ordered]@{ project = $project; platform = $config.platform; bootstrapUrl = $config.bootstrapUrl; cdnRoot = $config.cdnRoot; ready = $ready; editor = $status; result = $previous; buildState = (Read-OptionalJson 'hotupdate-build-state.json'); pending = (Test-Path -LiteralPath (Join-Path $queue 'pending-wechat-build.json')) } | ConvertTo-Json -Depth 12
    return
}
if ($config.platform -ne 'WeChat') { throw 'Only the WeChat adapter is implemented. Do not change platform implicitly.' }
if (!$config.appId -or !$config.cdnRoot -or !$config.bootstrapUrl) { throw 'WeChat appId, cdnRoot and bootstrapUrl are required.' }
$uri = [Uri]$config.bootstrapUrl
if (!$uri.IsAbsoluteUri -or $uri.Scheme -notin @('http', 'https') -or !$uri.AbsolutePath.EndsWith('/bootstrap.json')) { throw 'Invalid bootstrapUrl.' }
if (!$ready -or !$status -or $ready.version -ne 1 -or $ready.processId -ne $status.processId -or $ready.target -ne 'WebGL') { throw 'Queue adapter is unavailable or Unity PID/target does not match.' }
$process = Get-CimInstance Win32_Process -Filter "ProcessId = $($ready.processId)"
if (!$process -or $process.Name -ne 'Unity.exe') { throw 'Recorded process is not a live Unity editor.' }
$match = [regex]::Match($process.CommandLine, '(?i)(?:^|\s)-projectPath\s+(?:"([^"]+)"|(\S+))')
$openedProject = if ($match.Groups[1].Success) { $match.Groups[1].Value } else { $match.Groups[2].Value }
if (!$match.Success -or [IO.Path]::GetFullPath($openedProject).TrimEnd('\', '/') -ne $project.TrimEnd('\', '/')) { throw 'Unity process belongs to a different or unidentified project.' }
if ($status.isPlaying -or $status.isCompiling -or $status.isUpdating -or $status.isRunning) { throw 'Unity is busy. Do not submit another request.' }
$pending = Join-Path $queue 'pending-wechat-build.json'
if (Test-Path -LiteralPath $pending) { throw 'A request is already pending. Inspect it first.' }
$activeStates = @('preparing-hybridclr', 'generating-hybridclr', 'building-content', 'building-addressables', 'building-wechat')
if ($previous -and $previous.status -in $activeStates) { throw 'Previous request is not terminal. Inspect it; do not auto-resubmit.' }
$wireAction = if ($Action -eq 'publish-local') { 'publish' } else { $Action }
$request = [ordered]@{ requestId = [guid]::NewGuid().ToString('N'); processId = $ready.processId; action = $wireAction }
if ($Action -eq 'export') {
    $buildRoot = [IO.Path]::GetFullPath((Join-Path $project '../build'))
    $output = Join-Path $buildRoot ('build_wechat_' + (Get-Date -Format 'yyyyMMddHHmmssfff'))
    if (!$output.StartsWith($buildRoot + [IO.Path]::DirectorySeparatorChar) -or (Test-Path -LiteralPath $output)) { throw 'Unsafe or occupied build output.' }
    $request.outputPath = $output
}
if (!$PSCmdlet.ShouldProcess($project, "Submit $Action ($($request.requestId))")) { $request | ConvertTo-Json; return }
$temporary = Join-Path $queue ($request.requestId + '.tmp')
[IO.File]::WriteAllText($temporary, ($request | ConvertTo-Json), (New-Object System.Text.UTF8Encoding($false)))
# File.Move refuses to overwrite a competing pending request.
[IO.File]::Move($temporary, $pending)
[ordered]@{ requestId = $request.requestId; action = $Action; outputPath = $request.outputPath; resultPath = (Join-Path $queue 'wechat-build-result.json') } | ConvertTo-Json
