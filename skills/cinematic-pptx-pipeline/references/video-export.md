# Video Export (L4) — PPTX → MP4

Converts an **animated** PPTX (L3) into a faithful MP4 video. Each slide's
entrance cascade is reproduced element by element; slides are crossfaded.

## When to use

The user wants a video of the animated deck (for class playback, social, etc.),
or wants to embed the deck in a larger video, or PowerPoint's built-in
"Create Video" is unavailable / broken in the environment.

## Pipeline (two phases)

**Phase A — Per-slide staged frames (Windows, PowerPoint COM):**
For each slide, hide all non-picture shapes, export a PNG; then reveal shape 1
and export; then shape 2; ... until all visible. This produces a sequence of
frames where frame `k` shows the background plus the first k non-picture
shapes in z-order (i.e. the cascade state at step k). Script:

```powershell
powershell -File scripts/stage_export_frames.ps1 `
  -Src <L3.pptx> `
  -OutDir <frames-dir> `
  -InfoPath <info.txt> `
  -Prefix slide
```

**Phase B — Frame sequence → MP4 (cross-platform, ffmpeg):**
Chain the per-slide frames with `xfade` so each element fades in; then
crossfade between slides. Script:

```bash
python scripts/frames_to_video.py \
  --frames-dir <frames-dir> --info <info.txt> \
  --clips-dir <clips-dir> --out <final.mp4> \
  --step-d 0.22 --fade 0.10 --hold 2.0 --transition 0.5
```

Tune `--step-d` (per-element cadence) and `--hold` (reading pause) to taste.
Rule: `--fade < --step-d`.

## THE gotcha (read this before debugging)

ffmpeg's `xfade` `offset` is the **start time of the second input** in the
first input's timeline — NOT a transition-start offset. With equal per-input
duration D and fade F:

```
correct:   offset_k = k * (D - F)
WRONG:     offset_k = k * D - F    # silently truncates; output ends at the
                                   # last offset instead of the chain's tail
```

Symptom of the wrong formula: output duration is suspiciously small (e.g.
2.3s for a chain that should be 7s) and later frames / slides are silently
dropped. Validate with a 3-image minimal test (see `frames_to_video.py`
docstring).

The final label of any xfade chain MUST be mapped with `-map "[label]"` or
ffmpeg reports `Filter has output unconnected`.

## Platform / environment caveats

- **Phase A is Windows + PowerPoint COM only.** macOS / Linux have no
  PowerPoint; the cascade-stage trick needs the COM visibility API.
  Alternatives for those platforms: render the original HTML pages in a
  headless browser with CSS animations and record, or export frames from the
  HTML source directly (skip PPTX). This skill only ships the PowerPoint path.
- **PowerPoint source path must be ASCII.** A `.ps1` script file with Chinese
  path literals can be re-encoded at load time and trigger `Open` with
  HRESULT 0x8007007B. Copy the source pptx to an ASCII filename before
  running the script.
- **Run Phase A in the foreground**, not background. COM in a non-interactive
  session can crash with `0x800706BE` (RPC failed) after a few operations.
- **Read side: stage info file may be UTF-8 with BOM.** Use
  `encoding="utf-8-sig"` (`frames_to_video.py` already does).
- **PowerPoint COM `CreateVideo` is unreliable in sandboxed / partial Office
  installations** and fails immediately (status 3) even for trivial decks.
  Don't rely on it; this staged-export pipeline is the workaround.
- **Per-slide COM instance.** Opening one PowerPoint instance and exporting
  400 frames in one session is fragile (RPC death). The shipped script opens
  a fresh instance per slide and is resumable (skips slides whose first and
  last frames already exist).

## QA the produced video

```bash
ffprobe -v error -show_entries format=duration:stream=width,height,codec_name \
        -of default=noprint_wrappers=1 final.mp4
# extract frames at multiple timestamps and visually confirm the cascade
ffmpeg -ss <t> -i final.mp4 -frames:v 1 -q:v 2 frame_t<t>.png
```

Compare frames within the same slide at different times: they MUST differ
(proves the cascade is playing). Compare frames across slides: content must
match the original deck.

## Estimated effort

~600 PowerPoint Export calls take 5–8 min on a typical deck (depends on shapes
    per slide). The ffmpeg stage 1 produces 17 short clips and stage 2 joins
    them; combined another 1–3 min. Total ≈ 7–11 min for a 17-slide deck.