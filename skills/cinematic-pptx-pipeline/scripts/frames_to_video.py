"""Build a video from per-slide staged frames via ffmpeg xfade.

Each slide's frames encode a cascade: frame 0 shows only the background (picture
shapes); frame k adds the k-th non-picture shape on top. We chain frames with
`xfade` so each element fades in over `fade` seconds, holds for `step-fade`
seconds, then the next fades in. Between slides we crossfade.

Key ffmpeg gotcha (the whole reason this script exists):
  xfade's `offset` is the START TIME of the SECOND input in the first input's
  timeline, NOT a transition-start offset. With equal per-input duration D and
  fade F, the correct offset for the k-th transition (k >= 1) is
      offset_k = k * (D - F)
  NOT k*D - F. The wrong formula silently truncates the chain (later frames
  dropped; output ends at the last offset). See ../references/video-export.md.

Usage:
  python frames_to_video.py --frames-dir FRAMES [--prefix slide] --info INFO \
      --clips-dir CLIPS --out OUT [--step-d 0.22 --fade 0.10 --hold 2.0 \
      --transition 0.5 --fps 30]
"""

import argparse
import os
import re
import subprocess
import sys


def find_ffmpeg():
    env = os.environ.get("FFMPEG")
    if env and os.path.exists(env):
        return env
    # PATH lookup
    from shutil import which
    p = which("ffmpeg")
    if p:
        return p
    print("ERROR: ffmpeg not found. Set --ffmpeg or FFMPEG or install ffmpeg.",
          file=sys.stderr)
    sys.exit(2)


def run(cmd):
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       text=True)
    if r.returncode != 0:
        sys.stderr.write("CMD FAILED:\n" + " ".join(cmd[:6]) + " ...\n")
        sys.stderr.write(r.stderr[-2000:] + "\n")
        sys.exit("ffmpeg failed")


def read_info(path, prefix):
    """Parse 'NN=N' lines (with optional BOM/trailing whitespace).

    Returns dict { '01': 11, ... } and sorted key list.
    """
    counts = {}
    pat = re.compile(r"^[\ufeff\s]*(\d+)\s*=\s*(\d+)\s*$")
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            m = pat.match(line)
            if m:
                counts[m.group(1).zfill(2)] = int(m.group(2))
    ids = sorted(counts.keys())
    if not ids:
        sys.exit(f"info file empty: {path}")
    return counts, ids


def build_clip(ff, frames_dir, prefix, sid, N, D, F, HOLD, FPS, out_path):
    M = N + 1
    imgs = [os.path.join(frames_dir,
                         f"{prefix}{sid}_{k:03d}.png") for k in range(M)]
    for p in imgs:
        if not os.path.exists(p):
            sys.exit(f"missing frame {p}")
    cmd = [ff, "-y"]
    for i, p in enumerate(imgs):
        dur = D + HOLD if i == M - 1 else D
        cmd += ["-loop", "1", "-framerate", str(FPS), "-t", f"{dur:.3f}", "-i", p]
    parts = []
    prev = "0:v"
    # CORRECT xfade formula: offset_k = k*(D-F); see module docstring.
    for k in range(1, M):
        off = k * (D - F)
        out_label = f"v{k}"
        parts.append(f"[{prev}][{k}:v]xfade=transition=fade:"
                     f"duration={F}:offset={off:.3f}[{out_label}]")
        prev = out_label
    cmd += ["-filter_complex", ";".join(parts), "-map", f"[{prev}]",
            "-r", str(FPS), "-pix_fmt", "yuv420p",
            "-c:v", "libx264", "-crf", "18", "-preset", "medium", out_path]
    run(cmd)
    return M * D + HOLD - (M - 1) * F  # analytical, matches ffmpeg output


def concat_clips(ff, clip_paths, clip_durs, FT, FPS, out_path):
    cmd = [ff, "-y"]
    for cp in clip_paths:
        cmd += ["-i", cp]
    parts = []
    prev = "0:v"
    cum = 0.0
    for k in range(1, len(clip_paths)):
        cum += clip_durs[k - 1]
        off = cum - k * FT
        out_label = f"x{k}"
        parts.append(f"[{prev}][{k}:v]xfade=transition=fade:"
                     f"duration={FT}:offset={off:.3f}[{out_label}]")
        prev = out_label
    cmd += ["-filter_complex", ";".join(parts), "-map", f"[{prev}]",
            "-r", str(FPS), "-pix_fmt", "yuv420p",
            "-c:v", "libx264", "-crf", "18", "-preset", "medium", out_path]
    run(cmd)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames-dir", required=True)
    ap.add_argument("--info", required=True)
    ap.add_argument("--clips-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--prefix", default="slide")
    ap.add_argument("--step-d", type=float, default=0.22,
                    help="per-element step duration (s); D > fade")
    ap.add_argument("--fade", type=float, default=0.10,
                    help="intra-slide fade between elements (s)")
    ap.add_argument("--hold", type=float, default=2.0,
                    help="extra hold on each slide's final frame (s)")
    ap.add_argument("--transition", type=float, default=0.5,
                    help="inter-slide crossfade (s)")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--ffmpeg", default=None)
    args = ap.parse_args()

    if args.fade >= args.step_d:
        sys.exit("--fade must be < --step-d")

    ff = args.ffmpeg or find_ffmpeg()
    os.makedirs(args.clips_dir, exist_ok=True)

    counts, ids = read_info(args.info, args.prefix)
    clip_paths = []
    clip_durs = []
    for sid in ids:
        N = counts[sid]
        cp = os.path.join(args.clips_dir, f"clip_{sid}.mp4")
        clip_paths.append(cp)
        L = build_clip(ff, args.frames_dir, args.prefix, sid, N,
                       args.step_d, args.fade, args.hold, args.fps, cp)
        clip_durs.append(L)
        print(f"clip {sid}: N={N} dur={L:.2f}s")

    concat_clips(ff, clip_paths, clip_durs, args.transition, args.fps, args.out)
    total = sum(clip_durs) - (len(clip_paths) - 1) * args.transition
    print(f"FINAL: {args.out}")
    print(f"estimated duration={total:.2f}s ({total/60:.1f} min)")


if __name__ == "__main__":
    main()