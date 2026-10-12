using System;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

/// <summary>
/// 在隔离工程中验证真实启动、登录配置及 Main 加载流程。
/// </summary>
[InitializeOnLoad]
public static class FrameworkTemplateValidation {

    private const string Key = "Framework.TemplateValidation";
    private static double deadline;
    private static bool requestedMain;

    static FrameworkTemplateValidation() {
        EditorApplication.playModeStateChanged += OnStateChanged;
    }

    /// <summary>
    /// 批处理入口，使用已现场构建的资源进入实际游戏流程。
    /// </summary>
    public static void RunPlayMode() {
        SessionState.SetBool(Key, true);
        SessionState.SetString(Key + ".error", string.Empty);
        SessionState.SetBool(Key + ".passed", false);
        EditorSceneManager.OpenScene("Assets/Scenes/GameEntrance.unity");
        EditorApplication.isPlaying = true;
    }

    /**跨 Domain Reload 继续检查，结束后关闭本次验证实例*/
    private static void OnStateChanged(PlayModeStateChange state) {
        if (!SessionState.GetBool(Key, false)) {
            return;
        }
        if (state == PlayModeStateChange.EnteredPlayMode) {
            deadline = EditorApplication.timeSinceStartup + 90;
            requestedMain = false;
            Application.logMessageReceived += OnLog;
            EditorApplication.update += CheckFlow;
        } else if (state == PlayModeStateChange.EnteredEditMode) {
            SessionState.SetBool(Key, false);
            string error = SessionState.GetString(Key + ".error", string.Empty);
            bool success = SessionState.GetBool(Key + ".passed", false) && string.IsNullOrEmpty(error);
            File.WriteAllText("Library/template-runtime-validation.txt", success ? "ok: Opening -> Login -> Option -> Loading -> Main" : "failed: " + error);
            EditorApplication.Exit(success ? 0 : 1);
        }
    }

    /**运行时错误必须使验证失败*/
    private static void OnLog(string message, string stack, LogType type) {
        if (type == LogType.Error || type == LogType.Exception || type == LogType.Assert) {
            SessionState.SetString(Key + ".error", message + "\n" + stack);
        }
    }

    /**等待真实界面就绪后触发正式内容入口*/
    private static void CheckFlow() {
        if (!string.IsNullOrEmpty(SessionState.GetString(Key + ".error", string.Empty)) || EditorApplication.timeSinceStartup > deadline) {
            if (EditorApplication.timeSinceStartup > deadline) {
                SessionState.SetString(Key + ".error", "Startup timed out.");
            }
            Finish();
            return;
        }
        var main = UnityEngine.Object.FindObjectOfType<MainPanel>();
        if (main != null && main.isOpened) {
            SessionState.SetBool(Key + ".passed", true);
            Finish();
            return;
        }
        if (requestedMain) {
            return;
        }
        var login = UnityEngine.Object.FindObjectOfType<LoginPanel>();
        if (login != null && login.isOpened && login.txt.text == "点击屏幕或按任意键开始") {
            login.Close();
            PanelMgr.ins.OpenPanel(UIEnum.OPTION_PANEL);
        }
        var options = UnityEngine.Object.FindObjectOfType<OptionPanel>();
        if (options != null && options.isOpened) {
            requestedMain = true;
            options.SelectAndConfirm(OptionEnum.NEWGAME);
        }
    }

    /**停止监听并离开 Play，结果在 Domain Reload 后落盘*/
    private static void Finish() {
        EditorApplication.update -= CheckFlow;
        Application.logMessageReceived -= OnLog;
        EditorApplication.isPlaying = false;
    }

}
