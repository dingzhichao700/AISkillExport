---
name: ugui-feature-logic
description: Generate and adjust Unity uGUI feature-window gameplay logic from an approved prefab and UIBinder starting point. Use when continuing a confirmed uGUI window into runtime gameplay logic, input handling, event wiring, state transitions, validation, and project-conforming implementation.
---

# uGUI Feature Logic

Use this skill for Unity uGUI feature windows that already have an approved prefab, UIBinder, and exported members, and now need gameplay logic implemented or adjusted through conversation.

## Core scope

- Start from an already prepared window prefab and its bound view class.
- Follow the target project's existing Panel, View, Control, Model, event, config, and persistence patterns.
- Support iterative dialog-driven changes without hardcoding one specific screen into the skill itself.
- Preserve accepted art, layout, prefab hierarchy, and member selection unless the user explicitly asks to change them.
- Treat validation and compilation as required parts of the workflow after code or prefab changes.

## Current confirmed rules

- Window prefabs that behave as panels should bind to a `BasePanel` subclass.
- `BasePanel` subclasses must define a constructor and set the panel layer there.
- `BasePanel` subclasses must override `OnOpen` and `OnClose`.
- If keyboard input is needed, override `OnPanelOperate` and route by `PanelOperateEnum`.
- If a window listens to messages, open-time registration and close-time cleanup should be paired, usually through `AddLis` and `RemoveLis`.
- `BasePanel` window prefabs should use a centered root pivot by default unless the design explicitly requires otherwise.
- If Unity shows an editor/runtime load failure but the built player or Addressables build works, check registration state first: duplicate Addressables entries, stale paths, GUID mismatch, or leftover imported copies.
- Keep runtime-object identity separate from Sprite identity. Independent
  GameObjects may share one Sprite and still own separate movement, visibility,
  firing, upgrade, and interaction state.
- Do not duplicate a bitmap solely to represent left/right or repeated runtime
  instances. Use separate assets only when their approved pixels or import
  settings differ.
- Preserve approved art, layout, text bounds, font weight, alignment, and text
  effects during logic changes unless the user explicitly changes them.
- Add components and behaviour scripts only when the implemented feature logic
  actually consumes them or Unity enforces the dependency. Do not retain or
  introduce speculative `CanvasGroup`, animation, raycast, or helper
  components; preserve explicitly used components and remove only those whose
  lack of consumers has been verified.
- Preserve the approved one-to-one bitmap size chain during logic changes:
  non-scalable PNG pixels, Figma production bounds, and Unity Image bounds stay
  identical, and Prefab RectTransform positions and sizes remain integers.
- For a runtime value display, keep the fixed background private and bind only
  the dynamic fill unless another layer genuinely changes at runtime. A normal
  full-state fill may use `Image.Type = Filled`; a directionally sliced fill
  must set Border only on its stretched axis, keep the perpendicular Image size
  equal to the bitmap size, and change length, mask, or segments so required
  end caps are not clipped. Clamp values independently from bitmap geometry.
- Before updating a progress-like display, require explicit current value,
  full-state value, full-state display length, minimum safe length, direction,
  and runtime mechanism. Use `Clamp(current / full, 0, 1)` and calculate the
  visible length from the declared full-state length, never from geometry left
  by a previous runtime update. Restore that baseline on reopen or pool reuse.
- Keep business maxima separate from approved bitmap geometry. Changing a
  maximum changes the ratio only. At zero, use an explicit empty state rather
  than presenting a sliced fill's minimum safe length as remaining progress.
- Build data-driven routes and graph connections from reusable state Sprites,
  not from a whole-route bitmap or per-instance Figma preview images. Keep one
  runtime `Image` per connection, select its canonical Sprite from current
  state, set `Image.Type = Sliced`, preserve the declared perpendicular
  thickness, and change only its length and rotation.
- Derive every dynamic connection from explicit endpoint data. Place its local
  centerline start at the source point, calculate length with endpoint
  distance, and calculate rotation with `Atan2`; do not reuse Figma preview
  pixels or rotated axis-aligned bounds as runtime geometry. Recompute the
  state and geometry when topology, unlock state, or endpoint layout changes.

## Workflow

1. Read the current project rules before editing.
2. Inspect the already approved prefab, bound view class, and existing runtime patterns.
3. Implement only the requested gameplay logic and supporting code.
4. Keep the first pass minimal and testable.
5. Rebuild or re-import as needed, then verify compilation and runtime behavior.
6. Report unresolved deviations clearly before moving to the next adjustment.

## Boundary with AIUI-to-uGUI

- `aiui-to-ugui` owns the staged UI handoff, structural export, and member-export process.
- `ugui-feature-logic` starts after the approved prefab and member set already exist, and focuses on gameplay logic plus runtime adjustments.
- Do not re-derive the whole UI generation pipeline inside this skill.

## Output expectations

- Produce implementation that fits the target project instead of inventing a new framework.
- Keep the skill general; do not embed project-specific one-off files, logs, or prefab snapshots into the skill package.
