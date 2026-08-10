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
