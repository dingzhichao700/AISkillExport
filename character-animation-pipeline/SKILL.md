---
name: character-animation-pipeline
description: Generate character animation assets from approved references via external image-to-video APIs or supplied videos, review motion and loops, then export aligned transparent PNG sequences. Use for character walk, idle, and other actions with configurable camera views and directions; includes resumable Bailian video generation and configurable background extraction.
---

# Character animation pipeline

Deliver coherent directional character animations, not independently imagined pose sheets.
Treat user choices and approvals already in the conversation as authoritative.

## Contract and defaults

Record character, action, camera view/projection, direction (screen-relative), loop/one-shot, reference approval,
provider/model/region, source video, chosen range, export count, and shared geometry.
Defaults when unspecified: 8 transparent PNGs, body about 100 px high, a short 3 s
720p silent video, in-place motion, fixed camera. These are configurable, not limits.
For this workflow, idle/walk/run normally loop; attacks/hits normally play once.
Clarify ambiguous actions, rather than forcing every animation into a loop.

Camera view is a generation parameter, not a restriction of this skill. Preserve the
approved reference's view unless the user requests a change. Isometric/oblique, front,
back, side, and other views may be requested; do not impose an isometric or diagonal
view by default. View-specific examples below are conditional, not universal prompts.

Process requested directions/actions in order. Existing approved references are reused.
Keep outputs in the user's deliverable location and intermediate frames/masks in work/.
No default GIF, archive, full native-rate PNG delivery, or engine integration.

## Review flow

1. **View/direction reference approval**, only if missing. Preserve character design
   across requested views. For example, a back-diagonal astronaut needs a consistent
   backpack, helmet back, leg angle, and accessories, not a mirrored front.
   Use an available reference-image provider (the sibling game-art-asset-pipeline
   skill supports Qwen), or accept a supplied image. This skill's scripts generate
   videos, not reference art. Never silently switch image provider.
2. **One motion-video approval.** Generate once or import an existing video. For a
   loop, inspect movement, select a complete semantic cycle, and present a repeated
   MP4 directly. Do not require a separate raw-video approval first. One-shot actions
   retain anticipation, action and recovery; present them without artificial looping.
3. **Deliver the complete transparent sequence after video approval** (for a directional
   set, after all requested directions pass; see below). Internally
   inspect every output's silhouette and transparency on checker/dark backgrounds,
   then deliver all requested frames with timing and a static overview. Do not add a
   three-sample approval gate. Failed extraction remains unfinished, not an opaque
   substitute labeled final. No downstream Unity placement without a request.

Split review only when no useful cycle exists, trimming would discard meaningful
action, or a proposed repair changes motion. Explain the concrete issue. Default:
no RIFE, interpolation, reverse playback, crossfade, retiming, or synthetic frame repair.
Approval of a source video is not permission to hide an altered motion sequence.

## Directional sets

For a multi-direction action, review static direction references together before video
production: identity, proportions, camera elevation and relative scale. Use the project's
native-size scene standard when supplied; a magnified sheet alone does not prove scale.
Direction count and mirror mapping come from the project, not this skill's examples.
Generate and review one direction's video at a time, then export the set after all
requested directions pass, unless the user explicitly requests a partial export.
Repair only affected directions; retain other approved versions. Read
[processing.md](references/processing.md) for cross-direction scale and pivot review.

## Video generation and recovery

For Bailian read [provider-bailian.md](references/provider-bailian.md).
`scripts/video_api.py` exposes validate, submit and poll; submit never retries POST.
Use the user's environment-variable name (default QWEN_ANI), never a key literal.
Announce each paid submission, reuse existing authorization, and save returned task IDs.
Poll timeouts/network errors resume the SAME task. A submit without an ID is unknown:
stop and report, do not automatically buy another attempt or switch provider.
Other providers may supply an MP4 plus provenance; they must implement equivalent
submit/resume semantics before adding an adapter. No arbitrary endpoint fallback.

## Motion and extraction

Read [processing.md](references/processing.md) for commands, geometry, and alpha modes.
Use `scripts/animation.py analyze` to rank possible ranges, inspect source frames in
work/, and choose a range by anatomy and motion, not image similarity alone. A full
walk includes both legs' phases; similar poses can be a half-cycle. The displayed last
frame should advance naturally to the first; don't retain a duplicate boundary pose.
Idle should keep its feet planted, with restrained breathing, not stepping or drifting.
Keep camera, head, torso and limb identity consistent in the requested view.

Use a **character geometry profile** shared across actions. Specify reference body
height and ground anchor per direction (normalized in its camera frame), common output
canvas, target body height and pivot. Do not refit or recenter each frame. New videos
must keep their reference framing; inspect camera drift rather than correcting it
silently. Review cross-action switching at native size. Profiles are versioned files;
changing a profile requires re-exporting affected sets consistently.

Choose background/extraction based on the character palette: contrasting uniform pink
or green with no shadows/gradients is preferable for new assets when compatible with
the reference. Preserve the subject when preparing this input. Gray footage may use
foreground segmentation. `warm-gray` is a measured astronaut-specific option, NOT a
universal matting solution. Other subjects can use chroma or supplied alpha masks.
Never delete every similarly colored pixel globally or punch holes in costume details.

Validate alpha, complete silhouette, shadow removal, no edge clipping or stray islands,
stable scale/pivot and native-size leg readability. Technical checks don't prove motion
quality. For eight sampled frames preserve cycle duration in metadata; fewer drawings
can look less smooth than the approved video, and dense rendering isn't reconstructed.

## Delivery and evidence

Read [delivery.md](references/delivery.md) before export. Deliver each action + direction
as an independent directory such as `Fighter/Fly_Down/`, containing only `animation.json`
and `001.png...NNN.png` at the same level (no `frames/` subdirectory).
For an explicitly requested PNG-only stage, keep the same directories and defer JSON;
see the staged-delivery rules in delivery.md. This is not yet a packer-ready package.
The delivery JSON contains only duration (integer milliseconds), scale (downstream
percentage, default 100), and pivot (normalized on the untrimmed canvas, bottom-left
origin, X right, Y up). Never reuse the extraction resize factor as delivery scale.
Provide an absolute directory path AND clickable link to each animation directory,
plus inline overview. State frame count, canvas, order and frame/cycle duration.
Pass a separate `--evidence-out` outside the whole delivery root for overview and
provenance (source mapping/hash, geometry, extraction settings and loop intent).
Use only approved content, no placeholder frames. Save failures and trials in work/.
The validated history and its limitations are in [evidence.md](references/evidence.md).

Dependencies: Python 3.10+, Pillow, NumPy, OpenCV, ffmpeg and ffprobe on PATH.
Install Python packages from scripts/requirements.txt into a tool venv if missing;
don't depend on an unrelated RIFE environment. No RIFE executable is required.
Creation/maintenance checks: `python scripts/test_offline.py` (no API requests).
