using System;
using System.IO;
using System.Reflection;
using UnityEditor;
using UnityEngine;
using UnityEngine.Sprites;
using UnityEngine.UI;

public static class FrameShadowRegression {
    private static void Check(bool condition, string message) {
        if (!condition) {
            throw new InvalidOperationException(message);
        }
    }
    public static void Run() {
        var root = new GameObject("Fixture", typeof(RectTransform));
        var go = new GameObject("Shadow", typeof(RectTransform), typeof(CanvasRenderer), typeof(FrameShadowGraphic));
        go.transform.SetParent(root.transform, false);
        var graphic = go.GetComponent<FrameShadowGraphic>();
        var texture = new Texture2D(64, 64);
        var sprite = Sprite.Create(texture, new Rect(8, 12, 24, 32), Vector2.zero);
        string result = "";
        int code = 0;
        try {
            int count = 0;
            foreach (Vector2 pivot in new[] { new Vector2(12, 0), new Vector2(30, -8), new Vector2(-4, 20) }) {
                foreach (bool mirror in new[] { false, true }) {
                    foreach (float height in new[] { 0f, 40f, 80f }) {
                        foreach (float angle in new[] { 30f, 60f, 120f }) {
                            var ground = new Vector2(200, 300);
                            graphic.SetFrame(sprite, pivot, mirror, ground, height, angle, .6f, .3f);
                            Check(graphic.mainTexture == texture && !graphic.raycastTarget, "shared texture and input");
                            Check(graphic.rectTransform.anchorMin == new Vector2(0, 1), "top-left coordinate convention");
                            var bounds = FrameShadowGraphic.Bounds(sprite.rect.size, pivot, mirror, ground, height, angle, .6f);
                            using (var mesh = new VertexHelper()) {
                                typeof(FrameShadowGraphic).GetMethod("OnPopulateMesh", BindingFlags.Instance | BindingFlags.NonPublic | BindingFlags.DeclaredOnly).Invoke(graphic, new object[] { mesh });
                                Check(mesh.currentVertCount == 4 && mesh.currentIndexCount == 6, "quad topology");
                                Vector2[] points = { Vector2.zero, new Vector2(0, 32), new Vector2(24, 32), new Vector2(24, 0) };
                                var uv = DataUtility.GetOuterUV(sprite);
                                Vector2[] uvs = { new Vector2(uv.x, uv.y), new Vector2(uv.x, uv.w), new Vector2(uv.z, uv.w), new Vector2(uv.z, uv.y) };
                                for (int i = 0; i < 4; i++) {
                                    var vertex = new UIVertex();
                                    mesh.PopulateUIVertex(ref vertex, i);
                                    Vector2 point = points[i] - pivot;
                                    float projectedHeight = (point.y + height) * .6f;
                                    Vector2 expected = new Vector2(ground.x + (mirror ? -point.x : point.x) - (float)Math.Cos(angle * Math.PI / 180) * projectedHeight, -ground.y - (float)Math.Sin(angle * Math.PI / 180) * projectedHeight);
                                    Vector2 actual = graphic.rectTransform.anchoredPosition + (Vector2)vertex.position;
                                    Check(Vector2.Distance(expected, actual) < .001f, "trimmed/mirrored projection with altitude");
                                    Check(Vector2.Distance((Vector2)vertex.uv0, uvs[i]) < .0001f, "atlas UV preserved");
                                    Check(actual.x >= bounds.xMin - .001f && actual.x <= bounds.xMax + .001f && -actual.y >= bounds.yMin - .001f && -actual.y <= bounds.yMax + .001f, "culling bounds contain mesh");
                                }
                            }
                            count++;
                        }
                    }
                }
            }
            foreach (float bad in new[] { -1f, float.NaN, float.PositiveInfinity }) {
                bool rejected = false;
                try {
                    graphic.SetFrame(sprite, Vector2.zero, false, Vector2.zero, bad, 30, .6f, .3f);
                } catch (ArgumentOutOfRangeException) {
                    rejected = true;
                }
                Check(rejected, "invalid altitude rejected");
            }
            graphic.rectTransform.localScale = Vector3.one * 2;
            graphic.rectTransform.localRotation = Quaternion.Euler(0, 0, 20);
            graphic.ResetFrame();
            Check(!go.activeSelf && graphic.mainTexture == Texture2D.whiteTexture && graphic.color.a == 0, "recycle clears texture and visibility");
            Check(graphic.rectTransform.localScale == Vector3.one && graphic.rectTransform.localRotation == Quaternion.identity, "recycle clears transforms");
            go.SetActive(true);
            graphic.SetFrame(sprite, Vector2.zero, false, Vector2.zero, 0, 30, .6f, .3f);
            Check(graphic.mainTexture == texture, "pooled reuse");
            result = "passed: " + count + " Unity mesh cases; pivots outside crop; mirrored frame; 3 angles; heights 0/40/80; atlas UV; shared texture; culling bounds; invalid input; reset and reuse";
        } catch (Exception e) {
            code = 1;
            result = e.ToString();
            Debug.LogException(e);
        } finally {
            graphic.ResetFrame();
            UnityEngine.Object.DestroyImmediate(root);
            UnityEngine.Object.DestroyImmediate(sprite);
            UnityEngine.Object.DestroyImmediate(texture);
            File.WriteAllText("frame-shadow-result.txt", result);
        }
        EditorApplication.Exit(code);
    }
}
