# 数据契约:transcript.json / ledger.json / minutes.md

读本文的时机:执行步骤 1–3(证据化、建账本、写纪要)需要精确字段定义时。

## 1. transcript.json(证据底层,不可变)

由 `normalize_transcript.py` 生成,是"原话"层,所有结论最终都要能指回它。字段:

```json
{
  "source": "audio | text",
  "has_timestamps": true,
  "has_speakers": false,
  "audio_file": "meeting.m4a",
  "duration_sec": 3600.0,
  "segments": [
    {"i": 0, "start": 0.0, "end": 3.4, "speaker": "未知", "text": "逐字原文",
     "words": [{"w": "逐字", "s": 0.0, "e": 0.4}]}
  ]
}
```

`start`/`end` 为秒;文本稿缺时间戳时为 `null`。`speaker` v1 恒为 `"未知"`(除非文本稿本身带)。

## 2. ledger.json(语义账本)

由 agent 通读 transcript.json 后产出。原则:**只登记,不删除**。每条信息事件都是独立可寻址对象。

```json
{
  "meeting": {"title": "8月产品周会", "date": "2026-08-31", "participants": ["未知"]},
  "events": [
    {
      "id": "E01",
      "type": "decision",
      "topic": "小程序最迟10月底上线",
      "quote": "项目最迟不超过10月底上线,这个我们今天就定了。",
      "start_sec": 2851.0, "end_sec": 2859.0,
      "seg_i": 132,
      "speaker": "未知",
      "compress": "zero",
      "in_minutes": true,
      "note": "决策+deadline,逐字保留"
    }
  ]
}
```

## 3. minutes.md(纪要正文)

Markdown。每条来自会议的**关键结论**后必须挂引用锚点 `[↩ E01]`(账本事件 id)。示例:

```markdown
## 决策
- 小程序最迟不超过 10 月底上线 [↩ E01]。
- 客户数据不得用于模型训练 [↩ E07]。

## 案例(保留机制,未被压成一句话)
- 多模态辅助儿童写作:AI 按作文生成图片,画面与孩子想象的差距成为
  "表达能力镜子",形成 想象→写作→生成→发现差距→修改 的反馈闭环 [↩ E03]。
```

引用锚点是"正文一句 ↔ 原话 ↔ 录音时刻"的链路;build_html.py 会把 `[↩ Exx]` 变成可点击跳转。

## 4. 输出文件清单(全部放同一输出目录,HTML 相对引用音频)

```
output/
├── index.html            # 交互式可回溯纪要(交付主件)
├── meeting.m4a           # 音频副本(--copy-audio),供 HTML 跳转播放
├── transcript.json       # 证据底层(事实归档)
├── ledger.json / .csv    # 语义账本
├── minutes.md            # 组织纪要(正文)
└── audit.md              # 审计报告(丢了什么)
```
