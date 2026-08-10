---
name: aiui-to-ugui
description: Convert a game UI request into a reviewed Blueprint, visual mockup, isolated art assets, structured Figma design, Unity uGUI Prefab, project-conforming UIBinder initialization, and user-approved runtime member export. Use only when explicitly invoked for the staged AIUI-to-Unity workflow, including continuing or revising one of its stages.
---

# AIUI to Unity uGUI

Run the workflow as a sequence of explicit artifacts and approval gates. Keep the
process reversible and do not invent project-specific rules.

## Start a run

### First-use external image-provider enrollment (mandatory)

On the first use of this Skill in a workspace or conversation, stop before
any image generation and ask the user whether an external image-model API can
be provided. If the user agrees, request the provider name, endpoint/model
information, and the required environment-variable name and value through the
available secure environment configuration. Do not echo, persist, or place
secret values in chat, manifests, source files, prompts, or generated assets.

Run a minimal connectivity and generation smoke test using that provider. The
smoke test must report success or the concrete failure before the requested
visual generation begins. If configuration or debugging fails, stop and notify
the user; do not fall back to ChatGPT's built-in image generation.

After the external provider has passed its first-use smoke test, record its
provider identity (never its secret) as the workspace's selected image
provider. All later image generation for this Skill must use that provider by
default. Do not switch to ChatGPT's built-in image generation or another
provider unless the user explicitly authorizes a new provider enrollment and
the new provider passes the same smoke test.

1. Read `references/pipeline.md`.
2. Collect only the inputs required for the next requested stage.
3. Read `references/blueprint-contract.md` before creating or changing a
   Blueprint.
4. Read `references/artifact-contract.md` before generating files, editing
   Figma, or writing into a Unity project.
5. Read `references/figma-import.md` before creating or updating a structured
   Figma deliverable, including when generating a local import plugin.
6. Read `references/unity-code-binding.md` before generating binding code,
   exporting members, or attaching a generated view component to a Prefab.
7. State the current stage, the inputs being used, and the next approval gate
   or verification checkpoint.

### Image-provider preflight (mandatory)

Before any visual mockup or raster asset generation:

1. Check whether the `QWEN_ANI` environment variable is configured without
   printing, copying, persisting, or exposing its value.
2. If configured, select QWEN and record `imageProvider: QWEN` in the run
   manifest before generating.
3. If QWEN is configured but unavailable, fails, or cannot be invoked, stop the
   stage and notify the user with the concrete failure. Do not silently switch
   to another provider.
4. If no enrolled external provider is configured, report that fact and stop
   before generation. Ask the user to enroll an external provider; do not use
   ChatGPT's built-in image generation by assumption.
5. If the selected provider differs from the requested or configured provider,
   invalidate the draft output, mark the run as blocked at the provider
   checkpoint, and notify the user before continuing.

Accept partial runs. Resume from an existing artifact instead of recreating
approved upstream work.

### Figma transport preflight (mandatory)

Before any Figma read or write, determine and record the selected transport.
A Figma URL identifies a file or reference; it does not authorize Figma MCP.
Call Figma MCP only when the user explicitly requests an online Figma read,
write, synchronization, or MCP operation.

When a project has an established local importer or verified local handoff,
lock that as the default transport for the run. Do not probe MCP availability,
inspect an online file, or consume MCP quota merely because a URL is present.
Changing transports requires explicit user approval. If the selected transport
fails, stop and report the failure; do not silently switch transports.

## Preserve authority boundaries

- Treat the Blueprint as authoritative for intent, content, component roles,
  states, and initial layout constraints through visual generation.
- Treat the approved visual mockup as a visual target, not as the sole source
  of structure or coordinates.
- After Figma review, treat the approved Figma structure as authoritative for
  final hierarchy, geometry, text placement, and asset placement in Unity.
- The approved structure may be handed off through a verified local importer or
  structural snapshot. Figma MCP is an optional synchronization transport, not
  a hard dependency of Unity export or later stages.
- Do not silently write Figma edits back into the Blueprint. Record material
  differences in the handoff manifest.
- Treat project rules supplied by the user or found in the target repository as
  authoritative for paths, packages, naming, and code placement.

## Enforce approval gates

Do not proceed past either gate without explicit user approval:

1. Approve the visual mockup and isolated art assets before Figma
   reconstruction.
2. Approve the structured Figma result before Unity export.

Binding is one combined delivery stage when an explicit member-selection policy
is available. Configure `uiList`, invoke the existing member generator, and
record the exact exported set. If no policy is supplied, propose the set and
wait instead of exporting every visual node.

If the user requests only one stage, stop after reporting its artifacts and
validation result.

## Use tools conservatively

- Use QWEN as the mandatory default image provider when `QWEN_ANI` is
  configured. Complete the image-provider preflight before every generation
  stage, and record the selected provider in the run manifest.
- Do not silently switch image providers. Any unavailable provider, fallback,
  or provider mismatch is a user-visible stop condition; report it before
  generating or accepting artifacts.
- Use an existing Figma file, plugin, converter, or authenticated connection
  when the user supplies one. Do not install software or create unrelated Figma
  files without an explicit request.
- Treat local Figma Importer as the default when that workflow is already
  established for the project. Treat Figma MCP as a separately authorized
  transport, not as the default or an availability probe.
- After an approved Figma revision has been captured locally with traceable
  structure, assets, revision identity, and validation, prefer that local
  handoff for deterministic Unity work. Do not consume Figma MCP quota merely
  to repeat information already present in the current handoff.
- If Unity shows an editor/runtime load failure but the built player or
  Addressables build works, prioritize checking registration state first:
  duplicate Addressables entries, stale paths, GUID mismatch, or leftover
  imported copies. Only then suspect prefab structure or view code.
- For `BasePanel`-style window prefabs, keep the root RectTransform pivot at
  the center by default. Only deviate when the design explicitly requires a
  different window anchor/pivot.
- Target Unity uGUI. Map images to `UnityEngine.UI.Image` and text to
  TextMeshPro by default.
- Defer custom Unity component mappings until the Unity export stage. Never
  guess their types or serialized fields.
- Inspect the target Unity project's governing instructions before writing.
- For iterative Unity review, use the Stage 6 preview mode and the project's
  persistent `Library/AIUI` request queue when available. Do not use a temporary
  Editor C# generator, pack atlases, register Addressables, or build Player
  Content until the corresponding finalize or release checkpoint.
- Reuse the target project's existing code-binding and member-export mechanism.
  Do not introduce a new binding framework implicitly.
- In the combined binding stage, create the same-named class, attach `UIBinder`,
  assign its bound C# asset, configure the policy-approved `uiList`, and invoke
  the target project's existing UIBinder editor generation path. Do not
  synthesize an independent field writer.
- Match the accepted reference panel's local C# formatting, including blank
  lines, newline/brace style, and concise XML class comments. Add focused
  comments to key lifecycle, binding, state-transition, and interaction
  functions when their intent is not self-evident.
- Limit writes to paths the user placed in scope.

## Keep the skill clean

Do not package run-specific Blueprints, generated images, cutouts, Figma file
IDs, Unity project paths, Prefabs, logs, credentials, or examples as skill
resources. Add scripts or assets only after repeated use proves that a
deterministic implementation or reusable template is required.

## Finish each stage

Before handing work to another stage, apply the authority and freshness rules
in `references/artifact-contract.md`: synchronize the formal manifests with the
actual artifacts and do not present diagnostic reports or backups as current
delivery state.

Report:

- stage completed;
- artifacts created or changed;
- validation performed and unresolved deviations;
- approval or input required for the next stage.

Do not describe a stage as complete when its required artifact or validation is
missing.
