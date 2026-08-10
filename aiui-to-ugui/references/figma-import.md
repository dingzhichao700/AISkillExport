# Structured Figma import

Apply these rules whenever Stage 4 creates or updates the Figma deliverable.

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

## Place resources predictably

- Default to the established single-page handoff unless the user requests a
  separate resource page: place the production frame on the left and tile
  isolated art resources to its right.
- Put tiled assets inside a clearly named container such as
  `Resources [Do Not Export]`.
- Preserve each resource's intended pixel dimensions and proportions.
- Export to Unity from the production frame only. Never treat the resource
  container or a decorative source sheet as production UI.
- Keep exactly one resource master per unique bitmap asset. Multiple production
  nodes may reference that master; do not tile duplicate masters for identical
  pixels or for left/right instances of the same art.
- Treat the resource container as a visual audit and mapping surface, not as an
  atlas or the sole source of Unity export truth. The formal manifests, actual
  PNG files, and production-node references define the export set.

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
