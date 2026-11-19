# UI resource representation and vector exceptions

Default to bitmap resources for visible UI artwork: backgrounds, plates,
borders, icons, decorative lines, search rings and progress tracks/fills.
Use the standard Image/Sprite workflow with slicing, clipping, fill, rotation,
opacity or tint when needed. Keep text editable and independently bound.

Before using visible native/procedural vector elements in a production Figma
handoff or runtime UI, describe the exact elements, necessity, bitmap alternative
and tradeoffs, and implementation/maintenance impact. Obtain explicit human
confirmation for that scoped exception before implementation. Permission for UI
production, an approved layout, a shape appearing in a reference, or availability
of Figma geometry APIs is not approval to introduce vector rendering.

Record approved exceptions by element identity and revision with the human
decision and checks. If there is no explicit approval, deliver PNG/Sprite assets;
do not create a custom vector Graphic/mesh/shader as a shortcut around missing art.

This governs visible artwork, not editable text, empty layout containers, or
standard bitmap-control mechanics such as Image.Fill, nine-slice and clipping.
SVG/geometric data may remain as authoring sources, but that does not authorize
native-vector display in delivered production frames or runtime UI.

When replacing authoring geometry with bitmaps, preserve approved silhouette,
color, native size and layer order; reuse one asset per unique image. Record
source, alpha, intended size, slice/clip rules and instance references. Use
deterministic rasterization of established code/vector geometry when sufficient;
this is representation conversion, not a request to redesign existing art.

A measured progress fill asset represents the complete full state, with the
track separate. Current/full values drive standard clipping/fill; do not bake the
sample percentage into the fill image. An indeterminate moving segment is a
separate animation element and is not reported as measured progress.

At handoff, check both live definitions and expanded production instances for
unapproved vector paths/procedural shapes, native solid artwork used instead of
declared images, missing bitmap dependencies and incomplete render chains.
Fail before exporting an unapproved representation. Keep technical checks,
actual application execution and user review distinct.
