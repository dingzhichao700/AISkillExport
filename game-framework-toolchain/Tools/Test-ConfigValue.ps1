param([string]$ProjectPath = (Join-Path $PSScriptRoot '../Templates/GameFramework/ProjectFiles'))
$ErrorActionPreference = 'Stop'
$project = (Resolve-Path -LiteralPath $ProjectPath).Path
$work = Join-Path ([IO.Path]::GetTempPath()) ('ConfigValueTests-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $work | Out-Null
try {
    $sources = @(
        "$project/Assets/Scripts/csharp/login/cfg/**/*.cs",
        "$project/Packages/com.code-philosophy.luban/Runtime/*.cs",
        "$project/Packages/com.code-philosophy.luban/Runtime/SimpleJSON/SimpleJSON.cs",
        "$project/Assets/Scripts/csharp/login/config/CfgManager.cs",
        "$project/Assets/Scripts/csharp/login/config/helper/ConfigValueHelper.cs",
        "$project/Assets/Scripts/csharp/foundation/core/resource/constant/ResourceConst.cs",
        "$PSScriptRoot/Tests/ConfigValueRegression.cs"
    )
    $items = ($sources | ForEach-Object { '<Compile Include="' + [Security.SecurityElement]::Escape($_) + '" />' }) -join "`n"
    $xml = '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net8.0</TargetFramework><OutputType>Exe</OutputType><EnableDefaultCompileItems>false</EnableDefaultCompileItems><AllowUnsafeBlocks>true</AllowUnsafeBlocks></PropertyGroup><ItemGroup>' + $items + '</ItemGroup></Project>'
    [IO.File]::WriteAllText((Join-Path $work 'Test.csproj'), $xml)
    & dotnet run --project (Join-Path $work 'Test.csproj') -- "$project/Assets/ConfigBin"
    if ($LASTEXITCODE -ne 0) { throw 'ConfigValue regression failed.' }
} finally {
    $resolved = [IO.Path]::GetFullPath($work)
    $tempRoot = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\') + '\'
    if (!$resolved.StartsWith($tempRoot, [StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe cleanup path.' }
    Remove-Item -LiteralPath $resolved -Recurse -Force
}
