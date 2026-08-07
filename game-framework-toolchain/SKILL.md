---
name: game-framework-toolchain
description: Generate, validate, maintain, and standardize the self-contained Game Framework Unity template toolchain. Use when creating a sample Unity project, inspecting or repairing Templates/Tools/docs, validating Addressables or generated project structure, or syncing approved sample-project changes back into the reusable template.
---

# Game Framework Toolchain

Treat the directory containing this file as the repository root. Resolve every bundled path relative to it.

## Start every task

1. Read `AGENTS.md` completely.
2. Read `docs/目录与分包原则.md` for Assets paths, groups, atlases, Prefabs, UI exports, or Addressables placement.
3. Read `docs/模板与导出规范.md` for template, generator, or validation work.
4. Inspect `git status --short`; preserve unrelated and pre-existing changes.
5. Classify the request as inspection, generation, repair, or standardization. Do not broaden its scope.

## Generate a sample project

1. Require the user to provide the sample project's export root directory as an explicit plaintext path at least once in the current conversation. After it has been provided, reuse the most recently provided export root for later generation requests in the same conversation unless the user supplies a different path. Ask for the path only when the current conversation has no previously provided export root. Do not infer it from examples, environment variables, defaults, nearby directories, or another conversation.
2. Run `Tools/Test-GameFrameworkTemplate.ps1` before generation.
3. Inspect `Tools/Generate-GameFrameworkProject.ps1` parameters and resolve the exact output root, project name, and matching Unity editor.
4. Use only `Templates/GameFramework/ProjectFiles` as the Unity project source. Never read or clone another Unity project.
5. Never overwrite an existing target unless the user explicitly authorizes replacement and `-Force` is supplied.
6. Run the generator with the user-provided path passed explicitly to `-OutputRoot`; pass `-UnityEditor` only when auto-detection cannot find the template version.
7. Treat generation as incomplete until Unity compilation, Addressables output, final structural validation, and delivery-time Library pruning pass.

## Standardize approved changes

When the user says **标准化回写**:

1. Use only changes already accepted in a sample project or explicitly approved by the user.
2. Diff the verified sample against `Templates/GameFramework/ProjectFiles` and identify the reusable source of each change.
3. Sync reusable Unity files into `ProjectFiles`, workflow changes into `Tools`, and rules into `AGENTS.md` or `docs`.
4. Do not copy run-specific Blueprints, generated UI art, Prefabs, logs, file IDs, sample-only Addressables entries, or generated Unity directories unless explicitly promoted into the baseline.
5. Always rebuild Addressables during generation; do not add or copy a prebuilt Addressables cache.
6. Run template validation after the writeback. Do not commit Git unless explicitly requested.

## Validate outputs

Check proportionally to the change:

- the template contains `Assets`, `Packages`, `ProjectSettings`, embedded dependencies, and no external-project reference;
- no duplicated `docs/docs` or Unity-generated directories exist in the template;
- Unity logs contain no compiler or batch execution errors;
- Prefab Sprite GUIDs resolve and no Missing references remain;
- Addressables entries use canonical paths without sample-only content or duplicates;
- Player Content produces its success marker, catalog, settings, and bundles;
- the delivered `Library` retains `com.unity.addressables` but excludes regenerable import and compilation caches;
- owned temporary staging directories are cleaned after completion.

## Finish

Report changed source files, generated project path if any, validation performed, pending Unity-only checks, and uncommitted state.
