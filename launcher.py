"""
RawriisSTT — bootstrap launcher.

Run this instead of main.py when launching from source.
It checks for missing packages and installs them automatically before starting the app.

For end-users on Windows, use the .exe built by PyInstaller instead — it bundles
everything and requires no Python installation at all.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import os


# ── Required packages ──────────────────────────────────────────────────────
# (import_name, pip_spec, optional)
# optional=True means we warn but don't abort if install fails (e.g. platform-specific)
PACKAGES: list[tuple[str, str, bool]] = [
    ("PyQt6",                          "PyQt6>=6.6.0",                          False),
    ("faster_whisper",                 "faster-whisper>=1.0.0",                 False),
    ("azure.cognitiveservices.speech", "azure-cognitiveservices-speech>=1.35.0", True),
    ("vosk",                           "vosk>=0.3.45",                          True),
    ("speech_recognition",             "SpeechRecognition>=3.10.0",             True),
    ("pythonosc",                      "python-osc>=1.8.0",                     False),
    ("sounddevice",                    "sounddevice>=0.4.6",                    False),
    ("pyaudio",                        "PyAudio>=0.2.14",                       False),
    ("webrtcvad",                      "webrtcvad>=2.0.10",                     False),
    ("numpy",                          "numpy>=1.24.0",                         False),
    ("platformdirs",                   "platformdirs>=4.0.0",                   False),
    ("huggingface_hub",                "huggingface_hub>=0.20.0",               False),
    ("soundfile",                      "soundfile>=0.12.0",                     False),
    ("keyboard",                       "keyboard>=0.13.5",                      False),
    ("pyttsx3",                        "pyttsx3>=2.90",                         True),
    ("boto3",                          "boto3>=1.34.0",                         True),
    ("openvr",                         "openvr>=1.26.701",                      True),
]


def _is_importable(name: str) -> bool:
    # Handle dotted names (e.g. azure.cognitiveservices.speech)
    top = name.split(".")[0]
    return importlib.util.find_spec(top) is not None


def _install(pip_spec: str) -> bool:
    """Run pip install for a single package. Returns True on success."""
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "--quiet", pip_spec],
        capture_output=True,
    )
    return result.returncode == 0


def bootstrap() -> None:
    missing_required: list[str] = []
    missing_optional: list[str] = []

    for import_name, pip_spec, optional in PACKAGES:
        if not _is_importable(import_name):
            if optional:
                missing_optional.append(pip_spec)
            else:
                missing_required.append(pip_spec)

    all_missing = missing_required + missing_optional
    if not all_missing:
        return  # nothing to do

    print("=" * 60)
    print("RawriisSTT — first-run setup")
    print("=" * 60)
    if missing_required:
        print(f"Installing {len(missing_required)} required package(s):")
        for p in missing_required:
            print(f"  • {p}")
    if missing_optional:
        print(f"Installing {len(missing_optional)} optional package(s):")
        for p in missing_optional:
            print(f"  • {p}")
    print()

    failed: list[str] = []
    for pip_spec in all_missing:
        print(f"  Installing {pip_spec}...", end=" ", flush=True)
        ok = _install(pip_spec)
        if ok:
            print("done")
        else:
            print("FAILED")
            failed.append(pip_spec)

    if failed:
        required_failed = [p for p in failed if p in missing_required]
        optional_failed = [p for p in failed if p in missing_optional]

        if optional_failed:
            print(f"\nWarning: optional package(s) could not be installed (features may be unavailable):")
            for p in optional_failed:
                print(f"  • {p}")

        if required_failed:
            print(f"\nError: required package(s) failed to install:")
            for p in required_failed:
                print(f"  • {p}")
            print("\nTry running manually:  pip install " + " ".join(required_failed))
            sys.exit(1)

    print("\nAll packages ready.\n")


def main() -> None:
    # Must bootstrap before importing anything from src/ that depends on these packages
    bootstrap()

    # Add our project root to path so 'src' is importable
    project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    from main import main as app_main
    app_main()


if __name__ == "__main__":
    main()
