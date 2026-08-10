# Artifact contract

Keep workflow outputs separate from the skill itself. The exact folder names
may follow project rules; otherwise use this neutral layout:

```text
<run-output>/
├─ run.manifest.json
├─ blueprint/
├─ visual/
├─ assets/
├─ figma/
└─ unity/
```

## Run manifest

Record:

- run ID and current stage;
- target resolution;
- input and approved Blueprint revisions;
- image provider name without credentials;
- generated artifact paths and hashes when practical;
- Figma file and approved frame identifiers when available;
- target Unity project and output path only for this run;
- approval decisions;
- known deviations and unresolved items.

For Figma stages, record `figmaTransport`, `figmaTransportLocked`,
`figmaMcpAuthorized`, `localHandoffStatus`, and
`transportChangeApproval`. A URL alone must not set
`figmaMcpAuthorized: true`. Preserve the locked transport across later stages
until the user explicitly authorizes a change.

For any visual or raster generation, also record the provider preflight result:
`imageProvider`, whether `QWEN_ANI` was configured, and any provider failure or
fallback decision. A generated artifact from an unrecorded or mismatched
provider is non-authoritative until regenerated or explicitly re-approved.
For first use, record the external-provider enrollment and smoke-test status
without recording secrets. Subsequent runs must preserve the enrolled provider
identity unless the user explicitly authorizes re-enrollment.

## Which handoff file to read

Use these plain rules when one Skill hands work to the next:

- `run.manifest.json` is the task's main handoff. Read it first.
- `unity/export.manifest.json` is the detailed Unity handoff. Together these
  two files describe the current formal delivery.
- `Library/AIUI/*.export.json` is a diagnostic execution report, not a formal
  handoff.
- Files or folders containing `pre-`, `backup`, or `failed` are historical
  snapshots. Never treat them as the current result by default.

After changing a Prefab, script, resource, or member binding, update both formal
handoff manifests. Record actual counts and purposes, member-export status and
member set, validation results, and key file hashes. After Stage 8, do not leave
the handoff in an empty-member or "export later" state.

At the start of the next stage, compare the manifests with the actual Prefab,
code, and resources. If they agree, continue from the manifests. If they do
not, treat the real artifacts as facts, mark the manifests stale, and align the
records before continuing. Do not guess which of several JSON files is newest.

When the schema permits, mark formal handoffs with `artifactRole: handoff` and
`authoritative: true`; mark diagnostic reports with
`artifactRole: diagnostic-execution-report` and `authoritative: false`.

For ScrollList delivery, record `itemTemplateCount`, `previewCloneCount`,
`itemBinderCount`, and `runtimeDataCount` when known. Do not collapse them into
an ambiguous "item count"; runtime data count is independent from serialized
Prefab previews.

In short: read manifests for the formal handoff and inspect Prefabs and code for
the facts. If they disagree, align them first. Backups and Library reports are
for diagnosis only.

## Visual output

Store the composed mockup separately from isolated assets. Do not use a contact
sheet as an isolated-asset deliverable.

## Isolated assets

Each file must correspond to one declared asset ID unless a sprite sheet is an
explicit requirement. Record:

- file path;
- pixel width and height;
- intended display width and height;
- transparency status;
- source mockup and Blueprint revision;
- slicing metadata when applicable.

Reject opaque green, white, or other matte backgrounds when transparent output
is required. Check edge halos and unintended neighboring pixels.

### Incremental revisions and asset identity

- Freeze approved, unaffected nodes and assets. Regenerate only the declared
  change set, then run one low-cost global consistency check.
- Separate runtime-object identity from image-asset identity. Independent
  runtime objects may share one bitmap when their approved pixels are the same.
- Deduplicate identical visual resources across isolated PNGs, Figma resource
  masters, Unity atlas sources, and manifest asset IDs. Do not duplicate a
  bitmap merely because several nodes use it.
- Split objects with different gameplay semantics into independent nodes even
  when they appear as one composition in a mockup. Record their roles and
  independent runtime requirements in the Blueprint.
- Enforce semantic appearance constraints declared by the user; do not replace
  a weapon pod, companion, or other role with a visually adjacent category.
- Deliver visual image resources as raster PNGs. Keep text editable and record
  its approved weight, size, alignment, bounds, and effects.

Use tight visual bounds for isolated PNG assets:

- Crop fully transparent outer rows and columns unless the Blueprint declares
  that padding as intentional visual geometry.
- Apply the same crop basis to every visual state of one control. Normal,
  selected, pressed, disabled, and hover assets must retain matching dimensions,
  alignment origins, and base alpha silhouettes unless an approved state design
  explicitly requires a geometric change.
- When cropping removes leading transparent pixels, compensate the production
  node position by the same offset so the approved on-screen artwork position
  does not move. For example, after cropping 13 transparent pixels from the top,
  increase the node's Y coordinate by 13 reference pixels.
- Keep visual bounds separate from interaction bounds. Use a parent control or
  hit-area node for a larger clickable region; do not enlarge the raster asset
  with transparent padding solely to create a hit target.
- Record source bounds, crop offsets, final pixel dimensions, and compensated
  placement in the asset or handoff manifest when a crop changes geometry.

## Figma handoff

Record the production screen/frame ID separately from resource pages or source
asset layouts. Record material differences from the Blueprint, including user
edits made directly in Figma.

Follow `figma-import.md` for structured-layer, resource-placement, idempotency,
validation, and local-import-plugin rules.

Figma becomes the geometry source only after approval gate 2.

### MCP-independent Figma-to-Unity handoff

Figma MCP is a synchronization option, not a required runtime dependency of
the pipeline. After approval gate 2, Stage 6 and all later Unity stages may run
without Figma MCP when the formal local handoff contains:

- the approved Figma file/frame or revision identity;
- complete editable production hierarchy and geometry;
- current text content and fixed text bounds;
- all referenced local assets with dimensions and hashes when practical;
- the deterministic importer, structural snapshot, or equivalent source used
  to reconstruct the approved frame;
- validation and known deviations recorded in the formal manifests.

Do not spend Figma MCP quota to reconfirm unchanged data already represented by
that current handoff. Require a new synchronization only when Figma contains
unrecorded changes, the local handoff is incomplete, freshness cannot be
established, or the requested action directly reads or writes the Figma file.
Synchronization may use Figma MCP, a local Figma plugin, or another
user-approved transport. After synchronization, update the formal manifests
before Unity export.

### Text-bearing controls

Treat a button label as an independent text element with its own design bounds,
not as text stretched to the button bounds.

- Create the label as a child text node of the button or control.
- Give the label explicit `x`, `y`, `width`, and `height` values. Do not default
  its bounds to the button bounds.
- Use a fixed-width text box that is wide enough for the longest approved
  single-line label plus design-safe horizontal space.
- Keep the text-box height only slightly larger than its font size or resolved
  line height.
- Disable wrapping for single-line control labels. Resolve overflow by changing
  the approved text, font size, or text-box width instead of wrapping silently.
- Give labels in the same control group consistent height, vertical placement,
  and alignment. Width may be shared or designed per label.
- Preserve the approved label bounds during Figma-to-Unity conversion. Never
  replace them with the parent button's bounds or recompute them from the button
  unless the approved Figma design explicitly uses that layout.
- Pure decorative, explanatory, or placeholder Figma elements do not generate
  runtime Unity prefab objects; structural samples for runtime layout or
  repeated containers may be generated.

Example:

```json
{
  "name": "btnTabEquipment",
  "x": 600,
  "y": 286,
  "width": 230,
  "height": 73,
  "label": {
    "name": "txtLabel",
    "text": "EQUIPMENT",
    "x": 614,
    "y": 323,
    "width": 202,
    "height": 23,
    "fontSize": 19,
    "horizontalAlignment": "Center",
    "verticalAlignment": "Center",
    "wrap": false
  }
}
```

## Unity handoff

Record:

- Unity project root and destination directory;
- converter and version when known;
- source Figma file/frame;
- generated or modified files;
- asset import settings that affect rendering;
- component mapping decisions;
- validation result.
- whether Figma MCP was used, deliberately isolated, or unnecessary because a
  verified local structural handoff was used.

Do not copy the run manifest into the Unity project unless project rules or the
user require it.

### Addressables execution mode

Default AIUI Prefab iteration to development mode when the target project uses
Addressables `Use Asset Database`:

- refresh or register the generated runtime Prefab and runtime art entries;
- compile code and validate Prefab structure and references;
- do not run `BuildPlayerContent` during ordinary generation, correction, or
  human-review iterations;
- record `addressablesMode: Use Asset Database` and
  `addressablesBuilt: false` in the Unity handoff manifest.

Run a Player Content build only after the user explicitly requests production
mode, a formal export, an Addressables build, or delivery preparation. A full
sample-project export governed by the template toolchain remains a production
validation workflow and may require Addressables building independently of this
AIUI iteration default.

### ScrollList preview items

Keep one authoritative `itemTemplate`. The number of serialized editor-preview
or pool clones is not fixed: retain enough to verify the visible layout, with
only a small overflow unless an explicit comparison or debugging purpose needs
more. Estimate visible capacity from the viewport, item size, spacing, and row
or column limits; do not equate runtime data count with Prefab clone count.

Record the actual clone count and its purpose in the Unity handoff manifest.
Binding and delivery validation must inspect every retained clone without
asserting a universal exact count such as 50 or 100.

For every text-bearing control, validate that the generated TextMeshPro
`RectTransform` matches the approved Figma label bounds, remains single-line,
does not clip or overflow, and was not expanded to the parent control size.

### Unity Prefab hierarchy naming

Normalize Unity GameObject names after structural conversion. Treat this as a
Unity-side readability convention; do not rename Figma layers or change the
approved hierarchy, components, geometry, or visual result.

Use lower camel case in the form `<component-prefix><SemanticName>`:

| Unity role | Prefix or pattern | Examples |
|---|---|---|
| `Image` | `img` | `imgBg`, `imgBgTitle`, `imgQuality`, `imgItem` |
| TextMeshPro text | `txt` | `txtTitle`, `txtLabel` |
| Button | `btn` | `btnAll`, `btnEquipment`, `btnClose` |
| Semantic grid container | `grid` | `gridInventory` |
| Repeated item root | semantic lower camel case plus stable indices | `itemSlot_0_0` |

Apply these details:

- Keep the Prefab root named after its bound class, such as
  `LegendaryInventoryPanel`.
- Name the screen's unique primary background `imgBg`; name a title background
  `imgBgTitle`.
- Name a title text node `txtTitle` and a button's local text child `txtLabel`.
- Name semantic buttons directly, such as `btnAll` or `btnClose`; do not retain
  transport-oriented names such as `Tab_All__Button`.
- Allow repeated children under different parents to reuse local names such as
  `imgBg`, `imgQuality`, `imgItem`, and `txtLabel`.
- Preserve stable row and column indices on repeated slots.
- Do not encode component type suffixes such as `__Image`, `__Button`,
  `__TextMeshProUGUI`, or `__RectTransform` in Unity GameObject names.
- When target-project rules define a different prefix, follow the project rule
  and record the deviation in the handoff manifest.

Validate that no converter-style component suffix names remain in the
production Prefab unless explicitly required by the target project.

### Interactive control serialization

When the target project uses `GameButton`, configure its displayed text through
the component's own text-display contract instead of setting only the child
TextMeshPro text. Bind the component's label reference to the intended text
node and serialize the approved text value into the component so its editor and
runtime synchronization cannot clear or replace the label unexpectedly.

Controls whose interaction feedback scales their transform must use a centered
Pivot, normally `(0.5, 0.5)`, unless the approved design or project component
explicitly requires another scale origin. When normalizing Pivot during export,
compensate the anchored position so the approved visual bounds do not move.
Validate both the serialized Pivot and unchanged screen-space bounds.

## Unity code-binding handoff

Record:

- verified source Prefab and root object;
- binding mechanism and generator version or command when known;
- generated and user-authored code paths;
- attached root component type;
- binding-initialization state, member-export status, and actual exported-member
  counts;
- compile, serialization, missing-reference, and regeneration results;
- pending human member-selection and export state.

Do not place machine-specific absolute paths in generated source code. Do not
duplicate generated member declarations in the Blueprint or Figma handoff;
record initialization in the run manifest because later members are selected
manually from the approved Prefab.
