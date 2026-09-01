#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_html.py — Step 4: render the traceable interactive minutes (index.html).

Assembles transcript.json + ledger.json + minutes.md + audit.md into a single
self-contained interactive HTML page with an audio player. Every claim in the
minutes carries a [↩ E01] citation; clicking it seeks the audio to that moment,
highlights the source transcript segment, and opens the ledger card. This is the
"可回溯" core: the summary can be lossy, but any line can grow back into the
real meeting context.

Usage:
  python build_html.py --dir workspace --minutes workspace/minutes.md \
      --transcript workspace/transcript.json --ledger workspace/ledger.json \
      [--audit workspace/audit.md] [--title "周会纪要"] -o workspace/index.html

  --audio overrides the audio path; otherwise transcript.json:audio_file is used.
  Audio is referenced by RELATIVE path -> run with --copy-audio to place it in --dir.

Design rules baked in: flat design, CSS variables, NO gradients/shadows, NO
localStorage/sessionStorage (all state lives in JS memory), fragment-safe.
"""

import argparse
import json
import os
import re
import shutil
import sys


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def fmt_ts(sec):
    if sec is None:
        return "--:--"
    sec = int(round(sec))
    h, r = divmod(sec, 3600)
    m, s = divmod(r, 60)
    return (f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}")


# ---- minimal, dependency-free markdown -> HTML (headings, bullets, cites) ----
# Citations are protected with control-char sentinels (\x00 id \x01) BEFORE escaping,
# so esc()'s &quot; conversion can't break the anchor; they're restored after escaping.
def md_to_html(md):
    md = re.sub(r"\[↩\s*([A-Za-z0-9_]+)\s*\]",
                lambda m: "\x00%s\x01" % m.group(1), md)
    out, in_ul = [], False
    for line in md.splitlines():
        ln = line.rstrip()
        h = re.match(r"^(#{1,4})\s+(.*)$", ln)
        if ln.strip() == "":
            if in_ul:
                out.append("</ul>"); in_ul = False
            continue
        if h:
            if in_ul:
                out.append("</ul>"); in_ul = False
            lvl = len(h.group(1))
            out.append(f"<h{lvl}>{md_inline(h.group(2))}</h{lvl}>")
            continue
        b = re.match(r"^[-*]\s+(.*)$", ln)
        if b:
            if not in_ul:
                out.append("<ul>"); in_ul = True
            out.append(f"<li>{md_inline(b.group(1))}</li>")
            continue
        if in_ul:
            out.append("</ul>"); in_ul = False
        out.append(f"<p>{md_inline(ln)}</p>")
    if in_ul:
        out.append("</ul>")
    return "\n".join(out)


def md_inline(t):
    t = esc(t)
    t = re.sub(r"\x00([A-Za-z0-9_]+)\x01",
               r'<a class="cite" data-ev="\1">↩ \1</a>', t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    return t


TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
:root{--bg:#f6f7f9;--panel:#fff;--ink:#1c2530;--muted:#6b7684;--line:#e4e8ee;
--brand:#2f6bed;--brand-soft:#eaf1ff;--hl:#fff2c2;--zero:#e0483d;--low:#c47d1a;
--mid:#2f6bed;--high:#6b7684;}
*{box-sizing:border-box}body{margin:0;font:15px/1.7 -apple-system,"Segoe UI",Roboto,
"Microsoft YaHei",sans-serif;background:var(--bg);color:var(--ink)}
header{position:sticky;top:0;background:var(--panel);border-bottom:1px solid var(--line);
padding:12px 20px;z-index:10}
header h1{margin:0;font-size:17px}
header .sub{color:var(--muted);font-size:12px;margin-top:2px}
audio{width:100%;margin-top:10px}
.tabs{display:flex;gap:6px;margin-top:10px}
.tabs button{border:1px solid var(--line);background:var(--panel);color:var(--ink);
padding:6px 14px;border-radius:8px;cursor:pointer;font-size:13px}
.tabs button.on{background:var(--brand);color:#fff;border-color:var(--brand)}
main{display:grid;grid-template-columns:1fr 360px;gap:16px;padding:16px 20px;max-width:1200px;margin:0 auto}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px}
.col{min-height:200px}
#transcript .seg{padding:8px 10px;border-radius:8px;cursor:pointer;border:1px solid transparent}
#transcript .seg:hover{background:var(--brand-soft)}
#transcript .seg.active{background:var(--hl);border-color:#e6c86a}
#transcript .seg .meta{font-size:11px;color:var(--muted);display:flex;gap:8px}
#transcript .seg .ts{color:var(--brand);font-variant-numeric:tabular-nums}
#minutes p{margin:8px 0}#minutes h2{font-size:15px;margin:16px 0 4px;border-left:3px solid var(--brand);padding-left:8px}
#minutes ul{margin:6px 0;padding-left:22px}
a.cite{color:var(--brand);cursor:pointer;text-decoration:none;font-size:11px;margin-left:4px;
background:var(--brand-soft);padding:0 6px;border-radius:6px}
a.cite:hover{background:#d8e6ff}
.ev{border:1px solid var(--line);border-radius:10px;padding:10px;margin-bottom:8px}
.ev .tag{display:inline-block;font-size:11px;padding:1px 8px;border-radius:20px;color:#fff;margin-right:6px}
.ev .cmp{font-size:11px;color:var(--muted)}
.ev .quote{margin:6px 0;padding:6px 8px;background:#fafbfc;border-left:2px solid var(--line);font-size:13px}
.badge{font-size:11px;padding:1px 7px;border-radius:20px;background:var(--brand-soft);color:var(--brand)}
.badge.drop{background:#ffe8e6;color:var(--zero)}
#audit .item{padding:8px;border-bottom:1px solid var(--line);font-size:13px}
.hidden{display:none}
.small{font-size:12px;color:var(--muted)}
mark{background:var(--hl)}
</style></head><body>
<header>
  <h1>__TITLE__</h1>
  <div class="sub">可回溯会议纪要 · 正文有损,原话可查 · <span id="hd-meta"></span></div>
  <audio id="player" controls preload="metadata" __AUDIOSRC__></audio>
  <div class="tabs">
    <button data-tab="minutes" class="on">纪要</button>
    <button data-tab="transcript">转写原话</button>
    <button data-tab="ledger">语义账本</button>
    <button data-tab="audit">审计</button>
  </div>
</header>
<main>
  <section class="col"><div class="card">
    <div id="minutes"></div>
    <div id="transcript" class="hidden"></div>
    <div id="ledger" class="hidden"></div>
    <div id="audit" class="hidden"></div>
  </div></section>
  <aside class="col"><div class="card">
    <div style="font-weight:600;margin-bottom:8px">压缩与信息保全</div>
    <div id="stats" class="small"></div>
    <div style="font-weight:600;margin:14px 0 8px">被降权/未展示的事件</div>
    <div id="hiddenlist" class="small"></div>
    <div class="small" style="margin-top:14px">提示:点击正文中的 <a class="cite">↩ 编号</a> 或下方原话,可跳转并高亮对应录音时刻。</div>
  </div></aside>
</main>
<script>
const DATA = __DATA_JSON__;
const player = document.getElementById('player');
const TYPE_CN = {decision:'决策',action:'行动项',data:'数据',risk:'风险',opinion:'观点',
 case:'案例',rebuttal:'反驳',open_question:'未决问题',revision:'原观点修正',
 background:'背景',chitchat:'寒暄'};
const CTYPE = {zero:'var(--zero)',low:'var(--low)',mid:'var(--mid)',high:'var(--high)'};

function seek(sec, evId){
  if(sec==null) return;
  if(player && player.getAttribute('src')){ try{player.currentTime=sec; player.play();}catch(e){} }
  document.querySelectorAll('#transcript .seg').forEach(s=>s.classList.remove('active'));
  let seg = document.querySelector('#transcript .seg[data-ev="'+(evId||'')+'"]');
  if(!seg){ seg=[...document.querySelectorAll('#transcript .seg')]
      .find(s=>{const a=+s.dataset.start,b=+s.dataset.end; return a<=sec && (b==null||b>=sec);}); }
  if(seg){ showTab('transcript'); seg.scrollIntoView({behavior:'smooth',block:'center'}); seg.classList.add('active'); }
}
function showTab(t){
  ['minutes','transcript','ledger','audit'].forEach(x=>document.getElementById(x).classList.add('hidden'));
  document.getElementById(t).classList.remove('hidden');
  document.querySelectorAll('.tabs button').forEach(b=>b.classList.toggle('on', b.dataset.tab===t));
}
document.querySelectorAll('.tabs button').forEach(b=>b.onclick=()=>showTab(b.dataset.tab));

// transcript
const tt=document.getElementById('transcript');
tt.innerHTML='<div class="small" style="margin-bottom:8px">共 '+(DATA.segments||[]).length+
  ' 段。'+(DATA.has_timestamps?'点击任意段跳转到该时刻。':'（该转写稿未识别到时间戳,无法跳转播放。）')+'</div>'+
  (DATA.segments||[]).map(s=>
   '<div class="seg" data-idx="'+s.i+'" data-start="'+(s.start??'')+'" data-end="'+(s.end??'')+'" data-ev="'+(s.ev||'')+'">'+
   '<div class="meta"><span class="ts">'+fmt(s.start)+'</span><span>'+esc(s.speaker||'未知')+'</span></div>'+
   '<div>'+esc(s.text)+'</div></div>').join('');
[...tt.querySelectorAll('.seg')].forEach(seg=>seg.onclick=()=>{
  const a=parseFloat(seg.dataset.start); if(!isNaN(a)) seek(a, seg.dataset.ev);});

// ledger
const lg=document.getElementById('ledger');
const byId={}; (DATA.ledger||[]).forEach(e=>byId[e.id]=e);
lg.innerHTML=(DATA.ledger||[]).map(e=>
  '<div class="ev" id="ev-'+e.id+'"><span class="tag" style="background:'+(CTYPE[e.compress]||'var(--muted)')+'">'+
  (TYPE_CN[e.type]||e.type)+'</span><span class="badge">'+e.id+'</span> '+
  '<b>'+esc(e.topic)+'</b><div class="quote">“'+esc(e.quote)+'”</div>'+
  '<div class="cmp">压缩预算 '+e.compress+' · '+fmt(e.start_sec)+
  (e.speaker&&e.speaker!=='未知'?(' · '+esc(e.speaker)):'')+
  (e.start_sec!=null?('<button class="cite" onclick="seek('+e.start_sec+',\''+e.id+'\')">↩ 定位</button>'):'')+
  '</div></div>').join('') || '<div class="small">无账本数据。</div>';

// minutes (citation clicks)
const mn=document.getElementById('minutes');
mn.innerHTML=DATA.minutes_html;
[...mn.querySelectorAll('a.cite')].forEach(a=>a.onclick=()=>{
  const e=byId[a.dataset.ev]; if(e){ showTab('ledger'); const node=document.getElementById('ev-'+e.id);
    if(node){node.classList.remove('flash');void node.offsetWidth;node.scrollIntoView({behavior:'smooth',block:'center'});node.style.background='var(--hl)';}
    if(e.start_sec!=null) seek(e.start_sec, e.id);} });

// audit
const au=document.getElementById('audit');
if(DATA.audit_html){au.innerHTML=DATA.audit_html;}else{au.innerHTML='<div class="small">未生成审计文件。</div>';}

// stats
function renderStats(){
  const ev=DATA.ledger||[]; const dropped=ev.filter(e=>e.in_minutes===false);
  const ratio = DATA.compress_ratio!=null?Math.round(DATA.compress_ratio*100)+'%':'—';
  document.getElementById('stats').innerHTML =
    '原文 '+(DATA.orig_chars||'?')+' 字 → 纪要 '+(DATA.minutes_chars||'?')+' 字 (保留 '+ratio+')<br>'+
    '登记信息事件 '+ev.length+' 条;其中 '+(ev.filter(e=>e.compress==='zero').length)+' 条零压缩(决策/数据/责任人/deadline/限定条件)。<br>'+
    '<span style="color:var(--zero)">'+dropped.length+' 条被降权或标注为“本次未展示”。</span>';
  document.getElementById('hiddenlist').innerHTML = dropped.length? dropped.map(e=>
    '<div class="item" style="border:0;padding:2px 0">• <span class="badge drop">'+e.id+'</span> '+
    (TYPE_CN[e.type]||e.type)+' “'+esc(e.topic)+'” — '+esc(e.note||'已归档,未删除')+'</div>').join('')
    : '无。本次登记的事件均已体现在纪要中。';
  const hasAudio = !!(DATA.audio);
  document.getElementById('player').style.display = hasAudio?'block':'none';
  document.getElementById('hd-meta').textContent =
    (DATA.has_timestamps?'含时间戳':'缺时间戳')+' · '+(DATA.source==='audio'?'音频转写':'文本转写')+
    (hasAudio?' · 录音可跳转':' · 无录音,仅可查原话');
}
function fmt(s){return s==null?'--:--':(function(x){x=Math.round(x);var h=Math.floor(x/3600),m=Math.floor((x%3600)/60),ss=x%60;return (h?h+':':'')+String(m).padStart(h?2:1,'0')+':'+String(ss).padStart(2,'0');})(s);}
function esc(t){return (t==null?'':String(t)).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
renderStats();
</script></body></html>"""


def main():
    ap = argparse.ArgumentParser(description="Render traceable interactive minutes HTML.")
    ap.add_argument("--dir", default=".", help="workspace dir holding the data files")
    ap.add_argument("--transcript", required=True)
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--minutes", required=True)
    ap.add_argument("--audit", help="optional audit.md")
    ap.add_argument("--audio", help="override audio path")
    ap.add_argument("--copy-audio", action="store_true")
    ap.add_argument("--title", default="会议纪要")
    ap.add_argument("-o", "--out", default=None)
    args = ap.parse_args()

    tdoc = json.load(open(args.transcript, encoding="utf-8"))
    ledger = json.load(open(args.ledger, encoding="utf-8"))
    events = ledger.get("events", [])
    minutes_md = open(args.minutes, encoding="utf-8").read()
    audit_html = None
    if args.audit and os.path.isfile(args.audit):
        audit_html = md_to_html(open(args.audit, encoding="utf-8").read())

    # link transcript seg -> event id (nearest by time)
    ev_by_seg_start = {}
    for e in events:
        if e.get("start_sec") is not None:
            ev_by_seg_start[e["start_sec"]] = e["id"]
    for s in tdoc["segments"]:
        st = s.get("start")
        if st is not None:
            best = min(ev_by_seg_start, key=lambda x: abs(x - st), default=None)
            if best is not None and abs(best - st) < 2:
                s["ev"] = ev_by_seg_start[best]

    # audio resolution
    audio_src = args.audio or tdoc.get("audio_file")
    audio_ok = False
    if audio_src:
        if args.copy_audio and os.path.isfile(audio_src):
            dst = os.path.join(args.dir, os.path.basename(audio_src))
            if os.path.abspath(dst) != os.path.abspath(audio_src):
                shutil.copy2(audio_src, dst)
            audio_src = os.path.basename(audio_src)
            audio_ok = True
        else:
            cand = audio_src if os.path.isabs(audio_src) else os.path.join(args.dir, audio_src)
            audio_src = os.path.basename(audio_src)
            audio_ok = os.path.isfile(cand)
    audiosrc_attr = ('src="%s"' % esc(audio_src)) if audio_ok else ""

    orig_chars = sum(len(s["text"]) for s in tdoc["segments"])
    min_chars = len(re.sub(r"[\s#*\-\[\]↩A-Za-z0-9]", "", minutes_md))
    ratio = (min_chars / orig_chars) if orig_chars else None

    data = {
        "source": tdoc["source"], "has_timestamps": tdoc["has_timestamps"],
        "audio": audio_src if audio_ok else None,
        "segments": tdoc["segments"], "ledger": events,
        "minutes_html": md_to_html(minutes_md), "audit_html": audit_html,
        "orig_chars": orig_chars, "minutes_chars": min_chars, "compress_ratio": ratio,
    }
    html = (TEMPLATE.replace("__TITLE__", esc(args.title or (ledger.get("meeting", {}).get("title")) or "会议纪要"))
            .replace("__AUDIOSRC__", audiosrc_attr)
            .replace("__DATA_JSON__", json.dumps(data, ensure_ascii=False)))
    out = args.out or os.path.join(args.dir, "index.html")
    open(out, "w", encoding="utf-8").write(html)
    print("index.html written: %s" % out)
    print("  audio=%s timestamps=%s events=%d orig=%d min=%d ratio=%s" %
          (audio_src if audio_ok else None, tdoc["has_timestamps"], len(events),
           orig_chars, min_chars, ("%.0f%%" % (ratio * 100)) if ratio is not None else "—"))


if __name__ == "__main__":
    main()
