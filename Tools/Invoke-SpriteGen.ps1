# Repository-owned launcher; third-party code and environment remain local.
$ErrorActionPreference = 'Stop'
$python = Join-Path (Split-Path $PSScriptRoot -Parent) 'ThirdParty/sprite-gen/.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    throw 'SpriteGen Python environment is missing. See ThirdParty/README.md.'
}
$previousEncoding = $env:PYTHONIOENCODING
try {
    $env:PYTHONIOENCODING = 'utf-8'
    & $python -m sprite_gen.cli @args
    $resultCode = $LASTEXITCODE
} finally {
    $env:PYTHONIOENCODING = $previousEncoding
}
exit $resultCode
