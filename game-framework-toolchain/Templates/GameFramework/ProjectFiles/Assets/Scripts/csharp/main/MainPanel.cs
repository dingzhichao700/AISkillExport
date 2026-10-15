using UnityEngine.EventSystems;
using UnityEngine.UI;

/// <summary>
/// 展示核心模块加载完成，并提供返回登录的模板界面。
/// </summary>
public sealed class MainPanel : BasePanel {

    public Button btnBack;

    /**开发调试入口*/
    public Button btnGM;

    /**设置模板主界面的窗口层级*/
    public MainPanel() {
        layer = PanelLayer.SCALE_PANEL_FIRST;
    }

    public override void OnOpen() {
        GMControl.ins.Init();
        btnGM.onClick.AddListener(GMControl.ins.OpenPanel);
        btnBack.onClick.AddListener(ReturnToLogin);
    }

    public override void OnClose() {
        btnGM.onClick.RemoveListener(GMControl.ins.OpenPanel);
        btnBack.onClick.RemoveListener(ReturnToLogin);
        GMControl.ins.Shutdown();
    }

    /**返回已经装载的登录模块*/
    private void ReturnToLogin() {
        Close();
        PanelMgr.ins.OpenPanel(UIEnum.LOGIN_PANEL);
    }

}
