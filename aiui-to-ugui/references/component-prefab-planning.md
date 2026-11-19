# Component and Prefab planning

## When to provide the plan

For a new screen, a whole-screen redesign, or a revision that changes component
boundaries, ownership, nesting, reuse, or state structure, produce a component
plan and readable diagram during Blueprint design. Start from the current
screen, approved structure, and existing widgets/Prefabs before proposing new ones.

Reuse an approved plan for a small alignment, text, asset, or binding correction
that leaves those decisions unchanged; update only affected records. A
downstream-only task or isolated raster extraction does not authorize redesigning
the whole screen. Missing historical diagrams do not invalidate an approved
Prefab or force a new design cycle for an otherwise local fix.

Read [ui-resource-representation.md](ui-resource-representation.md) when selecting
visible artwork forms. Mark bitmap assets and any explicitly approved vector
exceptions in the component plan; do not silently choose procedural rendering
while defining component boundaries.

## Decide boundaries before splitting assets or flattening nodes

Distinguish reusable components, screen-local compositions, and ordinary visual
children. Record separately whether a reusable component maps to an existing
widget, a nested Unity Prefab, or another project-approved implementation;
componentization and Prefab creation are not automatically one-to-one.

- Repeated objects with the same semantic role and state contract use one
  definition with instances and explicit data/visual variants. Sharing a PNG
  alone does not make separate copied trees a reusable component.
- A single instance may justify a Prefab when it has independently reviewed
  states, lifecycle, or a meaningful reusable presentation responsibility. Reuse
  an existing control before creating another generic button, progress bar, or slot.
- Keep a one-off layout composition within its owning screen when it has no
  independent reuse/state/lifecycle reason to become a Prefab. Do not create a
  Prefab for each Image or TMP merely because it is a node.
- Show definitions and instance/parent relationships, including nested components
  and shared containers. A shared navigation bar, for example, stays with its
  owning screen/container rather than being duplicated in each internal view.
  Drawing a component boundary does not make an internal view a new Panel or Scene.
- Keep plate, icon, editable text, fill, lock, badge, and other conditional layers
  distinct when their display behavior differs. Define state exclusivity, reset
  behavior, and instance-specific data/events; do not bake one instance's state
  into shared artwork or let one instance's callback alter another.

Components consume presentation data and call approved business APIs. They do
not acquire authoritative gameplay, persistence, or reward rules from a diagram.
Unknown services or state triggers remain dependencies, not invented data.

## One source for diagram, hierarchy, and handoff

Extend the Blueprint with a `componentPlan` record or a revisioned reference to
one. Use stable semantic IDs, not transient Figma node IDs. Capture only relevant
fields:

| Record | Information |
| --- | --- |
| Plan | Revision/status, source layout revision, coordinate system, target size, diagram/vector/structured-data paths |
| Definition | ID, purpose and boundary rationale, reusable versus screen-local/leaf, existing control reference or proposed Prefab mapping |
| Instance | ID, definition ID, parent/owner, count or list of uses, local bounds/anchors, explicit size or visual variant |
| Layers/state | Ordered asset/text/overlay children, visibility/exclusivity/reset, read-only data sources, event/click context |
| Mapping/evidence | Intended Figma master/instance and Unity Prefab/container/child mapping; actual identities and validation results when available |

Provide a legible diagram at the project's design resolution when known, an
editable SVG or equivalent vector source, and the structured plan. Derive the
diagram, annotations, and hierarchy from the same geometry/data. Use clear IDs
and a legend for the classifications and nesting. Simple color blocks/outlines
are sufficient; label the result as a structural proposal rather than a new
visual mockup, actual Prefab, or runtime screenshot. If placement is schematic,
mark candidate bounds instead of claiming measured geometry.

Use project-owned dimensions, names, and output locations. Do not turn an
example's resolution, colors, component count, or Prefab list into a universal
template. Store run-specific diagrams/data outside the skill.

Merge review into the existing design/structure checkpoint. Preserve approved
boundaries and scope. An ambiguous new ownership/variant decision may need user
judgment, but every redraw or minor correction is not a new approval gate. Plan
approval is distinct from visual, actual Figma, and runtime approval.

The component plan defines reusable structure, not the visible image export
catalog. Follow [figma-import.md](figma-import.md#keep-the-image-resource-master-area-export-only)
for the clean resource area; hiding technical masters must preserve actual
instance relationships and does not remove required newly delivered images.

## Carry the identities through production

Use the plan to drive extraction layers/state assets, Figma definitions/instances,
Unity Prefab instances/nested containers, and member binding ownership. Keep
project-selected transports, converters, and bindings. If a chosen tool cannot
preserve required component identities/nesting, report the exact gap and use an
authorized compatible mapping; naming copied frames or embedding a whole-screen
image does not implement reusable components.

At each relevant downstream checkpoint, compare actual artifacts with the plan:

- Figma: masters/instances or the explicitly agreed equivalent, expected counts,
  variants, parent/owner, editable labels, and independent state layers.
- Unity: actual Prefab source/instance links and nested ownership, required
  overrides, shared asset identity, and propagation to the declared uses.
- Binding/runtime: operate leaf controls through the intended owning component;
  verify instance data/callback isolation, state reset/reopen behavior, and the
  relevant cross-view use. Keep production and explanatory nodes separate.

Record proposed, approved, generated, actually inspected, and runtime-verified
states separately. A matching screenshot or successful export alone does not
prove reuse/nesting. For a legitimate implementation deviation, record its
scope and update the affected plan/review without silently flattening the
hierarchy or reopening unrelated approved work.
