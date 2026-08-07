# Skill share checklist

To make these skills easy to use on another device:

1. Keep one root folder, for example `E:\ChatGPTSkills`.
2. Put each skill in its own subfolder:
   - `aiui-to-ugui`
   - `ugui-feature-logic`
   - `game-framework-toolchain`
3. Each skill folder must contain:
   - `SKILL.md`
   - `agents/openai.yaml`
4. Keep the `name` in `SKILL.md` identical to the folder name.
5. Use only lowercase letters, digits, and hyphens in the skill name.
6. Place the root folder in the device's actual Codex skill scan path, or point `CODEX_HOME` there.
7. If sharing by git, clone the repo and then sync the skill folders into the local Codex skill root.

Notes:

- `agents/openai.yaml` helps the UI show the skill more clearly.
- If a skill does not appear in `$` suggestions, check that it is in the real scan directory, not just in an arbitrary drive path.
