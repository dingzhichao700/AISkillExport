[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$Prompt,

    [Parameter(Mandatory = $true)]
    [ValidateCount(1, 4)]
    [string[]]$ReferenceImagePath,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$OutputPath,

    [string]$Model = 'wan2.6-image',
    [ValidateSet('1K', '2K')]
    [string]$Size = '1K',
    [switch]$ValidateOnly
)

$ErrorActionPreference = 'Stop'
$submitUri = 'https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation'

if (-not (Test-Path Env:QWEN_ANI)) {
    throw 'QWEN_ANI is not configured.'
}

$trimmedPrompt = $Prompt.Trim()
if ([string]::IsNullOrWhiteSpace($trimmedPrompt)) {
    throw 'The reference-image prompt must be a non-empty string.'
}

Add-Type -AssemblyName System.Drawing
$content = [System.Collections.Generic.List[object]]::new()
$content.Add(@{ text = $trimmedPrompt })

foreach ($path in $ReferenceImagePath) {
    $resolvedPath = [System.IO.Path]::GetFullPath($path)
    if (-not (Test-Path -LiteralPath $resolvedPath -PathType Leaf)) {
        throw "Reference image does not exist: $resolvedPath"
    }

    $sourceImage = [System.Drawing.Image]::FromFile($resolvedPath)
    try {
        $flattened = New-Object System.Drawing.Bitmap($sourceImage.Width, $sourceImage.Height, [System.Drawing.Imaging.PixelFormat]::Format24bppRgb)
        try {
            $graphics = [System.Drawing.Graphics]::FromImage($flattened)
            try {
                $graphics.Clear([System.Drawing.Color]::Magenta)
                $graphics.DrawImage($sourceImage, 0, 0, $sourceImage.Width, $sourceImage.Height)
            }
            finally {
                $graphics.Dispose()
            }

            $memory = New-Object System.IO.MemoryStream
            try {
                $flattened.Save($memory, [System.Drawing.Imaging.ImageFormat]::Jpeg)
                $base64 = [Convert]::ToBase64String($memory.ToArray())
            }
            finally {
                $memory.Dispose()
            }
        }
        finally {
            $flattened.Dispose()
        }
    }
    finally {
        $sourceImage.Dispose()
    }

    $content.Add(@{ image = 'data:image/jpeg;base64,' + $base64 })
}

$payload = @{
    model = $Model
    input = @{
        messages = @(
            @{
                role = 'user'
                content = $content
            }
        )
    }
    parameters = @{
        negative_prompt = '像素画，像素风，8-bit，16-bit，阶梯锯齿，马赛克，低分辨率，文字，水印，投影，尾焰，烟雾，场景，透视斜视角'
        size = $Size
        n = 1
        enable_interleave = $false
        prompt_extend = $false
        watermark = $false
    }
}

if ($payload.input.messages.Count -ne 1 -or $payload.input.messages[0].content.Count -lt 2) {
    throw 'Invalid local request schema for QWEN reference-image generation.'
}

if ($ValidateOnly) {
    Write-Output "VALIDATION_SUCCEEDED provider=QWEN model=$Model schema=input.messages references=$($ReferenceImagePath.Count) credential=QWEN_ANI_CONFIGURED"
    exit 0
}

$headers = @{ Authorization = 'Bearer ' + $env:QWEN_ANI }
$body = $payload | ConvertTo-Json -Depth 10 -Compress
$result = Invoke-RestMethod -Method Post -Uri $submitUri -Headers $headers -ContentType 'application/json' -Body $body
$imageUrl = $result.output.choices[0].message.content | Where-Object { $_.type -eq 'image' } | Select-Object -First 1 -ExpandProperty image
if ([string]::IsNullOrWhiteSpace($imageUrl)) {
    throw 'QWEN reference-image generation succeeded but returned no image URL.'
}

$resolvedOutput = [System.IO.Path]::GetFullPath($OutputPath)
$outputDirectory = [System.IO.Path]::GetDirectoryName($resolvedOutput)
if (-not [string]::IsNullOrWhiteSpace($outputDirectory)) {
    New-Item -ItemType Directory -Force -Path $outputDirectory | Out-Null
}
Invoke-WebRequest -Uri $imageUrl -OutFile $resolvedOutput
Write-Output "GENERATION_SUCCEEDED output=$resolvedOutput provider=QWEN model=$Model schema=input.messages references=$($ReferenceImagePath.Count)"
