# lotuseater-skills

Lotuseater 的 agent skills 合集。每个 skill 一个目录，位于 `skills/` 下，结构遵循 [docs/skill-spec.md](docs/skill-spec.md)。

## 安装（Claude Code 插件市场）

```
/plugin marketplace add HotRiceNoodles/lotuseater-skills
```

然后从 marketplace 按需安装单个 skill：

```
/plugin install traceable-meeting-minutes@lotuseater-skills
```

## 直接使用

也可以直接 clone 后把 skill 目录链接/复制到 `~/.claude/skills/`：

```bash
git clone https://github.com/HotRiceNoodles/lotuseater-skills.git
ln -s "$(pwd)/lotuseater-skills/skills/traceable-meeting-minutes" ~/.claude/skills/traceable-meeting-minutes
```

（Windows 下用 `mklink /D` 或复制目录。）

## Skills

| Skill | 用途 |
|-------|------|
| [traceable-meeting-minutes](skills/traceable-meeting-minutes/) | 会议录音/转写稿 → 可回溯纪要：语义账本 + 分级压缩 + 交互式 HTML（每句可跳回原话与录音时刻）+ "丢了什么"审计 |

## 收录规范

新 skill 必须遵守 [docs/skill-spec.md](docs/skill-spec.md)，要点：

- 每个 skill 一个目录（`skills/<name>/`），目录名 == frontmatter `name`（kebab-case）
- SKILL.md <200 行，只做路由 + 铁律；细节下沉到 `workflows/`、`references/`、`templates/`
- 平台无关：无硬编码密钥/个人路径/平台绑定，平台差异通过首次运行时自适应
- Python 脚本附 `scripts/requirements.txt`，import 失败提示友好
- 收录前过 spec §7 检查清单，`claude plugin validate .` 通过

## License

[MIT](LICENSE)
