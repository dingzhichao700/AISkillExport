---
name: aiui-to-ugui
description: Build or continue a Unity uGUI presentation layer from a game UI request or existing approved UI artifacts, covering reviewed UI design, UI visual assets, Figma structure, Prefab, UIBinder export, input wiring, view state, and calls into business APIs. Use for UI production or presentation-only runtime integration. Hand non-UI game art asset generation and production processing to game-art-asset-pipeline; do not own gameplay rules, authoritative business state, business configuration, or persistence.
---

# AIUI to Unity uGUI

Run the workflow as a sequence of explicit artifacts and approval gates. Keep the
process reversible and do not invent project-specific rules.

Non-UI game art such as characters, aircraft, enemies, equipment, projectiles,
world objects, gameplay icons, effects, textures, and progression series belongs to
`game-art-asset-pipeline`. This Skill owns visual assets only when they are part of a UI
design or presentation-layer delivery.

## Start a run

### 外部图像模型登记（首次使用时强制执行）

本 Skill 遇到视觉稿、独立位图或其他图像生成需求时，一律使用用户登记的
外部图像模型。禁止使用 Codex/ChatGPT 内置图像生成能力，除非用户明确取消
这一限制。

首次使用时，图像生成前只收集并登记以下信息：

1. 提供方名称；
2. 官方服务地址或官方接口文档；
3. 模型名称；
4. 保存 API Key 的环境变量名称。

API Key 只保存在用户配置的安全环境变量中。环境变量只存 API Key，不承载
服务地址、模型名称或其他公开连接配置。当前兼容约定为 `QWEN_ANI`；新提供方
可使用清晰的提供方专属变量名，或使用通用名称 `AIUI_IMAGE_API_KEY`。

只能在实际发送请求时使用 API Key。禁止在聊天、日志、manifest、源码、提示词
或生成资源中打印、输出、复制、持久化或展示它的值。允许检查环境变量是否存在，
并把提供方、服务地址、模型名称和环境变量名称作为非秘密配置记录到 run manifest。

使用登记的提供方执行一次最小连通性与生成冒烟测试。正式生成前必须报告测试
成功，或报告实际请求返回的具体失败。配置或测试失败时停止并通知用户，不得回退
到 Codex/ChatGPT 内置图像生成能力。

首次测试通过后，后续任务默认复用已登记的提供方和公开连接配置。只有用户明确
授权更换提供方时，才重新登记并执行同样的测试。

### 外部图像模型执行约定（强制）

- QWEN 是当前登记的提供方时，先读取 `references/qwen-image-provider.md`，并且只能
  使用 `scripts/invoke-qwen-image.ps1` 发起图像生成请求。禁止在任务中临时拼装请求体。
- 当已批准的资产可作为画风、视角、主体或结构参考时，优先读取
  `references/qwen-reference-image-provider.md`，并使用
  `scripts/invoke-qwen-reference-image.ps1` 发起单张参考图生成。不要继续依赖纯文字提示词
  猜测已批准的视觉语言。每次审核只设置 `n=1`，未经当前图片批准不得生成下一张。
- 其他提供方没有固定调用器时，代理才可以依据已登记的官方协议构造请求；缺少调用器
  本身不代表图像生成能力不可用。
- 在尚未实际执行连通性请求或最小生成测试前，不得判断“无法生成图像”或
  “图像能力不通”。
- 只有凭据缺失、公开连接配置缺失、网络不可用、鉴权被拒绝、模型不可用或实际
  请求失败，才可以阻塞图像生成；必须报告具体失败，不得把缺少内置脚本作为原因。

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

### 图像提供方预检（每次生成前强制执行）

每次生成视觉稿或位图资源前：

1. 检查已登记的 API Key 环境变量是否存在，不输出、复制、持久化或展示其值。
2. 核对已登记的提供方、服务地址、模型名称和请求协议；缺少公开连接配置时先补齐，
   不得猜测。
   QWEN 必须核对为 `input.prompt` 字符串协议，不得使用 `input.messages`。
3. 在 run manifest 中记录提供方、模型、环境变量名称、凭据是否已配置及预检结果，
   但绝不记录 API Key。
4. 实际调用外部图像模型前显式告知用户，然后执行最小测试或本次正式请求。
5. 若提供方不可用或请求失败，报告具体错误并停止，不得静默切换提供方。
6. 若没有已登记且已配置的外部提供方，图像生成前停止并请用户完成登记；不得默认
   使用 Codex/ChatGPT 内置图像生成能力。
7. 若实际使用的提供方与登记或用户指定的提供方不一致，废弃本次草稿，把 run 标记
   为阻塞，并在继续前通知用户。

Accept partial runs. Resume from an existing artifact instead of recreating
approved upstream work.

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

- 使用已经登记并通过冒烟测试的外部图像提供方。`QWEN_ANI` 存在时，只能在
  QWEN 已登记为当前提供方且公开连接配置完整时将其用作 API Key。每个生成阶段前
  完成提供方预检，并在 run manifest 中记录所选提供方，但不得记录密钥。
- Do not silently switch image providers. Any unavailable provider, fallback,
  or provider mismatch is a user-visible stop condition; report it before
  generating or accepting artifacts.
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
  Editor C# generator, pack atlases, register Addressables, or build Player
  Content until the corresponding finalize or release checkpoint.
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
