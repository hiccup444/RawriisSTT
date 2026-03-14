"""Preset save/load for user workflow configurations.

Presets capture all per-session choices (microphone, engine, voice, etc.) but
deliberately exclude credentials (API keys) and infrastructure (OSC address/port,
dark mode) which are global and not workflow-specific.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Settings fields that are serialised into a preset.
# API keys, OSC network config, and UI prefs (dark mode, always-on-top) are excluded.
PRESET_KEYS: list[str] = [
    # Audio devices (stored by name so they survive device-index changes)
    "input_device",
    "tts_headphones_device",
    "tts_cable_device",
    # STT engine + Whisper options
    "stt_engine",
    "whisper_model",
    "whisper_language",
    "whisper_device",
    "whisper_input_mode",
    "ptt_key",
    "ptt_live_transcribe",
    # VAD / recording
    "vad_enabled",
    "silence_threshold_ms",
    "vad_aggressiveness",
    "max_record_seconds",
    # TTS
    "tts_enabled",
    "tts_voice_engine",
    "elevenlabs_voice_id",
    "elevenlabs_model_id",
    "elevenlabs_stability",
    "elevenlabs_similarity_boost",
    "elevenlabs_style",
    "elevenlabs_use_speaker_boost",
    # Chatbox / OSC behaviour
    "send_osc",
    "use_chatbox",
    "chatbox_play_notification",
    "ptt_sound_volume",
    # TTS playback behaviour
    "tts_delay_before_audio_ms",
    "tts_stop_on_new",
    "tts_queue_enabled",
    "tts_queue_delay_ms",
    "tts_smart_split",
    "tts_smart_split_limit",
]


def _presets_path() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home()))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "RawriisSTT" / "presets.json"


def load_presets() -> dict[str, dict[str, Any]]:
    """Return the saved presets dict, or {} if none exist yet."""
    path = _presets_path()
    if not path.exists():
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except Exception as exc:
        logger.warning("Could not load presets: %s", exc)
    return {}


def save_presets(presets: dict[str, dict[str, Any]]) -> None:
    path = _presets_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(presets, f, indent=2)
    except Exception as exc:
        logger.error("Could not save presets: %s", exc)


def preset_from_settings(settings) -> dict[str, Any]:
    """Snapshot the preset-eligible fields from an AppSettings instance."""
    return {key: getattr(settings, key) for key in PRESET_KEYS if hasattr(settings, key)}


def apply_preset_to_settings(preset: dict[str, Any], settings) -> None:
    """Write preset values back onto an AppSettings instance (in-place)."""
    for key in PRESET_KEYS:
        if key in preset:
            setattr(settings, key, preset[key])
