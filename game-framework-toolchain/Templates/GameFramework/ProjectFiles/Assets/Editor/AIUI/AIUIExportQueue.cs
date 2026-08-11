#if UNITY_EDITOR
using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using TMPro;
using UnityEditor;
using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// 常驻 AIUI 预览导出队列。请求写入 Library，不通过增删 Editor 脚本触发导出。
/// </summary>
[InitializeOnLoad]
public static class AIUIExportQueue {
    const string PendingPath = "Library/AIUI/pending-preview.json";
    const string ResultPath = "Library/AIUI/preview-result.json";
    const string FinalizePendingPath = "Library/AIUI/pending-finalize.json";
    const string FinalizeResultPath = "Library/AIUI/finalize-result.json";
    static bool running;

    [Serializable]
    public class Request {
        public string requestId;
        public string prefabPath;
        public string rootName;
        public string fontAssetPath;
        public float width = 720;
        public float height = 1280;
        public Node[] nodes;
        public bool initializeBinding;
        public Binding binding;
    }

    [Serializable]
    public class Node {
        public string kind;
        public string name;
        public string parent;
        public string assetPath;
        public string text;
        public float x;
        public float y;
        public float width;
        public float height;
        public float fontSize;
        public string color = "#FFFFFFFF";
        public string shadowColor = "#00000000";
        public float shadowOffsetY;
        public bool omitLabel;
        public float labelX;
        public float labelY;
        public float labelWidth;
        public float labelHeight;
        public string labelColor = "#FFFFFFFF";
    }

    [Serializable]
    public class Binding {
        public string csharpAssetPath;
        public string summary;
        public string panelLayer = "SCALE_PANEL_FIRST";
        public Member[] members;
    }

    [Serializable]
    public class Member {
        public string node;
        public string type;
    }

    [Serializable]
    public class FinalizeRequest {
        public string requestId;
        public string prefabPath;
        public string[] prefabPaths;
        public string atlasSourcePath;
        public string atlasPath;
        public bool keepTransparentBounds = true;
        public string[] spriteNames;
        public LooseSpriteReplacement[] looseSpriteReplacements;
    }

    [Serializable]
    public class LooseSpriteReplacement {
        public string spriteName;
        public string assetPath;
    }

    static AIUIExportQueue() {
        EditorApplication.update += Poll;
    }

    static void Poll() {
        if (running || EditorApplication.isCompiling || EditorApplication.isUpdating) return;
        if (!File.Exists(PendingPath) && !File.Exists(FinalizePendingPath)) return;
        running = true;
        System.Diagnostics.Stopwatch stopwatch = System.Diagnostics.Stopwatch.StartNew();
        try {
            if (File.Exists(PendingPath)) {
                Request request = JsonUtility.FromJson<Request>(File.ReadAllText(PendingPath));
                Validate(request);
                GeneratePreview(request);
                WriteResult(ResultPath, request.requestId, "passed", null, stopwatch.ElapsedMilliseconds);
                File.Delete(PendingPath);
            } else {
                FinalizeRequest request = JsonUtility.FromJson<FinalizeRequest>(File.ReadAllText(FinalizePendingPath));
                Finalize(request);
                WriteResult(FinalizeResultPath, request.requestId, "passed", null, stopwatch.ElapsedMilliseconds);
                File.Delete(FinalizePendingPath);
            }
        } catch (Exception exception) {
            string activePath = File.Exists(PendingPath) ? PendingPath : FinalizePendingPath;
            string resultPath = activePath == PendingPath ? ResultPath : FinalizeResultPath;
            WriteResult(resultPath, null, "failed", exception.ToString(), stopwatch.ElapsedMilliseconds);
            Debug.LogException(exception);
            if (File.Exists(activePath)) {
                string failedPath = activePath + ".failed";
                if (File.Exists(failedPath)) File.Delete(failedPath);
                File.Move(activePath, failedPath);
            }
        } finally {
            running = false;
        }
    }

    static void Finalize(FinalizeRequest request) {
        if (request == null) throw new InvalidOperationException("AIUI finalize request is empty");
        string[] prefabPaths = request.prefabPaths != null && request.prefabPaths.Length > 0
            ? request.prefabPaths
            : new[] { request.prefabPath };
        foreach (string prefabPath in prefabPaths) {
            if (string.IsNullOrEmpty(prefabPath) || !prefabPath.StartsWith("Assets/Prefab/"))
                throw new InvalidOperationException("Every prefab path must be under Assets/Prefab");
        }
        if (string.IsNullOrEmpty(request.atlasPath) || !request.atlasPath.StartsWith("Assets/Art/atlas/"))
            throw new InvalidOperationException("atlasPath must be under Assets/Art/atlas");
        if (string.IsNullOrEmpty(request.atlasSourcePath) || !request.atlasSourcePath.StartsWith("Assets/Art/atlasSource/"))
            throw new InvalidOperationException("atlasSourcePath must be under Assets/Art/atlasSource");
        if (request.spriteNames == null || request.spriteNames.Length == 0)
            throw new InvalidOperationException("spriteNames are required");

        Dictionary<string, Sprite> looseSprites = new Dictionary<string, Sprite>();
        if (request.looseSpriteReplacements != null) {
            foreach (LooseSpriteReplacement replacement in request.looseSpriteReplacements) {
                if (string.IsNullOrEmpty(replacement.spriteName))
                    throw new InvalidOperationException("Loose Sprite replacement requires spriteName");
                if (string.IsNullOrEmpty(replacement.assetPath) ||
                    !replacement.assetPath.StartsWith("Assets/Art/unpack/"))
                    throw new InvalidOperationException("Loose Sprite must be under Assets/Art/unpack: " + replacement.assetPath);
                EnsureSpriteImporter(replacement.assetPath);
                Sprite sprite = AssetDatabase.LoadAssetAtPath<Sprite>(replacement.assetPath);
                if (sprite == null) throw new InvalidOperationException("Loose Sprite not found: " + replacement.assetPath);
                looseSprites[replacement.spriteName] = sprite;
            }
        }

        HashSet<string> looseReplaced = new HashSet<string>();
        if (looseSprites.Count > 0) {
            foreach (string prefabPath in prefabPaths) {
                GameObject root = PrefabUtility.LoadPrefabContents(prefabPath);
                try {
                    foreach (Image image in root.GetComponentsInChildren<Image>(true)) {
                        if (image.sprite == null || !looseSprites.TryGetValue(image.sprite.name, out Sprite looseSprite))
                            continue;
                        looseReplaced.Add(image.sprite.name);
                        image.sprite = looseSprite;
                    }
                    PrefabUtility.SaveAsPrefabAsset(root, prefabPath);
                } finally {
                    PrefabUtility.UnloadPrefabContents(root);
                }
            }
            foreach (string spriteName in looseSprites.Keys) {
                if (!looseReplaced.Contains(spriteName))
                    throw new InvalidOperationException("No Prefab uses loose Sprite replacement: " + spriteName);
            }
        }

        TexturePackerImporter.TexturePackerTool.PackAtlasSourceAssetPath(
            request.atlasSourcePath, trimTrans: !request.keepTransparentBounds);
        AssetDatabase.ImportAsset(request.atlasPath,
            ImportAssetOptions.ForceSynchronousImport | ImportAssetOptions.ForceUpdate);
        if (AssetImporter.GetAtPath(request.atlasPath) == null)
            throw new InvalidOperationException("Atlas generation failed: " + request.atlasPath);

        Dictionary<string, Sprite> sprites = new Dictionary<string, Sprite>();
        foreach (UnityEngine.Object asset in AssetDatabase.LoadAllAssetsAtPath(request.atlasPath)) {
            if (asset is Sprite sprite) sprites[sprite.name] = sprite;
        }
        foreach (string spriteName in request.spriteNames) {
            if (!sprites.ContainsKey(spriteName)) throw new InvalidOperationException("Atlas Sprite not found: " + spriteName);
        }

        HashSet<string> expected = new HashSet<string>(request.spriteNames);
        HashSet<string> replaced = new HashSet<string>();
        foreach (string prefabPath in prefabPaths) {
            GameObject root = PrefabUtility.LoadPrefabContents(prefabPath);
            try {
                foreach (Image image in root.GetComponentsInChildren<Image>(true)) {
                    if (image.sprite == null || !expected.Contains(image.sprite.name)) continue;
                    image.sprite = sprites[image.sprite.name];
                    replaced.Add(image.sprite.name);
                }
                PrefabUtility.SaveAsPrefabAsset(root, prefabPath);
            } finally {
                PrefabUtility.UnloadPrefabContents(root);
            }
        }
        foreach (string spriteName in expected) {
            if (!replaced.Contains(spriteName)) throw new InvalidOperationException("No Prefab uses Sprite: " + spriteName);
        }
        AssetDatabase.SaveAssets();
        Debug.Log("[AIUI Finalize] atlas references applied to " + prefabPaths.Length + " Prefab(s)");
    }

    static void Validate(Request request) {
        if (request == null) throw new InvalidOperationException("AIUI preview request is empty");
        if (string.IsNullOrEmpty(request.prefabPath) || !request.prefabPath.StartsWith("Assets/Prefab/"))
            throw new InvalidOperationException("prefabPath must be under Assets/Prefab");
        if (string.IsNullOrEmpty(request.rootName)) throw new InvalidOperationException("rootName is required");
        if (request.nodes == null) throw new InvalidOperationException("nodes are required");
        HashSet<string> names = new HashSet<string> { request.rootName };
        foreach (Node node in request.nodes) {
            if (string.IsNullOrEmpty(node.name)) throw new InvalidOperationException("Every node requires a name");
            if (!names.Add(node.name)) throw new InvalidOperationException("Duplicate node name: " + node.name);
            if (!string.IsNullOrEmpty(node.parent) && !names.Contains(node.parent))
                throw new InvalidOperationException("Parent must appear before child: " + node.parent + " -> " + node.name);
            if (node.kind == "image" || node.kind == "button") EnsureSpriteImporter(node.assetPath);
        }
        if (request.initializeBinding) {
            if (request.binding == null) throw new InvalidOperationException("binding is required when initializeBinding is true");
            if (string.IsNullOrEmpty(request.binding.csharpAssetPath) ||
                !request.binding.csharpAssetPath.StartsWith("Assets/Scripts/"))
                throw new InvalidOperationException("binding.csharpAssetPath must be under Assets/Scripts");
            if (request.binding.members == null) throw new InvalidOperationException("binding.members are required");
            foreach (Member member in request.binding.members) {
                if (!names.Contains(member.node)) throw new InvalidOperationException("Binding node not found: " + member.node);
                if (string.IsNullOrEmpty(member.type)) throw new InvalidOperationException("Binding type is required: " + member.node);
            }
        }
    }

    static void EnsureSpriteImporter(string path) {
        TextureImporter importer = AssetImporter.GetAtPath(path) as TextureImporter;
        if (importer == null && File.Exists(path)) {
            AssetDatabase.ImportAsset(path, ImportAssetOptions.ForceSynchronousImport | ImportAssetOptions.ForceUpdate);
            importer = AssetImporter.GetAtPath(path) as TextureImporter;
        }
        if (importer == null) throw new InvalidOperationException("Missing texture: " + path);
        bool changed = importer.textureType != TextureImporterType.Sprite ||
                       importer.spriteImportMode != SpriteImportMode.Single ||
                       importer.mipmapEnabled || !importer.alphaIsTransparency;
        if (!changed) return;
        importer.textureType = TextureImporterType.Sprite;
        importer.spriteImportMode = SpriteImportMode.Single;
        importer.spritePixelsPerUnit = 100;
        importer.alphaIsTransparency = true;
        importer.mipmapEnabled = false;
        importer.SaveAndReimport();
    }

    static void GeneratePreview(Request request) {
        GameObject root = new GameObject(request.rootName, typeof(RectTransform), typeof(CanvasGroup));
        RectTransform rootRect = root.GetComponent<RectTransform>();
        rootRect.anchorMin = rootRect.anchorMax = rootRect.pivot = new Vector2(0.5f, 0.5f);
        rootRect.sizeDelta = new Vector2(request.width, request.height);
        rootRect.anchoredPosition = Vector2.zero;
        Dictionary<string, RectTransform> parents = new Dictionary<string, RectTransform> { [request.rootName] = rootRect };

        foreach (Node node in request.nodes) {
            RectTransform parent = string.IsNullOrEmpty(node.parent) ? rootRect : parents[node.parent];
            RectTransform created;
            switch (node.kind) {
                case "image": created = CreateImage(parent, node); break;
                case "text": created = CreateText(parent, node, request.fontAssetPath); break;
                case "button": created = CreateButton(parent, node, request.fontAssetPath); break;
                case "container": created = CreateContainer(parent, node); break;
                default: throw new InvalidOperationException("Unsupported node kind: " + node.kind);
            }
            parents[node.name] = created;
        }

        if (request.initializeBinding) ConfigureBinding(root, parents, request.binding);

        string projectRoot = Directory.GetParent(Application.dataPath).FullName;
        string prefabDirectory = Path.GetDirectoryName(request.prefabPath.Replace('/', Path.DirectorySeparatorChar));
        Directory.CreateDirectory(Path.Combine(projectRoot, prefabDirectory));
        PrefabUtility.SaveAsPrefabAsset(root, request.prefabPath);
        UnityEngine.Object.DestroyImmediate(root);
        AssetDatabase.SaveAssets();
        Debug.Log("[AIUI Preview] generated: " + request.prefabPath);
    }

    static void ConfigureBinding(GameObject root, Dictionary<string, RectTransform> nodes, Binding binding) {
        EnsureViewClass(root.name, binding);
        UIBinder binder = root.AddComponent<UIBinder>();
        binder.csharpAssetPath = binding.csharpAssetPath;
        binder.csharpAsset = binding.csharpAssetPath;
        binder.uiList = new List<UIBindComponentData>();
        int id = 1;
        foreach (Member member in binding.members) {
            GameObject target = nodes[member.node].gameObject;
            if (target.GetComponent(member.type) == null)
                throw new InvalidOperationException("Component " + member.type + " not found on " + member.node);
            binder.uiList.Add(new UIBindComponentData {
                id = id++, uiName = member.node, uiTypeName = member.type,
                isCustomClass = false, customClassName = string.Empty, go = target
            });
        }

        Editor inspector = Editor.CreateEditor(binder);
        try {
            MethodInfo generate = inspector.GetType().GetMethod("GenerateUiBind", BindingFlags.Instance | BindingFlags.NonPublic);
            if (generate == null) throw new MissingMethodException(inspector.GetType().FullName, "GenerateUiBind");
            generate.Invoke(inspector, new object[] { binding.csharpAssetPath });
        } finally {
            UnityEngine.Object.DestroyImmediate(inspector);
        }
    }

    static void EnsureViewClass(string className, Binding binding) {
        string projectRoot = Directory.GetParent(Application.dataPath).FullName;
        string relative = binding.csharpAssetPath.Replace('/', Path.DirectorySeparatorChar);
        string absolute = Path.Combine(projectRoot, relative);
        Directory.CreateDirectory(Path.GetDirectoryName(absolute));
        if (File.Exists(absolute)) return;
        string summary = string.IsNullOrEmpty(binding.summary) ? className : binding.summary;
        string source =
            "/// <summary>\n/// " + summary + "\n/// </summary>\n" +
            "public class " + className + " : BasePanel {\n" +
            "    public " + className + "() {\n" +
            "        layer = PanelLayer." + binding.panelLayer + ";\n" +
            "    }\n\n" +
            "    public override void OnOpen() {\n    }\n\n" +
            "    public override void OnClose() {\n    }\n" +
            "}\n";
        File.WriteAllText(absolute, source, new System.Text.UTF8Encoding(false));
    }

    static RectTransform CreateContainer(RectTransform parent, Node node) {
        GameObject go = new GameObject(node.name, typeof(RectTransform));
        RectTransform rect = go.GetComponent<RectTransform>();
        SetTopLeft(rect, parent, node.x, node.y, node.width, node.height);
        return rect;
    }

    static RectTransform CreateImage(RectTransform parent, Node node) {
        GameObject go = new GameObject(node.name, typeof(RectTransform), typeof(CanvasRenderer), typeof(Image));
        RectTransform rect = go.GetComponent<RectTransform>();
        SetTopLeft(rect, parent, node.x, node.y, node.width, node.height);
        Image image = go.GetComponent<Image>();
        image.sprite = AssetDatabase.LoadAssetAtPath<Sprite>(node.assetPath);
        image.raycastTarget = false;
        return rect;
    }

    static RectTransform CreateText(RectTransform parent, Node node, string fontPath) {
        GameObject go = new GameObject(node.name, typeof(RectTransform), typeof(CanvasRenderer), typeof(TextMeshProUGUI));
        RectTransform rect = go.GetComponent<RectTransform>();
        SetTopLeft(rect, parent, node.x, node.y, node.width, node.height);
        TextMeshProUGUI text = go.GetComponent<TextMeshProUGUI>();
        text.font = AssetDatabase.LoadAssetAtPath<TMP_FontAsset>(fontPath);
        text.text = node.text ?? string.Empty;
        text.fontSize = node.fontSize;
        text.fontStyle = FontStyles.Bold;
        text.color = ParseColor(node.color);
        text.alignment = TextAlignmentOptions.Center;
        text.enableWordWrapping = false;
        text.overflowMode = TextOverflowModes.Overflow;
        text.raycastTarget = false;
        if (ParseColor(node.shadowColor).a > 0) {
            Shadow shadow = go.AddComponent<Shadow>();
            shadow.effectColor = ParseColor(node.shadowColor);
            shadow.effectDistance = new Vector2(0, -node.shadowOffsetY);
        }
        return rect;
    }

    static RectTransform CreateButton(RectTransform parent, Node node, string fontPath) {
        GameObject go = new GameObject(node.name, typeof(RectTransform), typeof(CanvasRenderer), typeof(Image),
            typeof(Button), typeof(CanvasGroup), typeof(GameButton));
        RectTransform rect = go.GetComponent<RectTransform>();
        SetTopLeft(rect, parent, node.x, node.y, node.width, node.height);
        rect.pivot = new Vector2(0.5f, 0.5f);
        rect.anchoredPosition += new Vector2(node.width * 0.5f, -node.height * 0.5f);
        Image image = go.GetComponent<Image>();
        image.sprite = AssetDatabase.LoadAssetAtPath<Sprite>(node.assetPath);
        Button button = go.GetComponent<Button>();
        button.targetGraphic = image;
        button.transition = Selectable.Transition.None;
        GameButton gameButton = go.GetComponent<GameButton>();
        gameButton.text = node.text;
        if (!node.omitLabel) {
            Node labelNode = new Node {
                name = "txtLabel", kind = "text", text = node.text,
                x = node.labelX, y = node.labelY, width = node.labelWidth, height = node.labelHeight,
                fontSize = node.fontSize, color = node.labelColor,
                shadowColor = node.shadowColor, shadowOffsetY = node.shadowOffsetY
            };
            RectTransform labelRect = CreateText(rect, labelNode, fontPath);
            SerializedObject serialized = new SerializedObject(gameButton);
            serialized.FindProperty("label").objectReferenceValue = labelRect.GetComponent<TextMeshProUGUI>();
            serialized.ApplyModifiedPropertiesWithoutUndo();
        }
        return rect;
    }

    static void SetTopLeft(RectTransform rect, RectTransform parent, float x, float y, float width, float height) {
        rect.SetParent(parent, false);
        rect.anchorMin = rect.anchorMax = rect.pivot = new Vector2(0, 1);
        rect.sizeDelta = new Vector2(width, height);
        rect.anchoredPosition = new Vector2(x, -y);
    }

    static Color ParseColor(string value) {
        return ColorUtility.TryParseHtmlString(value, out Color color) ? color : Color.white;
    }

    static void WriteResult(string path, string requestId, string status, string error, long durationMs) {
        Directory.CreateDirectory(Path.GetDirectoryName(path));
        string safeError = string.IsNullOrEmpty(error) ? string.Empty : error.Replace("\\", "\\\\").Replace("\"", "\\\"").Replace("\r", "").Replace("\n", "\\n");
        File.WriteAllText(path,
            "{\n  \"requestId\": \"" + (requestId ?? string.Empty) + "\",\n  \"status\": \"" + status +
            "\",\n  \"durationMs\": " + durationMs + ",\n  \"error\": \"" + safeError + "\"\n}");
    }
}
#endif
