<#
Example:
.\Pack-Animations.ps1 -InputDirectory 'D:\Delivery\Fighter' -OutputDirectory 'D:\Output\fighter' -TexturePacker 'D:\Tools\TexturePacker.exe'
Add -Overwrite to replace existing output, -Square for square POT textures.
Exit codes: 0 success; 1 arguments/startup; 2 one or more animations failed.
Without command-line arguments the application still opens its normal UI.
#>
param(
    [Parameter(Mandatory=$true)][string]$InputDirectory,
    [Parameter(Mandatory=$true)][string]$OutputDirectory,
    [Parameter(Mandatory=$true)][string]$TexturePacker,
    [string]$Executable = (Join-Path $PSScriptRoot 'bin\Debug\FrameAnimeExportor.exe'),
    [switch]$Overwrite,
    [switch]$Square
)
$ErrorActionPreference = 'Stop'
try {
    # Redirect handles explicitly because the application is a Windows GUI executable.
    $parts = @('pack')
    foreach ($pair in @(@('--input', $InputDirectory), @('--output', $OutputDirectory), @('--texture-packer', $TexturePacker))) {
        $path = [IO.Path]::GetFullPath($pair[1]).Replace('\', '/')
        if ($path.Contains('"')) { throw 'Invalid quote in path.' }
        $parts += $pair[0]
        $parts += '"' + $path + '"'
    }
    if ($Overwrite) { $parts += '--overwrite' }
    if ($Square) { $parts += '--square' }
    $start = [Diagnostics.ProcessStartInfo]::new([IO.Path]::GetFullPath($Executable))
    $start.Arguments = $parts -join ' '
    $start.UseShellExecute = $false
    $start.CreateNoWindow = $true
    $start.RedirectStandardOutput = $true
    $start.RedirectStandardError = $true
    $process = [Diagnostics.Process]::Start($start)
    $stdout = $process.StandardOutput.ReadToEndAsync()
    $stderr = $process.StandardError.ReadToEndAsync()
    $process.WaitForExit()
    [Console]::Out.Write($stdout.Result)
    [Console]::Error.Write($stderr.Result)
    $code = $process.ExitCode
    $process.Dispose()
    exit $code
} catch {
    [Console]::Error.WriteLine($_.Exception.Message)
    exit 1
}
