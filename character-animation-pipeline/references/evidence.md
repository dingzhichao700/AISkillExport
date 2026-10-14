# Recorded evidence and limitations

2026-10-14: one stocky astronaut, two diagonal views, walk and idle.
All four final sets were approved by the user, each 8 transparent PNGs.

| Action/view | Accepted source frames (one-based) | Native rate | Cycle |
|---|---|---|---|
| walk down-right | 38–82 | 30 fps | 1.5 s |
| walk up-right | 28–73 | 30 fps | 1.5333 s |
| idle down-right | 1–74 | 30 fps | 2.4667 s |
| idle up-right | 1–90 | 30 fps | 3 s |

Model: wan2.6-i2v-flash, Beijing, 720P/3 s/silent; no interpolation or motion repair.
The initial gray backgrounds needed foreground segmentation because simple matting left
ground-shadow patches. Warm-gray GrabCut worked for this character after visual review.
Back-reference image: wan2.6-image. PNG upload once timed out without task ID; a
user-authorized retry using quality-95 JPEG at unchanged dimensions succeeded.
No raw key, task IDs or machine-specific asset paths are distributed in this skill.

Previously attempted image-sheet walk generation repeated the same leading leg; merely
numbering frames or tightening per-frame prompts did not fix temporal ordering. RIFE
interpolation of bad/incomplete key poses did not rescue them. Hence video generation
and explicit cycle review became the preferred route for this task, not a universal
claim that video always works.

The four historical exports used per-set geometry and different canvas widths. They
validate motion/matting, NOT cross-action pivot consistency. The new shared profile
contract must be separately checked on each new character. New generic CLI validation
uses offline fixtures and existing clips, not new paid generations. Do not claim a
success rate across characters, providers or body plans based on these four sets.

## Skill implementation validation

Offline checks performed at creation:
- Five unittest cases: temporal sampling/bounds, chroma preserving an enclosed same-color
  costume patch, rejected duplicate POST after unknown submission, GET-only task recovery,
  and synthetic video -> eight RGBA frames with duration, overwrite and preview checks.
- `quick_validate.py`, relative documentation links, UI metadata and Python syntax pass.
- All four historical source clips re-exported through the generic warm-gray path, with
  eight frames each, a shared experimental 80x120 canvas/pivot (40,112) and body-height
  fraction .84. An earlier 80x116 canvas failed the head-margin check on idle-up; no
  per-action shrink was applied. This demonstrated the clipping guard and uniform
  profile revision. Result boards were visually inspected; this experimental profile
  is not a replacement for the user's previously approved delivered assets or a claim
  that cross-action transitions have been human-approved.
- Analysis and provider `validate` ran locally. No real API submit was made while
  creating the skill; network recovery is tested with mocks, not simulated as a live success.
