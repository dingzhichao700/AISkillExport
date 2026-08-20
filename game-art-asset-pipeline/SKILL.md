---
name: game-art-asset-pipeline
description: Generate, review, process, and deliver game-ready raster art assets, including individual assets, coherent series, level progressions, form evolutions, variants, icons, characters, equipment, buildings, projectiles, effects, and textures. Use when game art needs external-model generation, concept approval, reference-guided rendering, transparent-background extraction, sheet segmentation, naming, sizing, anchoring, quality validation, or placement into a game project. Do not use for UI layout/uGUI integration or gameplay rules and configuration.
---

# Game Art Asset Pipeline

Produce reviewable game art through explicit stages. Preserve approved upstream
artifacts and stop at every required approval gate.

## Establish the asset contract

1. Read the target project's governing instructions.
2. Record the asset family, semantic role, visual style, viewpoint, orientation,
   progression dimensions, count, naming pattern, production size, display size,
   transparent-background requirement, alignment mode, semantic anchor, destination,
   and current stage.
3. Separate model-generated artifacts from deterministic post-processing.
4. Create or update a run manifest without recording credentials.

## Select the workflow

- For a single independent asset, generate one review candidate at a time.
- For a coherent series or visible progression, read
  `references/series-asset-workflow.md` and use the concept-sheet workflow.
- Resume from an existing approved concept or formal sheet instead of regenerating it.

## Use external image providers

- Use the registered external image provider. Do not use Codex/ChatGPT built-in
  image generation unless the user explicitly changes this rule.
- Keep API keys only in their registered environment variables. Check only whether
  the variable exists; never print, log, persist, or expose its value.
- For QWEN, read the matching provider reference and invoke only the bundled script:
  - text-to-image: `references/qwen-image-provider.md` and
    `scripts/invoke-qwen-image.ps1`;
  - reference-guided image generation: `references/qwen-reference-image-provider.md`
    and `scripts/invoke-qwen-reference-image.ps1`.
- Tell the user immediately before every external model request.
- Request one review artifact per approval stage. A single sheet may contain a
  deliberately requested series; do not confuse that with multiple alternatives.
- Stop and report the concrete failure if credentials, public connection settings,
  network access, authentication, or the selected model fails. Do not silently switch
  provider or model.

## Enforce approval gates

For a series or progression, use these gates:

1. Approve the concept or silhouette sheet.
2. Generate one formal series sheet from the approved concept and approve it.
3. Extract transparency, segment, normalize, and produce a review sheet.
4. Approve the final individual assets before placing them in the game project.

Do not generate later stages before the current gate is explicitly approved.

## Process assets safely

- Choose a flat temporary background that contrasts with the actual subject palette;
  do not prescribe green, magenta, or any other fixed color.
- Remove only background connected to the canvas boundary. Never globally delete all
  pixels similar to the background color, because legitimate subject details may match.
- Detect real subject bounds. Never assume equal-width sheet cells when subjects can
  cross nominal partitions.
- Require safe spacing between series members and forbid unwanted text, labels, borders,
  mockup frames, or decorations in generation prompts.
- Preserve shared scale when relative size communicates progression. Use a common center
  axis and a declared anchor; do not independently fit every member to the canvas.
- Treat alignment as an explicit asset contract. Default ordinary presentation assets
  to rectangle alignment. Declare a replaceable series as pivot-aligned when its forms,
  levels, skins, equipment states, or other variants must share a semantic attachment
  point. Apply one alignment mode and one anchor meaning to the whole series.
- When a series may benefit from pivot alignment but the requirement has not declared
  it, prompt the user to confirm the asset identity as needed; do not infer a semantic
  anchor independently for every image. Examples of anchor meaning may include a support
  point, foot position, attachment point, or visual center, but the concrete meaning
  belongs to the current product rather than this Skill.
- Keep source sheets, transparent sheets, final assets, and review composites separate.
- Use deterministic scripts for extraction, segmentation, resizing, naming, and checks.

## Validate delivery

Verify the requested count, naming, format, dimensions, alpha channel, transparent
corners, complete silhouettes, absence of cross-member fragments, safe padding,
consistent viewpoint and anchor, and the intended progression. Visually inspect a
review composite before delivery.

For pivot-aligned series, also verify that every delivered asset records the same
alignment mode and semantic anchor meaning, while allowing the numeric pivot to differ
as required by each silhouette.

Do not place assets into Unity, register Addressables, create configuration, or run
content builds unless the user requests that stage. Hand game-domain configuration and
behavior to `game-feature-logic`; hand UI composition and uGUI wiring to
`aiui-to-ugui`.

## Finish a stage

Report the completed stage, artifacts, deterministic processing, validation results,
known deviations, and the exact approval required next.
