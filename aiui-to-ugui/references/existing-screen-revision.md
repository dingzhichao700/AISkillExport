# Existing-screen revision and acceptance

## Establish the real target

- Identify the normal game entry, loaded Prefab, owning Panel, internal view and
  shared navigation. A view inside a Panel is not a new independent window/Scene.
- Compare approved structure, current serialized assets and live code. Record
  which regions/nodes are retained, replaced or disabled and the scoped change set.
- Inspect manual edits before applying export differences. Preserve unrelated
  changes. Record untracked design changes and reconcile only affected parts;
  do not silently overwrite them using an older approved export.

## Keep components consistent

For changes to component boundaries, nesting, reuse, state structure, or owner,
apply [component-prefab-planning.md](component-prefab-planning.md) to the affected
parts. For an alignment/text/asset/binding fix within the approved structure,
consume that plan; do not require a whole-screen diagram or fresh approval cycle.

- Give repeated dynamic design objects a stable component identity across assets,
  Figma masters/instances, Unity Prefabs and bindings. Shared PNGs alone are not
  componentization. Separate fixed artwork, editable text and runtime states.
- Use instances of the same component for the same approved object. Record any
  intended size/state variants; if identity or dimensions are ambiguous, ask with
  the exact affected locations before creating a variant.
- Shared components may be nested inside different items. Keep instance data and
  click context independent, and validate that an instance update reaches all uses.

## Verify the whole screen

- Compare every region in scope against the approved structure: order, hierarchy,
  bounds, anchors, clipping/scrolling, buttons, texts, navigation ownership and
  replacement of obsolete controls. A passed component test is only component evidence.
- Inspect layout scripts, OnOpen/init, control synchronization and pooled-item
  refresh for overrides of Prefab geometry, labels, colors or state.
- Verify through the normal game entry after loading/layout settles. If a screenshot
  is needed for delivery or diagnosis, capture the actual run and identify its time
  or unique path. A scoped user-performed runtime check can be recorded directly;
  do not repeat it solely to obtain a screenshot the user does not request.
- Test the applicable changed states and reopening, not every unrelated feature.
  Do not alter persistent player data solely to stage an attractive screenshot.
- Independent preview may diagnose a defect; it does not prove real-entry behavior.
  If the entry is unavailable, report that acceptance as pending.

## Child-screen contracts

Record the target owner/API, opening item/context, source list and ordering,
previous/next behavior, return filter/scroll/focus, and refresh after save/cancel.
Distinguish independent child-screen tests from the actual parent-child-return path.
Missing business APIs stay explicit dependencies, not temporary UI business rules.

## Handoff evidence

Record approved structure revision, scoped changes, unresolved differences and
current screenshot path with capture context. Track component/program validation,
whole-screen runtime verification, user visual approval, cross-screen verification
and device verification separately. Only claim the scope supported by evidence;
compilation, successful export or sprite replacement is not whole-screen acceptance.
