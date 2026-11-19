#Requires -Version 5.1
<#
.SYNOPSIS
  Generate a self-contained Game Framework Unity sample project.

.DESCRIPTION
  Copies Templates/GameFramework/ProjectFiles and never reads another Unity project.
  Unity imports, compiles, builds Addressables, reopens, and validates the startup flow.

.EXAMPLE
  .\Generate-GameFrameworkProject.ps1 -ProjectName GameFrameworkTest9 -OutputRoot E:\UnityTemplateTest
#>
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[^\\/:*?"<>|]+$')]
    [string]$ProjectName,

    [string]$OutputRoot = 'D:\DingWork',
    [string]$TemplateRoot,
    [string]$UnityEditor,
    [ValidateSet("Standalone", "WeChat")][string]$Platform = "WeChat",
    [string]$BootstrapUrl,
    [string]$CdnRoot,
    [string]$AppId,
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
$RepoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
if ([string]::IsNullOrWhiteSpace($TemplateRoot)) {
    $TemplateRoot = Join-Path $RepoRoot 'Templates\GameFramework'
}
$TemplateRoot = [IO.Path]::GetFullPath($TemplateRoot)
$ProjectFiles = Join-Path $TemplateRoot 'ProjectFiles'
$OutputRoot = [IO.Path]::GetFullPath($OutputRoot)
$TargetRoot = [IO.Path]::GetFullPath((Join-Path $OutputRoot $ProjectName))
$TargetProject = Join-Path $TargetRoot 'Project'
$StageContainer = Join-Path ([IO.Path]::GetTempPath()) 'game-framework-toolchain'
$StageRoot = Join-Path $StageContainer ([guid]::NewGuid().ToString('N'))
$StageProjectRoot = Join-Path $StageRoot $ProjectName
$StageProject = Join-Path $StageProjectRoot 'Project'
$TexturePackerSource = Join-Path $RepoRoot 'ThirdParty\TexturePacker\4.9.0\win-x64'

function Write-Step([string]$Message) {
    Write-Host "[generate] $Message" -ForegroundColor Cyan
}

function Ensure-Directory([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function Assert-ChildPath([string]$Parent, [string]$Child) {
    $parentFull = [IO.Path]::GetFullPath($Parent).TrimEnd('\') + '\'
    $childFull = [IO.Path]::GetFullPath($Child)
    if (-not $childFull.StartsWith($parentFull, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Unsafe path outside output root: $childFull"
    }
}

function Copy-Tree([string]$Source, [string]$Destination) {
    if (-not (Test-Path -LiteralPath $Source)) {
        throw "Missing source: $Source"
    }
    Ensure-Directory $Destination
    $arguments = @(
        $Source, $Destination, '/E', '/COPY:DAT', '/DCOPY:DAT',
        '/R:2', '/W:1', '/NFL', '/NDL', '/NJH', '/NJS', '/NP',
        '/XD', 'Library', 'Temp', 'Logs', 'UserSettings', '.vs', 'obj', 'Build', 'Builds',
        '/XF', '*.csproj', '*.sln'
    )
    & robocopy @arguments | Out-Null
    if ($LASTEXITCODE -ge 8) {
        throw "robocopy failed ($LASTEXITCODE): $Source -> $Destination"
    }
}

function Get-TemplateUnityVersion {
    $versionFile = Join-Path $ProjectFiles 'ProjectSettings\ProjectVersion.txt'
    if (-not (Test-Path -LiteralPath $versionFile)) {
        throw "Missing template Unity version: $versionFile"
    }
    $line = Select-String -LiteralPath $versionFile -Pattern '^m_EditorVersion:\s*(.+)$' | Select-Object -First 1
    if (-not $line) {
        throw "Cannot read m_EditorVersion from $versionFile"
    }
    return $line.Matches[0].Groups[1].Value.Trim()
}

function Resolve-UnityEditor([string]$ExplicitPath) {
    if ($ExplicitPath) {
        $resolved = [IO.Path]::GetFullPath($ExplicitPath)
        if (-not (Test-Path -LiteralPath $resolved -PathType Leaf)) {
            throw "Unity editor not found: $resolved"
        }
        return $resolved
    }

    $version = Get-TemplateUnityVersion
    $baseVersion = $version
    if ($version -match '^(\d+\.\d+\.\d+f\d+)') {
        $baseVersion = $Matches[1]
    }
    $editorRoots = @(
        (Join-Path $env:ProgramFiles 'Unity\Hub\Editor'),
        'C:\Unity\Editor', 'D:\Unity\Editor', 'E:\Unity\Editor'
    )
    foreach ($root in $editorRoots) {
        foreach ($candidateVersion in @($version, $baseVersion)) {
            $candidate = Join-Path $root "$candidateVersion\Editor\Unity.exe"
            if (Test-Path -LiteralPath $candidate -PathType Leaf) {
                return $candidate
            }
        }
    }
    throw "Unity $version was not found. Pass -UnityEditor explicitly."
}

function Test-LogFailure([string]$LogFile) {
    if (-not (Test-Path -LiteralPath $LogFile)) { return $true }
    return [bool](Select-String -LiteralPath $LogFile -Pattern 'error CS\d+|Scripts have compiler errors|Compilation failed|executeMethod.*failed|batchmode.*aborted|Corrupted Library|database disk image is malformed' -CaseSensitive:$false)
}

function Wait-ProjectUnlocked([string]$ProjectPath, [int]$TimeoutSeconds = 120) {
    $lockFile = Join-Path $ProjectPath 'Temp\UnityLockfile'
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        if (-not (Test-Path -LiteralPath $lockFile)) { return }
        Start-Sleep -Seconds 2
    }
    throw "Unity project lock was not released: $lockFile"
}

function Invoke-UnityBatch([string]$ProjectPath, [string]$LogFile, [string]$ExecuteMethod) {
    $arguments = @('-batchmode', '-nographics', '-projectPath', $ProjectPath, '-logFile', $LogFile)
    if ($ExecuteMethod) {
        $arguments += @('-executeMethod', $ExecuteMethod)
    }
    else {
        $arguments += '-quit'
    }

    $quotedArguments = @($arguments | ForEach-Object { if ($_ -match "\s") { '"' + $_ + '"' } else { $_ } })
    $process = Start-Process -FilePath $script:UnityEditorPath -ArgumentList $quotedArguments -PassThru -WindowStyle Hidden
    if (-not $process.WaitForExit(900000)) {
        try { $process.Kill() } catch { }
        throw "Unity batch timed out after 15 minutes. Log: $LogFile"
    }
    $process.WaitForExit()
    $process.Refresh()
    $exitCode = $process.ExitCode
    if ($null -eq $exitCode -or [string]::IsNullOrWhiteSpace("$exitCode")) {
        $successPattern = if ($ExecuteMethod) {
            '\[export\] Addressables player content built\.'
        }
        else {
            'Exiting batchmode successfully now!|return code 0'
        }
        $successLine = Select-String -LiteralPath $LogFile -Pattern $successPattern -CaseSensitive:$false | Select-Object -Last 1
        $exitCode = if ($successLine) { 0 } else { 1 }
    }
    Wait-ProjectUnlocked -ProjectPath $ProjectPath
    if ($exitCode -ne 0 -or (Test-LogFailure $LogFile)) {
        throw "Unity batch failed (exit $exitCode). Log: $LogFile"
    }
}

function Update-GeneratedProject([string]$Root, [string]$ProjectPath) {
    $agentText = [IO.File]::ReadAllText((Join-Path $RepoRoot 'AGENTS.md')).Replace('(docs/README.md)', '(文档/规范/README.md)').Replace('(docs/', '(文档/规范/通用规范/')
    [IO.File]::WriteAllText((Join-Path $Root 'AGENTS.md'), $agentText, [Text.UTF8Encoding]::new($false))
    $docsSource = Join-Path $RepoRoot 'docs'
    if (Test-Path -LiteralPath $docsSource) {
        Copy-Tree $docsSource (Join-Path $Root '文档\规范\通用规范')
        $generalIndex = Join-Path $Root '文档\规范\通用规范\README.md'
        $indexText = [IO.File]::ReadAllText($generalIndex).Replace('(../AGENTS.md)', '(../../../AGENTS.md)')
        [IO.File]::WriteAllText($generalIndex, $indexText, [Text.UTF8Encoding]::new($false))
        Ensure-Directory (Join-Path $Root '文档\规范\专属规范')
        $rulesIndex = @'
# 项目规范索引

每项任务先读取 [AGENTS.md](../../AGENTS.md)，再按范围读取全部相关通用规范与项目专属约定。

- [通用规范索引](通用规范/README.md)：跨项目开发与配置规则。
- [专属规范目录](专属规范/)：本项目玩法、界面、美术及业务约定。
- [原始配置表](../配置表/)：源表保持原路径。

同一规则只维护一处。新增、移动或修订文档时同步索引、入口和引用，并检查链接。配置契约不等于功能已实现。
'@
        [IO.File]::WriteAllText((Join-Path $Root '文档\规范\README.md'), $rulesIndex, [Text.UTF8Encoding]::new($false))
    }
    $gitignore = Join-Path $PSScriptRoot 'unity-project.gitignore'
    if (Test-Path -LiteralPath $gitignore) {
        Copy-Item -LiteralPath $gitignore -Destination (Join-Path $Root '.gitignore') -Force
    }

    $settings = Join-Path $ProjectPath 'ProjectSettings\ProjectSettings.asset'
    if (Test-Path -LiteralPath $settings) {
        $content = Get-Content -LiteralPath $settings -Raw -Encoding UTF8
        $content = $content -replace '(?m)^  productName:.*$', "  productName: $ProjectName"
        $content = $content -replace '(?m)^  activeInputHandler:\s*[01]$', '  activeInputHandler: 2'
        Set-Content -LiteralPath $settings -Value $content -Encoding UTF8 -NoNewline
    }

    $generatedAt = Get-Date -Format 'yyyy-MM-dd HH:mm'
    $readme = @"
# $ProjectName

Game Framework sample generated from the self-contained `game-framework-toolchain` template.

- Open in Unity Hub: `Project/`
- Project rules: `AGENTS.md`
- Directory rules: `文档/规范/通用规范/目录与分包原则.md`
- Generated: $generatedAt

Addressables are prepared during export. If runtime loading fails, run **Tools -> Addressables -> Build All**.
"@
    Set-Content -LiteralPath (Join-Path $Root 'README.md') -Value $readme -Encoding UTF8
}

function Install-ProjectTexturePacker([string]$ProjectPath) {
    $sourceExe = Join-Path $TexturePackerSource 'bin\TexturePacker.exe'
    if (-not (Test-Path -LiteralPath $sourceExe -PathType Leaf)) {
        throw "TexturePacker tool source is incomplete: $sourceExe"
    }

    $destination = Join-Path $ProjectPath 'Tools\TexturePacker\win-x64'
    Write-Step "Install TexturePacker 4.9.0: $destination"
    Copy-Tree $TexturePackerSource $destination
}

function Assert-ExportComplete([string]$ProjectPath) {
    # Check actual output settings after Unity/platform tooling, not just the source template.
    $projectSettingsCheck = Join-Path $ProjectPath 'Tools\Test-GameFrameworkProjectSettings.ps1'
    if (-not (Test-Path -LiteralPath $projectSettingsCheck -PathType Leaf)) {
        throw "Missing exported project settings check: $projectSettingsCheck"
    }
    & $projectSettingsCheck -ProjectPath $ProjectPath
    Assert-LibraryReadyForReopen -ProjectPath $ProjectPath
    Assert-HybridCLRDependency -ProjectPath $ProjectPath
    if ($Platform -eq 'WeChat') {
        & (Join-Path $ProjectPath 'Tools/Test-WeChatSdkBackground.ps1') -PackagePath (Join-Path $ProjectPath 'Packages/com.qq.weixin.minigame')
    }
    foreach ($relative in @(
        'Assets\Scenes\GameEntrance.unity',
        'Assets\Scenes\UIEditor.unity',
        'Assets\Scripts\csharp\foundation\core\RookieEngine.cs',
        'Assets\Editor\GameFrameworkExportPipeline.cs',
        'Packages\manifest.json',
        'Packages\packages-lock.json',
        'Packages\com.code-philosophy.luban\package.json',
        'ProjectSettings\ProjectVersion.txt'
    )) {
        if (-not (Test-Path -LiteralPath (Join-Path $ProjectPath $relative))) {
            throw "Generated project is incomplete: $relative"
        }
    }
    foreach ($required in @('ConfigResource\luban.conf', 'ConfigResource\gen_json.bat', 'ConfigResource\gen_bin.bat', 'Tools\Luban\Luban.dll')) {
        if (!(Test-Path -LiteralPath (Join-Path $ProjectPath $required))) { throw "Missing exported Luban file: $required" }
    }
    $exportRoot = Split-Path $ProjectPath -Parent
    foreach ($required in @('文档\规范\README.md', '文档\规范\专属规范', '文档\规范\通用规范\README.md', '文档\配置表\__beans__.xlsx', '文档\配置表\__enums__.xlsx', '文档\配置表\__tables__.xlsx', '文档\配置表\GMResource.xlsx', '文档\配置表\SettingOptionResource.xlsx', '文档\配置表\ConfigValueResource.xlsx')) {
        if (!(Test-Path -LiteralPath (Join-Path $exportRoot $required))) { throw "Missing exported document: $required" }
    }
    if (Test-Path -LiteralPath (Join-Path $exportRoot 'docs')) {
        throw 'Generated project must use 文档/规范 instead of root docs.'
    }
    $marker = Join-Path $ProjectPath 'Assets\AddressableAssetsData\.export-baseline-complete.txt'
    if (-not ((Test-Path -LiteralPath $marker) -and ((Get-Content -LiteralPath $marker -Raw) -match '^ok\b'))) {
        throw "Addressables completion marker missing or failed: $marker"
    }
    $bundles = Get-ChildItem -LiteralPath (Join-Path $ProjectPath 'Library\com.unity.addressables') -Filter '*.bundle' -File -Recurse -ErrorAction SilentlyContinue
    if ($Platform -eq 'WeChat') { $bundles = Get-ChildItem -LiteralPath (Join-Path $ProjectPath 'ServerData') -Filter '*.bundle' -File -Recurse -ErrorAction SilentlyContinue }
    if (-not $bundles) {
        throw 'Addressables build produced no bundle files.'
    }
}

function Get-DirectoryLength([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return [long]0 }
    $measurement = Get-ChildItem -LiteralPath $Path -File -Recurse -Force -ErrorAction SilentlyContinue |
        Measure-Object -Property Length -Sum
    if ($null -eq $measurement.Sum) { return [long]0 }
    return [long]$measurement.Sum
}

function Assert-LibraryReadyForReopen([string]$ProjectPath) {
    $library = Join-Path $ProjectPath 'Library'
    if (Test-Path -LiteralPath (Join-Path $library 'CorruptedLibraryDetection')) {
        throw "Unity detected an incomplete or corrupt Library: $library"
    }
    foreach ($metadata in @('SourceAssetDB', 'ArtifactDB', 'LibraryFormatVersion.txt')) {
        $path = Join-Path $library $metadata
        if (-not (Test-Path -LiteralPath $path -PathType Leaf) -or (Get-Item -LiteralPath $path).Length -eq 0) {
            throw "Missing Library integrity metadata: $path"
        }
    }
}

function Assert-HybridCLRDependency([string]$ProjectPath) {
    $packageName = 'com.code-philosophy.hybridclr'
    $manifest = Get-Content -LiteralPath (Join-Path $ProjectPath 'Packages/manifest.json') -Raw | ConvertFrom-Json
    $locked = Get-Content -LiteralPath (Join-Path $ProjectPath 'Packages/packages-lock.json') -Raw | ConvertFrom-Json
    $requested = $manifest.dependencies.$packageName
    $platformConfig = Join-Path $ProjectPath 'ProjectSettings/FrameworkPlatform.json'
    if (Test-Path -LiteralPath $platformConfig -PathType Leaf) {
        $configuredPlatform = (Get-Content -LiteralPath $platformConfig -Raw | ConvertFrom-Json).platform
        # Explicit Standalone removes HybridCLR by design; a declared dependency still must validate.
        if ($configuredPlatform -eq 'Standalone' -and -not $requested) { return }
    }
    $dependency = $locked.dependencies.$packageName
    if (-not $requested -or -not $dependency -or $dependency.source -ne 'git' -or
        $dependency.version -ne $requested -or $dependency.hash -notmatch '^[a-fA-F0-9]{40}$' -or
        -not $requested.EndsWith('#' + $dependency.hash, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'HybridCLR manifest/lock must agree on a pinned git revision.'
    }
    $cache = Join-Path $ProjectPath 'Library/PackageCache'
    $resolved = @(Get-ChildItem -LiteralPath $cache -Directory -Filter "$packageName@*" -ErrorAction SilentlyContinue | Where-Object {
        $revision = $_.Name.Substring($packageName.Length + 1)
        $revision -match '^[a-fA-F0-9]{7,40}$' -and $dependency.hash.StartsWith($revision, [StringComparison]::OrdinalIgnoreCase)
    })
    if ($resolved.Count -ne 1) { throw 'HybridCLR pinned resolved package is missing or ambiguous.' }
    foreach ($relative in @('package.json', 'Runtime/HybridCLR.Runtime.asmdef', 'Runtime/RuntimeApi.cs', 'Editor/HybridCLR.Editor.asmdef')) {
        $file = Join-Path $resolved[0].FullName $relative
        if (-not (Test-Path -LiteralPath $file -PathType Leaf) -or (Get-Item -LiteralPath $file).Length -eq 0) {
            throw "HybridCLR resolved package is incomplete: $file"
        }
    }
    $package = Get-Content -LiteralPath (Join-Path $resolved[0].FullName 'package.json') -Raw | ConvertFrom-Json
    if ($package.name -ne $packageName) { throw 'HybridCLR resolved package identity mismatch.' }
}

function Assert-FirstRunEvidence([string]$ProjectPath, [string]$LogFile) {
    $marker = Join-Path $ProjectPath 'Library/template-runtime-validation.txt'
    $expected = 'ok: Opening -> Login -> Option -> Loading -> Main'
    if (-not (Test-Path -LiteralPath $marker -PathType Leaf) -or
        [IO.File]::ReadAllText($marker).Trim() -ne $expected) {
        throw 'First-run startup flow did not produce its success marker.'
    }
    if ((Test-LogFailure $LogFile) -or
        -not (Select-String -LiteralPath $LogFile -Pattern 'BatchMode:\s*0') -or
        (Select-String -LiteralPath $LogFile -Pattern '\b\w+Exception:|Assertion failed|^Error:|Asset import failed' -CaseSensitive:$false)) {
        throw "First-run non-batch editor validation failed. Log: $LogFile"
    }
}

function Invoke-UnityFirstRun([string]$ProjectPath, [string]$LogFile) {
    # Remove only this validator's old result; a previous run cannot satisfy this gate.
    $marker = Join-Path $ProjectPath 'Library/template-runtime-validation.txt'
    if (Test-Path -LiteralPath $marker) { Remove-Item -LiteralPath $marker -Force }
    if (Test-Path -LiteralPath $LogFile) { Remove-Item -LiteralPath $LogFile -Force }
    $arguments = @('-projectPath', $ProjectPath, '-logFile', $LogFile,
        '-executeMethod', 'FrameworkTemplateValidation.RunPlayMode')
    $quoted = @($arguments | ForEach-Object { if ($_ -match '\s') { '"' + $_ + '"' } else { $_ } })
    $process = Start-Process -FilePath $script:UnityEditorPath -ArgumentList $quoted -PassThru -WindowStyle Hidden
    if (-not $process.WaitForExit(900000)) {
        try { $process.Kill() } catch { }
        throw "Owned first-run validation timed out after 15 minutes. Log: $LogFile"
    }
    $process.WaitForExit()
    $process.Refresh()
    Wait-ProjectUnlocked -ProjectPath $ProjectPath
    if ($null -eq $process.ExitCode -or $process.ExitCode -ne 0) {
        throw "First-run editor failed (exit $($process.ExitCode)). Log: $LogFile"
    }
    Assert-FirstRunEvidence -ProjectPath $ProjectPath -LogFile $LogFile
    Assert-ExportComplete -ProjectPath $ProjectPath
}

function Optimize-GeneratedLibrary([string]$ProjectPath) {
    $library = [IO.Path]::GetFullPath((Join-Path $ProjectPath 'Library'))
    if (Test-Path -LiteralPath (Join-Path $ProjectPath 'Temp\UnityLockfile')) {
        throw "Cannot prune an open Unity project: $ProjectPath"
    }
    Assert-LibraryReadyForReopen -ProjectPath $ProjectPath
    $addressables = Join-Path $library 'com.unity.addressables'
    if (-not (Test-Path -LiteralPath $addressables -PathType Container)) {
        throw "Cannot optimize Library because Addressables output is missing: $addressables"
    }
    Assert-ChildPath -Parent $ProjectPath -Child $library
    $before = Get-DirectoryLength -Path $library
    # Remove only known regenerable caches. Preserve AssetDatabase indexes, version metadata,
    # Addressables outputs, and unknown metadata instead of creating a Library skeleton.
    foreach ($name in @('Artifacts', 'BuildCache', 'Bee', 'ScriptAssemblies', 'ShaderCache')) {
        $cachePath = [IO.Path]::GetFullPath((Join-Path $library $name))
        Assert-ChildPath -Parent $library -Child $cachePath
        if (Test-Path -LiteralPath $cachePath) { Remove-Item -LiteralPath $cachePath -Recurse -Force }
    }
    Assert-LibraryReadyForReopen -ProjectPath $ProjectPath
    $after = Get-DirectoryLength -Path $library
    $removedMb = [math]::Round(($before - $after) / 1MB, 1)
    Write-Step "Optimized Library: removed $removedMb MB; retained AssetDatabase integrity metadata and Addressables. Reopen validation is still required."
}

Assert-ChildPath -Parent $OutputRoot -Child $TargetRoot
if (-not (Test-Path -LiteralPath $ProjectFiles)) {
    throw "Self-contained template missing: $ProjectFiles"
}
foreach ($requiredRoot in @('Assets', 'Packages', 'ProjectSettings')) {
    if (-not (Test-Path -LiteralPath (Join-Path $ProjectFiles $requiredRoot))) {
        throw "Template root missing: $requiredRoot"
    }
}
# Reject a regressed source before creating staging or replacing an existing target.
$sourceSettingsCheck = Join-Path $ProjectFiles 'Tools\Test-GameFrameworkProjectSettings.ps1'
if (-not (Test-Path -LiteralPath $sourceSettingsCheck -PathType Leaf)) {
    throw "Missing template project settings check: $sourceSettingsCheck"
}
& $sourceSettingsCheck -ProjectPath $ProjectFiles
if (Test-Path -LiteralPath $TargetRoot) {
    if (-not $Force) {
        throw "Target already exists: $TargetRoot. Use -Force to replace it explicitly."
    }
    Write-Step "Removing existing target because -Force was supplied: $TargetRoot"
    Remove-Item -LiteralPath $TargetRoot -Recurse -Force
}

$exportSucceeded = $false
try {
    Write-Step "Copy self-contained template: $ProjectFiles"
    Ensure-Directory $StageProject
    Copy-Tree $ProjectFiles $StageProject
    Copy-Tree (Join-Path $TemplateRoot 'RootFiles') $StageProjectRoot
    Install-ProjectTexturePacker -ProjectPath $StageProject
    if ($Platform -eq 'WeChat') {
        $sdkSource = Join-Path $RepoRoot 'ThirdParty/WeChatSDK/d288776c50-background-r1/Package'
        & (Join-Path $ProjectFiles 'Tools/Test-WeChatSdkBackground.ps1') -PackagePath $sdkSource
        Copy-Tree $sdkSource (Join-Path $StageProject 'Packages/com.qq.weixin.minigame')
    }
    Update-GeneratedProject -Root $StageProjectRoot -ProjectPath $StageProject
    $platformArgs = @{ ProjectPath = $StageProject; Platform = $Platform }
    foreach ($key in @('BootstrapUrl', 'CdnRoot', 'AppId')) {
        if ($PSBoundParameters.ContainsKey($key)) { $platformArgs[$key] = $PSBoundParameters[$key] }
    }
    & (Join-Path $PSScriptRoot 'Set-GameFrameworkPlatform.ps1') @platformArgs
    Ensure-Directory (Join-Path $StageProjectRoot 'Tools')
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'Set-GameFrameworkPlatform.ps1') -Destination (Join-Path $StageProjectRoot 'Tools')
    $releaseWrapper = Join-Path $RepoRoot '../game-build-release/assets/Build-WeChatHotUpdate.ps1'
    if (!(Test-Path -LiteralPath $releaseWrapper)) { throw 'Missing sibling game-build-release skill.' }
    Copy-Item -LiteralPath $releaseWrapper -Destination (Join-Path $StageProjectRoot 'Tools')

    $script:UnityEditorPath = Resolve-UnityEditor -ExplicitPath $UnityEditor
    Write-Step "Unity: $script:UnityEditorPath"
    $logs = Join-Path $StageProject 'Logs'
    Ensure-Directory $logs
    Write-Step 'Generate baseline Luban JSON and C# from project workbooks'
    & (Join-Path $PSScriptRoot 'Invoke-LubanScript.ps1') -ConfigResourcePath (Join-Path $StageProject 'ConfigResource') -Format json
    Write-Step 'Unity pass 1/2: import and compile'
    Invoke-UnityBatch -ProjectPath $StageProject -LogFile (Join-Path $logs 'export-import.log')
    Write-Step 'Unity pass 2/2: initialize and build Addressables'
    Invoke-UnityBatch -ProjectPath $StageProject -LogFile (Join-Path $logs 'export-addressables.log') -ExecuteMethod 'GameFrameworkExportPipeline.ExportBaseline'

    Assert-ExportComplete -ProjectPath $StageProject
    Optimize-GeneratedLibrary -ProjectPath $StageProject
    Write-Step 'Reopen pruned staging project and validate AssetDatabase initialization'
    Invoke-UnityBatch -ProjectPath $StageProject -LogFile (Join-Path $logs 'export-reopen.log')
    Assert-ExportComplete -ProjectPath $StageProject
    Ensure-Directory $OutputRoot
    Move-Item -LiteralPath $StageProjectRoot -Destination $TargetRoot
    Write-Step 'Reopen project at final delivery path'
    Invoke-UnityBatch -ProjectPath $TargetProject -LogFile (Join-Path $TargetProject 'Logs\export-final-open.log')
    Assert-ExportComplete -ProjectPath $TargetProject
    Write-Step 'Validate first non-batch editor startup and runtime at final delivery path'
    Invoke-UnityFirstRun -ProjectPath $TargetProject -LogFile (Join-Path $TargetProject 'Logs\export-first-run.log')
    # Do not invalidate the Library state that just passed actual final-path reopening.
    $exportSucceeded = $true
    Write-Step "Done: $TargetRoot"
    Write-Step "Open in Unity Hub: $TargetProject"
}
finally {
    if ($exportSucceeded -and (Test-Path -LiteralPath $StageRoot)) {
        Remove-Item -LiteralPath $StageRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
    elseif (Test-Path -LiteralPath $StageRoot) {
        Write-Host "[generate] Failed staging retained for diagnosis: $StageRoot" -ForegroundColor Yellow
    }
}
