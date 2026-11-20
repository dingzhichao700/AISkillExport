# 验收与交付关卡

## 1. 尺寸先确认

新单位或尺度变更时，批量动作制作前，将候选按预计游戏显示比例置入目标战斗场景，与已有单位/建筑并列提交原尺寸对照。记录画布、可见本体尺寸、源几何版本、像素/世界单位换算、导出scale与运行时缩放及是否镜像。用户确认后锁定；正式输出前复核，尺寸改动重新确认。已有有效确认直接引用，不重问。缺场景或比例输入时明确缺项，不以透明底图或放大预览冒充场景尺寸通过。

## 2. 完整动作和验收边界

默认每个“单位×动作×朝向”是一个完整连续的序列、一个图集PNG/JSON对和一个独立播放入口。不得静默拆为多个时间片段或本体层要求业务组合；图集分页与动作拆段不是同一件事，超限先报告兼容性和方案。独立特效在契约中列清时序/挂点/用途；已有明确批准例外可沿用。

资源场景验收优先复用独立测试/预览入口，直接加载资产，检查尺寸、锚点、材质与动作切换，不依赖完整卡牌、建筑和产兵链。正式业务接入另查依赖并按授权执行；缺失警告不构成扩大任务或自动转交统筹实施的授权。原专项保持验收责任，说明最小方案并继续独立工作。离线合成必须标注，不能冒充引擎加载或实战验证。

## 3. 整包完成清单

- 约定动作与方向齐全；完整战斗单位若项目约定四动作，不能只交三动作。
- 场景尺寸有对应版本的用户确认；本次输出沿用同一几何和缩放。
- 本体动画可独立播放，无未批准拆段/组合；独立特效单列。
- 全帧结构、图集还原、顺序、原速时长和pivot检查完成，正常透明尾段有依据。
- 原尺寸场景切换视频齐全，覆盖约定动作；包含死亡时补充移动/攻击中死亡、完整终止和末态停留。重播须标明新实例，不尸体复活循环。
- 预览优先基于实际交付图集还原，标注源序列预览与实际包回放的区别；核对视频帧率/时长和可解码性。
- 独立ZIP包含透明序列、图集/配置、必要独立特效、使用说明和证据，CRC与逐文件SHA256核对通过。
- 直接提供预览、ZIP下载链接和包大小，列清已验证、未验证及待验收内容。链接指向真实产物；交付前检查存在和非空。

技术检查通过不等于用户视觉验收。缺项只能交范围明确的阶段样件，不标记整包完成。

最终回复示例（按实际任务删改，不硬编码项目参数）：

> 已完成［版本、动作/方向范围］，保持［批准的材质/颜色等约束］。
>
> - ［原尺寸场景切换］（实际文件链接）
> - ［动作中死亡补充］（任务含死亡时提供）
> - ［独立资源包，约XX MB］（实际ZIP链接）
>
> ［本体/独立效果帧数］；［图集还原、时长、锚点和ZIP检查结论］。［是否已接入、尚未验证范围］。
>
> ［按项目规则列具体待验收项、版本、最小操作及证据；不强制其他项目使用本项目会话编号格式。］

## 4. 配套工具

`python scripts/review_delivery.py <scene|check|archive> <input> <output>`。输出已存在时拒绝覆盖。Python3；scene需要Pillow。报告放整个序列根之外。

### scene：离线尺寸对照

输入JSON路径相对该JSON所在目录。background是有已知尺度的战斗背景，可包含已有单位/建筑；units也可显式加入参照单位。displayScale是原始PNG到场景像素的最终合成倍率，必须由预计运行时换算推导，不能为排版任意适配；不得重复乘打包scale。pivot为原画布左下归一化；anchor为背景左上像素。输出PNG不改变背景尺寸，附JSON记录最终画布和可见边界，状态始终为待用户确认。

```json
{"background":"battle.png","units":[{"name":"candidate","frame":"001.png","displayScale":1,"pivot":[0.5,0.2],"anchor":[200,300]}]}
```

### video：编码已合成切换帧

先按原速及动作契约，用实际图集还原帧和独立特效合成场景帧，命名000001.png起。工具只编码，不生成动作调度或证明组合正确。执行：

`python scripts/review_delivery.py video <frames> <preview.mp4> --ffmpeg <ffmpeg-path> --fps <preview-fps>`

FFmpeg由当前环境提供，不下载或捆绑二进制。使用后独立解码核对帧数/时长；原速不等于任意统一源采样率。预览帧率由时间轴推导，不能改变源动作总时长。

### check：交付清单门禁

输入manifest包含以下字段。所有文件/目录路径相对manifest，可用绝对路径；requiredAnimations由任务契约独立列出。每项atlases默认仅一对，playbackClips仅一个；批准例外用splitApproval写明真人批准来源及范围。

```json
{
  "scaleReview":{"status":"approved","evidence":"scale.png","approval":"批准记录来源及范围","geometryVersion":"geometry-r1"},
  "requiredAnimations":["Idle_UpRight"],
  "animations":[{"key":"Idle_UpRight","sequence":"delivery/Unit/Idle_UpRight","atlases":[{"png":"atlas/Idle_UpRight.png","json":"atlas/Idle_UpRight.json"}],"playbackClips":["Idle_UpRight"]}],
  "includesDeath":false,
  "previews":{"sceneTransitions":"scene.mp4"},
  "checks":{"sequences":{"status":"passed","evidence":"sequences.json"},"atlasRestore":{"status":"passed","evidence":"restore.json"},"timingPivot":{"status":"passed","evidence":"timing.json"}}
}
```

包含死亡时includesDeath=true并提供previews.interruptedDeath。工具检查缺项、文件存在/非空、声明的单动画/图集数量、动画配置scale一致，记录关联文件哈希；失败退出2。它不验证批准真实性、报告内容、视频可解码性或实际播放器行为，操作者仍须独立核实，不得以手填passed代替检查。

### archive：归档及逐文件核对

`python scripts/review_delivery.py archive <clean-package-directory> <outside-directory/package.zip>`

显式准备只含本次交付的干净目录；工具归档其中全部文件，拒绝空目录、外部文件链接及将ZIP写入源目录，校验CRC/条目数和全部条目SHA256，输出ZIP及同名.json。只用于交付材料，不收录凭证、虚拟环境、无关模型或第三方程序。check报告先入包，再archive；ZIP报告保留包外，避免循环哈希。
