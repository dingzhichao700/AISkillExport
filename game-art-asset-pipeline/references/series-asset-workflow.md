# Series and Progression Asset Workflow

Use this workflow when multiple assets must share a visual language or communicate
ordered evolution. Examples include level upgrades, age or damage states, equipment
tiers, building stages, character classes, item families, and themed icon sets.

## 1. Define the progression

State which properties remain fixed and which properties change. Common progression
dimensions include silhouette, size, complexity, material, color, equipment density,
damage, animation energy, rarity, and ornamentation.

For ordered levels, define an intentional relative-size progression when size matters.
Do not rely on the model to infer monotonic growth. Keep viewpoint, orientation,
lighting, center axis, and anchor fixed unless change is part of the requirement.

## 2. Generate a concept sheet

Generate one sheet showing the complete series. Prefer grayscale silhouettes or reduced
detail when the primary approval question is shape progression. Color is allowed when
color relationships are the main design question.

When an approved series sheet already establishes the desired viewpoint, line quality,
spacing, or progression language, prefer it as a style and composition reference while
explicitly redesigning the new subject. If text-only generation repeatedly introduces
forbidden infographic elements or an unsuitable style, stop blind retries and switch to
that approved reference. Never use a rejected draft as the authoritative style reference.

Prompt requirements:

- show exactly the requested number of members;
- use a simple, uniform background selected to contrast with the subject palette;
- reserve generous safe spacing between members;
- keep every silhouette entirely inside its own visual region;
- omit text, level labels, borders, frames, diagrams, and decorative UI;
- keep the declared viewpoint, orientation, lighting, and anchor consistent.

Stop for approval.

## 3. Generate the formal sheet

Use the approved concept sheet as the structural reference. Generate one formal sheet
containing the complete series, preserving silhouettes, order, relative size, viewpoint,
orientation, spacing, and style. Add final materials, colors, lighting, and details without
redesigning the approved progression.

Stop for approval before splitting.

## 4. Convert to production assets

1. Detect the actual temporary background from canvas edges.
2. Remove only edge-connected background regions.
3. Detect each subject's real bounds rather than dividing the sheet equally.
4. Reject ambiguous overlap or an unexpected subject count instead of guessing.
5. Apply one shared scale when relative size matters.
6. Align all members to the declared center axis and anchor.
7. Export individual transparent PNGs at the production canvas size.
8. Produce a checkerboard review composite without altering the individual files.

## 5. Validate

Check that:

- subject count and order match the contract;
- no subject is clipped or contains fragments from a neighbor;
- internal colors and same-color details were not made transparent;
- transparent corners and padding are valid;
- dimensions, naming, anchor, and shared scale match the contract;
- progression remains visually legible at production resolution.

If production resolution hides important structure, revise the formal design or simplify
details. Do not compensate with arbitrary sharpening or per-member scaling that breaks the
approved relationship.
