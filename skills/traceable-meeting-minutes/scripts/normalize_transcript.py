#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
normalize_transcript.py — Step 1 evidence layer of the traceable-minutes pipeline.

Turns a raw input into transcript.json: the immutable ground-truth layer every later
claim cites. Supports three inputs:

  1) Audio file            -> transcribe with faster-whisper (timestamps real)
       python normalize_transcript.py meeting.m4a -o workspace/transcript.json \
           --model medium --language zh --words
  2) Text transcript       -> parse timestamps / speaker names if present
       python normalize_transcript.py transcript.txt -o workspace/transcript.json
  3) Plain meeting notes   -> same as (2); lines with no timestamps become timestamp-less

Output schema (transcript.json):
{
  "source": "audio" | "text",
  "has_timestamps": true/false,
  "has_speakers": true/false,
  "language": "zh",
  "audio_file": "meeting.m4a" | null,   # basename, referenced from the output folder
  "duration_sec": 3600.0 | null,
  "segments": [ {"i":0,"start":0.0,"end":3.4,"speaker":"未知","text":"..."} , ... ]
}

Degrade, never guess: if timestamps/speakers are missing the fields are left null/"未知"
and the headline flags are set false. This script does NOT invent speaker identities.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys

# sibling modules (cloud_asr, engine_config) must be importable regardless of cwd
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
import cloud_asr           # noqa: E402
import engine_config       # noqa: E402
import preferences         # noqa: E402

TEXT_EXT = {".txt", ".md", ".srt", ".vtt", ".json", ".log"}
AUDIO_EXT = {".mp3", ".m4a", ".wav", ".aac", ".flac", ".ogg", ".opus", ".amr", ".wma", ".mp4", ".mov"}

# 0:47  |  01:02:03  |  1:23.4   (allow . or , for fractional seconds)
TS_RE = re.compile(r"(?P<h>\d{1,2}:)?(?P<m>\d{1,2}):(?P<s>\d{1,2})(?:[.,](?P<ms>\d{1,3}))?")
# "张三:" / "张三：" / "[讲者A]" / "- 李四：" at line start -> capture a short name label
SPK_RE = re.compile(r"^[\s\-·•>*]*[\[(【]?(?P<spk>[\w一-鿿]{1,12})[\])】]?\s*[:：]\s*(?P<rest>.*)$")


def to_sec(h, m, s, ms):
    sec = int(m) * 60 + int(s) + (int(h) * 3600 if h else 0)
    if ms:
        sec += int(ms) / (10 ** len(ms))
    return round(sec, 2)


def detect_audio_duration(path):
    if not shutil.which("ffprobe"):
        return None
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", path],
            capture_output=True, text=True, timeout=30)
        return float(out.stdout.strip())
    except Exception:
        return None


def decode_to_wav(src, dst):
    """Pre-decode any audio to 16k mono PCM wav with ffmpeg.

    Why: faster-whisper decodes via PyAV, which on some MP3s (VBR / stray
    'Header missing' frames) silently STOPS early and transcribes only the first
    few tens of seconds. ffmpeg is far more tolerant, so we hand the model a clean
    wav. Returns True on success. ffmpeg spews frame warnings to stderr; that is
    expected and we ignore it (decoded duration is what matters).
    """
    if not shutil.which("ffmpeg"):
        return False
    try:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src,
                        "-ac", "1", "-ar", "16000", "-f", "wav", dst],
                       capture_output=True, timeout=1800)
    except Exception:
        return False
    try:
        import wave
        with wave.open(dst) as w:
            got = w.getnframes() / w.getframerate()
        want = detect_audio_duration(src)
        if want and got < want * 0.95:
            return False
        return got > 0
    except Exception:
        return False


def parse_text(path):
    raw = open(path, encoding="utf-8").read()
    lines = [ln.rstrip() for ln in raw.splitlines()]
    segments, has_ts, has_spk = [], False, False
    # keep end-timestamp (from SRT "00:01 --> 00:03" style) as fallback boundary
    prev_start = None
    for ln in lines:
        if not ln.strip():
            continue
        text = ln.strip()
        start = end = None
        speaker = "未知"
        # SRT/VTT arrow line like "00:00:01,000 --> 00:00:04,000"
        arrow = re.match(r"^\s*(\S+)\s*-->\s*(\S+)\s*$", ln)
        if arrow:
            m1, m2 = TS_RE.search(arrow.group(1)), TS_RE.search(arrow.group(2))
            if m1 and m2:
                start = to_sec(*(m1.group('h'), m1.group('m'), m1.group('s'), m1.group('ms')))
                end = to_sec(*(m2.group('h'), m2.group('m'), m2.group('s'), m2.group('ms')))
                continue  # an index/timing line carries no spoken text
        # leading timestamp + optional speaker
        tsm = TS_RE.search(text[:24])
        if tsm:
            start = to_sec(tsm.group('h'), tsm.group('m'), tsm.group('s'), tsm.group('ms'))
            has_ts = True
            text = (text[:tsm.start()] + text[tsm.end():]).strip()
        spm = SPK_RE.match(text)
        if spm and len(spm.group('spk')) <= 12:
            speaker = spm.group('spk')
            has_spk = True
            text = spm.group('rest').strip()
        if not text:
            continue
        segments.append({"i": len(segments), "start": start, "end": end,
                         "speaker": speaker, "text": text})
        prev_start = start
    # fill segment end times from next start when we have timestamps
    for idx in range(len(segments) - 1):
        if segments[idx].get("end") is None and segments[idx + 1].get("start") is not None:
            segments[idx]["end"] = segments[idx + 1]["start"]
    if has_ts and segments and segments[-1]["end"] is None:
        segments[-1]["end"] = segments[-1]["start"]
    return {"segments": segments, "has_ts": has_ts, "has_spk": has_spk}


def transcribe_audio(path, model_size, language, word_ts, decode=True,
                     progress_every=100, heartbeat_sec=45):
    import time as _t
    try:
        from faster_whisper import WhisperModel
    except Exception as e:
        sys.stderr.write(
            "\nERROR: faster-whisper is not usable here (%s).\n"
            "Install: python -m pip install -r %s\n"
            "China mirror: set HF_ENDPOINT=https://hf-mirror.com before first run.\n\n"
            % (e, os.path.join(_HERE, "requirements.txt")))
        raise
    if os.environ.get("HF_ENDPOINT", "").strip() == "":
        os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
    device = "cpu"
    compute = "int8"
    try:
        import torch
        if torch.cuda.is_available():
            device, compute = "cuda", "float16"
    except Exception:
        pass
    t0 = _t.time()
    def _prog(msg):
        sys.stderr.write("[progress] %s +%.0fs\n" % (msg, _t.time() - t0))
        sys.stderr.flush()
    _prog("loading model=%s" % model_size)
    model = WhisperModel(model_size, device=device, compute_type=compute)
    # Pre-decode to wav with ffmpeg to dodge PyAV's early-stop bug on some MP3s.
    audio_in = path
    tmp_wav = None
    if decode and os.path.splitext(path)[1].lower() != ".wav":
        _prog("ffmpeg pre-decode ...")
        tmp_wav = path + ".decode16k.wav"
        if decode_to_wav(path, tmp_wav):
            audio_in = tmp_wav
            _prog("decoded wav ready")
        else:
            _prog("pre-decode unavailable, PyAV will read source directly")
    try:
        _prog("transcribing ...")
        seg_iter, info = model.transcribe(audio_in, language=language or None,
                                          word_timestamps=bool(word_ts),
                                          vad_filter=True)
        segments = []
        _last_beat = t0
        for s in seg_iter:
            item = {"i": len(segments), "start": round(s.start, 2), "end": round(s.end, 2),
                    "speaker": "未知", "text": s.text.strip()}
            if word_ts and getattr(s, "words", None):
                item["words"] = [{"w": w.word.strip(), "s": round(w.start, 2), "e": round(w.end, 2)}
                                 for w in s.words if w.word.strip()]
            segments.append(item)
            # progress heartbeat so the caller can poll instead of waiting blind
            now = _t.time()
            if (len(segments) % progress_every == 0) or (now - _last_beat) >= heartbeat_sec:
                _last_beat = now
                _prog("segs=%d audio_covered=%.0fs" % (len(segments), s.end))
        _prog("iteration finished, segs=%d" % len(segments))
    finally:
        if tmp_wav and os.path.isfile(tmp_wav):
            try:
                os.remove(tmp_wav)
            except Exception:
                pass
    duration = float(info.duration) if getattr(info, "duration", None) else None
    return {"segments": segments, "has_ts": True, "has_spk": False,
            "language": info.language, "duration": duration}


def main():
    ap = argparse.ArgumentParser(description="Build transcript.json evidence layer.")
    ap.add_argument("input", help="audio file, text transcript, or meeting notes")
    ap.add_argument("-o", "--out", required=True, help="output transcript.json path")
    ap.add_argument("--model", default=None,
                    help="faster-whisper size: small|medium|large-v3 (omit to use preferences default, else 'small')")
    ap.add_argument("--language", default=None,
                    help="language hint (zh / en / auto=empty). Omit to use preferences default, else 'zh'")
    ap.add_argument("--words", action="store_true", help="word-level timestamps (audio only)")
    ap.add_argument("--copy-audio", action="store_true",
                    help="copy the audio into the output folder for HTML playback")
    ap.add_argument("--no-decode", action="store_true",
                    help="skip ffmpeg pre-decode (transcribe audio directly; NOT recommended)")
    ap.add_argument("--engine", choices=["auto", "local", "cloud"], default=None,
                    help="transcription engine; omit to consult preferences (self-evolving) then fall back to local")
    ap.add_argument("--provider", choices=list(cloud_asr.PROVIDER_DEFAULTS.keys()),
                    help="cloud provider preset (only for --engine cloud)")
    ap.add_argument("--base-url", dest="base_url", help="cloud OpenAI-compatible base_url override")
    ap.add_argument("--cloud-model", dest="cloud_model", help="cloud model id, e.g. whisper-1")
    ap.add_argument("--api-key", dest="api_key", help="cloud API key (also readable via env TRACE_ASR_API_KEY)")
    ap.add_argument("--chunk-minutes", dest="chunk_minutes", type=int,
                    help="cloud: minutes per API request; ffmpeg-segmented then stitched (default 10)")
    ap.add_argument("--save-engine", action="store_true",
                    help="persist the effective engine config to engine.json for future runs")
    args = ap.parse_args()

    # capture which promotable args were EXPLICIT on CLI (vs inherited from
    # preferences or hardcoded defaults). Only explicit choices feed the
    # self-evolving observation log; otherwise defaults reinforce themselves.
    _explicit = {}
    if args.engine and args.engine != "auto":
        _explicit["engine"] = args.engine
    if args.model:
        _explicit["whisper_model"] = args.model
    if args.language and args.language not in ("", "auto"):
        _explicit["language"] = args.language
    if args.provider:
        _explicit["provider"] = args.provider
    if args.cloud_model:
        _explicit["cloud_model"] = args.cloud_model
    if args.base_url:
        _explicit["cloud_base_url"] = args.base_url
    if args.chunk_minutes:
        _explicit["chunk_minutes"] = int(args.chunk_minutes)

    path = os.path.abspath(args.input)
    if not os.path.isfile(path):
        sys.stderr.write("ERROR: input not found: %s\n" % path)
        sys.exit(2)
    ext = os.path.splitext(path)[1].lower()
    outdir = os.path.dirname(os.path.abspath(args.out))
    os.makedirs(outdir, exist_ok=True)

    engine_cfg = None
    if ext in AUDIO_EXT:
        engine, engine_cfg = engine_config.resolve(args)
        # backfill resolved values onto args so downstream reads stay simple
        if args.model is None:
            args.model = engine_cfg.get("whisper_model") or "small"
        if args.language is None:
            args.language = preferences.get_default("language") or "zh"
        lang = None if args.language in ("", "auto") else args.language

        def _log(msg):
            sys.stderr.write("[progress] %s\n" % msg)
            sys.stderr.flush()

        if engine == "cloud":
            _log("engine=cloud provider=%s base_url=%s model=%s" %
                 (engine_cfg.get("provider"), engine_cfg.get("base_url"), engine_cfg.get("model")))
            r = cloud_asr.transcribe_cloud(
                path,
                base_url=engine_cfg.get("base_url"),
                model=engine_cfg.get("model"),
                api_key=engine_cfg.get("api_key"),
                language=args.language or "zh",
                chunk_minutes=int(engine_cfg.get("chunk_minutes") or 10),
                log=_log,
                provider=engine_cfg.get("provider"))
        else:
            r = transcribe_audio(path, args.model, lang, args.words,
                                 decode=not args.no_decode)
        audio_ref = os.path.basename(path)
        if args.copy_audio and os.path.abspath(outdir) != os.path.dirname(path):
            shutil.copy2(path, os.path.join(outdir, audio_ref))
        doc = {"source": "audio", "engine": r.get("engine", "local"),
               "has_timestamps": r["has_ts"], "has_speakers": r["has_spk"],
               "language": r.get("language", args.language), "audio_file": audio_ref,
               "duration_sec": r.get("duration"), "segments": r["segments"]}
        if r.get("chunk_errors"):
            doc["chunk_errors"] = r["chunk_errors"]
    elif ext in TEXT_EXT:
        r = parse_text(path)
        if args.language is None:
            args.language = preferences.get_default("language") or "zh"
        doc = {"source": "text", "engine": "text",
               "has_timestamps": r["has_ts"], "has_speakers": r["has_spk"],
               "language": args.language, "audio_file": None, "duration_sec": None,
               "segments": r["segments"]}
    else:
        sys.stderr.write("ERROR: unsupported input type '%s'. Pass an audio file or text transcript.\n" % ext)
        sys.exit(2)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)

    if args.save_engine and engine_cfg:
        pinned = {
            "engine": engine_cfg.get("engine"),
            "whisper_model": engine_cfg.get("whisper_model") or args.model,
            "provider": engine_cfg.get("provider"),
            "cloud_base_url": engine_cfg.get("base_url"),
            "cloud_model": engine_cfg.get("model"),
            "chunk_minutes": engine_cfg.get("chunk_minutes"),
            "language": args.language,
        }
        for k, v in pinned.items():
            if v is None:
                continue
            if k in preferences.PROMOTABLE:
                try:
                    preferences.set_default(k, v)
                except ValueError:
                    pass
        pp = preferences.PREF_PATH
        print("pinned current effective config as defaults in %s" % pp)
        if engine_cfg.get("engine") == "cloud" and engine_cfg.get("api_key"):
            eng_path = os.path.join(preferences.SKILL_HOME, "engine.json")
            try:
                os.makedirs(preferences.SKILL_HOME, exist_ok=True)
                with open(eng_path, "w", encoding="utf-8") as f:
                    json.dump({"provider": engine_cfg.get("provider"),
                               "api_key": engine_cfg.get("api_key"),
                               "saved_at": __import__("datetime").datetime.now().astimezone().isoformat(timespec="seconds")},
                              f, ensure_ascii=False, indent=2)
                try:
                    os.chmod(eng_path, 0o600)
                except Exception:
                    pass
                print("  api_key written to %s — plaintext on disk. On shared machines "
                      "prefer env var TRACE_ASR_API_KEY." % eng_path)
            except Exception as e:
                sys.stderr.write("  WARN: failed to persist api_key: %s\n" % e)

    # self-evolving: feed explicit CLI choices into the observation log.
    # Only explicit args were captured (see _explicit above), so inherited
    # defaults do not reinforce themselves.
    if _explicit and ext in AUDIO_EXT:
        promotions = []
        for k, v in _explicit.items():
            try:
                p = preferences.observe(k, v, context="cmd=normalize_transcript")
                if p:
                    promotions.append(p)
            except Exception as e:
                sys.stderr.write("  WARN: preference observe failed for %s: %s\n" % (k, e))
        for p in promotions:
            print("  [promoted] %s -> %r (from %d consecutive; was %r) — 想改说 preferences.py clear %s"
                  % (p["key"], p["value"], p["from_count"], p["prev_value"], p["key"]))

    n = len(doc["segments"])
    print("transcript.json written: %s" % args.out)
    print("  source=%s engine=%s segments=%d has_timestamps=%s has_speakers=%s audio=%s" %
          (doc["source"], doc.get("engine", "local"), n,
           doc["has_timestamps"], doc["has_speakers"], doc["audio_file"]))
    if doc.get("chunk_errors"):
        print("  WARN: %d cloud chunk(s) failed: %s" %
              (len(doc["chunk_errors"]), "; ".join(doc["chunk_errors"])[:200]))
    if not doc["has_timestamps"]:
        print("  WARN: no timestamps detected -> traceability degrades to verbatim quotes only.")
    dur = doc.get("duration_sec")
    if dur and doc["segments"]:
        covered = max(s.get("end") or 0 for s in doc["segments"])
        if covered < dur * 0.8:
            print("  WARN: transcript covers only %.0fs of %.0fs (%.0f%%). Likely decode "
                  "truncation -> ensure ffmpeg is on PATH (the script pre-decodes to wav)."
                  % (covered, dur, covered / dur * 100))


if __name__ == "__main__":
    main()
