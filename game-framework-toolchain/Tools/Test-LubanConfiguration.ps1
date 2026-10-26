#Requires -Version 5.1
param([string]$TemplateRoot = (Join-Path $PSScriptRoot '..\Templates\GameFramework'))
$ErrorActionPreference = 'Stop'
$TemplateRoot = [IO.Path]::GetFullPath($TemplateRoot)
$work = Join-Path ([IO.Path]::GetTempPath()) ('Luban 配置验收 ' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path "$work\Project\Tools", "$work\文档" -Force | Out-Null
try {
    Copy-Item -LiteralPath "$TemplateRoot\ProjectFiles\ConfigResource" -Destination "$work\Project" -Recurse
    Copy-Item -LiteralPath "$TemplateRoot\ProjectFiles\Tools\Luban" -Destination "$work\Project\Tools" -Recurse
    Copy-Item -LiteralPath "$TemplateRoot\RootFiles\文档\配置表" -Destination "$work\文档" -Recurse
    # 复用导出器的实际文档映射函数，不启动 Unity、不覆盖样例工程。
    $RepoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
    $ProjectName = 'LubanValidation'
    $parseErrors = $null
    $ast = [Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot 'Generate-GameFrameworkProject.ps1'), [ref]$null, [ref]$parseErrors)
    if ($parseErrors) { throw ($parseErrors | Out-String) }
    foreach ($functionName in @('Ensure-Directory', 'Copy-Tree', 'Update-GeneratedProject')) {
        $definition = $ast.Find({ param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq $functionName }, $true)
        if (!$definition) { throw "Missing export function: $functionName" }
        $functionText = $definition.Extent.Text.Replace('$PSScriptRoot', ("'" + $PSScriptRoot.Replace("'", "''") + "'"))
        . ([scriptblock]::Create($functionText))
    }
    Update-GeneratedProject -Root $work -ProjectPath "$work\Project"
    if (!(Test-Path -LiteralPath "$work\文档\规范\通用规范\配置表工具链规范.md") -or (Test-Path -LiteralPath "$work\docs")) { throw 'Export documentation layout mismatch.' }
    if ([IO.File]::ReadAllText("$work\AGENTS.md").Contains('(docs/')) { throw 'Export AGENTS contains stale docs links.' }
    foreach ($relative in @('文档/规范/README.md', '文档/规范/专属规范', '文档/规范/通用规范/功能开启配置规范.md', '文档/规范/通用规范/道具表配置规范.md', '文档/规范/通用规范/常量表配置规范.md', '文档/规范/通用规范/GM表配置规范.md', '文档/规范/通用规范/设置表配置规范.md')) {
        if (!(Test-Path -LiteralPath (Join-Path $work $relative))) { throw "Missing exported rule: $relative" }
    }
    $ruleFiles = @(Get-Item -LiteralPath "$work/AGENTS.md") + @(Get-ChildItem -LiteralPath "$work/文档/规范" -Filter '*.md' -Recurse)
    foreach ($ruleFile in $ruleFiles) {
        foreach ($link in [regex]::Matches([IO.File]::ReadAllText($ruleFile.FullName), '\]\(([^)]+)\)')) {
            $target = $link.Groups[1].Value.Split('#')[0]
            if ($target -and $target -notmatch '^https?://') {
                if (!(Test-Path -LiteralPath (Join-Path $ruleFile.DirectoryName $target))) { throw "Broken rule link: $($ruleFile.Name) -> $target" }
            }
        }
    }
    foreach ($format in @('json', 'bin')) {
        $code = "$work\Project\Assets\Scripts\csharp\login\cfg"
        $data = "$work\Project\Assets\ConfigBin"
        & (Join-Path $PSScriptRoot 'Invoke-LubanScript.ps1') -ConfigResourcePath "$work\Project\ConfigResource" -Format $format
        foreach ($name in @('cfgobj_gmobj', 'cfgobj_settingoptionobj', 'cfgobj_configvalueobj')) {
            $extension = if ($format -eq 'json') { 'json' } else { 'bytes' }
            $file = Join-Path $data "$name.$extension"
            if (!(Test-Path -LiteralPath $file) -or (Get-Item -LiteralPath $file).Length -eq 0) { throw "Missing generated data: $file" }
            if ($format -eq 'json') { Get-Content -LiteralPath $file -Raw -Encoding UTF8 | ConvertFrom-Json | Out-Null }
        }
        if (!(Test-Path -LiteralPath "$code\Tables.cs")) { throw "Missing $format Tables.cs" }
    }
    Write-Host 'Original Luban JSON/bin scripts passed in isolated ConfigResource working directory.'
} finally {
    $resolvedWork = [IO.Path]::GetFullPath($work)
    $tempRoot = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\') + '\'
    if (!$resolvedWork.StartsWith($tempRoot, [StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe temporary cleanup path.' }
    Remove-Item -LiteralPath $resolvedWork -Recurse -Force
}
