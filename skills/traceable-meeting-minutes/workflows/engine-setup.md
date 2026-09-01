# 步骤 0 — 引擎选择 & 自进化偏好

读本文的时机:每次流程开始时先查偏好,首次运行时引导用户选引擎。

**依赖自检(首次必做):** 跑任何脚本前先确认 Python 依赖与系统依赖。缺失时提示用户:
```bash
python -m pip install -r scripts/requirements.txt   # faster-whisper(仅本地转写时)、requests(仅云端时)
```
系统依赖 `ffmpeg`/`ffprobe`:Windows `winget install Gyan.FFmpeg`、macOS `brew install ffmpeg`、Linux `apt install ffmpeg`。文本转写稿输入时不需要以上音频依赖。

**存储:** `~/.traceable-meeting-minutes/preferences.json`(defaults + observations + promoted 三段,跨平台通用)+ `engine.json`(仅存 api_key 时才有)。首次运行时脚本会自动探测所在 agent 平台并记入 preferences(可用 `preferences.py show` 查看),仅影响交付时的表述方式。

**自进化机制(核心):** 每次运行,agent/脚本对**用户显式做出**的选择(如 `--engine cloud --provider openai --model medium`)写进 observations;当同一 key 的**最近 3 次**(阈值)取值全一致且和当前 default 不同,自动把这个值升到 defaults 并在 stdout 打一行 `[promoted] key -> value (from 3 consecutive; was prev) — 想改说 preferences.py clear key`。**从 defaults 静默继承的值不再计入 observations**,避免自增循环。

**Agent 每次流程:**
1. `python scripts/preferences.py get engine` — 拿到就用,不再问;拿不到才弹问。同理 `whisper_model` / `provider` / `language` / `chunk_minutes` 先查 defaults。
2. 用户答完选项后,把选择显式传给 `normalize_transcript.py --engine X --model Y --save-engine`;脚本会 observe 并在满足阈值时升档。
3. 会话里当脚本 stdout 出现 `[promoted]` 时,**必须**在回复里告知用户一行,并提示可用 `preferences.py clear <key>` 或 `reset` 撤销。

**首次问(仅当 preferences 完全空):**
> **转写引擎选哪个?** — 本地 faster-whisper(免费/离线,首次下载 0.5–1.5GB,CPU 约 2× 实时)· 云端 OpenAI 兼容 API(免下载/按分钟计费/需自备 key,支持 OpenAI 官方、硅基流动、任意兼容端点)。

选云端再问 provider(`openai` / `siliconflow` / `custom`);`custom` 需 `base_url` + `model` id。任何 provider 都需要 `api_key`(CLI `--api-key` 或 env `TRACE_ASR_API_KEY`)。

**用户 CLI(主动管理偏好):**
```bash
python scripts/preferences.py show             # 完整配置
python scripts/preferences.py get engine       # 单项
python scripts/preferences.py set chunk_minutes 15
python scripts/preferences.py clear provider   # 撤销某项默认
python scripts/preferences.py reset            # 全部清空(defaults + observations)
```

**⚠ 安全边界:** preferences.json **从不存 api_key**;api_key 若持久化只落在 `engine.json`(0600/NTFS ACL,含明文,agent 首次保存时必须提醒用户)。想完全避开落盘,用 env `TRACE_ASR_API_KEY`。

**可升档的参数(范围,由用户设定):** engine / provider / whisper_model / cloud_model / cloud_base_url / language / chunk_minutes、输出层开关(output_html / output_ledger_csv / output_word / output_transcript_readable)、审计严格度(audit_limiter_words / audit_token_candidates)、账本密度(ledger_density_target)。
