# PyInstaller spec file — used for both Windows and Linux builds.
# Build with:  build\build_windows.bat   (Windows)
#              bash build/build_linux.sh  (Linux)
# Or manually: python -m PyInstaller build/windows.spec --distpath dist --workpath build/work --clean --noconfirm
#
# Output:  dist/RawriisSTT/RawriisSTT[.exe]  (folder distribution)

import sys
import importlib.util as _ilu
from pathlib import Path

ROOT = Path(SPECPATH).parent  # tts-project/our project/
IS_WINDOWS = sys.platform == "win32"

# Manually locate the openvr module so PyInstaller doesn't silently skip it.
# (When openvr_api.dll isn't on PATH at analysis time, PyInstaller's normal
# hiddenimports processing can fail to import the module and drop it.)
_ovr_spec = _ilu.find_spec("openvr")
_ovr_datas = []
if _ovr_spec and _ovr_spec.origin:
    _ovr_origin = Path(_ovr_spec.origin)
    if _ovr_origin.name == "__init__.py":
        # Package directory — copy the whole folder (includes bundled DLLs)
        _ovr_datas = [(str(_ovr_origin.parent), "openvr")]
    else:
        # Single-file module — copy the .py file into _internal root
        _ovr_datas = [(str(_ovr_origin), ".")]
    print(f"[spec] openvr found at {_ovr_origin}")
else:
    print("[spec] WARNING: openvr not installed — SteamVR input will be unavailable in the built exe")

# Resolve icon: Windows requires .ico; Linux accepts .png directly.
# If building on Windows, auto-convert RawriisIcon.png → RawriisIcon.ico using Pillow.
_png_icon = ROOT / "assets" / "RawriisIcon.png"
_ico_icon = ROOT / "assets" / "RawriisIcon.ico"

if IS_WINDOWS and _png_icon.exists():
    try:
        from PIL import Image
        img = Image.open(_png_icon)
        img.save(str(_ico_icon), format="ICO", sizes=[(256,256),(128,128),(64,64),(48,48),(32,32),(16,16)])
        print(f"[spec] Generated {_ico_icon.name} from {_png_icon.name}")
    except Exception as _e:
        print(f"[spec] Warning: could not convert PNG to ICO ({_e}); falling back to PNG")
        _ico_icon = _png_icon

_app_icon = str(_ico_icon if IS_WINDOWS else _png_icon) if _png_icon.exists() else None

block_cipher = None

# Platform-specific hiddenimports
_platform_imports = (
    [
        "pyttsx3.drivers.sapi5",
        "comtypes",
        "comtypes.client",
    ]
    if IS_WINDOWS else
    [
        "pyttsx3.drivers.espeak",
    ]
)

a = Analysis(
    [str(ROOT / "main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        # assets/ — icons (used by SteamVR vrmanifest) + PTT notification sounds
        (str(ROOT / "assets"), "assets"),
        # SteamVR action manifest, default bindings, and vrmanifest
        (str(ROOT / "steamvr"), "steamvr"),
    ] + _ovr_datas,
    hiddenimports=[
        # PyQt6
        "PyQt6.sip",
        # faster-whisper / ctranslate2
        "ctranslate2",
        "ctranslate2.specs",
        "tokenizers",
        "huggingface_hub",
        "huggingface_hub.file_download",
        # Audio
        "sounddevice",
        "soundfile",
        "pyaudio",
        "webrtcvad",
        # OSC
        "pythonosc",
        "pythonosc.udp_client",
        "pythonosc.osc_message_builder",
        # PTT / global hotkeys
        "keyboard",
        # TTS engines
        "pyttsx3",
        "pyttsx3.drivers",
        # Amazon Polly (optional — boto3 must be installed)
        "boto3",
        "boto3.session",
        "botocore",
        "botocore.session",
        # STT engines
        "azure.cognitiveservices.speech",
        "vosk",
        "speech_recognition",
        # Our modules — config
        "src.config.settings",
        "src.config.presets",
        # Our modules — audio
        "src.audio.devices",
        "src.audio.sound_player",
        # Our modules — OSC
        "src.osc.vrchat_osc",
        # Our modules — STT
        "src.stt.base",
        "src.stt.whisper_stt",
        "src.stt.whisper_models",
        "src.stt._whisper_proc",
        "src.stt.azure_stt",
        "src.stt.vosk_stt",
        "src.stt.vosk_models",
        "src.stt.system_stt",
        "src.stt.ptt_handler",
        # Our modules — TTS
        "src.tts.system_tts",
        "src.tts.elevenlabs_tts",
        "src.tts.espeak_tts",
        "src.tts.polly_tts",
        # Our modules — GUI
        "src.gui.main_window",
        "src.gui.settings_dialog",
        "src.gui.widgets",
        # Our modules — SteamVR input
        "src.input.steamvr_input",
        # OpenVR Python wrapper (runtime DLL is provided by SteamVR installation)
        "openvr",
    ] + _platform_imports,
    hookspath=[str(ROOT / "build" / "hooks")],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Trim unused stdlib
        "tkinter",
        "matplotlib",
        "scipy",
        "PIL",
        "cv2",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="RawriisSTT",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    uac_admin=False,        # Do NOT elevate — SteamVR runs as normal user and OpenVR can't cross privilege boundaries
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=_app_icon,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="RawriisSTT",
)
