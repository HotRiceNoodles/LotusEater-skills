---
name: traceable-meeting-minutes
description: Turn a meeting recording or transcript into lossless-evidence, traceable minutes — build a semantic ledger of information events, apply differential compression (numbers/dates/owners/deadlines kept verbatim), and render an interactive HTML where every claim jumps back to the original audio moment, plus an audit report on what info may have been dropped. Use when the user wants meeting minutes / 会议纪要 / 录音转纪要 / AI 摘要 that preserve evidence, or asks what important information AI summarization lost.
---

# 可回溯会议纪要 (Traceable Meeting Minutes)

把一份会议录音 / 转写稿,加工成"正文可有损、证据不可丢、每句可回溯"的纪要。解决 AI 纪要的真正风险:**不是写错,而是"正确但空洞"地悄悄删掉案例、限定条件、数据、deadline。**

核心信条(贯穿每一步):
- 正文可以压缩,**底层证据(原话+时间戳)绝不删除**。
- "不展示"≠"删除":被降权的信息一律进语义账本,可找回。
- 数字 / 日期 / 责任人 / deadline / 限定条件 / 决策 → 接近零压缩,逐字保留。
- 宁可标"未知 + 精确时间戳",也**绝不臆造**说话人或内容。

## 何时用

用户给一份会议**录音**(mp3/m4a/wav...)或**转写稿/笔记**,想要会议纪要、AI 摘要,或问"AI 到底替我丢了什么"。v1 只做时间戳级可回溯,不自动识别说话人(见文末 v2 路线)。

## 工作流(逐条勾选跟踪)

```
- [ ] 0 引擎选择:检测依赖与偏好,缺失则问用户(本地/云端),记住选择
- [ ] 1 接收与证据化:音频/文本 → transcript.json(不可变原话层)
- [ ] 2 语义账本:通读全文 → ledger.json(只登记不删,分类+压缩预算)
- [ ] 3 分级压缩生成纪要:minutes.md(关键结论逐字+挂 [↩ Exx] 锚点)+ 行动项
- [ ] 4 审计:audit.md(丢了什么,人工复核)
- [ ] 5 渲染:build_html → index.html(点句跳播/回溯原话)
- [ ] 6 交付:整目录交付 + 用一句话提示"丢了什么"待确认
```

先在输出目录建 `workspace/` 放中间产物,最终产物拷到 outputs 交付。每步的执行细节按需读对应 workflow:

| 步骤 | 读哪个文件 |
|------|-----------|
| 0 引擎选择 & 自进化偏好(依赖自检、preferences CLI、安全边界) | [workflows/engine-setup.md](workflows/engine-setup.md) |
| 1 证据化(命令行示例、降级处理、长音频主动 poll) | [workflows/transcribe.md](workflows/transcribe.md) |
| 2–3 语义账本 + 分级压缩纪要 | [workflows/ledger-and-minutes.md](workflows/ledger-and-minutes.md) |
| 4–6 审计 + HTML 渲染 + 交付话术 | [workflows/audit-render-deliver.md](workflows/audit-render-deliver.md) |

深入阅读(按需):
- [references/data-contracts.md](references/data-contracts.md) — transcript.json / ledger.json / minutes.md 字段定义与输出清单
- [references/taxonomy.md](references/taxonomy.md) — 信息事件 12 分类与 4 档压缩预算
- [references/environment.md](references/environment.md) — 依赖安装、本地引擎细节、云端 ASR provider 表与成本

## 铁律

- 任何脚本/正文**都不永久删除**用户文件或会议信息;降权=归档,不是销毁。
- 不臆造说话人、时间、数字、结论;不确定就在纪要里标"待定/存疑"并在审计里点出。
- transcript.json 一旦生成就当只读证据层;要改的是 minutes.md,不是原话。
- 交付前必跑审计,并把"丢了什么"如实告诉用户,而不是假装纪要无损。

## 范围之外 (v2)

自动声纹分离(pyannote/3D-Speaker + 回退链、说话人置信度、抢话存疑标注)。本 v1 恒以"未知+时间戳"交付,HTML/数据结构已预留 `speaker` 字段,升级无需返工。
