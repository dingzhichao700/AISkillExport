#Requires -Version 5.1
param(
    [Parameter(Mandatory = $true)][string]$ConfigResourcePath,
    [ValidateSet('json', 'bin')][string]$Format = 'json'
)
$ErrorActionPreference = 'Stop'
Push-Location -LiteralPath $ConfigResourcePath
try {
    # Preserve the original interactive BAT. Only this automation invocation redirects input.
    $output = @(& $env:ComSpec /d /c "call gen_$Format.bat <nul" 2>&1)
    $output | ForEach-Object { Write-Host $_ }
    $log = $output -join "`n"
    # PAUSE can replace dotnet's exit code; require Luban's successful completion log.
    if ($log -notmatch '\|INFO\|bye~' -or $log -match '\|(?:ERROR|FATAL)\|') {
        throw "Luban $Format generation did not complete successfully."
    }
} finally {
    Pop-Location
}
