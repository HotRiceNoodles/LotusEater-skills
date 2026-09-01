# 步骤 4–6 — 审计、渲染、交付

读本文的时机:minutes.md 写完之后——跑审计、渲染可回溯 HTML、向用户交付时。

## 步骤 4 — 审计 (audit.md)

```bash
python scripts/audit_minutes.py --transcript workspace/transcript.json \
    --ledger workspace/ledger.json --minutes workspace/minutes.md \
    -o workspace/audit.md
```
产出五节:压缩概览、关键事件/引用完整性、**可能被丢的硬信息**(原话里有、纪要里没有的数字/日期/期限,带时刻)、被降权/未展示但已归档的事件、限定词线索。**逐条人工复核**这些候选——脚本只报告、不下结论;确认要补的回步骤 3 补进正文或确保 `in_minutes:false` 已归档。

## 步骤 5 — 渲染可回溯 HTML (index.html)

```bash
python scripts/build_html.py --dir workspace \
    --transcript workspace/transcript.json --ledger workspace/ledger.json \
    --minutes workspace/minutes.md --audit workspace/audit.md \
    --title "会议标题" --copy-audio -o workspace/index.html
```
生成单文件交互页:纪要里每个 `[↩ Exx]` 可点→跳到语义账本卡片→并定位/播放录音到该时刻;"转写原话"面板可点段跳播;"审计"面板展示 audit.md。音频以**同目录相对路径**引用(`--copy-audio` 会把录音拷到 index.html 旁),整目录拷走即可离线打开。页面无 localStorage、无渐变阴影。

## 步骤 6 — 交付

把 `index.html`、`transcript.json`、`ledger.json`(可另存 .csv)、`minutes.md`、`audit.md`、音频副本一并拷到 outputs 目录交付:在回复中列出 outputs 文件清单(若所在平台提供文件呈现工具则用它),并附一句话指引"index.html 可直接双击离线打开,点纪要中的 [↩ Exx] 可跳回原话与录音时刻"。回复里**明确抛出审计结论**:例如"审计发现 3 个日期、1 处责任人、2 条案例机制未进正文,已在 HTML'审计'面板列出,请确认是否补入纪要"。
