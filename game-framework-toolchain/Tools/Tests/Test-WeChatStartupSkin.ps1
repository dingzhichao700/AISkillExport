#Requires -Version 5.1
param([string]$ProjectFiles = (Join-Path $PSScriptRoot '../../Templates/GameFramework/ProjectFiles'))
$ErrorActionPreference='Stop'
$ProjectFiles=[IO.Path]::GetFullPath($ProjectFiles)
$skin=Join-Path $ProjectFiles 'Assets/WeChatStartup'
foreach($f in @('theme.json','Runtime/index.js.txt','Runtime/skin-view.js.txt','Runtime/skin-lifecycle.js.txt','Runtime/theme.js.txt')) { if(-not(Test-Path -LiteralPath (Join-Path $skin $f))){throw "Missing startup skin $f"} }
$config=Get-Content -Raw -LiteralPath (Join-Path $skin 'theme.json')|ConvertFrom-Json
if($config.schemaVersion -ne 1){throw 'Invalid startup theme schema'}
$build=Get-Content -Raw -LiteralPath (Join-Path $ProjectFiles 'Assets/Editor/FrameworkWeChatBuild.cs')
if([regex]::Matches($build,'FrameworkWeChatStartupSkin.Apply\(output\);').Count -ne 1){throw 'Export must install startup skin exactly once'}
$helper=(Get-Content -Raw -LiteralPath (Join-Path $ProjectFiles 'Assets/Editor/FrameworkWeChatStartupSkin.cs')).Replace('#if UNITY_EDITOR','').Replace('#endif','')
$stubs=@"
namespace UnityEngine {
 public static class Application {public static string dataPath;}
 public static class JsonUtility {public static System.Func<string,System.Type,object> Parse;public static T FromJson<T>(string json){return (T)Parse(json,typeof(T));}}
}
"@
if(-not('FrameworkWeChatStartupSkin' -as [type])){Add-Type -TypeDefinition ($helper+$stubs) -IgnoreWarnings -WarningAction SilentlyContinue}
function Convert-ThemeObject($value,[type]$type){
 $result=[Activator]::CreateInstance($type,$true)
 foreach($field in $type.GetFields()){$property=$value.PSObject.Properties[$field.Name];if($null -eq $property -or $null -eq $property.Value){continue};if($field.FieldType -eq [string]){$field.SetValue($result,[string]$property.Value)}elseif($field.FieldType.IsPrimitive){$field.SetValue($result,[Convert]::ChangeType($property.Value,$field.FieldType))}else{$field.SetValue($result,(Convert-ThemeObject $property.Value $field.FieldType))}}
 return $result
}
[UnityEngine.JsonUtility]::Parse={param($json,$type) Convert-ThemeObject ($json|ConvertFrom-Json) $type}
foreach($nl in @("`n","`r`n")){$original="// unrelated$nl        gameManager.startGame();$nl// keep$nl";$patched=[FrameworkWeChatStartupSkin]::PatchEntry($original);if([FrameworkWeChatStartupSkin]::PatchEntry($patched) -cne $patched){throw 'Non-idempotent hook'};if(-not $patched.EndsWith("// keep$nl")){throw 'Unrelated code changed'}}
$failed=$false;try{[FrameworkWeChatStartupSkin]::PatchEntry('changed SDK entry')}catch{$failed=$true};if(-not $failed){throw 'SDK drift not rejected'}
$tempBase=[IO.Path]::GetFullPath([IO.Path]::GetTempPath());$scratch=Join-Path $tempBase ('wechat-startup-theme-'+[guid]::NewGuid().ToString('N'))
try{
 $assets=Join-Path $scratch 'Assets';$out=Join-Path $scratch 'export';$game=Join-Path $out 'minigame';New-Item -ItemType Directory -Path $assets,$game -Force|Out-Null;Copy-Item -LiteralPath $skin -Destination (Join-Path $assets 'WeChatStartup') -Recurse
 $sourceTheme=Join-Path $assets 'WeChatStartup/theme.json';'{"schemaVersion":1,"backgroundImage":"framework-loading-skin/assets/background.jpg","bar":{"fillImage":"framework-loading-skin/assets/fill.png"}}'|Set-Content -LiteralPath $sourceTheme -Encoding UTF8
 $themeAssets=Join-Path $assets 'WeChatStartup/ThemeAssets';New-Item -ItemType Directory -Path $themeAssets -Force|Out-Null
 [IO.File]::WriteAllBytes((Join-Path $themeAssets 'background.jpg'),[byte[]](1,2,3));[IO.File]::WriteAllBytes((Join-Path $themeAssets 'fill.png'),[byte[]](4,5,6))
 $entry=Join-Path $game 'game.js';[IO.File]::WriteAllText($entry,"gameManager.startGame();`n")
 [UnityEngine.Application]::dataPath=$assets;[FrameworkWeChatStartupSkin]::Apply($out);$first=[IO.File]::ReadAllText($entry);[FrameworkWeChatStartupSkin]::Apply($out);if([IO.File]::ReadAllText($entry) -cne $first){throw 'Repeated export duplicated hook'}
 $node=Get-Command node -ErrorAction SilentlyContinue;if($node){& $node.Source -e 'const t=require(process.argv[1]);if(t.schemaVersion!==1||!t.backgroundImage)process.exit(1)' (Join-Path $game 'framework-loading-skin/theme-config.js');if($LASTEXITCODE -ne 0){throw 'Generated theme JS failed'}}
 if(-not(Test-Path -LiteralPath (Join-Path $game 'framework-loading-skin/assets/fill.png'))){throw 'Image style not exported'}
 [IO.File]::WriteAllBytes((Join-Path $themeAssets 'background.jpg'),[byte[]](7,8,9));[FrameworkWeChatStartupSkin]::Apply($out);if([IO.File]::ReadAllBytes((Join-Path $game 'framework-loading-skin/assets/background.jpg'))[0] -ne 7){throw 'Version background not replaced'}
 '{"schemaVersion":1,"backgroundImage":"../outside.jpg"}'|Set-Content -LiteralPath $sourceTheme -Encoding UTF8;$failed=$false;try{[FrameworkWeChatStartupSkin]::Apply($out)}catch{$failed=$true};if(-not $failed){throw 'Out-of-package path accepted'}
}finally{if([IO.Path]::GetFullPath($scratch).StartsWith($tempBase,[StringComparison]::OrdinalIgnoreCase) -and (Split-Path $scratch -Leaf) -like 'wechat-startup-theme-*'){Remove-Item -LiteralPath $scratch -Recurse -Force}}
Write-Host 'PASS startup exporter: compiled with Unity API stubs, idempotence, image copy, background replacement, SDK drift and path guards.'