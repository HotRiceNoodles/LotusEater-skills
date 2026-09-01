# -*- coding: utf-8 -*-
"""Engine config: thin adapter over the self-evolving preferences store.

resolve(args) priority (highest first):
  1. explicit CLI flag (only if truthy and not 'auto')
  2. env override — TRACE_ASR_API_KEY / TRACE_ASR_BASE_URL / TRACE_ASR_MODEL
  3. preferences.defaults (self-evolving, see preferences.py)
  4. hardcoded fallback (engine=local, whisper_model=small, chunk_minutes=10)

Legacy engine.json is auto-migrated into preferences.defaults on first
preferences.load(); this module no longer writes engine.json directly.
`save()` is kept as a compat shim that forwards to preferences.set_default.
"""
import json
import os

try:
    from . import preferences
except ImportError:
    import preferences

LEGACY_ENGINE_PATH = os.path.join(preferences.SKILL_HOME, "engine.json")


def _legacy_api_key():
    """Read api_key from legacy engine.json if present (persisted via --save-engine).
    Checks both the current home and the pre-generalization ~/.qwenworkcn location."""
    for path in (LEGACY_ENGINE_PATH, getattr(preferences, "_QWENWORK_LEGACY_HOME", None) and
                 os.path.join(preferences._QWENWORK_LEGACY_HOME, "engine.json")):
        if not path:
            continue
        try:
            with open(path, encoding="utf-8") as f:
                key = json.load(f).get("api_key")
                if key:
                    return key
        except Exception:
            continue
    return None


def load():
    """Deprecated: use preferences.load()['defaults'] directly. Kept for compat."""
    return preferences.load().get("defaults", {})


def save(cfg):
    """Deprecated: writing goes through preferences.set_default. Kept for compat."""
    for k, v in (cfg or {}).items():
        if k in preferences.PROMOTABLE:
            try:
                preferences.set_default(k, v)
            except ValueError:
                pass
    return preferences.PREF_PATH


def resolve(args):
    """Return (engine_name, effective_config)."""
    d = preferences.load().get("defaults", {}) or {}

    def pick(cli_val, key, fallback=None):
        if cli_val not in (None, "", "auto"):
            return cli_val
        if key in d and d[key] not in (None, ""):
            return d[key]
        return fallback

    engine = pick(getattr(args, "engine", None), "engine", "local")
    whisper_model = pick(getattr(args, "model", None), "whisper_model", "small")
    provider = pick(getattr(args, "provider", None), "provider")
    base_url = pick(getattr(args, "base_url", None), "cloud_base_url")
    cloud_model = pick(getattr(args, "cloud_model", None), "cloud_model")
    chunk_minutes = pick(getattr(args, "chunk_minutes", None), "chunk_minutes", 10)
    api_key = getattr(args, "api_key", None)  # never sourced from preferences.defaults
    if not api_key:
        api_key = _legacy_api_key()  # fall back to engine.json persisted via --save-engine

    if os.environ.get("TRACE_ASR_API_KEY"):
        api_key = os.environ["TRACE_ASR_API_KEY"]
    if os.environ.get("TRACE_ASR_BASE_URL"):
        base_url = os.environ["TRACE_ASR_BASE_URL"]
    if os.environ.get("TRACE_ASR_MODEL"):
        cloud_model = os.environ["TRACE_ASR_MODEL"]

    out = {
        "engine": engine,
        "whisper_model": whisper_model,
        "provider": provider,
        "base_url": base_url,
        "model": cloud_model,
        "api_key": api_key,
        "chunk_minutes": chunk_minutes,
    }
    if engine == "cloud":
        try:
            import cloud_asr
        except ImportError:
            cloud_asr = None
        if cloud_asr:
            prov = out.get("provider") or "openai"
            out["provider"] = prov
            dd = cloud_asr.PROVIDER_DEFAULTS.get(prov, {})
            out["base_url"] = out.get("base_url") or dd.get("base_url")
            out["model"] = out.get("model") or dd.get("model")
            if not out.get("chunk_minutes"):
                out["chunk_minutes"] = dd.get("chunk_minutes", 10)
    return engine, out
