# Approved baselines, annotated differences and candidate promotion

Use this reference when preparing, revising or delivering UI extraction,
component structure, generated previews or a complete importer. It owns the
cross-stage comparison contract; transport/package details remain in
figma-import.md and component identity remains in component-prefab-planning.md.

## Identify the accepted object

Maintain separate baseline entries for independent artwork, component boundaries,
assembly geometry, state appearance, catalog layout, and actual application
execution. Each entry names its revision, evidence path/hash, accepted attributes
and human decision. Approval of one object does not silently approve another.
Apply the latest scoped decision without discarding unaffected earlier approvals.

For every review object record its role: independent image/export master,
structural component master, composition instance, state preview, or page-only
image. Record how it maps to asset IDs, definitions and consumers. A composition
does not substitute for an independent part; an image file does not prove a real
component link. Reuse accepted bitmaps for assembly/presentation faults; do not
recut or regenerate them merely because the catalog or state is wrong.

## Compare before delivery

The agent performs an annotated comparison before handing off a new visual
candidate or generated UI. This is an internal delivery check, not an automatic
extra human approval gate. Reuse the project's image-annotation/scale standard;
do not create a second drawing convention here.

Read back the executed candidate hierarchy and available actual output, not only
the source specifications. Compare against the accepted object at matched scale,
position, state and background where comparison requires them. For every intended
change, omission or unresolved difference record: object/location, baseline,
observed result, evidence, responsible layer and resolution. Keep confirmed
differences distinct from hypotheses. Inspect shape/alpha, native/display sizes,
visible text and effects, state overlays, parent-child relationships, resource
visibility and catalog role. A hash or node count is completeness evidence only;
it cannot replace this comparison. Self-produced expectations from the same
formula are not independent visual proof.

Unrequested differences must be fixed before delivery. Intentional differences
need a scoped human decision; unavailable runtime evidence stays explicitly
unverified. Use real application screenshots when authorized and available;
offline rendering and API surrogates must be labeled as such. Missing actual
execution must not be hidden by declaring the whole stage passed, nor become a
routine demand that the user repeatedly import candidates to debug them.

## Promote the accepted candidate

Generate the review evidence from the candidate's actual nodes/assets and retain
its code, payload, image manifest and evidence hashes. After approval, promote
that candidate; do not reinterpret the mockup, change assembly, recut artwork or
rerun uncontrolled generation during packaging. Version/path-only changes are
allowed, but compare normalized payload, all image bytes, generated hierarchy
and presentation settings to the accepted candidate, and repeat affected checks.
Any semantic/visual change becomes a new scoped candidate.

## Evidence and handoff

Report independently: resource/package completeness, structural/instance checks,
annotated visual comparison, actual Figma/Unity execution, and human acceptance.
Do not collapse these into an unqualified 'all passed'. The run manifest links
baseline entries, difference records, reviewed-candidate fingerprints and the
promotion comparison. Keep the approved scope and unresolved dependencies when
continuing; do not re-ask already settled artwork or layout decisions.
