# 异星军团已验证样板接续

这是历史索引与项目适配示例，不是通用默认值。先读当前项目入口及正式规范，再读输出当前状态；此文件不授予下载、接入或修改游戏的额外权限。

- 工作区：E:/Codex_Projects/异星军团；正式工程：E:/UnityTemplateTest/Starfront/Project。
- 权威规范：E:/UnityTemplateTest/Starfront/文档/规范/专属规范/作战单位3D转帧制作与验收规范.md；同时读其引用的美术、动作、阶段与光照规范。
- 独立状态：outputs/assault-mech-3d-animation-test-v1/process-state.json。公共卡牌协调另读项目协调Skill及任务契约，不从试验记录自行批准公共gate。
- 模型为社区Imperial Marauder改版，72骨骼，3网格，部分贴图缺失；不是原版完整官方资产。工具本地Blender4.5.3，M3导入器适配记录在既有工作目录，Skill不打包模型、贴图、Blender或插件。
- 静态几何基准static-calibration-v1/geometry.json；本角色两源UpRight/DownRight，112画布、448超采样、pivot(.5,.25)、公共ortho约1.97449、稳定高度标尺48px。新模型不可照抄。
- 源动作Stand0..94共95、Walk0..25共26、Attack Left/Right0..64各65，30fps，每向251合计502。Walk边界脚部差异是已披露来源问题，不能称技术无缺陷。
- v1纯色丢装饰；v2恢复大装饰并添加最终1px外边；v3头盔/肩甲细化；v5整武器亮银；v6末端阈值分区不准确；v7按实际圆柱网格分区，用户认可并要求动作导出、放入工程。v7使用面索引只能绑定该网格摘要，不可复制到其他模型。
- 当前有效材质源style-reskin-v7/Marauder-cylinder-steel-v7.blend；预览和序列style-motion-v7；图集与备份game-import-v7。
- 8组PNG/JSON已替换Assets/Art/frameAnimation/scene/Colonial/MarauderPreview，保留meta及Addressables；当轮UI并行开发，未触发Unity刷新或实战。接续必须重新检查当前导入/编辑器状态，不把该历史快照当live状态。
- 现有测试fixture：Assets/Editor/MarauderGamePreviewValidation.cs及MarauderCombatPreviewValidation.cs；正式业务映射不是本轮成果。攻击约2167ms与测试技能400ms流程不匹配，曾截断至约11–12帧；应由游戏业务任务处理。
