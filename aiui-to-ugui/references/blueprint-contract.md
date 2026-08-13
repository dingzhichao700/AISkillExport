# Blueprint contract

The Blueprint is structured design intent. Prefer JSON so later stages can
consume it deterministically.

## Required top-level information

```json
{
  "protocol": "aiui-blueprint",
  "version": "0.1",
  "screen": {},
  "visualDirection": {},
  "hierarchy": [],
  "assets": [],
  "interactions": [],
  "unity": {}
}
```

## `screen`

Include:

- stable screen ID and display name;
- reference width and height;
- safe-area or scaling assumptions when known;
- purpose and important user tasks.

## `visualDirection`

Describe style, palette roles, materials, lighting, typography intent, density,
and prohibited visual treatments. Do not embed credentials or model-specific
request IDs.

## `hierarchy`

Represent every meaningful UI element with:

- stable semantic ID;
- role such as frame, image, text, button, tab, grid, slot, or overlay;
- parent ID;
- content or label where relevant;
- layout constraints or reference bounds;
- visual state requirements;
- asset reference where relevant;
- intended Unity role where known.

Represent a button or other text-bearing control's label as an independent text
child with its own reference bounds. Do not assume the label fills its parent.

Use stable semantic IDs rather than Figma node IDs.

For progress-like controls, keep structural and visual responsibilities distinct: name the whole control `bar{Semantic}`, its fixed background image `img{Semantic}Bg`, its changing fill `img{Semantic}Fill`, and its numeric label `txt{Semantic}`. Do not name the whole control after the background image.

## `assets`

For each required art asset, include:

- stable asset ID;
- purpose and visual prompt;
- transparency requirement;
- expected proportions or reference display size;
- slicing or nine-slice intent when known;
- usage nodes;
- generation status and output path only in the run instance.

Do not force unrelated assets to a uniform pixel size.

## `interactions`

Describe states and transitions needed to understand the UI, such as selected
tabs, hover/pressed/disabled states, scroll regions, item selection, and
tooltips. Do not invent runtime game logic.

## `unity`

Record only known mapping intent:

- uGUI as the target UI system;
- `Image` for images;
- TextMeshPro for text;
- reference pixels per unit or canvas scaling only when supplied;
- custom component requirements only when supplied.

Do not include a machine-specific Unity project path in a reusable Blueprint.

## Revision rules

- Assign a revision identifier or content hash before generating visuals.
- Record which revision produced each downstream artifact.
- Do not silently mutate an approved revision.
- When Figma edits differ from the Blueprint, keep the Figma result and record
  the difference in the handoff manifest unless the user asks to reconcile the
  Blueprint.
