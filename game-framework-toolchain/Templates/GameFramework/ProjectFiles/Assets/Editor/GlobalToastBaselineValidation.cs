#if UNITY_EDITOR
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// 独立模板真实启动后验证公共提示与资源策略，不依赖样例游戏业务。
/// </summary>
/// <remarks>由FrameworkTemplateValidation调用；只写Library诊断，不修改玩家存档。</remarks>
public static class GlobalToastBaselineValidation {

    [Serializable] private sealed class Result { public string status; public string error; public string[] checks; }

    private static readonly List<string> checks = new List<string>();

    private sealed class AlternatePolicy : IResourcePresentationPolicy {
        public string ResolveUI(string id) => "example/ui/" + id;
        public ImageResource ResolveImage(string id) => new ImageResource("example/images/" + id, ResType.UnpackImage);
        public string ResolveAudio(int id) => "example/audio/" + id;
        public int ResolveButtonSound(ButtonSoundType type, bool interactable) => 0;
        public Material GetFrameMaterial() => null;
    }

    public static async Task RunAsync() {
        checks.Clear();
        try {
            Check(typeof(ResourcePresentation).Assembly.GetName().Name == "Foundation", "resource contract in Foundation");
            Check(typeof(ResourceConst).Assembly.GetName().Name == "Login", "resource paths owned by Login");
            Check(typeof(AudioConst).Assembly.GetName().Name == "Login", "audio mappings owned by Login");
            Check(!typeof(ResourcePresentation).Assembly.GetReferencedAssemblies().Any(a => a.Name == "Login" || a.Name == "Main"), "Foundation has no reverse business assembly dependency");
            var original = ResourcePresentation.Policy;
            try {
                ResourcePresentation.Install(new AlternatePolicy());
                Check(ResourcePresentation.Policy.ResolveUI("panel") == "example/ui/panel", "policy supplies UI address");
                Check(ResourcePresentation.Policy.ResolveImage("image").Address == "example/images/image", "policy supports explicit nonconventional image address");
                Check(ResourcePresentation.Policy.ResolveAudio(1) == "example/audio/1", "policy supplies audio address");
            } finally {
                ResourcePresentation.Install(original);
            }
            Check(CfgManager.IsInitialized && ConfigValueHelper.GetInt(100) == 3 && GlobalToast.MaxVisible == 3, "framework constant100 loaded through actual startup");
            GlobalToast.Clear();
            GlobalToast.Warn("Repeated hint");
            GlobalToast.Warn("Repeated hint");
            await GlobalToast.EnsureReadyAsync();
            var host = GlobalToast.Host;
            Check(host != null && host.ActiveCount == 2, "actual Addressables global prefab and binder initialized");
            await Task.Delay(300);
            var first = host.ActiveItems[0];
            float startY = first.Trans.anchoredPosition.y;
            float age = first.Age;
            GlobalToast.Warn("Repeated hint");
            Check(Mathf.Abs(first.Trans.anchoredPosition.y - startY) < .01f && first.Age == age, "new hint does not snap or reset existing age");
            await Task.Delay(260);
            Check(host.ActiveCount == 3 && first.Trans.anchoredPosition.y > startY, "three repeated hints stack with upward motion");
            for (int i = 0; i < host.ActiveCount; i++) {
                var item = host.ActiveItems[i];
                item.txtMessage.ForceMeshUpdate();
                Check(item.txtMessage.textInfo.lineCount == 1, "single-line TMP " + i);
                Check(item.GetComponentInChildren<ToastGradientGraphic>().GetComponent<CanvasRenderer>() != null, "gradient renderer dependency " + i);
                Check(item.GetComponentsInChildren<Graphic>().All(g => !g.raycastTarget), "no mouse or touch interception " + i);
                if (i > 0) {
                    Check(host.ActiveItems[i - 1].Trans.anchoredPosition.y - item.Trans.anchoredPosition.y >= 55.99f, "separate hint lanes " + i);
                }
            }
            GlobalToast.Warn("Queued hint");
            Check(GlobalToast.PendingCount == 1, "fourth hint queued");
            await Task.Delay(1800);
            Check(host.ActiveCount <= 1 && GlobalToast.PendingCount == 0, "expired hints recycle and queue advances");
            GlobalToast.Clear();
            Check(host.ActiveCount == 0 && host.PoolCount <= 3, "bounded item pool after clear");
            await ResourceLoader.LoadListAsync(new List<ResLoadInfo> { new ResLoadInfo(ResourcePresentation.Policy.ResolveUI(UIEnum.WARNING_PANEL), ResType.Prefab) });
            PanelMgr.ins.OpenPanel(UIEnum.WARNING_PANEL, new object[] { "Confirmation remains interactive", null });
            GlobalToast.Warn("Above confirmation");
            Check(host.transform.GetSiblingIndex() > PanelMgr.ins.GetPanel(UIEnum.WARNING_PANEL).transform.GetSiblingIndex(), "global layer above confirmation");
            PanelMgr.ins.ClosePanelByType(UIEnum.WARNING_PANEL);
            PanelMgr.ins.CloseAllPanel();
            await Task.Delay(100);
            Check(host.isOpened, "global host survives normal page close-all");
            GlobalToast.Shutdown();
            Check(GlobalToast.Host == null && GlobalToast.PendingCount == 0, "shutdown resets host and queue");
            Write(null);
        } catch (Exception error) {
            Write(error);
            throw;
        }
    }

    private static void Check(bool condition, string message) {
        if (!condition) {
            throw new InvalidOperationException("Baseline toast: " + message);
        }
        checks.Add(message);
    }

    private static void Write(Exception error) {
        File.WriteAllText("Library/global-toast-baseline-result.json", JsonUtility.ToJson(new Result { status = error == null ? "passed" : "failed", error = error?.ToString(), checks = checks.ToArray() }, true));
    }

}
#endif
