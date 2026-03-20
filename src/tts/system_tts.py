"""System TTS engine.

Uses pyttsx3 which maps to:
  - Windows: Microsoft SAPI5 (built-in, no install required)
  - Linux:   espeak / espeak-ng  (needs: sudo apt install espeak-ng)
  - macOS:   NSSpeechSynthesizer (built-in)

Audio is synthesized to a temporary WAV file and then played through
each requested sounddevice output device selector independently.
"""
from __future__ import annotations

import logging
import os
import tempfile
import threading
from typing import List, Optional

logger = logging.getLogger(__name__)


def speak_text(
    text: str,
    device_indices: List[Optional[int | str]],
    volume: float = 0.8,
) -> None:
    """Synthesize *text* and play it through every device in *device_indices*.

    Runs in a background daemon thread — returns immediately.
    ``None`` entries in *device_indices* are skipped.
    """
    active = [d for d in device_indices if d is not None]
    if not active or not text.strip():
        return
    thread = threading.Thread(
        target=_speak_worker,
        args=(text, active, volume),
        daemon=True,
        name="SystemTTS",
    )
    thread.start()


def _speak_worker(text: str, device_indices: List[int | str], volume: float) -> None:
    tmp_path: Optional[str] = None
    try:
        import pyttsx3
        import sounddevice as sd
        import soundfile as sf
    except ImportError as exc:
        logger.warning(
            "System TTS unavailable — install pyttsx3, sounddevice, soundfile: %s", exc
        )
        return

    try:
        # Synthesize to a temp WAV file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name

        engine = pyttsx3.init()
        try:
            engine.setProperty("volume", max(0.0, min(1.0, volume)))
            engine.save_to_file(text, tmp_path)
            engine.runAndWait()
        finally:
            engine.stop()

        # Read synthesized audio
        data, samplerate = sf.read(tmp_path, dtype="float32")

        if data.size == 0:
            logger.warning("TTS engine produced empty audio for: %r", text)
            return

        # Ensure 2-D (frames × channels)
        if data.ndim == 1:
            data = data.reshape(-1, 1)

        # Pre-query devices and prepare per-device audio (done on this thread before spawning)
        playback_tasks = []
        for device_selector in device_indices:
            try:
                dev_info = sd.query_devices(device_selector)
                out_channels = int(dev_info["max_output_channels"])
                if out_channels < 1:
                    logger.warning("Device %s has no output channels, skipping.", device_index)
                    continue
                if data.shape[1] == 1 and out_channels >= 2:
                    play_data = data.repeat(2, axis=1)
                elif data.shape[1] > out_channels:
                    play_data = data[:, :out_channels]
                else:
                    play_data = data
                playback_tasks.append((play_data, samplerate, device_selector))
            except Exception as exc:
                logger.warning("TTS device prep failed for device %s: %s", device_selector, exc)

        # Play to all devices concurrently
        threads = [
            threading.Thread(target=_play_on_device, args=task, daemon=True)
            for task in playback_tasks
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

    except Exception as exc:
        logger.exception("System TTS synthesis error: %s", exc)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


def _play_on_device(data, samplerate: int, device_selector: int | str) -> None:
    """Play *data* on a single output device, blocking until playback completes."""
    import sounddevice as sd

    done = threading.Event()
    idx = [0]

    def _cb(outdata, frames, _time, _status):
        remaining = len(data) - idx[0]
        if remaining == 0:
            outdata[:] = 0
            raise sd.CallbackStop
        chunk = min(frames, remaining)
        outdata[:chunk] = data[idx[0] : idx[0] + chunk]
        if chunk < frames:
            outdata[chunk:] = 0
        idx[0] += chunk

    try:
        with sd.OutputStream(
            samplerate=samplerate,
            channels=data.shape[1],
            dtype="float32",
            device=device_selector,
            callback=_cb,
            finished_callback=done.set,
        ):
            done.wait(timeout=len(data) / samplerate + 5.0)
    except Exception as exc:
        logger.warning("TTS playback failed on device %s: %s", device_selector, exc)
