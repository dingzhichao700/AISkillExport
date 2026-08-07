#Requires -Version 5.1
<#
.SYNOPSIS
  Generate a self-contained Game Framework Unity sample project.

.DESCRIPTION
  Copies Templates/GameFramework/ProjectFiles and never reads another Unity project.
  Unity is used only to import, compile, initialize, and build Addressables.

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
    return [bool](Select-String -LiteralPath $LogFile -Pattern 'error CS\d+|Scripts have compiler errors|Compilation failed|executeMethod.*failed|batchmode.*aborted' -CaseSensitive:$false)
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

    $process = Start-Process -FilePath $script:UnityEditorPath -ArgumentList $arguments -PassThru -NoNewWindow
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
    Copy-Item -LiteralPath (Join-Path $RepoRoot 'AGENTS.md') -Destination (Join-Path $Root 'AGENTS.md') -Force
    $docsSource = Join-Path $RepoRoot 'docs'
    if (Test-Path -LiteralPath $docsSource) {
        Copy-Tree $docsSource (Join-Path $Root 'docs')
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
- Directory rules: `docs/目录与分包原则.md`
- Generated: $generatedAt

Addressables are prepared during export. If runtime loading fails, run **Tools -> Addressables -> Build All**.
"@
    Set-Content -LiteralPath (Join-Path $Root 'README.md') -Value $readme -Encoding UTF8
}

function Assert-ExportComplete([string]$ProjectPath) {
    foreach ($relative in @(
        'Assets\Scenes\GameEntrance.unity',
        'Assets\Scenes\UIEditor.unity',
        'Assets\Scripts\csharp\com\core\RookieEngine.cs',
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
    if (Test-Path -LiteralPath (Join-Path (Split-Path $ProjectPath -Parent) 'docs\docs')) {
        throw 'Generated project contains duplicated docs/docs nesting.'
    }
    $marker = Join-Path $ProjectPath 'Assets\AddressableAssetsData\.export-baseline-complete.txt'
    if (-not ((Test-Path -LiteralPath $marker) -and ((Get-Content -LiteralPath $marker -Raw) -match '^ok\b'))) {
        throw "Addressables completion marker missing or failed: $marker"
    }
    $bundles = Get-ChildItem -LiteralPath (Join-Path $ProjectPath 'Library\com.unity.addressables') -Filter '*.bundle' -File -Recurse -ErrorAction SilentlyContinue
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

function Optimize-GeneratedLibrary([string]$ProjectPath) {
    $library = [IO.Path]::GetFullPath((Join-Path $ProjectPath 'Library'))
    $addressables = Join-Path $library 'com.unity.addressables'
    if (-not (Test-Path -LiteralPath $addressables -PathType Container)) {
        throw "Cannot optimize Library because Addressables output is missing: $addressables"
    }

    Assert-ChildPath -Parent $ProjectPath -Child $library
    $before = Get-DirectoryLength -Path $library
    foreach ($item in Get-ChildItem -LiteralPath $library -Force) {
        if ($item.Name -eq 'com.unity.addressables') { continue }
        Assert-ChildPath -Parent $library -Child $item.FullName
        Remove-Item -LiteralPath $item.FullName -Recurse -Force
    }
    $after = Get-DirectoryLength -Path $library
    $removedMb = [math]::Round(($before - $after) / 1MB, 1)
    $retainedMb = [math]::Round($after / 1MB, 1)
    Write-Step "Optimized Library: removed $removedMb MB of regenerable cache; retained $retainedMb MB of Addressables output"
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
    Update-GeneratedProject -Root $StageProjectRoot -ProjectPath $StageProject

    $script:UnityEditorPath = Resolve-UnityEditor -ExplicitPath $UnityEditor
    Write-Step "Unity: $script:UnityEditorPath"
    $logs = Join-Path $StageProject 'Logs'
    Ensure-Directory $logs
    Write-Step 'Unity pass 1/2: import and compile'
    Invoke-UnityBatch -ProjectPath $StageProject -LogFile (Join-Path $logs 'export-import.log')
    Write-Step 'Unity pass 2/2: initialize and build Addressables'
    Invoke-UnityBatch -ProjectPath $StageProject -LogFile (Join-Path $logs 'export-addressables.log') -ExecuteMethod 'GameFrameworkExportPipeline.ExportBaseline'

    Assert-ExportComplete -ProjectPath $StageProject
    Optimize-GeneratedLibrary -ProjectPath $StageProject
    Assert-ExportComplete -ProjectPath $StageProject
    Ensure-Directory $OutputRoot
    Move-Item -LiteralPath $StageProjectRoot -Destination $TargetRoot
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
