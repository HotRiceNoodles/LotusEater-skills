#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_minutes.py — Step 3 audit: "AI 替我丢掉了什么,还能找回来吗?"

The dangerous loss in AI minutes is not hallucination — it is being *correct but
hollow*: quietly deleting the case, the qualifier, the deadline, the number. This
script diffs the minutes against the immutable evidence layer (transcript.json)
and the semantic ledger, and surfaces what may have been dropped. It NEVER edits
the minutes; it produces a report (audit.md) the human/agent must review.

Usage:
  python audit_minutes.py --transcript transcript.json --ledger ledger.json \
      --minutes minutes.md -o audit.md

Checks:
  A. Compression ratio (原文字数 → 纪要字数) and how many events are 降权/未展示.
  B. Citation integrity: every [↩ Exx] in minutes exists in ledger; high-criticality
     events (decision/data/action/risk) that are NOT cited anywhere -> HIGH alert.
  C. High-risk token loss: numbers / money / percentages / dates / deadline words /
     limiter words found in the transcript but absent from the minutes -> candidate
     silent loss, listed with the source timestamp so it can be traced back.
"""

import argparse
import json
import re
import sys

NUM_TOKEN = re.compile(
    r"(?:\d[\d,]*\.?\d*\s*(?:万|亿|千|元|块|美元|美金|人民币|%|％|个点|"
    r"次|个|天|周|月|日|号|小时|分钟|人|位|条|项|台|家|倍)|"
    r"\d{1,2}\s*月\s*\d{1,2}\s*[日号]|\d{4}[年/-]\d{1,2}|deadline|"
    r"第?\d+季|Q[1-4]|[上下]半年)")
DATE_TOKEN = re.compile(r"(?:\d{1,2}\s*月|\d{1,2}[:：]\d{2}|周[一二三四五六日]|下周|月底|月初|年底)")
LIMITER = re.compile(r"(?:暂不|暂时不|暂时|不能|不得|不可|绝对|必须|仅限|只有|仅供|严禁|优先|延后|搁置|待定|存疑)")
CRITICAL_TYPES = {"decision", "data", "action", "risk"}


def fmt(sec):
    if sec is None:
        return "--:--"
    sec = int(round(sec)); h, r = divmod(sec, 3600); m, s = divmod(r, 60)
    return (f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}")


def norm(s):
    return re.sub(r"[\s,，.。、:：;；\"'“”‘’()（）\[\]【】]", "", s or "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--transcript", required=True)
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--minutes", required=True)
    ap.add_argument("-o", "--out", default="audit.md")
    args = ap.parse_args()

    tdoc = json.load(open(args.transcript, encoding="utf-8"))
    ledger = json.load(open(args.ledger, encoding="utf-8"))
    minutes = open(args.minutes, encoding="utf-8").read()
    events = ledger.get("events", [])
    ev_ids = {e["id"] for e in events}
    cited = set(re.findall(r"\[↩\s*([A-Za-z0-9_]+)\s*\]", minutes))
    min_norm = norm(minutes)

    # --- A: compression ---
    orig_chars = sum(len(s["text"]) for s in tdoc["segments"])
    min_chars = len(norm(minutes))
    ratio = (min_chars / orig_chars) if orig_chars else None
    hidden = [e for e in events if e.get("in_minutes") is False]

    # --- B: citation integrity ---
    bad_refs = sorted(cited - ev_ids)
    crit_missing = [e for e in events
                    if e.get("type") in CRITICAL_TYPES
                    and e.get("in_minutes", True) and e["id"] not in cited]

    # --- C: high-risk token loss ---
    src_tokens = {}
    for s in tdoc["segments"]:
        for tok in set(NUM_TOKEN.findall(s["text"]) + DATE_TOKEN.findall(s["text"])):
            tok = tok.strip()
            if tok and tok not in src_tokens:
                src_tokens[tok] = s.get("start")
    dropped_tokens = []
    for tok, st in src_tokens.items():
        if norm(tok) and norm(tok) not in min_norm:
            dropped_tokens.append((tok, st))
    dropped_tokens.sort(key=lambda x: (x[1] is None, x[1]))

    limiter_hits = [s for s in tdoc["segments"] if LIMITER.search(s["text"])]

    lines = []
    lines.append("# 信息审计:这份纪要丢掉了什么\n")
    lines.append("> 本文件由 audit_minutes.py 生成,只报告、不修改纪要。逐条人工确认——"
                 "真正的危险不是写错,而是“正确但空洞”地删掉了重要信息。\n")

    lines.append("## 一、压缩概览\n")
    lines.append(f"- 转写原文:约 **{orig_chars}** 字 → 纪要:约 **{min_chars}** 字"
                 + (f",保留 **{ratio*100:.0f}%**" if ratio is not None else "") + "。")
    lines.append(f"- 登记信息事件 **{len(events)}** 条,其中零压缩(决策/数据/责任人/"
                 f"deadline/限定)**{sum(1 for e in events if e.get('compress')=='zero')}** 条;"
                 f"标注“本次未展示/降权” **{len(hidden)}** 条。")
    lines.append(f"- 转写稿含时间戳:**{'是' if tdoc['has_timestamps'] else '否'}**;"
                 f"说话人识别:**{'有' if tdoc['has_speakers'] else 'v1 未做(仅时间戳)'}**。\n")

    lines.append("## 二、引用与高危事件完整性\n")
    if bad_refs:
        lines.append(f"- ⚠ 正文引用了不存在的账本编号:{', '.join(bad_refs)}(请补登或改编号)。")
    if crit_missing:
        lines.append(f"- 🔴 以下**关键事件(决策/数据/行动/风险)已登记却未在正文出现**,可能已被漏写:")
        for e in crit_missing:
            lines.append(f"    - {e['id']} · {e.get('type')} · “{e.get('topic')}”"
                         f" · {fmt(e.get('start_sec'))}")
    else:
        lines.append("- ✅ 所有关键类型事件均已在正文中被引用。")
    lines.append("")

    lines.append("## 三、可能被悄悄丢掉的硬信息(候选清单)\n")
    if dropped_tokens:
        lines.append(f"下列数字/日期/期限在原话中出现,但未在纪要正文里找到。逐项核对是否"
                     f"需要保留(带时间戳可回溯到原话):\n")
        lines.append("| 令牌 | 原话时刻 | 状态 |")
        lines.append("|---|---|---|")
        for tok, st in dropped_tokens[:80]:
            lines.append(f"| {tok} | {fmt(st)} | 纪要中未出现 |")
        if len(dropped_tokens) > 80:
            lines.append(f"\n_(另有 {len(dropped_tokens)-80} 条未列出)_")
    else:
        lines.append("- ✅ 未检测到原话中出现但纪要缺失的数字/日期/期限令牌。")
    lines.append("")

    lines.append("## 四、被降权/未展示但已归档(可找回)的事件\n")
    if hidden:
        for e in hidden:
            lines.append(f"- {e['id']} · {e.get('type')} · “{e.get('topic')}”"
                         f" · {fmt(e.get('start_sec'))} — {e.get('note','已归档,未删除')}")
    else:
        lines.append("- 无。本次登记的每条事件都已体现在纪要中。")
    lines.append("")

    lines.append("## 五、限定条件与语气线索(需人工确认是否脱离语境)\n")
    lines.append(f"- 原话中含“暂不/不得/绝对/仅限/待定/存疑”等限定词的句子共 "
                 f"**{len(limiter_hits)}** 处,示例:")
    for s in limiter_hits[:12]:
        snippet = s["text"].strip()
        lines.append(f"    - {fmt(s.get('start'))} · {snippet[:60]}"
                     + ("…" if len(snippet) > 60 else ""))
    if not limiter_hits:
        lines.append("    - (未检测到明显限定词)")
    lines.append("")

    report = "\n".join(lines)
    open(args.out, "w", encoding="utf-8").write(report)
    print("audit.md written: %s" % args.out)
    print("  compression=%s  hidden_events=%d  crit_missing=%d  bad_refs=%d  "
          "candidate_lost_tokens=%d  limiter_lines=%d" %
          (("%.0f%%" % (ratio * 100)) if ratio is not None else "—",
           len(hidden), len(crit_missing), len(bad_refs), len(dropped_tokens), len(limiter_hits)))
    if crit_missing or dropped_tokens:
        print("  >> 需要人工复核:存在关键事件缺失或硬信息疑似丢失。")


if __name__ == "__main__":
    main()
