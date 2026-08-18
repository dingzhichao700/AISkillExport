# Unity uGUI View Integration

Read this reference after an approved Prefab, UIBinder, and runtime member set
exist, or when a request starts from equivalent project-owned artifacts.

## Ownership boundary

Own presentation behavior: input, event subscriptions, view-local state,
visibility, text, images, progress displays, animation, and calls into business
APIs. Do not decide whether a business action is allowed, calculate its lasting
result, mutate authoritative state directly, design business configuration, or
persist gameplay data. Request those capabilities from `game-feature-logic`.

## Project integration

- Inspect the target project's Panel, View, event, input, and binding patterns.
- Bind panel Prefabs to a `BasePanel` subclass when that is the project convention.
- Define the required constructor and panel layer, and pair `OnOpen` with `OnClose`.
- Route keyboard input through the project's panel operation mechanism.
- Pair open-time event registration with close-time cleanup.
- Preserve approved art, hierarchy, geometry, member selection, text, and effects.
- Add components only when the implemented presentation behavior consumes them or Unity requires them.
- Keep independent runtime GameObjects separate even when they share one Sprite.

## Dynamic presentation

- Bind dynamic content and controls; keep fixed backgrounds private unless they genuinely change at runtime.
- Keep business maxima separate from bitmap geometry. Clamp displayed ratios and restore declared geometry baselines on reopen or pool reuse.
- Build dynamic graph connections from endpoint data and reusable state Sprites, not whole-route preview bitmaps.
- Recompute dynamic geometry and state when topology, layout, or unlock state changes.

## Code structure

- Keep View and UI Item classes under the feature module's `view/` directory.
- Keep business mutation behind Control APIs. Views may read display data but must not directly mutate authoritative Models or VOs.
- Preserve generated binder regions and third-party formatting.
- Apply the target project's human-authored C# formatting outside generated regions.
- Add intent-focused comments only at non-obvious lifecycle, asynchronous, state-transition, resource, pooling, numeric, and cross-layer boundaries.

## Validation

Verify compilation, Prefab references, event cleanup, reopen behavior, input,
display refresh, and calls into business APIs. Report missing or provisional
business interfaces instead of embedding temporary business rules in the View.
