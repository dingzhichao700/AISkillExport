# UI 功能逻辑规范

> 适用范围：基于本模板开发的 Unity uGUI 窗口绑定类与功能逻辑代码。

## BasePanel 窗口规范

1. UI 作为窗口使用时，对应的绑定类必须继承 `BasePanel`。
2. 每个 `BasePanel` 子类必须声明构造函数，并在构造函数中设置 `layer`。具体窗口层级根据页面替换、覆盖关系和交互需求选择，不固定套用某个层级。
3. 每个 `BasePanel` 子类必须覆写 `OnOpen()` 和 `OnClose()`，即使当前没有额外逻辑也保留生命周期入口。
4. 界面需要接收键盘操作时，必须覆写 `OnPanelOperate(PanelOperateEnum operateCode)`，并根据 `PanelOperateEnum` 将操作分发到对应响应逻辑。
5. 窗口需要注册消息或交互监听时，通常在 `OnOpen()` 中调用私有函数 `AddLis()`，并在 `OnClose()` 中调用私有函数 `RemoveLis()`。注册与注销必须一入一出、严格成对。

`AddLis` 和 `RemoveLis` 是项目约定命名，不替换为其他同义名称。

## C# 换行风格

使用 K&R 风格：类、函数、条件和 `switch` 的左花括号与声明位于同一行。

```csharp
public class ExamplePanel : BasePanel {
    public ExamplePanel() {
        layer = PanelLayer.SCALE_PANEL_SECOND;
    }

    public override void OnOpen() {
        AddLis();
    }

    public override void OnClose() {
        RemoveLis();
    }

    private void AddLis() {
    }

    private void RemoveLis() {
    }

    public override void OnPanelOperate(PanelOperateEnum operateCode) {
        switch (operateCode) {
            case PanelOperateEnum.ESC:
                Close();
                break;
        }
    }
}
```

UIBinder 自动生成的成员区域继续由工程既有生成器维护；功能逻辑写在生成标记区域之外。

## C# 注释规范

1. 类注释使用多行 `/// <summary>`。带参数且逻辑复杂的函数也使用 `/// <summary>`，参数或返回值语义不直观时补充 `param`、`returns`。
2. 变量、属性和简单函数使用单行 `/**注释内容*/`，不使用单行 XML 注释。
3. 生命周期、状态转换、异步回调、资源加载、对象池复用、数值计算和跨界面流程等关键逻辑，必须说明设计意图、前置条件或副作用。注释重点回答“为什么这样处理”，不得逐行复述代码。
4. Demo 中暂时代替正式配置系统的常量或规则，必须在所属类型或配置入口注明未来替换来源，例如 Luban；不要求为每个同类常量重复注释。
5. 本节注释与换行风格只约束人为撰写和维护的代码。UIBinder 自动生成区域、第三方代码及其他机器维护区域保持各自生成格式，不得为了人工代码风格修改生成器或整理其内部成员。
6. 人为代码中显而易见的赋值和监听注册不强制注释，避免制造注释噪音。
7. 人为代码的类左花括号后、类右花括号前至少保留一个空行；变量、属性和函数之间至少保留一个空行。人工代码与自动生成区域交界处保留一个空行即可。
8. 修改功能逻辑后的检查必须包含：人为代码的注释类型是否符合成员复杂度、关键状态和异步边界是否有意图注释、成员间空行是否完整、已有注释是否仍与代码一致。过期注释按缺陷处理。
