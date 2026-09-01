# -*- coding: utf-8 -*-
"""Self-evolving preferences for the traceable-meeting-minutes skill.

Layered design (see SKILL.md step 0):
  1. observations  — append-only log of every EXPLICIT choice the user made
                     (defaults applied silently never re-observe, to avoid
                     feedback loops).
  2. promotion     — if the same key has taken the same value in the last
                     N consecutive observations (default 3) AND that value
                     differs from current default, promote it to `defaults`.
                     Emit a `promoted` entry so agent can surface one line to
                     the user: "已按你最近 N 次选择把 X 设为 Y".
  3. defaults      — the effective values read at run time; any key present
                     here means "don't ask, just use".

Storage: ~/.traceable-meeting-minutes/preferences.json (platform-agnostic).
Platform detection (see detect_platform) runs on first use and only affects
how the agent phrases delivery in chat — never where files are stored.
Backwards-compat: on first load, if a legacy engine.json exists (either in
the new home or under ~/.qwenworkcn/traceable-minutes) and preferences.json
does not, migrate `engine/provider/base_url/model/chunk_minutes` into
defaults. Legacy files are left alone (never deleted here).

Security: this file never stores `api_key` in `observations`. Any explicit CLI
`--api-key` values are used at runtime only. Defaults dict CAN carry
non-secret cloud config (provider/base_url/chunk_minutes) but NOT api_key.
"""
from __future__ import annotations
import json
import os
import sys
import tempfile
from datetime import datetime

SKILL_HOME = os.path.join(os.path.expanduser("~"), ".traceable-meeting-minutes")
PREF_PATH = os.path.join(SKILL_HOME, "preferences.json")
LEGACY_ENGINE_PATH = os.path.join(SKILL_HOME, "engine.json")
# pre-generalization location kept for one-shot migration reads only
_QWENWORK_LEGACY_HOME = os.path.join(os.path.expanduser("~"), ".qwenworkcn", "traceable-minutes")

# Keys that participate in promotion (values here NEVER include api_key)
PROMOTABLE = {
    "engine", "provider", "cloud_base_url", "cloud_model", "whisper_model",
    "language", "chunk_minutes",
    "output_html", "output_markdown", "output_ledger_csv", "output_word",
    "output_transcript_readable", "output_html_title_from_meeting",
    "audit_limiter_words", "audit_token_candidates", "audit_critical_missing_only",
    "ledger_density_target",
}
DEFAULT_THRESHOLD = 3

_EMPTY = {"version": 1, "threshold": DEFAULT_THRESHOLD,
          "defaults": {}, "observations": [], "promoted": []}


def detect_platform():
    """Best-effort detection of the host agent platform. Recorded once in
    preferences.json so delivery phrasing can adapt (e.g. list files in chat
    vs. call a platform file-presentation tool). Falls back to 'generic'."""
    if os.environ.get("CLAUDECODE") or os.environ.get("CLAUDE_CODE_ENTRYPOINT"):
        return "claude-code"
    if os.environ.get("QWENWORK") or os.environ.get("QWENWORK_ENTRYPOINT"):
        return "qwenwork"
    return "generic"


def platform():
    """Cached platform id (persisted on first call, then reused)."""
    cfg = load()
    p = cfg.get("platform")
    if p:
        return p
    p = detect_platform()
    cfg["platform"] = p
    save(cfg)
    return p


def _now():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _atomic_write(path, obj):
    d = os.path.dirname(path)
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".pref.", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
        try:
            os.chmod(path, 0o600)
        except Exception:
            pass
    finally:
        if os.path.isfile(tmp):
            try:
                os.remove(tmp)
            except Exception:
                pass


def _migrate_legacy(cfg):
    if os.path.isfile(PREF_PATH):
        return cfg
    candidates = [LEGACY_ENGINE_PATH,
                  os.path.join(_QWENWORK_LEGACY_HOME, "engine.json")]
    for legacy_path in candidates:
        if not os.path.isfile(legacy_path):
            continue
        try:
            legacy = json.load(open(legacy_path, encoding="utf-8"))
            for k_src, k_dst in (("engine", "engine"), ("provider", "provider"),
                                 ("base_url", "cloud_base_url"), ("model", "cloud_model"),
                                 ("chunk_minutes", "chunk_minutes"),
                                 ("whisper_model", "whisper_model")):
                v = legacy.get(k_src)
                if v is not None and k_dst not in cfg["defaults"]:
                    cfg["defaults"][k_dst] = v
        except Exception:
            pass
    return cfg


def load():
    if not os.path.isfile(PREF_PATH):
        cfg = dict(_EMPTY)
        cfg = _migrate_legacy(cfg)
        if cfg["defaults"]:
            _atomic_write(PREF_PATH, cfg)
        return cfg
    try:
        with open(PREF_PATH, encoding="utf-8") as f:
            cfg = json.load(f)
    except Exception:
        return dict(_EMPTY)
    if not isinstance(cfg, dict):
        return dict(_EMPTY)
    for k, v in _EMPTY.items():
        cfg.setdefault(k, v if not isinstance(v, (list, dict)) else type(v)())
    return cfg


def save(cfg):
    _atomic_write(PREF_PATH, cfg)
    return PREF_PATH


def get_default(key):
    return load().get("defaults", {}).get(key)


def observe(key, value, context=None):
    """Append an observation. Returns a `promoted` entry dict if a promotion
    just happened for this key, else None."""
    if key not in PROMOTABLE:
        return None
    if key == "api_key":  # belt-and-suspenders; api_key is not in PROMOTABLE anyway
        return None
    cfg = load()
    obs = cfg["observations"]
    # don't re-append if last observation of same key has identical value within
    # a 60s window (guards against multi-step scripts calling observe twice)
    if obs:
        last_same = next((o for o in reversed(obs) if o["key"] == key), None)
        if last_same and last_same.get("value") == value:
            try:
                dt_last = datetime.fromisoformat(last_same["at"])
                if (datetime.now().astimezone() - dt_last).total_seconds() < 60:
                    return None
            except Exception:
                pass
    obs.append({"key": key, "value": value, "at": _now(), "context": context})
    # keep log bounded
    if len(obs) > 500:
        cfg["observations"] = obs[-500:]
    promoted = _maybe_promote(cfg, key)
    save(cfg)
    return promoted


def _maybe_promote(cfg, key):
    """If last N observations of `key` are all same value and differ from
    current default, promote."""
    n = int(cfg.get("threshold") or DEFAULT_THRESHOLD)
    if n < 2:
        return None
    tail = [o["value"] for o in cfg["observations"] if o["key"] == key][-n:]
    if len(tail) < n:
        return None
    if any(v is None for v in tail) or len(set(map(_hashable, tail))) != 1:
        return None
    new_val = tail[0]
    cur = cfg["defaults"].get(key)
    if cur == new_val:
        return None
    cfg["defaults"][key] = new_val
    entry = {"key": key, "value": new_val, "at": _now(),
             "from_count": n, "prev_value": cur}
    cfg["promoted"] = (cfg.get("promoted") or [])[-99:] + [entry]
    return entry


def _hashable(v):
    try:
        hash(v)
        return v
    except TypeError:
        return json.dumps(v, sort_keys=True, ensure_ascii=False)


def set_default(key, value):
    if key not in PROMOTABLE:
        raise ValueError("not a promotable key: %s" % key)
    cfg = load()
    cfg["defaults"][key] = value
    save(cfg)
    return value


def clear_default(key):
    cfg = load()
    if key in cfg["defaults"]:
        v = cfg["defaults"].pop(key)
        save(cfg)
        return v
    return None


def reset_all():
    if os.path.isfile(PREF_PATH):
        os.remove(PREF_PATH)
    return True


# ---------- CLI ----------
def _cli():
    import argparse
    ap = argparse.ArgumentParser(description="Preferences for traceable-meeting-minutes.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("show")
    g = sub.add_parser("get"); g.add_argument("key")
    s = sub.add_parser("set"); s.add_argument("key"); s.add_argument("value")
    c = sub.add_parser("clear"); c.add_argument("key")
    r = sub.add_parser("reset")
    o = sub.add_parser("observe"); o.add_argument("key"); o.add_argument("value")
    o.add_argument("--context", default=None)
    args = ap.parse_args()
    if args.cmd == "show":
        cfg = load()
        cfg.setdefault("platform", platform())
        print(json.dumps(cfg, ensure_ascii=False, indent=2))
    elif args.cmd == "get":
        v = get_default(args.key)
        if v is not None:
            print(v)
    elif args.cmd == "set":
        # coerce obvious numeric/boolean strings
        raw = args.value
        val = raw
        if raw.lower() in ("true", "false"):
            val = raw.lower() == "true"
        else:
            try: val = int(raw)
            except ValueError:
                try: val = float(raw)
                except ValueError: pass
        set_default(args.key, val)
        print("set %s = %r" % (args.key, val))
    elif args.cmd == "clear":
        v = clear_default(args.key)
        print("cleared %s (was %r)" % (args.key, v))
    elif args.cmd == "reset":
        reset_all()
        print("all preferences reset")
    elif args.cmd == "observe":
        p = observe(args.key, args.value, args.context)
        if p:
            print("PROMOTED %s -> %s (from %d consecutive)" % (p["key"], p["value"], p["from_count"]))
        else:
            print("observed %s = %s" % (args.key, args.value))


if __name__ == "__main__":
    _cli()
