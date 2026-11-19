#if UNITY_EDITOR
using System;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;
using UnityEngine;

/// <summary>Project-owned startup theme applied after SDK export. Never changes loading stages.</summary>
public static class FrameworkWeChatStartupSkin {
    private const string Begin = "// FRAMEWORK_STARTUP_SKIN_BEGIN";
    private const string End = "// FRAMEWORK_STARTUP_SKIN_END";
    [Serializable] private class BarPaths { public string trackImage; public string fillImage; }
    [Serializable] private class ThemePaths { public int schemaVersion; public string backgroundImage; public string brandingImage; public BarPaths bar; }

    public static void Apply(string output) {
        string source = Path.Combine(Application.dataPath, "WeChatStartup");
        string gameRoot = Path.GetFullPath(Path.Combine(output, "minigame"));
        string gameFile = Path.Combine(gameRoot, "game.js");
        string themeFile = Path.Combine(source, "theme.json");
        if (!File.Exists(gameFile) || !File.Exists(themeFile)) throw new InvalidOperationException("Startup skin requires exported game.js and Assets/WeChatStartup/theme.json.");
        string text = File.ReadAllText(gameFile);
        string patched = PatchEntry(text);
        string theme = File.ReadAllText(themeFile);
        ThemePaths settings = JsonUtility.FromJson<ThemePaths>(theme);
        if (settings == null || settings.schemaVersion != 1) throw new InvalidOperationException("Unsupported startup theme schema.");
        string target = Path.Combine(gameRoot, "framework-loading-skin");
        Directory.CreateDirectory(target);
        foreach (string name in new[] { "index.js", "skin-view.js", "skin-lifecycle.js", "theme.js" }) {
            File.Copy(Path.Combine(source, "Runtime", name + ".txt"), Path.Combine(target, name), true);
        }
        File.WriteAllText(Path.Combine(target, "theme-config.js"), "module.exports = JSON.parse(" + EncodeJsonString(theme) + ");\n", new UTF8Encoding(false));
        string assetRoot = Path.Combine(source, "ThemeAssets");
        if (Directory.Exists(assetRoot)) foreach (string file in Directory.GetFiles(assetRoot, "*", SearchOption.AllDirectories)) {
            string ext = Path.GetExtension(file).ToLowerInvariant();
            if (ext != ".png" && ext != ".jpg" && ext != ".jpeg" && ext != ".webp") continue;
            string relative = file.Substring(assetRoot.Length).TrimStart(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
            string destination = Path.Combine(target, "assets", relative);
            Directory.CreateDirectory(Path.GetDirectoryName(destination));
            File.Copy(file, destination, true);
        }
        ValidateImage(gameRoot, settings.backgroundImage);
        ValidateImage(gameRoot, settings.brandingImage);
        if (settings.bar != null) { ValidateImage(gameRoot, settings.bar.trackImage); ValidateImage(gameRoot, settings.bar.fillImage); }
        File.WriteAllText(gameFile, patched, new UTF8Encoding(false));
    }

    public static string PatchEntry(string text) {
        string newline = text.Contains("\r\n") ? "\r\n" : "\n";
        text = Regex.Replace(text, @"(?m)^[ \t]*// FRAMEWORK_STARTUP_SKIN_BEGIN\r?\n[\s\S]*?^[ \t]*// FRAMEWORK_STARTUP_SKIN_END\r?\n", "");
        var entry = new Regex(@"(?m)^(?<indent>[ \t]*)gameManager\.startGame\(\);[ \t]*\r?$", RegexOptions.CultureInvariant);
        if (entry.Matches(text).Count != 1) throw new InvalidOperationException("SDK startup entry changed; expected one gameManager.startGame(). Review SDK compatibility before export.");
        return entry.Replace(text, match => {
            string indent = match.Groups["indent"].Value;
            return indent + Begin + newline + indent + "require('./framework-loading-skin/index').installSkin(gameManager, { wx, unityNamespace, canvas: GameGlobal.canvas });" + newline + indent + End + newline + match.Value;
        }, 1);
    }

    private static string EncodeJsonString(string value) {
        var result = new StringBuilder("\"");
        foreach (char c in value) {
            if (c == '\\' || c == '"' || c < 32 || c == '\u2028' || c == '\u2029') result.Append("\\u").Append(((int)c).ToString("x4"));
            else result.Append(c);
        }
        return result.Append('"').ToString();
    }
    private static void ValidateImage(string root, string relative) {
        if (string.IsNullOrEmpty(relative)) return; // Inherit SDK's configured image.
        if (relative.Contains(":") || relative.Contains("\\") || Path.IsPathRooted(relative)) throw new InvalidOperationException("Startup theme paths must be local package-relative paths: " + relative);
        string normalizedRoot = Path.GetFullPath(root).TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar;
        string absolute = Path.GetFullPath(Path.Combine(root, relative));
        if (!absolute.StartsWith(normalizedRoot, StringComparison.OrdinalIgnoreCase) || !File.Exists(absolute)) throw new InvalidOperationException("Startup theme image missing or outside package: " + relative);
    }
}
#endif