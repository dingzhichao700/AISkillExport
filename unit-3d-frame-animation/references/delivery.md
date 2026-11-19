# 交付与验证

使用可用的character-animation-pipeline/references/delivery.md作为PNG/animation.json接口权威；以下为独立使用时的兼容字段摘要，不另加项目专属字段。配置需要变更时同步上下游。

`delivery/<Unit>/<Action>_<Direction>/001.png…`，同级`animation.json`，仅含：
`{"duration":1000,"scale":100,"pivot":{"x":0.5,"y":0.25}}`。

duration为已确认总时长整数毫秒且不小于帧数；scale为打包百分比10–200（不重复填超采样缩小系数）；pivot是原未裁画布左下归一化，取值0–1。PNG编号连续、统一位数、保留RGBA画布，不逐帧裁边或居中。方向/动作由目录名表达，loop/源帧/哈希等制作信息放整个delivery之外。项目未要求不额外生成方向或动作。用户要求PNG先交时可延后JSON，明确不是完整打包包。

检查脚本要求Pillow；执行`python scripts/validate_sequences.py <delivery> --report <evidence.json>`。报告必须位于delivery根之外，脚本不改输入。它检查所有动画配置、编号、同动画尺寸、Alpha存在、可见内容、完全透明边界、目录杂项。边界非透明视为需检查裁切；不能仅为了过检查删除角色像素。几何共用尺寸、源锚点和动作连续性仍需相应制作证据和视觉检查。

打包明确授权后，使用frame-animation-packer和实际可用TexturePacker。验证PNG/JSON成对、顺序与源帧数、总duration精确相等、均分毫秒差不超过1、pivot、sourceSize、无意外旋转、裁剪偏移与图集矩形边界。上限失败不偷偷缩图/减帧。抽样还原图集帧检查量化后细节与半透明边缘。

接入使用已有目标目录与资源名，覆盖前备份旧PNG/JSON并保留meta/GUID、人工Addressables归属和导入设置。新资源检查唯一GUID、Texture/Sprite类型、过滤/压缩、最大尺寸和加载地址。只写资源不等于Unity已导入。编辑器刷新按项目队列及并行工作约定；不为验素材改UI代码、场景、玩法、技能、配置或存档。分别报告文件落地、编辑器导入、运行视觉、构建/设备状态。

攻击动画总长与技能前摇/后摇不匹配时记录截断帧与范围，不擅改战斗业务。正式造兵接入和测试fixture映射需区分，测试图集被替换不代表生产配置已经引用。
