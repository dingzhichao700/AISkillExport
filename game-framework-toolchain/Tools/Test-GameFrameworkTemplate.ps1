#Requires -Version 5.1
param([string]$TemplateRoot)

$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($TemplateRoot)) {
    $TemplateRoot = Join-Path $PSScriptRoot '..\Templates\GameFramework'
}
$TemplateRoot = [IO.Path]::GetFullPath($TemplateRoot)
$ProjectFiles = Join-Path $TemplateRoot 'ProjectFiles'
$errors = [Collections.Generic.List[string]]::new()

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
    'Assets\Scripts\csharp\com\core\RookieEngine.cs',
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
    foreach ($forbiddenPackage in @('com.unity.render-pipelines.universal', 'wechat', 'runtimeinspector')) {
        if ($manifest -match [regex]::Escape($forbiddenPackage)) {
            $errors.Add("Forbidden package in manifest: $forbiddenPackage")
        }
    }
}

$rookieEnginePath = Join-Path $ProjectFiles 'Assets\Scripts\csharp\com\core\RookieEngine.cs'
if (Test-Path -LiteralPath $rookieEnginePath) {
    $rookieEngine = Get-Content -LiteralPath $rookieEnginePath -Raw -Encoding UTF8
    $timerInit = $rookieEngine.IndexOf('_timer = new Timer()', [StringComparison]::Ordinal)
    $settingsRead = $rookieEngine.IndexOf('PersistentDataControl.ins.ReadUserSetting()', [StringComparison]::Ordinal)
    if ($timerInit -lt 0 -or $settingsRead -lt 0 -or $timerInit -gt $settingsRead) {
        $errors.Add('RookieEngine must initialize timer before ReadUserSetting; setting correction dispatches timer-dependent events.')
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
}

if ($errors.Count -gt 0) {
    $errors | ForEach-Object { Write-Error $_ -ErrorAction Continue }
    throw "Template validation failed with $($errors.Count) error(s)."
}

$version = Get-Content -LiteralPath (Join-Path $ProjectFiles 'ProjectSettings\ProjectVersion.txt') -Encoding UTF8 | Select-Object -First 1
$fileCount = (Get-ChildItem -LiteralPath $ProjectFiles -File -Recurse -Force | Measure-Object).Count
Write-Host "Template validation passed: $fileCount files; $version" -ForegroundColor Green
