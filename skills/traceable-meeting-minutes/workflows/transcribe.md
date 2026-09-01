# 步骤 1 — 证据化 (transcript.json)

读本文的时机:拿到音频/文本输入,要生成不可变原话层时。

**引擎自动模式**(推荐):`--engine auto` 会读步骤 0 保存的 `engine.json`。首次运行请搭配 `--save-engine` 把选择持久化。

本地 faster-whisper(默认 `small`,追求准确率 `medium`/`large-v3`):
```bash
python scripts/normalize_transcript.py 会议.m4a -o workspace/transcript.json \
    --engine local --model small --language zh --copy-audio --save-engine
```
云端 OpenAI 兼容 API(示例:OpenAI 官方 whisper-1,长音频自动切块+重试):
```bash
python scripts/normalize_transcript.py 会议.m4a -o workspace/transcript.json \
    --engine cloud --provider openai \
    --api-key "$OPENAI_KEY" --chunk-minutes 10 \
    --language zh --copy-audio --save-engine
```
自建/其他兼容端点(如硅基流动、vLLM):把 `--provider openai` 换成 `--provider custom --base-url https://... --cloud-model whisper-large-v3`。

文本转写稿(能识别 `[00:47]`/`01:02:03`/`00:01 --> 00:03` 等时间戳与 `张三:` 说话人;没有则降级):
```bash
python scripts/normalize_transcript.py 转写稿.txt -o workspace/transcript.json
```

读 stderr/stdout 摘要。**若 `has_timestamps=false`**:告知用户"缺时间戳,可回溯只能到逐字引用、无法跳播",继续但降低承诺。**若 transcript.json 出现 `chunk_errors`**:告知用户"云端有 X 片转写失败,已记录在案,可在账本/审计里点出",让用户决定是否重跑或换引擎。**本地首次跑音频若报 faster-whisper/ffmpeg 缺失**,按 [references/environment.md](../references/environment.md) 装依赖并设 `HF_ENDPOINT=https://hf-mirror.com`。

## 长音频必须"主动 poll",不要傻等完成通知

超过 ~10 分钟的音频,CPU 转写会跑几十分钟。脚本每 45 秒 / 每 100 段会往 stderr 打一行 `[progress] segs=N audio_covered=Xs +Ys`,启动时把 stderr 重定向到 log:

```bash
export PYTHONUNBUFFERED=1
python scripts/normalize_transcript.py meeting.mp3 -o workspace/transcript.json \
    --model small --copy-audio > workspace/transcribe.log 2>&1
```

**云端引擎**同样发 `[progress]` 心跳(每个 chunk 上传成功/失败/重试都会打一行)。若某片重试用尽仍失败,脚本不阻塞,把错误写进 `transcript.json:chunk_errors`;agent 在 poll 结束读到该字段要如实报告。

**后台任务的完成通知不总可靠送达**(长任务 / 会话切换 / 进程 detach 都可能漏——任何 agent 平台皆如此)。不要只依赖通知:
- 每 **3–5 分钟**主动 `tail -5 workspace/transcribe.log`,看是否出现 `transcript.json written:` ——这是唯一可信的 DONE 信号;
- 或 `ls -la workspace/transcript.json` 查 mtime 是否已更新到"启动时间之后"(避免被旧文件误判);
- 若 `[progress]` 行 **超过 3 分钟没更新** 或进程消失但没 DONE 行,判定卡住:读整段 log 找原因(HF 下载超时/内存不足/网络中断),必要时换 `--model base`/`tiny` 重试或切云端;
- **不要 sleep 高频轮询,也不要假设"没收到通知就是没完成"**。3-5 分钟一次是合理节奏。
