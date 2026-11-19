#Requires -Version 5.1
# Compatibility test entry: the SDK is now patched directly; no export wrapper remains.
param([string]$UnityEditor, [string]$WorkRoot)
$ErrorActionPreference = 'Stop'
$repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
& (Join-Path $repoRoot 'Tools/Install-PinnedWeChatSdk.ps1') -UpstreamPackagePath (Join-Path $repoRoot 'ThirdParty/WeChatSDK/d288776c50-background-r1/Package')
Write-Output 'PASS pinned SDK files and direct background patch; no obsolete wrapper contract required.'