---
name: game-feature-logic
description: Implement or adjust upper-layer game features in a Unity project, including gameplay rules, authoritative runtime state, Models and Controls, business configuration design and generation, persistence, events, and feature-level validation. Use for combat, stages, rewards, progression, aircraft, companions, talents, inventory, or other game-domain behavior. Do not use for reusable framework/toolchain maintenance or presentation-only uGUI production and wiring.
---

# Game Feature Logic

Implement complete game-domain behavior while fitting the target project's
existing architecture and reusable infrastructure.

## Start every feature

1. Read the target project's governing instructions and current implementation.
2. Separate rules, authoritative state, configuration, persistence, events,
   presentation requirements, and provisional assumptions.
3. Identify reusable infrastructure already supplied by the project. Use it;
   do not create a competing framework.
4. Define a minimal, testable vertical slice and state its validation boundary.

## Own the business layer

- Own eligibility, costs, rewards, calculations, state transitions, and lasting results.
- Keep authoritative mutation behind project-conforming Control or service APIs.
- Create a module-named `{Module}Model` only when the module has business data that needs management; do not create an empty or artificial Model merely to satisfy a directory convention. When its responsibilities become too large or ambiguous, split additional Models by clear business responsibility instead of forcing all data management into one class.
- Keep collection, lookup, initialization, and storage boundaries in Models.
- Use VOs or equivalent data objects for individual runtime records; place `{Semantic}VO.cs` files under the module's `model/vo/` directory and do not let Views mutate them directly.
- Emit project-conforming events after successful state changes so presentation code can refresh without duplicating rules.

## Keep human-authored code readable

- In human-authored gameplay code, control-flow bodies such as `if`, `else`, `for`, `foreach`, `while`, and `do` must use braces and occupy separate lines. Do not compress a condition and its statement into one line, even for `return`, `continue`, or `break`.

## Separate scene simulation from presentation

- Treat the scene Model as the single source of truth. Scene element VOs own logical position, rotation, lifecycle, and gameplay state, and must not retain `GameObject`, `Transform`, `RectTransform`, `Image`, or other presentation objects.
- Give every scene element a stable unique id and an explicit scene Timer type at creation. Drive scene logic from scaled Timer delta messages rather than reading `Time.deltaTime` directly inside gameplay objects.
- Subscribe the scene Model once per Timer category and fan updates out to its grouped elements; do not register large numbers of individual elements directly on the Timer.
- Keep off-screen logical elements running. Create, synchronize, or recycle Views according to viewport visibility without treating View recycling as logical destruction.
- Before entering a scene, follow configuration references to collect the complete set of predictable entity, projectile, effect, and related resource dependencies. Deduplicate and preload them, and surface missing references before gameplay begins; keep dependency collection separate from loading and gameplay behavior.
- Keep collision detection factual: collision services report contacts, Models apply authoritative damage and lifecycle changes, and presentation code consumes the resulting events.
- Pair Timer and event subscriptions with teardown, cancel owned asynchronous callbacks, and fully reset mutable presentation state before reusing pooled Views.
- Keep temporary gameplay overrides explicit. When restoring production configuration, restore dependent tests in the same change rather than deleting assertions that expose stale test assumptions.
- Do not call a refactor complete when it only moves directories, splits files, or reduces line counts. Verify authoritative state ownership, dependency direction, presentation-reference removal, redundant-wrapper removal, compilation, and a representative runtime flow.

## Make business data configurable

- Identify repeated, balancing-sensitive, relational, or content-authored values that should not remain hardcoded.
- Design project-specific tables, beans, enums, keys, references, defaults, and validation constraints from approved feature requirements.
- Use the project's existing configuration toolchain, runtime manager, loading lifecycle, and Addressables conventions. When the project provides a Luban generation script such as `gen_json.bat`, invoke that script from its intended working directory; never bypass it by inventing or reconstructing Luban command-line parameters. For automation, satisfy a trailing interactive `pause` non-interactively without changing the script's generation semantics.
- Generate code and runtime data through the established tool; do not hand-edit generated files.
- Register finite categorical values as configuration enums instead of magic numbers. Store readable aliases in business tables, add alias-based data-validation dropdowns that cover future data rows, regenerate through the project script, replace duplicate handwritten runtime enums with generated types, and verify representative reads plus compilation.
- In Luban business workbooks, use `##var` for field names and nested child fields, `##type` for declared types, and `##` for concise configuration-facing descriptions. Expand ordinary nested Beans through additional `##var` rows. Put child fields that are at the same nesting depth on the same `##var` row instead of creating redundant format rows.
- Use alias-based dropdowns consistently: enum fields list enum item aliases, polymorphic Bean `$type` fields list concrete Bean aliases, and boolean fields list `true` and `false`. Extend validation beyond current data so newly added rows inherit the same constrained choices.
- Prefer Luban multi-row layout for a variable-length `list,Bean` whose elements contain several fields. Prefix the table field with `*`, such as `*bulletLaunchers`; expand the element Bean fields once on the next nested `##var` row; place each list element on its own data row; leave the owning record fields blank on continuation rows; and begin the next record when its key field becomes nonblank. Do not expand numbered list elements horizontally when the multi-row form is clearer and prevents table width from growing with list capacity.
- Merge Luban configuration cells to express ownership without changing the underlying schema: horizontally merge a parent Bean header across all of its child columns, and horizontally merge a `*listBean` header across the element-field columns. When one owning record spans multiple list-element rows, vertically merge the owning record's non-list cells across those rows while leaving the list-element cells unmerged. Store each merged region's value only in its top-left cell, and preserve blank continuation cells required by Luban's multi-row parser.
- Keep each custom Bean in `__beans__.xlsx` as one visually coherent block. Separate adjacent Bean blocks with one blank row; put Bean metadata and the first field on the first row, then continue additional fields on following rows with the Bean metadata cells left blank. Use an outside border only for the complete block, with no internal horizontal borders between its field rows.
- Name Bean types in PascalCase and fields in lowerCamelCase. Use concise Chinese `alias` values for configuration-facing type names; keep `comment` as optional explanatory text for constraints, purpose, or special meaning instead of overloading the alias. Preserve the workbook's established font, size, alignment, spacing, borders, and column widths when adding or changing Bean definitions.
- Format each enum definition as one visually coherent block using the workbook's established font and size and an outside border only. When adding the outside border, modify only that border property; do not copy an entire neighboring block or rebuild unrelated formatting.
- Treat an established workbook's font family, font size, and cell alignment as workbook-wide rules when it uses a consistent baseline. Before modifying or adding cells, read and reuse these properties from a representative cell with the same semantic role; never substitute a visually similar font, guess the size, or leave added rows at application defaults. Apply one consistent horizontal and vertical alignment to cells of the same kind. After export, compare computed styles from original and changed cells to confirm that font, size, and alignment match, unless the workbook or the user explicitly requires an exception.
- Give every populated Luban schema row and every effective data row the workbook's established border treatment. An effective data row includes continuation rows belonging to a multi-row list record; blank reserved rows outside the active table do not require borders. When adding rows, explicitly inherit the neighboring same-kind row's font, size, alignment, borders, number formats, validations, and comments instead of relying on application defaults.
- Autofit all populated columns in each affected Luban sheet after editing, using non-merged field headers and representative effective-row content. Keep widths compact and proportional, apply sensible minimums and maximums for unusually long text, do not let merged parent headers inflate child columns, and repair clipped schema markers or field names before delivery. Put detailed field guidance in a header-cell comment when it would otherwise force an excessively wide column. Preserve existing comments, validations, styles, and manually approved width adjustments unless the task explicitly changes them, then visually verify data, dropdowns, comments, fonts, alignment, borders, and widths.
- Keep resource-location fields concise when their conventions are stable. If every value shares a fixed directory prefix, store only the relative portion and document the code-owned prefix in the column comment. If the resource format is also fixed, such as every referenced image being a PNG, omit that fixed suffix as well and document the implied format in the same comment. Store a full path or suffix only when values genuinely vary or the project loader requires it.
- Add focused business query helpers instead of leaking generated table details throughout gameplay code.
- Create a helper under `com/game/config/mgr/` only when a table or related table family has recurring secondary-query needs, such as retrieving a configuration list by type; do not create one manager per table mechanically. Keep these helpers limited to querying, filtering, indexing, or combining generated Luban mapping objects and returning Luban mapping objects. If logic converts configuration into business VOs, combines it with runtime state, or implements gameplay rules, keep it in the owning feature Model instead.
- Treat generator, loader, registration, or framework defects as a handoff to `game-framework-toolchain`; do not silently redesign shared infrastructure.

### Optimize repeated configuration edits

Use a fast incremental path when the same workbook schema and formatting conventions have
already been verified and the task only adds or changes data rows:

1. Reconfirm file freshness, target ranges, identifiers, references, and the current data-row style; do not repeat broad repository discovery or full-workbook inspection without evidence that structure changed.
2. Reuse the verified schema and style baseline. On the first edit, explicitly apply the established data-row font, alignment, borders, number formats, validation, and comments to new rows; do not rely on an unverified copy operation and then repair formatting in a second pass.
3. Inspect the modified ranges, scan formula or reference errors, and render each affected sheet once after editing. Add another render only when the first verification exposes a concrete visual defect.
4. Combine deterministic checks for row counts, unique IDs, foreign keys, enum aliases, resource-name existence, dimensions, and generated-data values into one validation run where practical.
5. Invoke the project's approved generation script once after the workbooks pass validation. Do not run Luban repeatedly while still repairing spreadsheet content or formatting.
6. Update configuration tests in the same pass when their expected counts or representative records change.
7. Check Unity import or compilation once after files settle. If an open editor has not refreshed external changes, report the pending refresh immediately instead of waiting or polling repeatedly; never start a competing editor instance.

Do not use this fast path for schema changes, unfamiliar workbooks, manually modified files
whose style baseline is uncertain, or changes involving enums, comments, validations, merged
regions, or other structures that require renewed inspection.

## Respect the presentation boundary

- Provide stable read APIs, commands, results, and events to `aiui-to-ugui`.
- Do not own UI art, Figma structure, Prefab hierarchy, UIBinder members, or presentation-only interaction wiring.
- When a feature includes UI, finish and test the business layer independently where practical, then hand its interface to the presentation layer.

## Persistence and lifecycle

- Distinguish session state, run state, and permanent progression explicitly.
- Initialize in a deterministic order and make invalid early access visible.
- Save only after successful authoritative mutations, following the project's existing storage and migration patterns.
- Define reset, reload, teardown, and failure behavior for owned state.

## Validate

- Test configuration generation and representative reads when tables change.
- Test success, rejection, boundary, upgrade, reload, and missing-data paths as relevant.
- Verify compilation and runtime behavior in proportion to risk.
- Keep project-specific tables, values, assets, logs, and snapshots out of this Skill; standardize only reusable workflow rules after user approval.

## Finish

Report implemented rules, configuration changes, public business interfaces,
validation performed, presentation handoff needs, and remaining provisional assumptions.
