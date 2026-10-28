#Requires -Version 5.1
param([string]$TemplateRoot)

$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($TemplateRoot)) {
    $TemplateRoot = Join-Path $PSScriptRoot '..\Templates\GameFramework'
}
$TemplateRoot = [IO.Path]::GetFullPath($TemplateRoot)
$ProjectFiles = Join-Path $TemplateRoot 'ProjectFiles'
$RepoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$errors = [Collections.Generic.List[string]]::new()

foreach ($relative in @('ConfigResource\luban.conf', 'ConfigResource\Defines\builtin.xml', 'ConfigResource\gen_json.bat', 'ConfigResource\gen_bin.bat', 'ConfigResource\gen.sh', 'Tools\Luban\Luban.dll', 'Tools\Luban\Luban.runtimeconfig.json', 'Tools\Luban.lock.json')) {
    if (!(Test-Path -LiteralPath (Join-Path $ProjectFiles $relative))) { $errors.Add("Missing Luban tooling: $relative") }
}
foreach ($name in @('__beans__', '__enums__', '__tables__', 'GMResource', 'SettingOptionResource', 'ConfigValueResource')) {
    if (!(Test-Path -LiteralPath (Join-Path $TemplateRoot "RootFiles\文档\配置表\$name.xlsx"))) { $errors.Add("Missing source workbook: $name") }
}
foreach ($required in @('Assets/Scripts/csharp/login/config/helper/ConfigValueHelper.cs', 'Assets/Scripts/csharp/login/cfg/resource/ConfigValueResource.cs', 'Assets/ConfigBin/cfgobj_configvalueobj.json')) {
    if (!(Test-Path -LiteralPath (Join-Path $ProjectFiles $required))) { $errors.Add("Missing constant configuration baseline: $required") }
}
$lockPath = Join-Path $ProjectFiles 'Tools\Luban.lock.json'
if (Test-Path -LiteralPath $lockPath) {
    $toolLock = Get-Content -LiteralPath $lockPath -Raw -Encoding UTF8 | ConvertFrom-Json
    foreach ($entry in $toolLock.files) {
        $file = Join-Path $ProjectFiles ('Tools\Luban\' + $entry.path)
        if (!(Test-Path -LiteralPath $file) -or (Get-FileHash -LiteralPath $file).Hash -ne $entry.sha256) { $errors.Add("Luban distribution mismatch: $($entry.path)") }
    }
}

function Require-Path([string]$RelativePath) {
    if (-not (Test-Path -LiteralPath (Join-Path $ProjectFiles $RelativePath))) {
        $errors.Add("Missing: $RelativePath")
    }
}

foreach ($path in @(
    'Assets',
    'Packages\manifest.json',
    'Packages\packages-lock.json',
    'Packages\com.code-philosophy.luban\package.json',
    'ProjectSettings\ProjectVersion.txt',
    'ProjectSettings\ProjectSettings.asset',
    'ProjectSettings\EditorBuildSettings.asset',
    'Assets\Scenes\GameEntrance.unity',
    'Assets\Scenes\UIEditor.unity',
    'Assets\Scripts\csharp\foundation\core\RookieEngine.cs',
    'Assets\Scripts\csharp\foundation\core\component\frameAnimation\view\FrameShadowGraphic.cs',
    'Assets\Scripts\csharp\foundation\core\component\frameAnimation\view\FrameShadowGraphic.cs.meta',
    'Assets\Scripts\csharp\login\config\CfgManager.cs',
    'Assets\Scripts\csharp\login\opening\OpeningPanel.cs',
    'Assets\Scripts\csharp\main\gm\GMControl.cs',
    'Assets\Scripts\csharp\main\gm\view\GmPanel.cs',
    'Assets\Scripts\csharp\main\gm\view\GMItem.cs',
    'Assets\Prefab\default\gm\GmPanel.prefab',
    'Assets\Art\atlas\default\gm.png',
    'Assets\Editor\GameFrameworkExportPipeline.cs',
    'Assets\Editor\uiComponent\UIBinderInspector.cs',
    'Assets\AddressableAssetsData\AddressableAssetSettings.asset',
    'Assets\Prefab\title\option\OptionPanel.prefab',
    'Assets\Art\unpack\title\title\bg_option.png'
)) { Require-Path $path }

foreach ($forbiddenDirectory in @('Library', 'Temp', 'Logs', 'UserSettings', '.vs', 'obj')) {
    if (Test-Path -LiteralPath (Join-Path $ProjectFiles $forbiddenDirectory)) {
        $errors.Add("Forbidden generated directory: $forbiddenDirectory")
    }
}

$forbiddenPatterns = @(
    '[\\/]UIReference([\\/]|\.meta$)',
    '[\\/](bag|bagcartoon|baglegendary|shop)([\\/]|\.meta$)',
    '[\\/](bag|bagcartoon|baglegendary|shop)\.png(\.meta)?$'
)
Get-ChildItem -LiteralPath $ProjectFiles -File -Recurse -Force | ForEach-Object {
    foreach ($pattern in $forbiddenPatterns) {
        if ($_.FullName -match $pattern) {
            $errors.Add("Sample-only file in template: $($_.FullName.Substring($ProjectFiles.Length + 1))")
            break
        }
    }
}

$allowedAiuiFiles = @(
    'Assets\Editor\AIUI.meta',
    'Assets\Editor\AIUI\AIUIExportQueue.cs',
    'Assets\Editor\AIUI\AIUIExportQueue.cs.meta'
)
$aiuiRoot = Join-Path $ProjectFiles 'Assets\Editor\AIUI'
if (Test-Path -LiteralPath $aiuiRoot) {
    Get-ChildItem -LiteralPath $aiuiRoot -File -Recurse -Force | ForEach-Object {
        $relative = $_.FullName.Substring($ProjectFiles.Length + 1)
        if ($relative -notin $allowedAiuiFiles) {
            $errors.Add("Temporary AIUI exporter in template: $relative")
        }
    }
}

$manifestPath = Join-Path $ProjectFiles 'Packages\manifest.json'
if (Test-Path -LiteralPath $manifestPath) {
    $manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8
    foreach ($dependency in @('com.code-philosophy.luban', 'com.unity.addressables', 'com.unity.inputsystem', 'com.unity.textmeshpro', 'com.unity.modules.physics', 'com.unity.modules.physics2d', 'com.unity.modules.particlesystem')) {
        if ($manifest -notmatch [regex]::Escape('"' + $dependency + '"')) {
            $errors.Add("Required package missing from manifest: $dependency")
        }
    }
    foreach ($forbiddenPackage in @('com.unity.render-pipelines.universal', 'runtimeinspector')) {
        if ($manifest -match [regex]::Escape($forbiddenPackage)) {
            $errors.Add("Forbidden package in manifest: $forbiddenPackage")
        }
    }
}

$rookieEnginePath = Join-Path $ProjectFiles 'Assets\Scripts\csharp\foundation\core\RookieEngine.cs'
if (Test-Path -LiteralPath $rookieEnginePath) {
    $rookieEngine = Get-Content -LiteralPath $rookieEnginePath -Raw -Encoding UTF8
    $timerInit = $rookieEngine.IndexOf('_timer = new Timer()', [StringComparison]::Ordinal)
    $entryStart = $rookieEngine.IndexOf('GameEntrance.ins.StartGame()', [StringComparison]::Ordinal)
    if ($timerInit -lt 0 -or $entryStart -lt 0 -or $timerInit -gt $entryStart -or $rookieEngine -match 'PersistentDataControl') {
        $errors.Add('Foundation must initialize timer before starting modules and must not reference business persistence.')
    }
}

$cfgManagerPath = Join-Path $ProjectFiles 'Assets\Scripts\csharp\login\config\CfgManager.cs'
if (Test-Path -LiteralPath $cfgManagerPath) {
    $cfgManager = Get-Content -LiteralPath $cfgManagerPath -Raw -Encoding UTF8
    if ($cfgManager -notmatch 'public static void Init\(\)' -or $cfgManager -notmatch 'ResourceManager\.GetJsonNode\(path\)') {
        $errors.Add('CfgManager must initialize Luban Tables from JSON already preloaded by ResourceManager.')
    }
    if ($cfgManager -notmatch 'CfgManager 尚未初始化' -or $cfgManager -notmatch 'Luban 配置尚未通过 Addressables 预加载') {
        $errors.Add('CfgManager must fail explicitly on early table access or missing preloaded JSON.')
    }
}

$openingPanelPath = Join-Path $ProjectFiles 'Assets\Scripts\csharp\login\opening\OpeningPanel.cs'
if (Test-Path -LiteralPath $openingPanelPath) {
    $openingPanel = Get-Content -LiteralPath $openingPanelPath -Raw -Encoding UTF8
    if ($openingPanel -match 'CfgManager|ALL_CONFIG_LIST|LoadModuleAsync') {
        $errors.Add('OpeningPanel must not initialize configuration or Main.')
    }
    $loginPanel = Get-Content -LiteralPath (Join-Path $ProjectFiles 'Assets/Scripts/csharp/login/title/view/LoginPanel.cs') -Raw -Encoding UTF8
    if ($loginPanel -notmatch 'CfgManager.EnsureLoadedAsync') {
        $errors.Add('LoginPanel must initialize configurations before entering dependent screens.')
    }
}

$uiBinderInspectorPath = Join-Path $ProjectFiles 'Assets\Editor\uiComponent\UIBinderInspector.cs'
if (Test-Path -LiteralPath $uiBinderInspectorPath) {
    $uiBinderInspector = Get-Content -LiteralPath $uiBinderInspectorPath -Raw -Encoding UTF8
    if ($uiBinderInspector -notmatch 'EnsureComponentNamespaces') {
        $errors.Add('UIBinderInspector must add namespaces required by exported component types.')
    }
    if ($uiBinderInspector -notmatch 'SyncSiblingCloneBinders') {
        $errors.Add('UIBinderInspector must synchronize ScrollList item bindings to retained sibling clones.')
    }
    if ($uiBinderInspector -notmatch 'AnimationUtility\.CalculateTransformPath') {
        $errors.Add('UIBinder clone synchronization must resolve member targets by relative transform path.')
    }
}

$groupFiles = Get-ChildItem -LiteralPath (Join-Path $ProjectFiles 'Assets\AddressableAssetsData\AssetGroups') -Filter '*.asset' -File -ErrorAction SilentlyContinue
foreach ($groupFile in $groupFiles) {
    $matches = Select-String -LiteralPath $groupFile.FullName -Pattern 'bag|bagcartoon|baglegendary|shop|UIReference' -CaseSensitive:$false
    if ($matches) {
        $errors.Add("Sample-only Addressables entry in $($groupFile.Name)")
    }
}

$prebuiltCache = Join-Path $TemplateRoot 'AddressablesBuild'
if (Test-Path -LiteralPath $prebuiltCache) {
    $errors.Add('AddressablesBuild must not exist; exports must build Addressables from ProjectFiles.')
}

$generator = Join-Path $PSScriptRoot 'Generate-GameFrameworkProject.ps1'
if (Test-Path -LiteralPath $generator) {
    $external = Select-String -LiteralPath $generator -Pattern 'GoldenSource|B1Source|FromB1|myWorkSpace' -CaseSensitive:$false
    if ($external) {
        $errors.Add('Generator still contains an external-project dependency.')
    }
    $cacheBranch = Select-String -LiteralPath $generator -Pattern 'SkipAddressablesBuild|Copy-PrebuiltAddressables|AddressablesBuild' -CaseSensitive:$false
    if ($cacheBranch) {
        $errors.Add('Generator still contains a prebuilt Addressables cache branch.')
    }
    $generatorText = Get-Content -LiteralPath $generator -Raw -Encoding UTF8
    if ($generatorText -notmatch 'Optimize-GeneratedLibrary' -or $generatorText -notmatch "item\.Name -eq 'com\.unity\.addressables'") {
        $errors.Add('Generator must prune regenerable Library caches while retaining built Addressables output.')
    }
    if ($generatorText -notmatch 'Install-ProjectTexturePacker') {
        $errors.Add('Generator must deploy the repository TexturePacker into each generated project.')
    }
}

$texturePackerExe = Join-Path $RepoRoot 'ThirdParty\TexturePacker\4.9.0\win-x64\bin\TexturePacker.exe'
if (-not (Test-Path -LiteralPath $texturePackerExe -PathType Leaf)) {
    $errors.Add('Repository TexturePacker 4.9.0 executable is missing.')
}

$texturePackerTool = Join-Path $ProjectFiles 'Assets\Editor\TexturePackerTool.cs'
if (Test-Path -LiteralPath $texturePackerTool -PathType Leaf) {
    $texturePackerToolText = Get-Content -LiteralPath $texturePackerTool -Raw -Encoding UTF8
    if ($texturePackerToolText -notmatch '\.\./Tools/TexturePacker/win-x64/bin/TexturePacker\.exe') {
        $errors.Add('TexturePackerTool must resolve the project-local executable first.')
    }
    if ($texturePackerToolText -match '[A-Za-z]:[/\\].*TexturePack') {
        $errors.Add('TexturePackerTool must not contain a machine-specific absolute executable path.')
    }
}

# A fresh default project must already contain the WeChat integration inputs.
$platformConfig = Get-Content (Join-Path $ProjectFiles 'ProjectSettings/FrameworkPlatform.json') -Raw | ConvertFrom-Json
if ($platformConfig.platform -ne 'WeChat') { $errors.Add('Template default must be WeChat-ready.') }
$packageConfig = Get-Content (Join-Path $ProjectFiles 'Packages/manifest.json') -Raw | ConvertFrom-Json
foreach ($dependency in @('com.code-philosophy.hybridclr', 'com.qq.weixin.minigame')) {
    if (!$packageConfig.dependencies.$dependency) { $errors.Add("Missing WeChat dependency: $dependency") }
}
$hybridConfig = Get-Content (Join-Path $ProjectFiles 'ProjectSettings/HybridCLRSettings.asset') -Raw
foreach ($module in @('login/Login', 'main/Main')) {
    $meta = Get-Content (Join-Path $ProjectFiles ("Assets/Scripts/csharp/" + $module + '.asmdef.meta')) -Raw
    $moduleGuid = [regex]::Match($meta, 'guid: ([a-f0-9]+)').Groups[1].Value
    if (!$moduleGuid -or !$hybridConfig.Contains($moduleGuid)) { $errors.Add("Missing hot-update assembly: $module") }
}
if ((Get-Content (Join-Path $ProjectFiles 'Assets/csc.rsp') -Raw) -notmatch 'GAMEFRAMEWORK_WECHAT') { $errors.Add('Missing WeChat compilation symbol.') }

# The baseline must not recreate the old whole-common-atlas migration.
foreach ($obsolete in @('Assets/Art/atlas/title/common.png', 'Assets/Art/atlasSource/title/common')) {
    if (Test-Path -LiteralPath (Join-Path $ProjectFiles $obsolete)) {
        $errors.Add("Obsolete title common atlas baseline: $obsolete")
    }
}
$dependencyChecker = Join-Path $ProjectFiles 'Assets/Editor/addressable/AddressablesPrefabDependencyChecker.cs'
if (!(Test-Path -LiteralPath $dependencyChecker)) {
    $errors.Add('Missing stage dependency checker.')
}
foreach ($buildEntry in @('Assets/Editor/addressable/AddressablesAutoBuilder.cs', 'Assets/Editor/FrameworkWeChatBuild.cs')) {
    $buildSource = Get-Content -LiteralPath (Join-Path $ProjectFiles $buildEntry) -Raw
    $buildCount = [regex]::Matches($buildSource, 'AddressableAssetSettings.BuildPlayerContent\(').Count
    $gateCount = [regex]::Matches($buildSource, 'AddressablesPrefabDependencyChecker.ValidateOrThrow\(\);\s*AddressableAssetSettings.BuildPlayerContent\(').Count
    if ($buildCount -eq 0 -or $gateCount -ne $buildCount) {
        $errors.Add("Every content build must validate stage dependencies first: $buildEntry")
    }
}

try {
    & (Join-Path $PSScriptRoot 'Test-GMBaseline.ps1') -ProjectFiles $ProjectFiles
} catch {
    $errors.Add("GM/configuration validation: $($_.Exception.Message)")
}

foreach ($animationSourceFile in @('Tools/AnimationSource/animation_source.py', 'Tools/AnimationSource/requirements.txt')) {
    if (-not (Test-Path -LiteralPath (Join-Path $ProjectFiles $animationSourceFile) -PathType Leaf)) {
        $errors.Add("Missing animation source delivery tool: $animationSourceFile")
    }
}

if ($errors.Count -gt 0) {
    $errors | ForEach-Object { Write-Error $_ -ErrorAction Continue }
    throw "Template validation failed with $($errors.Count) error(s)."
}

$version = Get-Content -LiteralPath (Join-Path $ProjectFiles 'ProjectSettings\ProjectVersion.txt') -Encoding UTF8 | Select-Object -First 1
& (Join-Path $PSScriptRoot 'Test-LubanConfiguration.ps1') -TemplateRoot $TemplateRoot
$fileCount = (Get-ChildItem -LiteralPath $ProjectFiles -File -Recurse -Force | Measure-Object).Count
Write-Host "Template validation passed: $fileCount files; $version" -ForegroundColor Green
