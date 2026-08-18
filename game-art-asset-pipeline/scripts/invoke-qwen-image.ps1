[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$Prompt,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$OutputPath,

    [string]$Model = 'qwen-image-plus',
    [ValidatePattern('^\d+\*\d+$')]
    [string]$Size = '1024*1024',
    [switch]$ValidateOnly
)

$ErrorActionPreference = 'Stop'
$submitUri = 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis'
$taskUriBase = 'https://dashscope.aliyuncs.com/api/v1/tasks/'

if (-not (Test-Path Env:QWEN_ANI)) {
    throw 'QWEN_ANI is not configured.'
}

$trimmedPrompt = $Prompt.Trim()
if ([string]::IsNullOrWhiteSpace($trimmedPrompt)) {
    throw 'Input.prompt must be a non-empty string.'
}

$payload = @{
    model = $Model
    input = @{
        prompt = $trimmedPrompt
    }
    parameters = @{
        size = $Size
        n = 1
        prompt_extend = $false
        watermark = $false
    }
}

if (($payload.input.Keys -contains 'messages') -or
    -not ($payload.input.prompt -is [string]) -or
    [string]::IsNullOrWhiteSpace($payload.input.prompt)) {
    throw 'Invalid local request schema: QWEN image generation requires input.prompt as a non-empty string.'
}

if ($ValidateOnly) {
    Write-Output 'VALIDATION_SUCCEEDED provider=QWEN model=qwen-image-plus schema=input.prompt credential=QWEN_ANI_CONFIGURED'
    exit 0
}

$headers = @{
    Authorization = 'Bearer ' + $env:QWEN_ANI
    'X-DashScope-Async' = 'enable'
}
$body = $payload | ConvertTo-Json -Depth 6
$submission = Invoke-RestMethod -Method Post -Uri $submitUri -Headers $headers -ContentType 'application/json' -Body $body
$taskId = $submission.output.task_id
if ([string]::IsNullOrWhiteSpace($taskId)) {
    throw 'QWEN did not return a task ID.'
}

$status = 'PENDING'
for ($attempt = 0; $attempt -lt 120; $attempt++) {
    Start-Sleep -Seconds 3
    $result = Invoke-RestMethod -Method Get -Uri ($taskUriBase + $taskId) -Headers @{ Authorization = 'Bearer ' + $env:QWEN_ANI }
    $status = $result.output.task_status
    if ($status -eq 'SUCCEEDED') { break }
    if ($status -in @('FAILED', 'CANCELED', 'UNKNOWN')) {
        $code = $result.output.code
        $message = $result.output.message
        throw "QWEN generation failed: status=$status code=$code message=$message"
    }
}

if ($status -ne 'SUCCEEDED') {
    throw "QWEN generation timed out: status=$status"
}

$imageUrl = $result.output.results[0].url
if ([string]::IsNullOrWhiteSpace($imageUrl)) {
    throw 'QWEN generation succeeded but returned no image URL.'
}

$resolvedOutput = [System.IO.Path]::GetFullPath($OutputPath)
$outputDirectory = [System.IO.Path]::GetDirectoryName($resolvedOutput)
if (-not [string]::IsNullOrWhiteSpace($outputDirectory)) {
    New-Item -ItemType Directory -Force -Path $outputDirectory | Out-Null
}
Invoke-WebRequest -Uri $imageUrl -OutFile $resolvedOutput
Write-Output "GENERATION_SUCCEEDED output=$resolvedOutput provider=QWEN model=$Model schema=input.prompt"
