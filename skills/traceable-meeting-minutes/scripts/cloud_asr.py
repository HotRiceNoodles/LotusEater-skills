# -*- coding: utf-8 -*-
"""Cloud ASR via an OpenAI-compatible /audio/transcriptions endpoint.

Chosen because the same one-liner works against OpenAI (whisper-1),
SiliconFlow, Groq, Together, DeepInfra, self-hosted vLLM/WhisperX, etc.
No provider SDK dependency — pure `requests` + `ffmpeg` for chunking.

Long-audio handling: OpenAI caps a request at 25MB; SiliconFlow is more
generous but still finite. We re-encode to compact mono 32kbps mp3 segments
(default 10 min each) and stitch results back with a per-chunk time offset.
Individual chunk failures retry up to N times with exponential backoff; a chunk
that ultimately fails is recorded in `chunk_errors` and does NOT abort the run.

Public entry: transcribe_cloud(...) -> dict, matching the shape that
transcribe_audio() returns so downstream is engine-agnostic.
"""

import json
import os
import shutil
import subprocess
import sys
import time


PROVIDER_DEFAULTS = {
    "openai":      {"base_url": "https://api.openai.com/v1",
                    "model": "whisper-1",
                    "chunk_minutes": 10, "max_mb": 25},
    "siliconflow": {"base_url": "https://api.siliconflow.cn/v1",
                    "model": "funan-ai/Whisper-large-v3",
                    "chunk_minutes": 15, "max_mb": 100},
    "custom":      {"base_url": None,
                    "model": None,
                    "chunk_minutes": 10, "max_mb": 25},
}


def _import_requests():
    try:
        import requests
        return requests
    except Exception as e:
        sys.stderr.write(
            "ERROR: cloud ASR needs the `requests` library.\n"
            "Install: python -m pip install -r %s\n"
            "Details: %s\n" % (os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "requirements.txt"), e))
        raise


def _duration(path):
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


def _chunk_audio(src, workdir, chunk_seconds):
    """Split src into uniform 32kbps mono mp3 chunks under API size limits."""
    os.makedirs(workdir, exist_ok=True)
    pat = os.path.join(workdir, "chunk_%03d.mp3")
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", src,
         "-c:a", "libmp3lame", "-b:a", "32k", "-ac", "1",
         "-f", "segment", "-segment_time", str(int(chunk_seconds)), pat],
        capture_output=True, timeout=1800, check=True)
    names = sorted(n for n in os.listdir(workdir)
                   if n.startswith("chunk_") and n.endswith(".mp3"))
    return [(i * chunk_seconds, os.path.join(workdir, n)) for i, n in enumerate(names)]


def _post_one(chunk_path, base_url, model, api_key, language, timeout=300):
    requests = _import_requests()
    url = base_url.rstrip("/") + "/audio/transcriptions"
    data = {"model": model, "response_format": "verbose_json"}
    if language:
        data["language"] = language
    with open(chunk_path, "rb") as fh:
        files = {"file": (os.path.basename(chunk_path), fh, "audio/mpeg")}
        headers = {"Authorization": "Bearer " + api_key}
        r = requests.post(url, headers=headers, data=data, files=files, timeout=timeout)
    if r.status_code != 200:
        raise RuntimeError("HTTP %s: %s" % (r.status_code, r.text[:250]))
    try:
        return r.json()
    except ValueError as e:
        raise RuntimeError("non-JSON response: %s" % e)


def _with_retry(chunk_path, base_url, model, api_key, language, retries, log):
    last = None
    for attempt in range(retries):
        try:
            return _post_one(chunk_path, base_url, model, api_key, language)
        except Exception as e:
            last = e
            if log:
                log("cloud retry %d/%d: %s" % (attempt + 1, retries, str(e)[:100]))
            if attempt < retries - 1:
                time.sleep(1.5 * (2 ** attempt))
    raise RuntimeError("all %d attempts failed: %s" % (retries, last))


def _normalize_segs(payload, offset=0.0):
    out = []
    for s in payload.get("segments") or []:
        try:
            start = float(s.get("start") or 0) + offset
            end = float(s.get("end") or 0) + offset
        except Exception:
            continue
        text = (s.get("text") or "").strip()
        if not text:
            continue
        out.append({"start": round(start, 2), "end": round(end, 2), "text": text})
    return out


def transcribe_cloud(path, base_url, model, api_key, language="zh",
                     chunk_minutes=10, workdir=None, retries=3, log=None,
                     provider=None):
    """Main entry. Returns dict compatible with normalize_transcript.transcribe_audio."""
    if not base_url or not model or not api_key:
        raise RuntimeError(
            "cloud ASR needs base_url + model + api_key. "
            "Configure via --provider/--base-url/--cloud-model/--api-key, "
            "or env TRACE_ASR_API_KEY. See SKILL.md.")
    if provider:
        d = PROVIDER_DEFAULTS.get(provider, {})
        base_url = base_url or d.get("base_url")
        model = model or d.get("model")
        chunk_minutes = chunk_minutes or d.get("chunk_minutes", 10)
    duration = _duration(path)
    if duration is None:
        raise RuntimeError("cannot probe audio duration; is ffprobe on PATH?")
    size_mb = os.path.getsize(path) / (1024 * 1024)
    threshold_mb = PROVIDER_DEFAULTS.get(provider or "custom", {}).get("max_mb", 25) * 0.9

    segs_raw = []
    chunk_errors = []
    if size_mb <= threshold_mb and duration <= chunk_minutes * 60 + 30:
        if log:
            log("cloud single-shot upload %.0fMB / %.0fs" % (size_mb, duration))
        payload = _with_retry(path, base_url, model, api_key, language, retries, log)
        segs_raw = _normalize_segs(payload, offset=0.0)
        provider_lang = payload.get("language") or language
        provider_dur = payload.get("duration")
    else:
        if workdir is None:
            workdir = os.path.splitext(path)[0] + ".asrchunks"
        cs = max(60, int(chunk_minutes * 60))
        n_expected = int(duration / cs) + 1
        if log:
            log("cloud chunking into ~%d x %dmin pieces" % (n_expected, chunk_minutes))
        chunks = _chunk_audio(path, workdir, cs)
        provider_lang = language
        provider_dur = None
        for off, cp in chunks:
            try:
                payload = _with_retry(cp, base_url, model, api_key, language, retries, log)
                for s in _normalize_segs(payload, offset=off):
                    segs_raw.append(s)
                if log:
                    log("cloud chunk @%ds ok" % off)
            except Exception as e:
                chunk_errors.append("chunk@%ds: %s" % (off, str(e)[:120]))
                if log:
                    log("cloud chunk @%ds FAILED -> recorded, continuing" % off)
        try:
            shutil.rmtree(workdir)
        except Exception:
            pass

    segments = []
    for s in segs_raw:
        segments.append({"i": len(segments), "start": s["start"], "end": s["end"],
                         "speaker": "未知", "text": s["text"]})
    return {"segments": segments, "has_ts": True, "has_spk": False,
            "language": provider_lang,
            "duration": float(provider_dur) if provider_dur else duration,
            "engine": "cloud",
            "chunk_errors": chunk_errors}
