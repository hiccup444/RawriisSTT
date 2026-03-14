"""Vosk model management — download and cache detection."""

from __future__ import annotations

import logging
import os
import sys
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

logger = logging.getLogger(__name__)


def _models_dir() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home()))
    else:
        base = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    return base / "RawriisSTT" / "vosk_models"


@dataclass(frozen=True)
class VoskModelInfo:
    key: str       # short identifier used throughout the app
    display: str   # human label shown in the UI
    size_mb: int   # approximate download size in MB
    url: str       # direct download URL (.zip)
    dir_name: str  # top-level directory name inside the zip


MODELS: list[VoskModelInfo] = [
    VoskModelInfo(
        key="small-en-us-0.15",
        display="Small English (0.15)",
        size_mb=40,
        url="https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip",
        dir_name="vosk-model-small-en-us-0.15",
    ),
]


def get_model_dir(key: str) -> Path:
    """Return the expected path to the extracted model directory."""
    info = _get_info(key)
    if info is None:
        raise ValueError(f"Unknown Vosk model key: {key!r}")
    return _models_dir() / info.dir_name


def is_model_cached(key: str) -> bool:
    """Return True if the model directory exists and contains files."""
    try:
        path = get_model_dir(key)
        return path.is_dir() and any(path.iterdir())
    except (ValueError, OSError):
        return False


def get_model_path(key: str) -> Optional[str]:
    """Return the absolute path string for the model, or None if not cached."""
    try:
        path = get_model_dir(key)
        return str(path) if path.is_dir() and any(path.iterdir()) else None
    except (ValueError, OSError):
        return None


def get_cached_size_mb(key: str) -> Optional[float]:
    """Return the on-disk size in MB for a cached model, or None."""
    try:
        path = get_model_dir(key)
        if not path.is_dir():
            return None
        total = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
        return round(total / 1_048_576, 1)
    except (ValueError, OSError):
        return None


def download_model(
    key: str,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> None:
    """Download and extract a Vosk model zip into the managed cache directory."""
    info = _get_info(key)
    if info is None:
        raise ValueError(f"Unknown Vosk model key: {key!r}")

    dest_dir = _models_dir()
    dest_dir.mkdir(parents=True, exist_ok=True)
    zip_path = dest_dir / f"{info.dir_name}.zip"

    if progress_callback:
        progress_callback(f"Downloading {info.display} (~{info.size_mb} MB)…")

    try:
        urllib.request.urlretrieve(info.url, zip_path)
    except Exception as exc:
        if zip_path.exists():
            zip_path.unlink()
        raise RuntimeError(f"Download failed: {exc}") from exc

    if progress_callback:
        progress_callback("Extracting…")

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(dest_dir)
    except Exception as exc:
        raise RuntimeError(f"Extraction failed: {exc}") from exc
    finally:
        if zip_path.exists():
            zip_path.unlink()

    if progress_callback:
        progress_callback(f"{info.display} ready.")


def delete_model(key: str) -> None:
    """Delete the cached model directory."""
    import shutil
    path = get_model_dir(key)
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)


def _get_info(key: str) -> Optional[VoskModelInfo]:
    for m in MODELS:
        if m.key == key:
            return m
    return None
