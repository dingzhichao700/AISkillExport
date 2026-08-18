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

## Make business data configurable

- Identify repeated, balancing-sensitive, relational, or content-authored values that should not remain hardcoded.
- Design project-specific tables, beans, enums, keys, references, defaults, and validation constraints from approved feature requirements.
- Use the project's existing configuration toolchain, runtime manager, loading lifecycle, and Addressables conventions. When the project provides a Luban generation script such as `gen_json.bat`, invoke that script from its intended working directory; never bypass it by inventing or reconstructing Luban command-line parameters. For automation, satisfy a trailing interactive `pause` non-interactively without changing the script's generation semantics.
- Generate code and runtime data through the established tool; do not hand-edit generated files.
- Register finite categorical values as configuration enums instead of magic numbers. Store readable aliases in business tables, add alias-based data-validation dropdowns that cover future data rows, regenerate through the project script, replace duplicate handwritten runtime enums with generated types, and verify representative reads plus compilation.
- Format each enum definition as one visually coherent block using the workbook's established font and size and an outside border only. When adding the outside border, modify only that border property; do not copy an entire neighboring block or rebuild unrelated formatting.
- Keep spreadsheet columns compact and proportional to normal content, with a reasonable maximum for unusually long text. Put detailed field guidance in a header-cell comment when it would otherwise force an excessively wide column. Preserve existing comments, validations, styles, and manually approved adjustments unless the task explicitly changes them, then visually verify data, dropdowns, comments, borders, and widths.
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
