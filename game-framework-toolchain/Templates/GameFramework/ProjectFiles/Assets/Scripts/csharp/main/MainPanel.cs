using UnityEngine.EventSystems;
using UnityEngine.UI;

/// <summary>
/// 展示核心模块加载完成，并提供返回登录的模板界面。
/// </summary>
public sealed class MainPanel : BasePanel {

    public Button btnBack;

    /**设置模板主界面的窗口层级*/
    public MainPanel() {
        layer = PanelLayer.SCALE_PANEL_FIRST;
    }

    public override void OnOpen() {
        btnBack.onClick.AddListener(ReturnToLogin);
    }

    public override void OnClose() {
        btnBack.onClick.RemoveListener(ReturnToLogin);
    }

    /**返回已经装载的登录模块*/
    private void ReturnToLogin() {
        Close();
        PanelMgr.ins.OpenPanel(UIEnum.LOGIN_PANEL);
    }

}
