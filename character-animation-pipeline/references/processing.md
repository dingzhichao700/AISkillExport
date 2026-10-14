# Motion processing and shared geometry

The CLI keeps full frames in memory/work only. It never creates GIF or calls RIFE.
```
python scripts/animation.py analyze --video work/take/source.mp4 --out work/analysis.json --min-seconds 1.2 --max-seconds 3
python scripts/animation.py cut --video work/take/source.mp4 --start 28 --length 46 --out work/cycle.mp4 --preview outputs/cycle-review.mp4 --repeats 4
```
`start` is ONE-based, length is frame count. The range is [start, start+length-1].
Read analysis candidates as suggestions, not approval. Inspect contact identity, both
leg phases and direction; a low pixel difference can be a still or half-cycle. Choose
action-specific min/max duration (walk ≠ idle). Frame counts use the video's measured
rate. Variable-frame-rate footage is rejected rather than silently retimed.
For one-shot use the full meaningful range and repeats=1; do not apply loop gates.

## Profile

Create one geometry.json per character before exporting the set. Example structure,
NOT universal coordinates; measure the approved reference and inspect an overlay:
```json
{
  "character": "example",
  "version": 1,
  "target_body_height": 100,
  "canvas": [80,120],
  "pivot": [40,112],
  "directions": {
    "down-right": {"body_height_fraction":0.84,"ground_anchor":[0.5,0.91]},
    "up-right": {"body_height_fraction":0.84,"ground_anchor":[0.5,0.91]}
  }
}
```
The fractions are relative to each direction's reference canvas; ground_anchor is a
fixed ground contact point, not each frame's lowest pixel. Target pivot is a pixel
coordinate shared by all directions/actions. Body height excludes shadow/empty margins.
Keep the same framing between reference and video. If framing differs, diagnose it and
record a validated direction/profile revision; never independently normalize every pose.
If art doesn't fit the canvas the exporter fails. Enlarge the common canvas/pivot and
re-export the set, do not shrink just the offending action. At native size compare idle
and walk transitions and both directions for scale/foot-position jumps.

## Export

After the motion video has passed, export all requested frames at once:
```
python scripts/animation.py export --video work/take/source.mp4 --start 28 --length 46 --count 8 --direction up-right --profile geometry.json --matte warm-gray --out outputs/walk-up
```
Modes:
- `warm-gray`: GrabCut initialized from warm character colors vs cool gray backdrop.
  Preserves enclosed interior detail; keeps largest foreground component. Inspect every
  frame for lost accessories, spaces between limbs, and retained shadow. Not suitable
  for detached effects, multiple subjects or cool/gray subjects with indistinct outlines.
- `chroma --key FF00FF --tolerance 65`: remove ONLY matching background connected to
  canvas edges. The tolerance is RGB Euclidean distance; choose it by inspecting a
  checker/dark composite. Truly enclosed background gaps may remain: use reviewed masks
  for those instead of deleting costume pixels globally. Avoid choosing a costume color.
- `masks --masks-dir work/masks`: external foreground segmentation, 01.png...08.png
  grayscale alpha masks at video resolution. Masks must match the selected frame mapping;
  preserve provenance and inspect subject edges. This is the escape hatch for other
  backgrounds, NOT an automatic fallback. Refuse opaque delivery if extraction fails.

All modes retain one source-coordinate transform, with soft alpha edges and zero RGB
under fully transparent pixels. No pose edits, frame interpolation or per-frame recenter.
The source videos may differ in duration. Export count does not imply FPS; each frame
holds for cycle_duration/count (or action_duration/count for one-shot with --one-shot).
Integer source sampling approximates equal time slots; source_frame is recorded.
For one-shot the first AND last source pose are retained. For loops an end-boundary
duplicate should be excluded at cut selection, not duplicated as an extra drawing.

Output: frames/01.png...08.png, overview.png, animation.json. The metadata includes
source hash, indices, common geometry, durations and matte settings. The output folder
must be new; existing final assets are not overwritten. Internal QA includes RGBA,
transparent border, one foreground component and safe canvas fit. Visually inspect
overview before delivering; checks alone do not certify anatomy or temporal consistency.
