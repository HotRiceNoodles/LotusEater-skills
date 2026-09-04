# lotuseater-skills

[English](README.md) | 中文

Lotuseater 的 agent skills 合集。每个 skill 一个目录，位于 `skills/` 下，结构遵循 [docs/skill-spec.md](docs/skill-spec.md)。

## 安装（Claude Code 插件市场）

```
/plugin marketplace add HotRiceNoodles/lotuseater-skills
```

然后从 marketplace 按需安装单个 skill：

```
/plugin install traceable-meeting-minutes@lotuseater-skills
```

## 直接使用（Claude Code 手动安装）

也可以直接 clone 后把 skill 目录链接/复制到 `~/.claude/skills/`：

```bash
git clone https://github.com/HotRiceNoodles/lotuseater-skills.git
ln -s "$(pwd)/lotuseater-skills/skills/traceable-meeting-minutes" ~/.claude/skills/traceable-meeting-minutes
```

（Windows 下用 `mklink /D` 或复制目录。）

## 其他平台安装

本合集的 skill 遵循 [Agent Skills 开放规范](https://agentskills.io/specification)（SKILL.md + YAML frontmatter），可安装到任何兼容该规范的 agent 平台。通用做法：clone 本仓库，把 `skills/<skill-name>/` 整个目录复制或软链接到目标平台的 skills 目录。

| 平台 | skills 目录 / 安装方式 |
|------|------------------------|
| **Claude Code** | 插件市场（见上）或 `~/.claude/skills/`（用户级）/ `.claude/skills/`（项目级） |
| **Codex** | `~/.codex/skills/`（用户级）或 `.codex/skills/`（项目级）。注：Codex 对软链接支持不佳（[#9365](https://github.com/openai/codex/issues/9365)），建议直接复制目录 |
| **OpenClaw** | `openclaw skills install <path-or-url> [--global]`；全局目录 `~/.openclaw/skills/`，或手动放入工作区 `skills/` 目录 |
| **Hermes Agent** | `hermes skills install <url>` 或手动放入 `~/.hermes/skills/`。注：URL 安装多文件 skill 可能只下载 SKILL.md（[known issue](https://github.com/NousResearch/hermes-agent/issues/35125)），建议 git clone 后手动复制完整目录 |
| **千问办公 (QwenWork)** | `~/.qwenworkcn/skills/` |
| **豆包（办公任务模式）** | 豆包桌面端 → 办公任务模式 → 技能广场导入；或将 skill 目录放入本地技能目录（以客户端内指引为准） |
| **腾讯 WorkBuddy** | `~/.workbuddy/skills/<skill-name>/SKILL.md`（Windows 亦可放 `%APPDATA%\WorkBuddy\skills\`）；或在客户端「Skills 管理」中导入。依赖 Node.js / Git /（Windows）.NET Runtime |

示例（以 Codex 为例）：

```bash
git clone https://github.com/HotRiceNoodles/lotuseater-skills.git
cp -r lotuseater-skills/skills/traceable-meeting-minutes ~/.codex/skills/
```

> 本合集的 skill 均为平台无关设计：运行时自动探测所在平台，配置统一存放在 skill 自己的 `~/.<skill-name>/` 目录，不依赖任何平台专有路径。含 Python 脚本的 skill 首次使用时按提示安装 `scripts/requirements.txt`。

## Skills

| Skill | 用途 |
|-------|------|
| [traceable-meeting-minutes](skills/traceable-meeting-minutes/) | 会议录音/转写稿 → 可回溯纪要：语义账本 + 分级压缩 + 交互式 HTML（每句可跳回原话与录音时刻）+ "丢了什么"审计 |
| [cinematic-pptx-pipeline](skills/cinematic-pptx-pipeline/) | 多风格 PPT/课件全流水线（电影质感/手绘涂鸦/国潮/玻璃拟态）：AI 插图 → HTML 页面 → 截图 QA → 三级 PPTX 交付（位图/可编辑/动画）→ MP4 视频 |

## 收录规范

新 skill 必须遵守 [docs/skill-spec.md](docs/skill-spec.md)，要点：

- 每个 skill 一个目录（`skills/<name>/`），目录名 == frontmatter `name`（kebab-case）
- SKILL.md <200 行，只做路由 + 铁律；细节下沉到 `workflows/`、`references/`、`templates/`
- 平台无关：无硬编码密钥/个人路径/平台绑定，平台差异通过首次运行时自适应
- Python 脚本附 `scripts/requirements.txt`，import 失败提示友好
- 收录前过 spec §7 检查清单，`claude plugin validate .` 通过

## License

[MIT](LICENSE)
