"""Whisper model management — cache detection and controlled downloads."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

logger = logging.getLogger(__name__)

# faster-whisper stores models under the standard HuggingFace cache.
# Repo IDs follow the pattern:  Systran/faster-whisper-{size}
_HF_CACHE = Path.home() / ".cache" / "huggingface" / "hub"

# "large" is an alias for large-v2 in faster-whisper
_REPO_MAP: dict[str, str] = {
    "tiny":     "Systran/faster-whisper-tiny",
    "base":     "Systran/faster-whisper-base",
    "small":    "Systran/faster-whisper-small",
    "medium":   "Systran/faster-whisper-medium",
    "large":    "Systran/faster-whisper-large-v2",
    "large-v3": "Systran/faster-whisper-large-v3",
}


@dataclass(frozen=True)
class ModelInfo:
    key: str          # key used by faster-whisper (e.g. "base")
    display: str      # human label shown in UI
    size_mb: int      # approximate download size in MB
    repo_id: str      # HuggingFace repo


MODELS: list[ModelInfo] = [
    ModelInfo("tiny",     "Tiny",      75,   _REPO_MAP["tiny"]),
    ModelInfo("base",     "Base",      145,  _REPO_MAP["base"]),
    ModelInfo("small",    "Small",     480,  _REPO_MAP["small"]),
    ModelInfo("medium",   "Medium",    1500, _REPO_MAP["medium"]),
    ModelInfo("large",    "Large v2",  3000, _REPO_MAP["large"]),
    ModelInfo("large-v3", "Large v3",  3000, _REPO_MAP["large-v3"]),
]


def _model_cache_dir(repo_id: str) -> Path:
    """Return the HuggingFace cache directory for a given repo."""
    return _HF_CACHE / ("models--" + repo_id.replace("/", "--"))


def get_model_path(model_key: str) -> Optional[str]:
    """Return the absolute path to the cached model snapshot directory.

    Passing this path directly to WhisperModel avoids any network requests.
    Returns None if the model is not cached.
    """
    info = _get_info(model_key)
    if info is None:
        return None
    cache_dir = _model_cache_dir(info.repo_id)
    for model_bin in cache_dir.glob("snapshots/*/model.bin"):
        return str(model_bin.parent)
    return None


def is_model_cached(model_key: str) -> bool:
    """Return True if the model is fully present in the local HF cache."""
    info = _get_info(model_key)
    if info is None:
        return False
    cache_dir = _model_cache_dir(info.repo_id)
    if not cache_dir.exists():
        return False
    # A downloaded snapshot always has at least model.bin
    return any(cache_dir.glob("snapshots/*/model.bin"))


def get_cached_size_mb(model_key: str) -> Optional[float]:
    """Return the on-disk size in MB for a cached model, or None if not cached."""
    info = _get_info(model_key)
    if info is None:
        return None
    cache_dir = _model_cache_dir(info.repo_id)
    if not cache_dir.exists():
        return None
    total = sum(f.stat().st_size for f in cache_dir.rglob("*") if f.is_file())
    return round(total / 1_048_576, 1)


def download_model(
    model_key: str,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> None:
    """Download a Whisper model to the HF cache.

    Args:
        model_key: One of "tiny", "base", "small", "medium", "large", "large-v3".
        progress_callback: Called with a status string during download.
    """
    import io
    import os
    import sys

    info = _get_info(model_key)
    if info is None:
        raise ValueError(f"Unknown Whisper model key: {model_key!r}")

    if progress_callback:
        progress_callback(f"Downloading {info.display} (~{info.size_mb} MB)…")

    # huggingface_hub uses tqdm which writes to sys.stdout/sys.stderr.
    # In a PyInstaller frozen app (console=False) these are None, which causes
    # "'NoneType' object has no attribute 'write'". Fix: disable HF progress bars
    # and ensure stdout/stderr are not None before the download call.
    os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
    _null = io.StringIO()
    _old_stdout = sys.stdout
    _old_stderr = sys.stderr
    if sys.stdout is None:
        sys.stdout = _null
    if sys.stderr is None:
        sys.stderr = _null

    try:
        from huggingface_hub import snapshot_download

        snapshot_download(
            repo_id=info.repo_id,
            local_files_only=False,
        )
        if progress_callback:
            progress_callback(f"{info.display} downloaded successfully.")
    except Exception as exc:
        logger.exception("Model download failed: %s", exc)
        raise
    finally:
        sys.stdout = _old_stdout
        sys.stderr = _old_stderr


def _get_info(model_key: str) -> Optional[ModelInfo]:
    for m in MODELS:
        if m.key == model_key:
            return m
    return None
