# Skill 编写规范（lotuseater-skills）

> 本仓库所有 skill 必须遵守本规范。新 skill 收录前按 §7 检查清单逐项验收。
> 依据：[Agent Skills 开放规范](https://agentskills.io/specification)、[Claude Code 插件市场文档](https://code.claude.com/docs/en/plugin-marketplaces)。

## 1. 仓库布局

```
lotuseater-skills/
├── .claude-plugin/marketplace.json   # 市场清单：plugins 数组，一个 skill 一个条目
├── README.md                          # 安装方式 + skill 索引
├── docs/skill-spec.md                 # 本规范
└── skills/
    └── <skill-name>/                  # 每个 skill 一个目录，目录名 == frontmatter name
```

- skill 统一放 `skills/` 下，扁平不分组（未来数量 >15 且主题明显分散时再议分组）。
- 新 skill 先进 `incoming/`（已 gitignore）整理，验收后迁入 `skills/`。

## 2. Skill 目录结构

没有对应内容的目录**不创建**（结构服务于内容，不是反过来）：

```
<skill-name>/
├── SKILL.md                    # 必需。总入口：路由 + 铁律，保持精简
│
├── references/                 # 知识、规则、范例、参考资料（按需加载）
│   ├── methodology.md          # 核心方法论
│   ├── rules.md                # 判断规则 / 约束
│   ├── examples.md             # 正反案例
│   └── glossary.md             # 术语定义，可选
│
├── workflows/                  # 不同任务的执行流程（SKILL.md 只做路由）
│   ├── analyze.md              # 分析类工作流
│   ├── create.md               # 创作类工作流
│   └── review.md               # 审核 / 评分工作流
│
├── templates/                  # 输出模板（报告、清单、文档骨架）
│   └── report.md
│
├── scripts/                    # 确定性程序，可选
│   ├── validate.py
│   └── requirements.txt        # 有 pip 依赖时必需
│
├── assets/                     # 静态资源（schema、示例数据）
│   └── schema.json
│
└── tests/                      # 测试集，非常推荐（开发时验证用，平台不自动跑）
    ├── cases.md
    ├── good_cases/
    ├── bad_cases/
    └── expected/
```

禁止的目录/文件：
- `bin/` —— claude.ai 市场同步直接拒绝
- `__pycache__/`、`*.pyc`、虚拟环境等编译/运行产物
- 平台专有元数据文件（如 `.skill-metadata.yaml`）——平台差异必须通过首次运行时自适应处理（探测平台 → 调整表述/行为），而非静态平台文件

## 3. SKILL.md 要求

### frontmatter（硬性约束）

| 字段 | 约束 |
|------|------|
| `name` | 必填。kebab-case，≤64 字符，**必须与目录名一致** |
| `description` | 必填。≤1024 字符，必须同时说明**做什么 + 何时用**（含中英文触发词，如适用）。这是 skill 被正确选中的唯一依据 |

可选字段遵循 Agent Skills 开放规范（`license`、`allowed-tools` 等），按需添加。

### 正文（渐进式披露）

- **<200 行**（官方上限 500，本规范从严）。超了就是该下沉到 workflows/ 或 references/ 的信号。
- 结构：一句定位 → 何时用 → 核心信条/铁律 → 工作流路由表（指向 workflows/）→ 深入阅读指引（指向 references/）。
- 细节**必须下沉**：SKILL.md 是地图，不是领土。执行细节放 workflows/，领域知识放 references/，输出格式放 templates/。
- 引用同级文件用相对路径（`workflows/transcribe.md`），引用脚本用相对于 skill 根的路径（`scripts/validate.py`）。

### workflows/、references/、templates/ 内文件

- 单文件同样建议 <300 行；一个文件一个主题。
- 文件开头一句话说明本文件何时需要被读（"做 X 时读本文"）。
- 命名：kebab-case 或小写单词，动词开头（`transcribe.md`、`render-html.md`）。

## 4. scripts/ 要求

- 每个 pip 依赖的 skill 必须有 `scripts/requirements.txt`，注释区分必需/可选依赖（如"仅本地转写时需要"）。
- import 失败时必须给出指向 `requirements.txt` 的友好提示，不许裸抛 ImportError。
- 系统级依赖（ffmpeg 等）在 SKILL.md 依赖自检段写明三平台安装命令。
- 配置/状态写入 `~/.<skill-name>/`（跨平台通用路径），首次运行时自动探测所在 agent 平台并自适应，不硬编码任何平台专有路径、工具名或行为。
- 敏感信息（api_key 等）：优先环境变量；必须落盘时用 0600 权限并在文档显著提示；**绝不**写入 preferences 类明文日志、绝不提交进仓库。

## 5. 通用化与安全

- 无硬编码密钥、token、内网地址。
- 无个人机器痕迹（"本机 Python 3.14"、"已用 winget 装了 X"之类的记录改写为通用指引）。
- 脚本对输入做基本校验；错误信息可操作（告诉用户下一步做什么）。
- 不永久删除用户文件；降级 = 归档，不是销毁。

## 6. marketplace.json 登记

每个 skill 发布时在 `.claude-plugin/marketplace.json` 的 `plugins` 数组加一个条目：

```json
{
  "name": "<skill-name>",
  "source": "./",
  "strict": false,
  "skills": ["./skills/<skill-name>"],
  "description": "一句话英文描述（市场展示用）",
  "category": "workflow"
}
```

- `name` kebab-case，与 skill 目录名一致；改名对用户是破坏性操作，须走 marketplace 的 `renames` 机制。
- 提交前跑 `claude plugin validate .` 验证。

## 7. 收录检查清单（验收必过）

- [ ] frontmatter：name 与目录名一致、kebab-case、≤64 字符
- [ ] description 含"做什么 + 何时用"，≤1024 字符
- [ ] SKILL.md <200 行，只做路由 + 铁律
- [ ] 目录结构符合 §2，无多余目录，无禁止文件
- [ ] 引用的所有文件（workflows/references/templates/scripts）实际存在
- [ ] scripts 有 requirements.txt（如有 pip 依赖），import 失败提示友好
- [ ] 无密钥、无个人路径、无平台硬绑定（或有平台自适应机制）
- [ ] `python -m py_compile`（或对应语言等价物）通过；脚本冒烟测试通过
- [ ] marketplace.json 已登记，`claude plugin validate .` 通过
- [ ] README.md 索引表已更新
