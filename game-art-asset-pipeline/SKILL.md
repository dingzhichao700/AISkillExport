---
name: game-art-asset-pipeline
description: Generate, review, process, and deliver game-ready raster art assets, including individual assets, coherent series, level progressions, form evolutions, variants, icons, characters, equipment, buildings, projectiles, effects, and textures. Use when game art needs Image-model generation, concept approval, reference-guided rendering, transparent-background extraction, sheet segmentation, naming, sizing, anchoring, quality validation, or placement into a game project. Do not use for UI layout/uGUI integration or gameplay rules and configuration.
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
5. Place generated and intermediate artifacts under the target project's declared
   work/artifact directory when one exists. Do not default large outputs to the system
   drive when the project is on another writable drive.

## Select the workflow

- For a single independent asset, generate one review candidate at a time.
- For a coherent series or visible progression, read
  `references/series-asset-workflow.md` and use the concept-sheet workflow.
- Resume from an existing approved concept or formal sheet instead of regenerating it.
- Translate product semantics into visual language before prompting. Omit domain terms
  that predictably imply the wrong physical object when the desired result is defined by
  appearance alone; keep those terms in the asset contract and validation criteria.

## Image generation and provider routing

- Default all static image generation and editing to the built-in Image model via
  `image_gen`; read the available `imagegen` Skill for tool use and saving outputs.
  This includes concepts, references, directional stills, cards, UI bitmap assets,
  backgrounds, effects stills, variants, and transparency requests.
- Only `character-animation-pipeline` defaults to the QWEN/DashScope API for motion
  video generation. Static references used by that pipeline still default to Image.
- The built-in Image path does not require the local QWEN credential CSV, external
  provider registration, an API connectivity test, or the QWEN shared queue.
  Do not block it on a paused QWEN queue or an unavailable QWEN credential.
- Inspect local references before using them. Preserve approved identity, camera,
  palette, proportions, and declared invariants; keep reference roles explicit.
- For transparent images, request real transparency and preserve the generated alpha.
  Save project-bound results into the declared workspace output directory, keeping
  original sources and review artifacts distinct.
- Use an external image API only when the user explicitly chooses that provider
  for the current task; past provider use or the mere presence of a key is not a
  standing default. If Image is unavailable, report it without silently falling
  back to QWEN, another API, or a credential-based CLI.
- Legacy QWEN image references/scripts are retained solely for explicitly chosen
  external workflows: `references/qwen-image-provider.md` and
  `references/qwen-reference-image-provider.md`. Read only the matching reference
  in that case; use the registered credential reader and any applicable project
  queue, never print/copy/upload credentials. Announce external requests, preserve
  approval boundaries, and never automatically resubmit an unknown result.
- Request one review artifact per approval stage; a deliberately requested sheet
  can contain its declared views/series. Preserve all existing approval gates.

## Enforce approval gates

For a series or progression, use these gates:

1. Approve the concept or silhouette sheet.
2. Generate one formal series sheet from the approved concept and approve it.
3. Extract transparency, segment, normalize, and produce a review sheet.
4. Approve the final individual assets before placing them in the game project.

Do not generate later stages before the current gate is explicitly approved.
If an approved concept already has formal-source quality, report that assessment and let
the user explicitly promote it to the formal source instead of generating a redundant
near-duplicate.

## Process assets safely

- Prefer native transparent Image output when transparency is required; preserve its alpha.
  For an existing opaque source or an explicitly required temporary background, choose a
  flat color contrasting with the subject palette, not a universal fixed key color.
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
- Before choosing production dimensions, inspect the target resolution and existing
  comparable in-game assets. Record visible dimensions separately from transparent
  canvas dimensions.
- After extraction and resizing, remove isolated fragments that are not connected to the
  intended subject, then inspect a checkerboard review composite for residual pixels and
  cross-member contamination.

## Validate delivery

Verify the requested count, naming, format, dimensions, alpha channel, transparent
corners, complete silhouettes, absence of cross-member fragments, safe padding,
consistent viewpoint and anchor, and the intended progression. Visually inspect a
review composite before delivery.

When placing approved assets into Unity, also verify the destination taxonomy, unique
`.meta` GUIDs, Sprite importer settings, transparent corners, and Addressables entries
when the project loads those assets through Addressables. Do not build player content
unless that stage is requested.

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
