# lotuseater-skills

English | [中文](README.zh-CN.md)

Lotuseater's collection of agent skills. Each skill lives in its own directory under `skills/`, following the structure defined in [docs/skill-spec.md](docs/skill-spec.md) (in Chinese).

## Install (Claude Code plugin marketplace)

```
/plugin marketplace add HotRiceNoodles/lotuseater-skills
```

Then install individual skills on demand:

```
/plugin install traceable-meeting-minutes@lotuseater-skills
```

## Manual Install (Claude Code)

Alternatively, clone the repo and link/copy the skill directory into `~/.claude/skills/`:

```bash
git clone https://github.com/HotRiceNoodles/lotuseater-skills.git
ln -s "$(pwd)/lotuseater-skills/skills/traceable-meeting-minutes" ~/.claude/skills/traceable-meeting-minutes
```

(On Windows, use `mklink /D` or copy the directory.)

## Other Platforms

These skills follow the [Agent Skills open specification](https://agentskills.io/specification) (SKILL.md + YAML frontmatter) and work on any compatible agent platform. The general approach: clone this repo, then copy or symlink the whole `skills/<skill-name>/` directory into the target platform's skills directory.

| Platform | Skills directory / install method |
|----------|-----------------------------------|
| **Claude Code** | Marketplace (see above), or `~/.claude/skills/` (user-level) / `.claude/skills/` (project-level) |
| **Codex** | `~/.codex/skills/` (user-level) or `.codex/skills/` (project-level). Note: symlinked skills may not be picked up ([#9365](https://github.com/openai/codex/issues/9365)) — copying the directory is recommended |
| **OpenClaw** | `openclaw skills install <path-or-url> [--global]`; global directory `~/.openclaw/skills/`, or drop into the workspace `skills/` directory |
| **Hermes Agent** | `hermes skills install <url>` or manually into `~/.hermes/skills/`. Note: installing a multi-file skill by URL may fetch only the SKILL.md ([known issue](https://github.com/NousResearch/hermes-agent/issues/35125)) — clone the repo and copy the full directory instead |
| **QwenWork (千问办公)** | `~/.qwenworkcn/skills/` |
| **Doubao (office task mode)** | Doubao desktop → office task mode → import from the skill plaza, or place the skill directory in the local skills folder (follow the in-app guide) |
| **Tencent WorkBuddy** | `~/.workbuddy/skills/<skill-name>/SKILL.md` (on Windows, `%APPDATA%\WorkBuddy\skills\` also works), or import via "Skills 管理" in the client. Requires Node.js / Git / (Windows) .NET Runtime |

Example (Codex):

```bash
git clone https://github.com/HotRiceNoodles/lotuseater-skills.git
cp -r lotuseater-skills/skills/traceable-meeting-minutes ~/.codex/skills/
```

> All skills in this collection are platform-agnostic: they detect the host agent platform at runtime and keep their configuration in the skill's own `~/.<skill-name>/` directory, with no dependency on platform-specific paths. For skills with Python scripts, install `scripts/requirements.txt` when prompted on first use.

## Skills

| Skill | What it does |
|-------|--------------|
| [traceable-meeting-minutes](skills/traceable-meeting-minutes/) | Meeting recording/transcript → traceable minutes: semantic ledger + differential compression + interactive HTML (every claim jumps back to the original words and audio moment) + a "what was dropped" audit |
| [cinematic-pptx-pipeline](skills/cinematic-pptx-pipeline/) | Multi-style PPT/courseware pipeline (cinematic / hand-drawn / guochao / glassmorphism): AI illustrations → HTML pages → screenshot QA → PPTX in three tiers (bitmap / editable / animated) → MP4 video |

## Contribution Spec

New skills must follow [docs/skill-spec.md](docs/skill-spec.md) (in Chinese). Key points:

- One directory per skill (`skills/<name>/`); directory name == frontmatter `name` (kebab-case)
- SKILL.md under 200 lines, routing + iron rules only; details live in `workflows/`, `references/`, `templates/`
- Platform-agnostic: no hardcoded secrets/personal paths/platform bindings; platform differences adapt at first run
- Python scripts ship with `scripts/requirements.txt` and friendly import-failure messages
- Pass the spec §7 checklist and `claude plugin validate .` before merging

## License

[MIT](LICENSE)
