---
name: frame-animation-packer
description: Validate and batch-pack delivered PNG animation sequences and animation.json into atlas PNG and playback JSON using the bundled FrameAnimeExportor Windows tool. Use for character actions, directional animations, effects, batch exports, and maintaining this packing tool; does not generate artwork or integrate assets into a game.
---

# 帧动画打包导出

使用本 Skill 自带的工具处理用户指定的源资源目录。源码在 `tool/`，可运行程序及依赖在
`runtime/`，统一命令入口为 `scripts/Pack-Animations.ps1`。路径都相对本 Skill 目录，
运行不依赖最初的 `D:\DingWork\CSharpWorks\FrameAnimeExportor` 工程。

## 输入与职责

每个动画独立目录；角色的动作＋朝向可命名为 `Fighter/Fly_Down`。
同级放 `animation.json` 与连续编号的 `001.png...NNN.png`，不设 frames 子目录。
上层目录只用于分类。配置为 UTF-8：

```json
{"duration":600,"scale":100,"pivot":{"x":0.5,"y":0.5}}
```

- duration：总时长，整数毫秒，不小于帧数。
- scale：打包缩放百分比，10～200，缺省 100；不要与制作阶段缩放系数混淆。
- pivot：0～1 数值，原始未裁剪画布的左下角原点，X 向右、Y 向上。
- 编号位数一致，按数字排序；同一动画画布尺寸一致。保留完整透明画布。
- 不需要角色名、action、loop 字段；预览与来源记录放在交付根目录之外。

旧格式（frames 子目录、制作记录型 JSON）不能直接打包。用户要求转换时，保留原件，
在新目录整理；根据已知时长、锚点转换配置，不猜测未知参数。只检查的请求不生成产物。
本 Skill 不生成 PNG 内容、不逐帧重新居中、不修改源配置来偷偷缩小素材。

## 执行

先检查输入路径、配置、帧编号和尺寸；输出必须位于输入目录之外。
使用用户已安装的 TexturePacker，其路径通过 `-TexturePacker` 传入；不复制许可证或软件。
本机已知位置为 `D:\DingWork\U3Dproj\TexturePakcer\bin\TexturePacker.exe`，每次先检查存在。
Windows 需支持 .NET Framework 4.6.1 的运行环境。正常打包无需编译或启动 UI。

```powershell
& '<skill>\scripts\Pack-Animations.ps1' `
  -InputDirectory 'D:\Delivery\Fighter' `
  -OutputDirectory 'D:\Output\Fighter' `
  -TexturePacker 'D:\Tools\TexturePacker.exe'
```

在独立 PowerShell 进程调用脚本并读取退出码（脚本使用 exit）。
可选 `-Square` 强制正方形 POT；默认允许矩形 POT。`-Overwrite` 仅在用户授权覆盖时使用。
当前工具固定最大边长 2048；没有可用的 MaxSize 参数，不能宣称无限尺寸。
超限时报告失败与调整选项，只有获得对应授权后才缩放、减少帧或改尺寸限制。
退出码：0 全部成功；1 参数或启动失败；2 至少一个动画失败。读取日志定位失败项，
已成功产物可能保留。升级期限警告不等于打包失败，应以退出码及产物验证为准。

## 产物验证

输出为同名 PNG＋JSON。批量根目录下的相对分类路径保留；单个动画输入时输出其目录名。
检查所有动画均有两个产物、帧数及编号顺序对应输入、总时长精确相等、各帧相差最多 1ms、
pivot 数值一致、缩放后的 sourceSize 正确、帧矩形不超出图集。
当前输出为旧 UI 兼容格式：pivot.x/y 是数值字符串，meta 为 null，不把它误判成输入配置。
报告产物绝对路径及链接、帧数、时长、尺寸和失败项。结构验证不代表已验证动作观感。

## 维护

用户要求修改打包行为时维护 `tool/`，用 `scripts/Build-Tool.ps1` 构建并刷新 runtime。
原始工程仅为复制来源，不自动双向同步。TexturePacker 保持外部依赖。
维护后至少做一次无界面真实打包、JSON/PNG 核对和覆盖保护检查。验证输出放在独立临时目录。
无参数运行 runtime/FrameAnimeExportor.exe 仍可打开桌面 UI，但常规批处理不使用 UI。
不自动提交、推送或导入 Unity。
