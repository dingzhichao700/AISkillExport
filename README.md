# ChatGPT Skills repository

This repository stores reusable Codex skills for Unity uGUI and the Game Framework toolchain.

Current skills:

- `game-project-coordination`
- `aiui-to-ugui`
- `game-ui-reference-extraction`
- `game-art-asset-pipeline`
- `game-feature-logic`
- `game-framework-toolchain`
- `game-build-release`
- `character-animation-pipeline`
- `frame-animation-packer`

Each skill folder contains:

- `SKILL.md`
- `agents/openai.yaml`

Recommended usage:

1. Clone this repo on the target device.
2. Ask ChatGPT/Codex to inspect this repository and install its skills by reference.
3. On Windows, run `Tools\Install-Skills.ps1`. It creates directory junctions in the
   active Codex skill scan directory; it does not copy the skill contents.
4. Restart Codex so `$` suggestions are refreshed.

The repository must remain at the same path after installation. Editing a skill in this
checkout updates the installed skill immediately because the scan-directory entry is only
a link to the checkout.

See `SKILL_SHARE_GUIDE.md` for installation, verification, conflicts, and other platforms.

Commit and push messages follow [AGENTS.md](AGENTS.md): list each changed skill by its exact name and purpose, followed by its concrete changes.
