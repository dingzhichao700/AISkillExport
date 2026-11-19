# Pipeline

## Operating rules

- Execute only the requested stage or the next eligible stage. Approved upstream
  outputs are reused; the stages below are checkpoints, not a requirement to
  recreate every artifact or rerun every check on each iteration.
- Reuse approved artifacts by their accepted attributes and roles; execute the comparison and candidate-promotion contract in [review-baseline-and-diff.md](review-baseline-and-diff.md).
- Keep generated artifacts in a run-specific output directory, never inside
  this skill.
- Ask only for information that blocks the next action.
- Do not treat a rendered screenshot as structured design data.

## Scoped execution and verification

For resource selection, assembly, binding and runtime delivery, apply [resource production and consumption](resource-production-and-consumption.md).

- Before import, classify only this batch: resource identity/type, production
  source versus runtime asset, shared versus module-owned use, target directory,
  Group, bundle label/key, and required importer settings. Read project rules and
  the authoritative resource manifest; do not copy project routing tables into
  this Skill or infer new ownership from an old directory. Source images are not
  runtime registrations. Reuse existing shared assets rather than copying them.
- After import/assembly, verify that those routes and required references actually
  match. Unresolved ownership or an actual collision blocks the affected item,
  not independent work. Existing-asset migration, deduplication/deletion, global
  package policy and governance tooling belong to the project resource owner.
- Do not wait for unrelated library cleanup, generic tooling completion, or its
  full failure/recovery suite. Use an existing supported import/editor path for
  the authorized batch when it meets the same resource contract. Missing tooling
  is not a passed check; record the direct route and its actual result. Do not
  disable gates or silently change governance manifests to bypass a real error.
- Reproducible generated assets/Prefabs do not require extra Unity backup copies.
  Keep the approved upstream source and generator. Before replacement, identify
  and preserve manual changes and user code that cannot be regenerated. Existing
  asset migrations follow their separate project rules; do not apply migration
  backup/recovery procedures to ordinary UI generation by default.
- Consolidate checks into one result for the candidate: batch routing/import,
  compilation, required hierarchy/instance/binding references, visual comparison,
  and the changed runtime behavior. Later chapters describe coverage, not new
  runs of the same checks. Recheck only changed or failed portions; widen coverage
  only when a concrete dependency requires it. No unrelated full-library scan.
- Use the actual normal entrance for runtime delivery. Preview is optional when
  it answers an unresolved design question; it is not an obligatory detour before
  an already-approved formal integration. Reuse existing Game View sizes; do not
  add presets without explicit permission. Scoped user runtime verification can
  supply acceptance evidence without repeating it merely for another screenshot.
- Keep one current handoff record linking upstream sources and actual results;
  existing required manifests may reference it rather than duplicate narratives.
  Retain visual/structure approval gates and label preliminary, functional and
  device/release acceptance separately. Do not expand a user's preliminary pass.

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

Apply [component-prefab-planning.md](component-prefab-planning.md) when this
scope includes new or changed component boundaries. Record the diagram,
definitions/instances, nesting/ownership, state layers, and intended Prefab
mappings in or beside the Blueprint. Reuse the approved plan for unchanged local
fixes, and include any necessary review in the existing design checkpoint.

Allow conversational revision. Before starting image generation, identify the
exact Blueprint revision and applicable component-plan revision being used.

## Stage 3 — Visual mockup and art assets

Generate the visual mockup from the approved working Blueprint. Generate or
extract the individual raster assets needed for reconstruction.

For every isolated asset:

- use a true transparent background when transparency is expected;
- avoid colored matte, halo, unrelated decoration, text, or neighboring UI;
- preserve the element's visual proportions;
- record both pixel dimensions and intended display dimensions;
- do not rescale merely to make all files the same size.

Compare independent parts, their assembly and state previews separately with the mockup; record omissions or substitutions using the linked comparison contract.

Stop for approval gate 1. Apply requested visual or asset revisions before
continuing.

## Stage 4 — Structured Figma reconstruction

Prepare the complete JSON plugin delivery from the Blueprint, approved mockup,
and isolated assets. Follow `figma-import.md` for the actual import schema,
complete dependencies, delivery layout and validation. Provide the absolute JSON
entry path or containing directory. The user manually imports into Figma; do not
claim reconstruction is executed merely because the package was generated.

- Use named layers and meaningful hierarchy.
- Use actual text nodes for text.
- Follow the text-bearing-control rules in `artifact-contract.md`; preserve
  independent fixed label bounds instead of stretching labels to buttons.
- Use independent nodes for interactive controls. Instantiate repeated semantic
  objects from the planned component definition, with separate editable labels,
  state layers, and instance data. Preserve the planned nested ownership rather
  than replacing it with unrelated copied frames or shared PNGs alone.
- Place isolated art assets without changing their intended proportions.
- Match the approved mockup while retaining editable structure.
- Keep reference or source assets outside the production screen frame, in a
  clearly named resources section or page.

Do not interpret a decorative reference sheet as part of the production
screen.

## Stage 5 — Figma review and handoff

After the user has manually imported the JSON plugin, inspect the resulting
editable structure using the user-provided evidence or authorized transport and
compare it with the approved visual target. Validate resolution, hierarchy, bounds, alignment, text,
clipping, asset usage, and repeated structures. When a component plan applies,
inspect actual definition/instance links, counts, variants, parent ownership, and
nested relationships against it; a matching PNG does not prove component reuse.

Record material differences between the Blueprint and Figma using the linked comparison contract. Do not silently rewrite the Blueprint or treat an offline preview as actual Figma verification. Promote the reviewed candidate without semantic or visual reinterpretation.

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

Do not make user-performed JSON export a default prerequisite when a complete,
verified local handoff already exists. Synchronize only the demonstrated stale
or missing parts through the selected transport; distinguish source templates
from captured actual-node snapshots in evidence.

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
- repeated cells → instances of the reusable definition/Prefab specified by the
  component plan; ordinary non-reusable groups remain child RectTransforms.
  Resolve missing ownership/mapping before flattening a reusable definition.
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
- actual Prefab source/instance links, nesting, expected instance counts and
  overrides against the component plan when applicable; shared Sprites alone
  are not evidence of Prefab reuse;
- requested reference-canvas layout;
- pixel alignment against the approved Figma result;
- text-bearing controls preserve each label's independent bounds and single-line
  behavior;
- no unintended objects from resource sheets.

Report all deviations that remain.

### Stage 6 execution modes

Select the lightest mode that satisfies the current checkpoint; these are alternatives or scoped operations, not four mandatory sequential gates. An approved formal integration may combine necessary import, atlas work, assembly and binding in one execution, reusing prior visual approval:

1. **Preview** — synchronize changed raster assets and generate the visual
   Prefab from independent Sprites. Do not create or modify view C# files,
   initialize UIBinder, pack an atlas, register Addressables, or build Player
   Content.
2. **Finalize** — after visual approval, pack the module atlas, replace preview
   Sprite references, and continue into Stage 7 when binding is requested.
   Create or regenerate C# only when the view class or selected member schema
   actually changes.
3. **Runtime integration** — use the existing project loader. With Use Asset
   Database, update or add only required runtime registrations; check stable
   GUIDs, addresses, groups and duplicate entries. Registration does not build
   bundles and is not deferred until release. Reuse existing atlas resources;
   changing atlas output requires the explicit finalize checkpoint above.
4. **Release** — validate final registrations and build Addressables Player
   Content only within the authorized build/release workflow. A UI export or
   integration request alone does not authorize a content build.

For an existing screen, apply only the approved differences in every mode;
never use a full preview regeneration to overwrite unrelated manual changes.
After runtime integration, apply `existing-screen-revision.md` to the real entry
and whole screen, not just isolated Prefabs.

Prefer a persistent Editor exporter installed with the project template. Drive
it with a request file under `Library/AIUI`; do not add and delete one-off C#
scripts under `Assets` for each export. Adding or updating the persistent tool
may cause one compilation/domain reload during installation, but normal preview
requests must not.

Before copying or importing a raster asset, compare its content and importer
settings. Skip unchanged files and call `SaveAndReimport` only when the required
Sprite settings differ. A preview may rebuild its target Prefab, but it must not
reimport unchanged source images or run finalization/release work implicitly.

Run finalization as one persistent `Library/AIUI` request when supported: use
the approved resource route and rebuild only changed atlases when needed.
Loose runtime images do not require atlas packing. Update consumers and their
assembly/export producers together, validate saved references/paths and bindings,
then write a result file containing status and duration.
Do not use an `Assets` marker, Editor-log scraping, or a temporary script as the
completion signal. If a request remains unconsumed for five seconds, inspect
the installed runner/import state immediately instead of waiting through a
long generic timeout. Template/Skill validation belongs to tool changes, not
ordinary UI-content finalization.

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

Include compilation, the bound script asset, Prefab integrity, generated member
declarations and exact member references in the consolidated candidate check;
record the selection policy and exported set in the run manifest. Classify candidates by runtime need and keep
static visual-only nodes out. If the policy is absent or ambiguous, stop before
writing members and request it.

- Preserve the planned component/member ownership. Operate reusable child views
  through their declared interface where the project supports it; do not expose
  every internal Image/TMP to the screen merely to bypass nested ownership.
- Export directly operated interaction components.
- Export dynamically controlled lists, images, text, state containers, or
  visibility targets.
- For `ScrollListItem`, export dynamic item visuals and quality/state elements;
  keep a static slot background private unless runtime logic controls it.
- Invoke the target project's existing UIBinder Inspector one-click generation
  logic after configuring `uiList`.
- Require that generator to preserve user code, add component namespaces, and
  synchronize existing pool/preview clones when the project keeps them.

The same consolidated check covers generated fields, imports, Prefab references,
template/clone parity and compilation; do not repeat it because this chapter
ends. Binding generation itself does not implement interaction or business behavior.
