# Resource production and consumption

Read before choosing/importing art, editing generators/assembly tools, adding
custom image fields, and runtime delivery. Follow the target project's current
resource directory, reuse, persistence and loading rules and authoritative
manifest. Resolve the current engineering root; historical paths are not write
permission. This does not authorize old-asset cleanup or content builds.

## Select resources by business use

- Check current business purpose and actual consumers before creating/copying
  art. Residual references do not prove an obsolete asset is still needed.
- Reuse one authoritative asset where pixels and importer/display contracts are
  compatible. Different fields, screens and display sizes alone do not justify
  duplicates. Preserve approved Pivot, Border, PPU, materials and geometry;
  identify a real incompatibility before creating a derived resource.
- Separate authoring sources, runtime atlas products and loose runtime images.
  Production Prefabs must not recursively depend on atlas production sources.
  Temporary source-image previews are allowed but are not runtime delivery.
- Choose atlas or loose assets from loading lifetime, independent use, packing
  cost and project policy, not size alone. Common ownership requires actual
  shared consumers; a common directory is not automatically a Group. Do not
  infer ownership from old folders or register every dependency independently.
- Record this batch's identity, authority/address, source/runtime role,
  consumers, import contract and approved directory/Group/bundle route in the
  existing handoff/manifest. Do not copy project routes into this Skill.

## Update producers and consumers together

Identify affected exporters, generators, editor menus, assembly setters,
configuration sources/generators, Prefabs/variants and runtime consumers.
Fixing a Prefab while its producer recreates old references is incomplete.
Update both within authorized scope; if another owner must change a producer,
record the precise dependency and leave that regeneration path unverified.
Use the project's original config generator, not generated-JSON-only repairs.

Follow the project persistence contract. Where custom components must store
image paths, do not add public/[SerializeField] Sprite asset fields, including
arrays/lists or nested serialized data. Keep Sprite values as runtime caches
and use existing path setters/loaders. This is a project policy, not a universal
ban across Unity projects. Built-in Image/Button Sprite fields and UIBinder
component references are distinct and may use approved runtime assets.
Literal, configured and registered-ID-derived addresses are valid under project
rules; do not guess unregistered paths from display names.

For setters that convert Sprite arrays to saved paths, fill a local array and
assign the complete property once. Getter-element writes may change temporary
arrays without persisting anything. Reload saved data and verify actual path
fields and nonempty array/list entries, not only in-memory setter results.

## Consolidated delivery verification

1. Check routes/registration and actual recursive Unity dependencies via
   AssetDatabase.GetDependencies, including affected nested Prefabs/variants.
   Report each illegal Prefab-to-source dependency. Inspect custom serialized
   fields and dynamic paths too: dependency scanning cannot discover all
   runtime addresses. Compilation/non-null references are not enough.
2. Reload saved Prefabs/data. Exercise the affected producer using its supported
   generation path when safe; isolate output if regeneration could overwrite
   manual changes. Compare relevant asset identities/paths, not an unrelated
   full-screen rebuild. An unexercised producer remains explicitly unverified.
3. Use the normal UI entry to check changed images/states, navigation/reopen and
   affected pool reuse. If asynchronous loading changed, check rapid content
   changes/closing before completion: stale results must not replace current
   content or leak handles. Use the existing loader and per-consumer release;
   closing one consumer must not destroy another consumer's shared art. Do not
   add another loader or change valid UI visibility behavior to fit bad tests.
4. Preserve unrelated layout, text, approved display parameters and user data.
   Asset deletion/migration needs approved scope; within it update source,
   product/meta, consumers, producers and registration together. Full-library
   cleanup and full tool-test suites are not prerequisites for ordinary new UI.

Link actual results and unverified cases in the current handoff. Keep static
checks, actual Unity loading/lifecycle, Bundle/device evidence and user acceptance
separate. PNG hashes/disk savings do not prove memory or startup improvements.
These instructions do not install a universal automated Sprite enforcement gate.
Use the next authorized real feature to test behavior; do not invent game changes
just to validate this Skill.