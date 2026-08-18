# Skill installation standard

Install skills from a Git checkout by reference. Do not copy skill folders into the Codex
skill directory. This keeps the checkout as the single source of truth and makes `git pull`
updates immediately available to Codex.

## Required layout

1. Keep one root folder, for example `E:\ChatGPTSkills`.
2. Put each skill in its own subfolder:
   - `aiui-to-ugui`
   - `game-art-asset-pipeline`
   - `game-feature-logic`
   - `game-framework-toolchain`
3. Each skill folder must contain:
   - `SKILL.md`
   - `agents/openai.yaml`
4. Keep the `name` in `SKILL.md` identical to the folder name.
5. Use only lowercase letters, digits, and hyphens in the skill name.

## Standard request to ChatGPT/Codex

After cloning, ask:

> Inspect this Skill repository and install its skills by reference. Do not copy files.

The agent must:

1. Inspect every listed skill for `SKILL.md` and `agents/openai.yaml`.
2. Resolve the scan directory as `$CODEX_HOME\skills` when `CODEX_HOME` is set, otherwise
   `%USERPROFILE%\.codex\skills` on Windows or `~/.codex/skills` on macOS/Linux.
3. Create one platform-native directory link per skill from the scan directory to this checkout.
4. Never delete or overwrite an existing real directory or a link pointing elsewhere. Report
   the conflict and request direction instead.
5. Verify each installed entry resolves to the checkout and exposes `SKILL.md`.
6. Tell the user to restart Codex to refresh `$` suggestions.

## Windows installation

Run from any PowerShell location:

```powershell
& "<checkout>\Tools\Install-Skills.ps1"
```

The script creates directory junctions and is safe to run again. It skips links that already
point to the correct source and stops on conflicts. It never copies or removes skill contents.

## macOS and Linux installation

Create symbolic links with `ln -s` from the resolved Codex skill directory to each skill
folder in the checkout. Apply the same conflict and verification rules above.

## Lifecycle

- Pulling or editing files in the checkout updates the installed skills in place.
- Moving, renaming, unmounting, or deleting the checkout breaks the links.
- To uninstall, remove only the link in the Codex skill directory, never its source folder.
- Restart Codex after installing, uninstalling, or changing skill metadata.

Notes:

- `agents/openai.yaml` helps the UI show the skill more clearly.
- If a skill does not appear in `$` suggestions, verify the link target, `SKILL.md`, the resolved
  scan directory, and that Codex was restarted.
