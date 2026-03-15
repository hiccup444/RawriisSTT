from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class AudioDevice:
    index: int
    name: str
    max_input_channels: int
    max_output_channels: int
    default_sample_rate: float


_device_cache: tuple[List[AudioDevice], List[AudioDevice]] | None = None


def invalidate_device_cache() -> None:
    global _device_cache
    _device_cache = None


def enumerate_all_devices() -> tuple[List[AudioDevice], List[AudioDevice]]:
    """Return (input_devices, output_devices) from a single sd.query_devices() call.
    Result is cached; call invalidate_device_cache() to force a refresh.
    """
    global _device_cache
    if _device_cache is not None:
        return _device_cache
    try:
        import sounddevice as sd
        inputs: List[AudioDevice] = []
        outputs: List[AudioDevice] = []
        for idx, dev in enumerate(sd.query_devices()):
            entry = AudioDevice(
                index=idx,
                name=dev["name"],
                max_input_channels=dev["max_input_channels"],
                max_output_channels=dev["max_output_channels"],
                default_sample_rate=dev["default_samplerate"],
            )
            if dev["max_input_channels"] > 0:
                inputs.append(entry)
            if dev["max_output_channels"] > 0:
                outputs.append(entry)
        _device_cache = (inputs, outputs)
        return _device_cache
    except Exception:
        return [], []


def enumerate_input_devices() -> List[AudioDevice]:
    """Return all available audio input devices."""
    return enumerate_all_devices()[0]


def enumerate_output_devices() -> List[AudioDevice]:
    """Return all available audio output devices."""
    return enumerate_all_devices()[1]


def find_device_by_name(name: str) -> AudioDevice | None:
    """Return the first input device whose name contains *name* (case-insensitive)."""
    for dev in enumerate_input_devices():
        if name.lower() in dev.name.lower():
            return dev
    return None


def default_input_device() -> AudioDevice | None:
    try:
        import sounddevice as sd
        idx = sd.default.device[0]  # (input, output) tuple
        if idx is None or idx < 0:
            return None
        info = sd.query_devices(idx)
        return AudioDevice(
            index=idx,
            name=info["name"],
            max_input_channels=info["max_input_channels"],
            max_output_channels=info["max_output_channels"],
            default_sample_rate=info["default_samplerate"],
        )
    except Exception:
        return None
