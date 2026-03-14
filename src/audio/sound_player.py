"""Non-blocking audio notification player using soundfile + sounddevice."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


def _find_asset(filename: str) -> Path:
    """Locate a bundled asset whether running frozen or from source."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "assets" / filename  # type: ignore[attr-defined]
    # Dev mode: assets/ sits at the project root (three levels above this file)
    return Path(__file__).parent.parent.parent / "assets" / filename


class SoundPlayer:
    """Plays short notification sounds from any thread.

    Audio data is decoded once at construction time and then replayed via
    sounddevice.play() — which is thread-safe and non-blocking.
    """

    def __init__(self, volume: float = 0.8) -> None:
        self.volume = max(0.0, min(1.0, volume))
        self._start: Optional[tuple[np.ndarray, int]] = None
        self._stop: Optional[tuple[np.ndarray, int]] = None
        self._load()

    def _load(self) -> None:
        try:
            import soundfile as sf
        except ImportError:
            logger.warning("soundfile not available — PTT sounds disabled.")
            return

        for attr, filename in (("_start", "PTT_start.mp3"), ("_stop", "PTT_stop.mp3")):
            path = _find_asset(filename)
            try:
                data, rate = sf.read(str(path), dtype="float32", always_2d=False)
                setattr(self, attr, (data, rate))
                logger.debug("Loaded sound: %s", path)
            except Exception as exc:
                logger.warning("Could not load %s: %s", path, exc)

    def play_start(self) -> None:
        self._play(self._start)

    def play_stop(self) -> None:
        self._play(self._stop)

    def set_volume(self, volume: float) -> None:
        self.volume = max(0.0, min(1.0, volume))

    def _play(self, sound: Optional[tuple[np.ndarray, int]]) -> None:
        if sound is None or self.volume == 0.0:
            return
        data, rate = sound
        try:
            import sounddevice as sd
            sd.play(data * self.volume, rate)
        except Exception as exc:
            logger.debug("Sound playback error: %s", exc)
