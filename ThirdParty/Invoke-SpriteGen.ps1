# Compatibility entry point. Maintain the implementation in Tools.
$ErrorActionPreference = 'Stop'
& (Join-Path (Split-Path $PSScriptRoot -Parent) 'Tools/Invoke-SpriteGen.ps1') @args
exit $LASTEXITCODE
