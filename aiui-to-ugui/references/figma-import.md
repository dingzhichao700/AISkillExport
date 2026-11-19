# Structured Figma import

When a component plan applies, preserve and inspect its reusable definitions,
instances, variants and nested ownership in the actual file. Follow
[component-prefab-planning.md](component-prefab-planning.md) for the mapping and
evidence; copied frames with matching names/images are not proof of reuse.

Apply these rules whenever Stage 4 creates or updates the Figma deliverable.

## Figma 插件交付格式与人工审核

2026-11-11 用户明确纠正：完整插件是完整目录，不是给任意JSON改一个“完整插件”名称。

1. **开发插件清单**固定命名为 `manifest.json`，只声明插件入口与权限；它不包含完整界面。**完整开发插件**是该清单及其引用的脚本、UI、图片/数据与必要依赖组成的目录。**完整项目数据 JSON**是被指定导入器读取的数据，不是Figma开发插件清单。三者在交付说明中必须分开。
2. 默认交付完整开发插件目录，直接提供其中 `manifest.json` 的可点击绝对路径；清单的 `name` 使用固定短名称，版本写入插件窗口和发布记录，不能把清单重命名为“中文名.json”“完整插件.json”。这是本流程交付约定，不宣称Figma技术上只接受这一文件名。同目录依赖由助手准备，不能要求用户拼装。ZIP只能附带，不替代可用目录和入口路径。
3. 用户要求“完整插件”时，包内须包含当前已确认版本的完整界面、组件及图片引用。不得交局部补丁、纯项目数据、只有manifest的空壳，也不得依赖旧插件、旧节点或未说明的本地服务。明确批准的固定导入器可继续作为另一路径，但必须说明“固定导入器＋项目数据”，不得冒称自包含完整插件；用户改要完整插件时按完整目录交付。
4. 交付前重新打开磁盘文件，核查：入口basename为manifest.json；字段符合开发插件实际结构；main及可选ui引用存在且解析到包内；全部其他资源依赖齐全；脚本语法可用；本轮全部界面分区、文字、组件、状态及图片引用可重建；入口路径和版本与最终回复一致。能自动检查的必须执行并保存结果，不以文件名或口头声明代替完整性验证。
5. run.manifest.json分别记录插件入口/目录/格式/版本/依赖/校验，以及项目数据路径（有则另列）、实际导入状态和结构批准状态。兼容字段pluginJsonPath仅表示manifest路径，不表示完整项目数据。程序检查通过、排队成功、任务succeeded均不能替代真实图层和完整截图核验。
6. 用户手动导入为默认；代操作须明确授权。首次安装、插件重启、任务提交、实际执行、截图导出、用户结构批准分开记录。用户已完成某步不重复催办；缺少任务提交由助手补齐。实际结构版本获用户通过后再进入Unity导出或对齐，现有手工修改必须保留。

### 全屏界面的标准稿与长屏适配稿

- 全屏界面的完整Figma插件至少生成一个项目标准尺寸Frame和一个更高的相对分辨率Frame；尺寸由项目指定，通用Skill不写死720×1280。窗口明确标注尺寸，支持分别导出实际结构和PNG。
- 两稿共用组件、资源和业务示例，按该界面的已确认适配策略生成不同布局。显式声明增加的高度由哪一区域承接、顶部/底部锚定、背景覆盖与裁切方法；不得只纵向拉伸整页、默认拉高牌库或用整页截图假装可编辑结构。
- 安全区与平台遮挡是另一维度：记录每稿边距和平台模拟条件。无安全区的长屏稿不能当作胶囊或真机验证；必要时另增已声明边距的适配稿，不伪装成真实设备数据。
- 交付前检查两稿实际Frame尺寸、裁切、整页背景覆盖、关键元素边界、组件等比及共享引用；分别记录离线验证、实际Figma结果与用户验收。只交本会话界面范围，相关界面不得为凑齐长屏页混入插件。

### 固定插件入口与版本辨识

- 每个界面维护一个稳定的完整插件交付目录、manifest路径、plugin id和短显示名称。名称采用“项目｜界面”，不塞版本号、修改摘要或“完整/固定”多套近似名称。版本及修改摘要显示在插件窗口内，并写入release记录。版本在窗口顶部独立醒目显示短版本及完整版本号，并绑定实际包数据，不以说明段落中的小字代替。
- 后续发布更新同一目录中的完整代码、UI和资源；更新前保存可回退历史，历史产物不再作为新插件反复注册。保留既有id，不能因改名随意换id导致旧pluginData不可见；确需迁移时核验旧稿归属，禁止按名称批删或强行认领。
- 首次迁移交付明确给出插件显示名、manifest绝对路径及“首次导入”；以后说明“关闭正在运行的插件后重新运行，无需重新导入”。必须区分版本文件已更新和Figma运行实例已加载，未实测不承诺热加载。
- 固定入口仍可为自包含完整插件，不等同本地队列服务。使用固定导入器+队列须按既有授权另行说明。完整插件目录内包含当前完整界面，不以固定入口为由只交补丁。
- 迁移核验后清理旧开发插件注册项，保留源文件、历史包和设计稿；只处理已核实属于本界面的条目，不清理其他专项。没有可靠注册管理接口时，由用户在Figma管理入口移除，列出确切名称与路径，不直接改写运行中应用内部数据库。
- 交付检查增加：稳定名称/路径/id与上版一致；窗口版本与包版本一致；链接指向当前固定入口；历史条目清理状态和实际导入状态分别记录。

推荐交付语句：“完整插件已放在此目录，选择 [manifest.json](绝对路径) 导入；同目录依赖已齐全。”不得称“这个单独JSON就是完整插件”。


Run `scripts/validate_figma_delivery.py <plugin-directory> --report <path>` before delivery. This checks manifest/dependency packaging only; it does not prove complete screen reconstruction, actual Figma import, or visual approval. Record those checks separately. Do not change plugin identity merely to revise a display name; identity changes may affect access to importer-owned plugin data.


## Choose the write method

- Run a transport preflight before reading or writing Figma. Record the chosen
  transport, whether it is locked, whether MCP is explicitly authorized, and
  whether a current local handoff exists.
- A Figma URL is reference data only. It does not authorize MCP access.
- Prefer the transport explicitly selected by the user. If the project already
  uses a local Figma development plugin or verified local handoff, lock that as
  the default transport and use it directly; do not try MCP first.
- Call Figma MCP only after the user explicitly requests an online Figma read,
  write, synchronization, or MCP operation. Never call it merely to inspect
  availability, discover a page, obtain a screenshot, or repeat information
  represented by current local artifacts.
- If the selected transport fails, stop and report the concrete failure. Do
  not switch between local importer, MCP, or another transport without explicit
  user approval.
- Keep a local importer self-contained and deterministic. Do not require
  network access when all Blueprint and raster inputs already exist locally.
- Store run-specific importer source and embedded assets under the run output,
  never inside this Skill. Promote a script into the Skill only after repeated
  use proves it is reusable.

## Choose the approved artwork representation

Follow [ui-resource-representation.md](ui-resource-representation.md): bitmap
artwork is the default; native/procedural vector display needs prior scoped
human approval. A Figma polygon or solid rectangle that looks correct is not
proof that production image delivery is complete. Convert authoring geometry
to declared bitmap assets before handoff when no vector exception is approved.

## Deliver one editable production structure

- Create a named production frame at the reference resolution.
- Use real Figma text nodes for text. Do not flatten the approved mockup into a
  single production image.
- Keep buttons, labels, images, repeated cells, quality overlays, and item
  images as independent named nodes with meaningful hierarchy.
- Apply the fixed independent label bounds from `artifact-contract.md` to every
  text-bearing control.
- Give repeated controls a consistent child structure. For an inventory cell,
  prefer a structure equivalent to:

```text
ItemSlot_<row>_<column>
  Background__Image
  Quality__Image
  Item__Image             # only when populated
```

## Separate image exports, component masters and review compositions

- Declare the accepted catalog roles and layout before arranging nodes. Independent
  image exports, true structural masters, composition instances and state samples
  are different review objects; apply [review-baseline-and-diff.md](review-baseline-and-diff.md).
- Default to production frames on the left and unique image exports on the right.
  Explicit human-approved catalog layouts may show a separate component library
  and group page-only images below it; preserve that scoped layout rather than
  silently restoring the default.
- The independent image export area contains one PNG master per unique exported
  bitmap at declared dimensions. Do not put headings, composition examples,
  state samples or diagrams inside it. Store names/sizes/provenance in layer names
  and manifests. A separately approved review/component area may use labels and
  a neutral inspection background; those helpers are never material exports.
- Keep structural masters and preview-only definitions separate from the image
  export set. Hide technical definitions by default; show the requested actual
  component masters when the user approved that view, retaining real instance
  links and excluding them from material export. Do not substitute assembled
  controls for the independent pieces requested for inspection. If some image
  export nodes are deliberately hidden, record that visibility exception and
  still provide an inspectable independent-part review; do not claim its visible
  set equals the complete export set.
- Existing common-library resources need not be re-delivered. Record traceable
  provenance separately for existing, newly created, extracted, locally repaired,
  and reference-only assets. Reusable in principle does not mean already present
  in a shared library. Do not hide a newly extracted frame or repaired button
  from the current delivery solely because it could later be shared.
- Keep independently replaceable content and frames separate, such as avatar
  portraits and avatar borders or card artwork and quality frames. Repeated
  uses instantiate the same canonical image master; do not bake or duplicate
  left/right combinations into additional images.
- Review composition and adaptation in complete production frames by default. An explicitly requested extraction/assembly comparison may show a representative composition with its independent parts, clearly labeled by role; do not proliferate redundant state boards.
  If only a number/progress/text changes within one structure, use representative
  examples and editable data; still cover genuinely different structures/states.
- Export Unity from the production hierarchy, never from the image-resource
  container. Keep the formal image export list, actual image-export nodes and delivered PNG files identical as sets; separately verify the declared visible subset and accepted catalog layout. Check duplicate/missing images and reject non-image auxiliary nodes within the independent image-export area.

## Make local importers safe to rerun

- Make each importer idempotent for its run. A rerun may replace nodes created
  by that importer, but must not delete or overwrite unrelated user content.
- Tag generated nodes with a run marker and semantic role. When using
  `SharedPluginData`, use a namespace containing only letters, digits,
  underscores, or periods; validate it against `^[A-Za-z0-9_.]+$` before use.
- Clean partial results by exact run marker, stable node ID, or exact reserved
  root name. Never use broad prefix matching that could select user nodes.
- If an earlier transport created a known incomplete temporary page, remove it
  only when the page identity and expected generated contents both match the
  recorded partial state.

## Validate assets before import

- Verify the expected asset count and exact filenames.
- Verify embedded or copied bytes against the source files with hashes or
  byte-for-byte comparison.
- Verify PNG dimensions, alpha channels, transparent corners where expected,
  and the absence of matte backgrounds or key-color fringes.
- Reject unintended fully transparent outer rows or columns. When transparent
  padding is intentional, require an explicit Blueprint or manifest declaration.
- Do not silently substitute a stale source sheet or previous run's asset.

## Preserve control-state geometry

- Give all visual states of one control the same tight image dimensions,
  alignment origin, and base alpha silhouette unless the approved design
  explicitly changes geometry.
- Derive tint, brightness, glow, and similar state variants from the canonical
  base geometry when practical. Do not introduce state differences through
  scale, border displacement, inconsistent cropping, or transparent padding.
- If transparent pixels are cropped from the top or left, offset the image node
  by the cropped amount so its visible artwork remains at the approved screen
  coordinates.
- Separate the visual image node from the interaction container. A larger
  button hit area belongs to the parent control; it must not be encoded as
  transparent pixels inside the image asset.
- Validate state assets for equal dimensions and alpha-mask alignment, then
  validate their visible bounds contain no unintended transparent margin.

## Avoid hidden visual blockers

- Do not add an opaque full-canvas image or rectangle when the production root
  already supplies the same background, unless the Blueprint explicitly
  requires a separate overlay.
- Keep background and dimming layers below production content and confirm their
  stacking order.
- After import, verify that the panel, title, controls, and at least one repeated
  cell are visible before declaring the write successful.

## Make execution observable and recoverable

- Show the current import stage when using a local plugin.
- On failure, keep an error surface visible and report both the failing stage
  and the concrete error. Do not silently close and leave an unexplained partial
  canvas.
- On success, report the production frame identity and resource-container
  identity.
- Record the chosen write method, generated file or plugin path, production
  frame ID when available, partial-state information, and unresolved work in
  the run manifest.
- Never describe the local importer as a fallback when it is the selected or
  project-default transport.

## Preserve authority boundaries

- Use the approved Blueprint and visual assets for the initial Figma import.
- Do not silently write later manual Figma edits back into the Blueprint.
- After approval gate 2, treat the current Figma hierarchy, geometry, text
  placement, and asset placement as authoritative for Unity export.
