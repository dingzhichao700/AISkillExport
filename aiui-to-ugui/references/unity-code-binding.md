# Unity UIBinder initialization and member export

Apply these rules after the uGUI Prefab has been generated and verified. The
initialization and member export are one combined delivery stage when an
explicit member-selection policy is available.

## Establish the project convention

### Local C# style

Use the accepted reference panel as the formatting authority. Preserve its
blank-line/newline style and brace layout. Every generated panel class must
include a concise XML class summary in the project's established language and
style. Add brief comments to non-obvious lifecycle, binding-recovery,
state-transition, and interaction functions; avoid comments for trivial
assignments.

Read the target repository's governing instructions and inspect representative
sibling UI implementations before writing. Determine:

- view or panel base class and namespace;
- generated-code and user-code locations;
- whether generated classes use partial classes, inheritance, or another split;
- the `UIBinder` type, serialized bound-script field, and required root object;
- the view-code path, class base type, namespace, and empty binding markers;
- the editor workflow the user will later use for manual member export.

Prefer an existing project generator when one is configured. If no generator
exists, reproduce the established local convention only when it is
unambiguous. Do not introduce a package, reflection framework, naming protocol,
or editor extension without explicit approval.

## Initialize the binding

1. Derive the class name exactly from the Prefab name.
2. Create the class in the module's project-defined view-code directory.
3. Use the project's required view or panel base class and namespace.
4. Include empty generated-member markers when the existing inspector expects
   them, without adding member declarations.
5. Attach `UIBinder` to the Prefab root.
6. Assign the binder's C# asset/path to the new class.
7. Configure `uiList` from the explicit member-selection policy. Keep static
   visual-only nodes out; if the policy is absent or ambiguous, stop before
   writing members and request it.

Do not attach the generated view class directly when the project convention
expects `UIBinder` to add it at runtime.

## Preserve the human decision boundary

The user decides which UI elements may change at runtime. Codex may configure
and generate the approved set when explicitly requested, but must not:

- expand the approved set implicitly;
- export every visual node by default;
- replace the project's UIBinder editor generator with an independent writer;
- generate interaction or business logic.

Use the following selection rules when the user asks Codex to apply them:

- export directly operated interaction elements, including buttons and
  explicitly clickable text or containers;
- export dynamically controlled lists, sprites, text, state visuals, and
  visibility targets;
- omit static backgrounds, titles, and decoration unless runtime logic must
  control them;
- for a list item, export dynamic content such as the item Sprite and quality
  presentation; omit a static slot background unless it represents a runtime
  state.

## Execute approved member export

1. Configure `uiList` with only the approved nodes and their actual component
   types.
2. Invoke the same `UIBinderInspector` one-click generation method used by a
   human in Unity; automation must not handwrite an equivalent member block.
3. Ensure the editor generator derives and adds required namespaces from the
   real component types, such as `UnityEngine.UI` and `TMPro`.
4. If a `ScrollList` retains editor preview or pool clones, synchronize their
   binders from the item template by relative child path, or regenerate them
   after binding. Do not leave stale empty clone binders.
5. Preserve all code outside the generated-member markers.

## Size ScrollList editor previews

- Keep one authoritative node assigned to `ScrollList.itemTemplate`. Treat only
  its sibling editor-preview or pool clones as a variable-size set.
- Do not require a universal clone count such as 50 or 100. Estimate visible
  capacity from the viewport, item size, spacing, and row or column limits.
- Retain enough clones to inspect distribution, spacing, edges, and visual
  fidelity. A small overflow for scroll continuity is acceptable; substantial
  excess requires an explicit comparison or debugging purpose.
- Keep runtime data count independent from serialized preview count. Use the
  ScrollList pool and scrolling reuse for larger data sets instead of storing
  an equal number of clones in the Prefab.
- Record the actual retained clone count and its purpose in the handoff
  manifest. Validate every retained template and clone, but never hard-code an
  exact clone count in binding or delivery checks.

## Generate safely

- Treat the verified Prefab hierarchy as the binding source of truth.
- Keep the generated empty class deterministic and recognizable.
- Never overwrite user-authored behavior outside the generated-member region.
- Resolve serialized references through the project's supported editor or
  exporter workflow; do not edit Unity YAML blindly when an established safe
  path exists.
- Do not change approved layout or art while generating bindings.

If a generated root component already exists, update only its generated
surface. Never replace or truncate its user-authored implementation.

## Validate

Verify, using the project's supported tooling where available:

- the same-named class compiles in the correct assembly;
- the Prefab has exactly the expected `UIBinder` on its root;
- the binder resolves the intended C# asset/path;
- combined initialization and export produces exactly the policy-approved
  declarations and imports;
- list templates and retained pool/preview clones have equivalent non-null
  bindings;
- the Prefab has one authoritative item template, and its retained clone count
  is proportionate to viewport capacity or has an explicit validation purpose;
- the Prefab still matches the approved geometry and visual result.

Report whether member selection is pending or the approved export has passed.
