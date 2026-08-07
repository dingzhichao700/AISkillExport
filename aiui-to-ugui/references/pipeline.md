# Pipeline

## Operating rules

- Execute only the requested stage or the next eligible stage.
- Reuse approved artifacts.
- Keep generated artifacts in a run-specific output directory, never inside
  this skill.
- Ask only for information that blocks the next action.
- Do not treat a rendered screenshot as structured design data.

## Stage 1 — Initialize

Determine the run scope and read available project constraints.

Required before the relevant downstream stage:

- UI request and target resolution;
- existing Blueprint or starting description;
- image provider configuration before image generation;
- Figma destination before Figma writing;
- Unity project and output directory before Unity writing;
- project-specific rules before writing into a project.

Create a run manifest when files begin to be generated. Do not put secrets in
it.

## Stage 2 — Blueprint

Create or revise the Blueprint using `blueprint-contract.md`.

The Blueprint describes semantic structure, intended layout, visual direction,
states, asset needs, and Unity-facing roles. Keep it independent from a
particular generated image and from transient Figma node IDs.

Allow conversational revision. Before starting image generation, identify the
exact Blueprint revision being used.

## Stage 3 — Visual mockup and art assets

Generate the visual mockup from the approved working Blueprint. Generate or
extract the individual raster assets needed for reconstruction.

For every isolated asset:

- use a true transparent background when transparency is expected;
- avoid colored matte, halo, unrelated decoration, text, or neighboring UI;
- preserve the element's visual proportions;
- record both pixel dimensions and intended display dimensions;
- do not rescale merely to make all files the same size.

Compare the asset set with the mockup and record omissions or substitutions.

Stop for approval gate 1. Apply requested visual or asset revisions before
continuing.

## Stage 4 — Structured Figma reconstruction

Build a structured Figma representation from the Blueprint, approved mockup,
and isolated assets. Follow `figma-import.md` for the delivery layout, write
method, recovery behavior, and local-plugin requirements.

- Use named layers and meaningful hierarchy.
- Use actual text nodes for text.
- Follow the text-bearing-control rules in `artifact-contract.md`; preserve
  independent fixed label bounds instead of stretching labels to buttons.
- Use independent nodes for interactive controls and repeated inventory cells.
- Place isolated art assets without changing their intended proportions.
- Match the approved mockup while retaining editable structure.
- Keep reference or source assets outside the production screen frame, in a
  clearly named resources section or page.

Do not interpret a decorative reference sheet as part of the production
screen.

## Stage 5 — Figma review and handoff

Render or inspect the reconstructed screen and compare it with the approved
visual target. Validate resolution, hierarchy, bounds, alignment, text,
clipping, asset usage, and repeated structures.

Record material differences between the Blueprint and Figma. Do not silently
rewrite the Blueprint.

After user edits, capture the current Figma structure through an available
transport. A verified local importer or structural snapshot is sufficient when
it represents the approved revision; an older screenshot or unversioned cached
coordinates are not sufficient.

Stop for approval gate 2.

## Stage 6 — Unity uGUI export and verification

Read the current target-project rules before writing. Use the approved Figma
structure as the source of final geometry and hierarchy. Consume it from the
verified local handoff when one exists; Stage 6 must not require Figma MCP only
to reread an already captured and approved revision.

Before using a local Figma handoff, verify that it identifies the approved
revision and contains the complete production hierarchy, geometry, text,
asset references, and hashes or equivalent freshness evidence. If Figma has
newer unsynchronized edits, mark the local handoff stale and synchronize it
before export. Synchronization may use Figma MCP, a local plugin, or another
user-approved transport.

Default mappings:

- raster or sliced visual node → `UnityEngine.UI.Image`;
- text node → TextMeshPro component;
- screen root → uGUI Canvas-compatible hierarchy;
- groups and frames → `RectTransform` hierarchy;
- repeated cells → repeated child objects unless project rules require a
  reusable component.
- Pure decorative or explanatory nodes are omitted; only structural samples
  that represent runtime layout or repeated containers are exported.

Normalize the generated Unity hierarchy using the Unity Prefab naming rules in
`artifact-contract.md`. Keep Figma layer names unchanged and preserve the
approved structure and geometry.

Use the user's configured Figma-to-Unity converter, including Figma Converter
to Unity when selected. Do not install or replace a converter implicitly.

Resolve custom component mappings only now. If their types, namespaces,
required components, or serialized fields are unknown, stop and request the
mapping instead of inventing it.

Verify the generated assets and Prefab in proportion to the available tooling:

- import without compile or serialization errors;
- expected hierarchy and component types;
- reference resolution;
- requested reference-canvas layout;
- pixel alignment against the approved Figma result;
- text-bearing controls preserve each label's independent bounds and single-line
  behavior;
- no unintended objects from resource sheets.

Report all deviations that remain.

## Stage 7 — Unity binding export (combined initialization and member export)

Read `unity-code-binding.md` before changing code or attaching scripts. Start
from the verified Prefab and inspect the target project's rules, neighboring UI
implementations, and existing `UIBinder` implementation.

- Create a same-named C# class in the module's required view-code directory.
- Attach `UIBinder` to the Prefab root.
- Set the binder's C# asset/path to the newly created class.
- Apply the explicit member-selection policy, configure `uiList`, and invoke
  the target project's existing UIBinder member generator in this same stage.
- Preserve existing business logic and user-authored code when resuming.

Verify compilation, the bound script asset, Prefab integrity, generated member
declarations, exact member references, and record the selection policy and
exported set in the run manifest. Classify candidates by runtime need and keep
static visual-only nodes out. If the policy is absent or ambiguous, stop before
writing members and request it.

- Export directly operated interaction components.
- Export dynamically controlled lists, images, text, state containers, or
  visibility targets.
- For `ScrollListItem`, export dynamic item visuals and quality/state elements;
  keep a static slot background private unless runtime logic controls it.
- Invoke the target project's existing UIBinder Inspector one-click generation
  logic after configuring `uiList`.
- Require that generator to preserve user code, add component namespaces, and
  synchronize existing pool/preview clones when the project keeps them.

Validate generated fields, imports, Prefab references, template/clone parity,
and Unity compilation. Do not generate interaction or business behavior in
this stage.
