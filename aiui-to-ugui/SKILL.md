---
name: aiui-to-ugui
description: Build or continue a Unity uGUI presentation layer from a game UI request or existing approved UI artifacts, covering reviewed UI design, UI visual assets, Figma structure, Prefab, UIBinder export, input wiring, view state, and calls into business APIs. Use for UI production or presentation-only runtime integration. Hand non-UI game art asset generation and production processing to game-art-asset-pipeline; do not own gameplay rules, authoritative business state, business configuration, or persistence.
---

# AIUI to Unity uGUI

Run the workflow as a sequence of explicit artifacts and approval gates. Before UI review or delivery, apply [approved baselines, annotated differences and candidate promotion](references/review-baseline-and-diff.md). Keep the process reversible and do not invent project-specific rules.

Non-UI game art such as characters, aircraft, enemies, equipment, projectiles,
world objects, gameplay icons, effects, textures, and progression series belongs to
`game-art-asset-pipeline`. This Skill owns visual assets only when they are part of a UI
design or presentation-layer delivery.

## Existing-screen revisions

Declare whether this is a new UI, an existing-screen revision, or a local fix.
For revisions, read [references/existing-screen-revision.md](references/existing-screen-revision.md)
before export or integration. Component replacement alone does not complete a screen revision.

## Component and Prefab planning

For new-screen/whole-screen design or changes to component boundaries, ownership,
nesting, reuse, or state structure, read
[references/component-prefab-planning.md](references/component-prefab-planning.md).
Include the diagram and revisioned plan in the Blueprint checkpoint; carry the
same identities into extraction, actual Figma instances, Unity Prefabs, and
bindings. Reuse an approved plan for local fixes that leave those decisions
unchanged. This adds no automatic extra approval round.

## UI artwork representation

Default to bitmap artwork. Before choosing or changing image/vector delivery,
read [references/ui-resource-representation.md](references/ui-resource-representation.md).
Visible native/procedural vector UI requires explicit prior human confirmation
for the named elements; layout approval alone does not authorize that exception.

## Start a run

For design dimensions, full-screen layout, safeContent, device safe areas or mini-game menu avoidance, read [references/viewport-safe-area.md](references/viewport-safe-area.md). Use project-owned dimensions and orientation; no sample resolution is a universal default.


### 图像生成默认入口

- 生成或修复图片，默认直接调用内置 Image 图像模型（`image_gen`）。不读取环境变量，
  不读取 API Key 文件，也不要求用户配置图片接口密钥。执行时读取 `imagegen` Skill，
  按项目目录保存产物；能复用的已批准素材不重新生成。
- 只有 `character-animation-pipeline` 的动画视频生成默认走 QWEN/DashScope；
  静态图片不因用于动画参考而改走该接口。
- Image 默认流程不要求读取 QWEN API Key、登记外部提供方、冒烟测试或进入 QWEN
  队列。QWEN凭据缺失、队列暂停不阻塞内置 Image 生图。
- 优先复用已批准参考，明确哪些是主体/画风/结构参考。透明素材请求真实Alpha并保留；
  每个审核阶段只制作该阶段要求的候选，不改变既有Figma/Unity验收门槛。
- 用户为当前任务明确选择外部图像API时才使用对应提供方。历史登记或凭据存在不能
  作为默认选择；内置Image失败时报告，不静默回退其他API或CLI。
- 旧QWEN调用器仅保留为显式外部模式：文生图读取 `references/qwen-image-provider.md`，
  参考图读取 `references/qwen-reference-image-provider.md`；仅此模式适用对应接口、
  凭据、队列及审批规则。凭据不得写入聊天、日志、manifest、源码或产物。

1. Identify whether the request starts from UI design, an intermediate artifact,
   Unity export, or an approved Prefab/UIBinder that only needs view integration.
2. Read `references/pipeline.md` for design-through-export work. For view-only
   integration, read `references/unity-view-integration.md` instead.
3. Collect only the inputs required for the next requested stage.
4. Read `references/blueprint-contract.md` before creating or changing a
   Blueprint.
5. Read `references/artifact-contract.md` before generating files, editing
   Figma, or writing into a Unity project.
6. Read `references/figma-import.md` before creating or updating a structured
   Figma deliverable, including when generating a local import plugin.
7. Read `references/unity-code-binding.md` before generating binding code,
   exporting members, or attaching a generated view component to a Prefab.
8. State the current stage, the inputs being used, and the next approval gate
   or verification checkpoint.

### 图像生成前核对

核对本轮目标、已批准输入、尺寸/透明要求、产物路径及审核停止点；manifest记录
实际使用的模型/工具和参考来源。默认Image路径不读API凭据，不请求外部测试。
只有用户明确选择外部API时，才额外核对官方协议、凭据安全和适用队列；调用前
说明上传内容及目标服务，未知结果不自动重发，不静默切换提供方。

Accept partial runs. Resume from an existing artifact instead of recreating
approved upstream work. Apply the scoped execution and verification rules in
`references/pipeline.md`: do not turn full-library governance or completion of
general-purpose tooling into a UI-content prerequisite. The UI owner checks this
batch against project-owned resource types, directories, Groups and bundle keys;
project resource governance owns those rules and existing-asset migration.

### Figma 插件交付与人工导入（必需）

- 完整开发插件是目录：标准 `manifest.json` 加其引用的代码、UI和全部依赖；清单JSON与完整项目数据JSON不是同一种产物。不得将清单重命名成“完整插件.json”来暗示单文件完整性。
- 直接给出该目录中 `manifest.json` 的可点击绝对路径，依赖由助手准备齐全；用户不用拼装，ZIP不替代入口。完整插件应包含当前已确认范围的完整界面，而非补丁；固定导入器＋项目数据另行标明，不混称。
- 图片母版区只展示实际导出图片，保持纯净且每图唯一；结构组件与已有引用保留在隐藏技术区。来源分类、独立框/内容拆分、清单一致性及组合单入口核验按 `references/figma-import.md` 执行。
- 每个界面使用固定短名称、目录和plugin id；版本显示在插件窗口。后续覆盖完整包并归档，不每版新增注册项。按figma-import.md核验迁移与历史注册清理。
- 交付前执行 `scripts/validate_figma_delivery.py` 并核对整页重建范围、脚本语法和最终回复路径。详细规则见 `references/figma-import.md`。
- 生成文件、程序检查、任务排队或完成回执不等于实际导入和结构通过。导入后核验真实图层及完整截图，用户批准该结构版本后才能进入Unity导出或结构对齐。
- 用户手动导入为默认；未获明确授权不代操作Figma。分别记录安装/重启/任务提交/实际导入/结构批准，不让用户重复完成已完成步骤。


### Figma transport preflight (mandatory)

Before any Figma read or write, determine and record the selected transport.
A Figma URL identifies a file or reference; it does not authorize Figma MCP.
Call Figma MCP only when the user explicitly requests an online Figma read,
write, synchronization, or MCP operation.

When a project has an established local importer or verified local handoff,
lock that as the default transport for the run. Do not probe MCP availability,
inspect an online file, or consume MCP quota merely because a URL is present.
Changing transports requires explicit user approval. If the selected transport
fails, stop and report the failure; do not silently switch transports.

## Preserve authority boundaries

- Treat the Blueprint as authoritative for intent, content, component roles,
  states, and initial layout constraints through visual generation.
- Treat the approved visual mockup as a visual target, not as the sole source
  of structure or coordinates.
- After Figma review, treat the approved Figma structure as authoritative for
  final hierarchy, geometry, text placement, and asset placement in Unity.
- The approved structure may be handed off through a verified local importer or
  structural snapshot. Figma MCP is an optional synchronization transport, not
  a hard dependency of Unity export or later stages.
- Do not silently write Figma edits back into the Blueprint. Record material
  differences in the handoff manifest.
- Treat project rules supplied by the user or found in the target repository as
  authoritative for paths, packages, naming, and code placement.

## Enforce approval gates

Do not proceed past either gate without explicit user approval:

1. Approve the visual mockup and isolated art assets before Figma
   reconstruction.
2. Approve the structured Figma result before Unity export.

Binding is one combined delivery stage when an explicit member-selection policy
is available. Configure `uiList`, invoke the existing member generator, and
record the exact exported set. If no policy is supplied, propose the set and
wait instead of exporting every visual node.

If the user requests only one stage, stop after reporting its artifacts and
validation result.

## Complete the presentation layer

After an approved Prefab, UIBinder, and member set exist, continue with
`references/unity-view-integration.md` when the UI needs runtime behavior.

- Wire buttons, tabs, keyboard input, view-local state, events, and display refresh.
- Call business APIs and render their results; do not reproduce business rules in a Panel or View.
- Treat gameplay state, eligibility, rewards, costs, persistence, and business
  configuration as owned by `game-feature-logic`.
- Permit partial runs that begin from an existing approved Prefab/UIBinder; do
  not require rebuilding earlier visual stages.
- Validate compilation and runtime presentation behavior before handoff.

## Use tools conservatively

- Use built-in Image for bitmap generation/editing by default. Record the actual
  tool and reference provenance; API keys and provider registration are not needed.
- Honor an explicitly selected external provider for the current task; report a
  failure without silently changing providers. Do not reuse an old external run's
  provider setting as the default for a new Image task.
- Use an existing Figma file, plugin, converter, or authenticated connection
  when the user supplies one. Do not install software or create unrelated Figma
  files without an explicit request.
- Treat local Figma Importer as the default when that workflow is already
  established for the project. Treat Figma MCP as a separately authorized
  transport, not as the default or an availability probe.
- After an approved Figma revision has been captured locally with traceable
  structure, assets, revision identity, and validation, prefer that local
  handoff for deterministic Unity work. Do not consume Figma MCP quota merely
  to repeat information already present in the current handoff.
- If Unity shows an editor/runtime load failure but the built player or
  Addressables build works, prioritize checking registration state first:
  duplicate Addressables entries, stale paths, GUID mismatch, or leftover
  imported copies. Only then suspect prefab structure or view code.
- For `BasePanel`-style window prefabs, keep the root RectTransform pivot at
  the center by default. Only deviate when the design explicitly requires a
  different window anchor/pivot.
- Target Unity uGUI. Map images to `UnityEngine.UI.Image` and text to
  TextMeshPro by default.
- Defer custom Unity component mappings until the Unity export stage. Never
  guess their types or serialized fields.
- Inspect the target Unity project's governing instructions before writing.
- For iterative Unity review, use the Stage 6 preview mode and the project's
  persistent `Library/AIUI` request queue when available. Do not use a temporary
  Editor C# generator. Static preview does not register Addressables. Runtime
  integration may register only the assets required by the existing loader; this
  is not a content build. Atlas finalization and Player Content builds follow the
  separate checkpoints in `references/pipeline.md`.
- Reuse the target project's existing code-binding and member-export mechanism.
  Do not introduce a new binding framework implicitly.
- In the combined binding stage, create the same-named class, attach `UIBinder`,
  assign its bound C# asset, configure the policy-approved `uiList`, and invoke
  the target project's existing UIBinder editor generation path. Do not
  synthesize an independent field writer.
- Match the accepted reference panel's local C# formatting, including blank
  lines, newline/brace style, and concise XML class comments. Add focused
  comments to key lifecycle, binding, state-transition, and interaction
  functions when their intent is not self-evident. Apply human-authored code
  style only outside generated binder regions. Preserve generated and
  machine-maintained regions in their native format, and do not modify the
  project's generator solely to restyle its output.
- Limit writes to paths the user placed in scope.

## Keep the skill clean

Do not package run-specific Blueprints, generated images, cutouts, Figma file
IDs, Unity project paths, Prefabs, logs, credentials, or examples as skill
resources. Add scripts or assets only after repeated use proves that a
deterministic implementation or reusable template is required.

## Resource production and consumption

Before choosing/copying art, editing producers or custom image fields, and runtime delivery, read [resource production and consumption](references/resource-production-and-consumption.md). Follow project-specific persistence rules and update producers and consumers together. Before handing off formally generated or incrementally updated UI Prefabs, run a check of this batch's actual recursive Unity dependencies (AssetDatabase.GetDependencies). A formal Prefab must not depend on atlas production-source images such as `Assets/Art/atlasSource/`; use generated atlas Sprites or approved runtime loose Sprites instead. Report each offending Prefab → source image, and do not mark runtime delivery complete until this check passes. Normal source import and temporary visual preview remain allowed. Attach the actual check result; a missing or unexecuted check is not a pass. Use the project's existing check entry where available; this requirement does not authorize full-library cleanup.
## Finish each stage

Before handing work to another stage, apply the authority and freshness rules
in `references/artifact-contract.md`: synchronize the formal manifests with the
actual artifacts and do not present diagnostic reports or backups as current
delivery state.

Report:

- stage completed;
- artifacts created or changed;
- validation performed and unresolved deviations;
- approval or input required for the next stage.

Do not describe a stage as complete when its required artifact or validation is
missing.
