# 环境准备与云端 ASR 引擎

读本文的时机:首次跑音频转写前装依赖,或用户选云端转写引擎需要 provider 参数与成本信息时。

## 环境准备(音频输入时)

- Python 依赖:`python -m pip install -r scripts/requirements.txt`(faster-whisper 仅本地转写需要;requests 仅云端需要;脚本在缺失时会给出同样的提示)。**不要用 openai-whisper**(新版 Python 上 numba 装不上),统一 faster-whisper。
- HuggingFace 国内镜像:首次运行前设 `HF_ENDPOINT=https://hf-mirror.com`(脚本内也会兜底设置)。
- `ffmpeg`/`ffprobe`:faster-whisper 解码依赖。Windows `winget install Gyan.FFmpeg`;macOS `brew install ffmpeg`;Linux `apt install ffmpeg`。
- 模型档位:默认 `small`(快);追求准确率可 `medium` 或 `large-v3`。GPU 可用时脚本自动切 cuda/float16。
- **MP3 直读陷阱**:faster-whisper 内部用 PyAV 解码,遇到某些 VBR/含杂帧的 MP3 会在 ~55s 处**静默截断**。脚本已默认先 ffmpeg 预解码到 16k mono wav 再喂模型,并在覆盖率<80% 时告警。`--no-decode` 可关掉(不推荐)。
- 声纹分离:**v1 不做**(见 SKILL.md 的 v2 路线);转写里 `speaker` 恒为"未知",除非文本稿自带。

## 云端 ASR 引擎

**协议:** 走 OpenAI 兼容 `POST {base_url}/audio/transcriptions`,统一一个实现覆盖 OpenAI 官方、硅基流动、Groq、Together、自建 vLLM/WhisperX 等。

**Profile 与默认值:**

| provider | base_url | 默认 model | chunk | 单请求上限 |
|---|---|---|---|---|
| `openai` | https://api.openai.com/v1 | `whisper-1` | 10 分钟 | 25MB |
| `siliconflow` | https://api.siliconflow.cn/v1 | `funan-ai/Whisper-large-v3` | 15 分钟 | 100MB |
| `custom` | 用户提供 | 用户提供 | 10 分钟 | 25MB |

**长音频切块:** 单请求大小或时长超阈值时,`cloud_asr.py` 用 ffmpeg `-f segment` 重采样为 32kbps mono mp3 分片上传,拿到各片 segments 后按 `chunk_index * chunk_seconds` 加绝对偏移,拼成完整时间轴。**单片失败重试 3 次(指数退避)**,最终失败记入 `transcript.json:chunk_errors`,不阻塞其余分片。

**API key 存储优先级:** CLI `--api-key` > 环境变量 `TRACE_ASR_API_KEY` > `engine.json:api_key`。同理 `TRACE_ASR_BASE_URL` / `TRACE_ASR_MODEL` 覆盖 config。

**配置文件:** `~/.traceable-meeting-minutes/engine.json`(0600 unix / NTFS ACL Windows;旧版 `~/.qwenworkcn/traceable-minutes/` 下的配置会被自动迁移读取)。含明文 `api_key`,共享机器建议改用环境变量并删除文件。

**成本估算(用户问起时):** OpenAI whisper-1 官方 $0.006/分钟,1 小时会议约 $0.36;硅基流动 Whisper-large-v3 定价更低,具体以官方页面为准。

**本地 vs 云端选择建议:** 单次/低频用云端(省 1.5GB 模型下载 + 免 CPU 排队);高频/敏感数据用本地(离线、数据不出机器)。
